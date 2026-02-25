from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QHeaderView, QLabel, QComboBox,
                               QPushButton, QLineEdit, QMessageBox, QDateEdit,
                               QTableWidgetSelectionRange)
from PySide6.QtCore import Qt, QDate, QRect
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen
from datetime import datetime
from attendance_processor import AttendanceCalculator
import sqlite3

class AttendanceDashboard(QWidget):
    def __init__(self, employee_manager=None):
        super().__init__()
        self.calculator = AttendanceCalculator()
        self.employee_manager = employee_manager
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.selected_date = QDate.currentDate()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title_label = QLabel("Attendance Dashboard")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Controls
        controls_layout = QHBoxLayout()
        layout.addLayout(controls_layout)

        # View toggle
        controls_layout.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Monthly Summary", "Daily Details"])
        self.view_combo.currentTextChanged.connect(self.on_view_changed)
        controls_layout.addWidget(self.view_combo)

        # Date controls (hidden by default, shown for daily view)
        self.prev_day_btn = QPushButton("◀ Prev Day")
        self.prev_day_btn.setVisible(False)
        self.prev_day_btn.clicked.connect(self.go_to_previous_day)
        controls_layout.addWidget(self.prev_day_btn)

        self.date_label = QLabel("Date:")
        self.date_label.setVisible(False)
        controls_layout.addWidget(self.date_label)

        self.date_display = QLabel("")
        self.date_display.setVisible(False)
        self.date_display.setStyleSheet("font-weight: bold; min-width: 150px;")
        controls_layout.addWidget(self.date_display)

        self.next_day_btn = QPushButton("Next Day ▶")
        self.next_day_btn.setVisible(False)
        self.next_day_btn.clicked.connect(self.go_to_next_day)
        controls_layout.addWidget(self.next_day_btn)

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(self.selected_date)
        self.date_picker.dateChanged.connect(self.on_date_changed)
        self.date_picker.setVisible(False)
        controls_layout.addWidget(self.date_picker)

        # Month selector (for monthly view)
        self.month_label = QLabel("Month:")
        self.month_selector = QComboBox()
        self.month_selector.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        self.month_selector.setCurrentIndex(self.current_month - 1)
        self.month_selector.currentIndexChanged.connect(self.on_month_changed)

        # Year selector
        self.year_label = QLabel("Year:")
        self.year_selector = QComboBox()
        for year in range(2024, 2031):
            self.year_selector.addItem(str(year), year)
        self.year_selector.setCurrentText(str(self.current_year))
        self.year_selector.currentTextChanged.connect(self.on_year_changed)

        controls_layout.addWidget(self.month_label)
        controls_layout.addWidget(self.month_selector)
        controls_layout.addWidget(self.year_label)
        controls_layout.addWidget(self.year_selector)

        controls_layout.addStretch()

        self.lock_button = QPushButton("🔒 Lock Month")
        self.lock_button.clicked.connect(self.toggle_month_lock)
        controls_layout.addWidget(self.lock_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_data)
        controls_layout.addWidget(self.refresh_button)

        # Summary stats
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        layout.addWidget(self.summary_label)

        # Table
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSortingEnabled(True)
        layout.addWidget(self.data_table)

        # Start in monthly view
        self.on_view_changed("Monthly Summary")

    def on_view_changed(self, view_type):
        """Show/hide controls based on view type"""
        is_daily = (view_type == "Daily Details")

        # Toggle date/month controls visibility
        self.prev_day_btn.setVisible(is_daily)
        self.date_label.setVisible(is_daily)
        self.date_display.setVisible(is_daily)
        self.next_day_btn.setVisible(is_daily)
        self.date_picker.setVisible(is_daily)

        self.month_label.setVisible(not is_daily)
        self.month_selector.setVisible(not is_daily)
        self.year_label.setVisible(not is_daily)
        self.year_selector.setVisible(not is_daily)

        self.load_data()

    def go_to_previous_day(self):
        """Navigate to previous day"""
        self.selected_date = self.selected_date.addDays(-1)
        self.load_data()

    def go_to_next_day(self):
        """Navigate to next day"""
        self.selected_date = self.selected_date.addDays(1)
        self.load_data()

    def on_date_changed(self, date):
        """Handle date picker change"""
        self.selected_date = date
        self.load_data()

    def on_month_changed(self, index):
        self.current_month = index + 1
        self.load_data()
        if self.view_combo.currentText() == "Monthly Summary":
            self.check_month_locked()

    def on_year_changed(self, text):
        self.current_year = int(text)
        self.load_data()
        if self.view_combo.currentText() == "Monthly Summary":
            self.check_month_locked()

    def load_data(self):
        # Refresh employees first to ensure we have the latest list
        self._refresh_employees_if_needed()

        view_type = self.view_combo.currentText()

        if view_type == "Monthly Summary":
            self.load_monthly_summary()
            self.check_month_locked()
        else:
            self.load_daily_details()

    def _refresh_employees_if_needed(self):
        """Check if employees exist, if not, auto-import from raw logs"""
        import sqlite3

        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            # Check if any active employees exist
            cursor.execute('SELECT COUNT(*) FROM employees WHERE is_active = 1')
            employee_count = cursor.fetchone()[0]
            conn.close()

            # If no active employees and we have access to employee_manager, auto-import
            if employee_count == 0 and self.employee_manager:
                # Check if there are raw logs to import from
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM raw_logs WHERE hidden = 0')
                log_count = cursor.fetchone()[0]
                conn.close()

                if log_count > 0:
                    # Auto-import employees from logs
                    self.employee_manager.auto_import_employees()
        except Exception as e:
            # If refresh fails, continue anyway (don't block dashboard)
            pass

    def refresh_employees(self):
        """Explicitly refresh employee list from employee_manager"""
        if self.employee_manager:
            self.employee_manager.load_employees()

    def load_monthly_summary(self):
        """Show monthly summary per employee"""
        # Clear any existing cell widgets from previous view
        self._clear_table_widgets()

        summaries = self.calculator.get_all_employees_summary(
            self.current_year, self.current_month
        )

        if not summaries:
            self.data_table.setRowCount(0)
            self.summary_label.setText("No data for selected period")
            return

        # Setup table columns with Holidays column
        self.data_table.setColumnCount(11)
        self.data_table.setHorizontalHeaderLabels([
            "En No", "Name", "Present", "Absent", "Holidays",
            "Half-Day", "Late", "Missing Checkout", "Total Hours", "Working Days", "Details"
        ])

        self.data_table.setRowCount(len(summaries))

        total_present = 0
        total_absent = 0
        total_hours = 0

        for row_idx, summary in enumerate(summaries):
            # En No
            self.data_table.setItem(row_idx, 0, self._create_item(summary['en_no']))

            # Name
            self.data_table.setItem(row_idx, 1, self._create_item(summary['name']))

            # Present (green bold text)
            present_item = self._create_item(str(summary['days_present']))
            if summary['days_present'] > 0:
                present_item.setForeground(QColor(34, 139, 34))  # Forest green
                font = present_item.font()
                font.setBold(True)
                present_item.setFont(font)
            self.data_table.setItem(row_idx, 2, present_item)

            # Absent (dark red bold text)
            absent_item = self._create_item(str(summary['days_absent']))
            if summary['days_absent'] > 0:
                absent_item.setForeground(QColor(178, 34, 34))  # Fire brick red
                font = absent_item.font()
                font.setBold(True)
                absent_item.setFont(font)
            self.data_table.setItem(row_idx, 3, absent_item)

            # Holidays (blue bold text)
            holiday_item = self._create_item(str(summary.get('days_holiday', 0)))
            if summary.get('days_holiday', 0) > 0:
                holiday_item.setForeground(QColor(65, 105, 225))  # Royal blue
                font = holiday_item.font()
                font.setBold(True)
                holiday_item.setFont(font)
            self.data_table.setItem(row_idx, 4, holiday_item)

            # Half-day (orange bold text)
            half_item = self._create_item(str(summary['days_half_day']))
            if summary['days_half_day'] > 0:
                half_item.setForeground(QColor(218, 165, 32))  # Golden rod
                font = half_item.font()
                font.setBold(True)
                half_item.setFont(font)
            self.data_table.setItem(row_idx, 5, half_item)

            # Late (red bold text if excessive)
            late_item = self._create_item(str(summary['days_late']))
            if summary['days_late'] > 2:
                late_item.setForeground(QColor(220, 20, 60))  # Crimson
                font = late_item.font()
                font.setBold(True)
                late_item.setFont(font)
            self.data_table.setItem(row_idx, 6, late_item)

            # Missing Checkout (red bold text if any)
            mc_item = self._create_item(str(summary['days_missing_checkout']))
            if summary['days_missing_checkout'] > 0:
                mc_item.setForeground(QColor(220, 20, 60))  # Crimson
                font = mc_item.font()
                font.setBold(True)
                mc_item.setFont(font)
            self.data_table.setItem(row_idx, 7, mc_item)

            # Total Hours
            self.data_table.setItem(row_idx, 8, self._create_item(f"{summary['total_hours']:.1f}"))

            # Working Days
            self.data_table.setItem(row_idx, 9, self._create_item(str(summary['total_days'])))

            # Details button
            details_btn = QPushButton("📋 View")
            details_btn.clicked.connect(lambda checked, en_no=summary['en_no'], name=summary['name']:
                                        self.show_monthly_details(en_no, name))
            self.data_table.setCellWidget(row_idx, 10, details_btn)

            # Totals for summary
            total_present += summary['days_present']
            total_absent += summary['days_absent']
            total_hours += summary['total_hours']

        # Resize columns
        header = self.data_table.horizontalHeader()
        for col in range(11):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        # Update summary label
        month_name = self.month_selector.currentText()
        self.summary_label.setText(
            f"{month_name} {self.current_year} | "
            f"Employees: {len(summaries)} | "
            f"Total Present: {total_present} | "
            f"Total Absent: {total_absent} | "
            f"Total Hours: {total_hours:.1f}"
        )

    def load_daily_details(self):
        """Show attendance for a single selected day"""
        # Clear any existing cell widgets from previous view
        self._clear_table_widgets()

        date_str = self.selected_date.toString("yyyy-MM-dd")

        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()

        cursor.execute('SELECT en_no, name FROM employees WHERE is_active = 1 ORDER BY en_no')
        employees = cursor.fetchall()
        conn.close()

        daily_records = []

        # Get attendance for each employee on selected date
        for en_no, name in employees:
            record = self.calculator.calculate_day(en_no, date_str)
            if record:
                record['name'] = name
                daily_records.append(record)
            else:
                # Employee with no logs on this day
                daily_records.append({
                    'en_no': en_no,
                    'name': name,
                    'date': date_str,
                    'first_scan': '-',
                    'last_scan': '-',
                    'total_hours': 0.0,
                    'status': 'Absent',
                    'is_late': 0,
                    'missing_checkout': 0,
                    'scan_count': 0
                })

        # Sort by employee number
        daily_records.sort(key=lambda x: x['en_no'])

        # Find earliest and latest times for the day (for timeline scale)
        earliest_time = "08:00"
        latest_time = "20:00"

        for record in daily_records:
            if record['first_scan'] != '-':
                try:
                    scan_time = datetime.strptime(record['first_scan'], "%Y-%m-%d %H:%M:%S")
                    time_str = scan_time.strftime("%H:%M")
                    if time_str < earliest_time:
                        earliest_time = time_str
                except:
                    pass
            if record['last_scan'] != '-':
                try:
                    scan_time = datetime.strptime(record['last_scan'], "%Y-%m-%d %H:%M:%S")
                    time_str = scan_time.strftime("%H:%M")
                    if time_str > latest_time:
                        latest_time = time_str
                except:
                    pass

        # Setup table WITH Timeline column
        self.data_table.setColumnCount(8)
        self.data_table.setHorizontalHeaderLabels([
            "En No", "Name", "Status", "Timeline", "First Scan", "Last Scan", "Hours", "Flags"
        ])

        self.data_table.setRowCount(len(daily_records))

        present_count = 0
        absent_count = 0
        late_count = 0

        for row_idx, record in enumerate(daily_records):
            # En No
            self.data_table.setItem(row_idx, 0, self._create_item(record['en_no']))

            # Name
            self.data_table.setItem(row_idx, 1, self._create_item(record['name']))

            # Status with colored bold text
            status = record['status']
            status_item = self._create_item(status)

            if status == 'Present':
                status_item.setForeground(QColor(34, 139, 34))  # Forest green
                present_count += 1
            elif status == 'Absent':
                status_item.setForeground(QColor(178, 34, 34))  # Fire brick red
                absent_count += 1
            elif status == 'Half-day':
                status_item.setForeground(QColor(218, 165, 32))  # Golden rod
                present_count += 1
            elif status == 'Holiday':
                status_item.setForeground(QColor(147, 112, 219))  # Medium purple

            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            self.data_table.setItem(row_idx, 2, status_item)

            # Timeline visualization
            timeline = TimelineWidget(
                record['first_scan'] if record['first_scan'] and record['first_scan'] != '-' else None,
                record['last_scan'] if record['last_scan'] and record['last_scan'] != '-' else None,
                earliest_time,
                latest_time
            )
            self.data_table.setCellWidget(row_idx, 3, timeline)

            # First Scan
            first_scan = record['first_scan']
            if first_scan and first_scan != '-' and isinstance(first_scan, str):
                first_scan = first_scan.split(' ')[1]  # Just time
            elif first_scan == '-' or not first_scan:
                first_scan = '-'
            self.data_table.setItem(row_idx, 4, self._create_item(first_scan))

            # Last Scan
            last_scan = record['last_scan']
            if last_scan and last_scan != '-' and isinstance(last_scan, str):
                last_scan = last_scan.split(' ')[1]  # Just time
            elif last_scan == '-' or not last_scan:
                last_scan = '-'
            self.data_table.setItem(row_idx, 5, self._create_item(last_scan))

            # Hours (blue bold if > 0)
            hours_item = self._create_item(f"{record['total_hours']:.1f}")
            if record['total_hours'] > 0:
                hours_item.setForeground(QColor(0, 102, 204))  # Blue
                font = hours_item.font()
                font.setBold(True)
                hours_item.setFont(font)
            self.data_table.setItem(row_idx, 6, hours_item)

            # Flags
            flags = []
            if record['is_late']:
                flags.append("⏰ LATE")
                late_count += 1
            if record['missing_checkout']:
                flags.append("❌ NO CHECKOUT")

            flags_text = ' | '.join(flags) if flags else '✓ OK'

            flags_item = self._create_item(flags_text)
            if flags:
                flags_item.setForeground(QColor(178, 34, 34))  # Fire brick red
                font = flags_item.font()
                font.setBold(True)
                flags_item.setFont(font)
            else:
                flags_item.setForeground(QColor(34, 139, 34))  # Forest green

            self.data_table.setItem(row_idx, 7, flags_item)

        # Resize columns
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name stretches
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Timeline fixed
        header.resizeSection(3, 200)  # Timeline width
        for col in [0, 2, 4, 5, 6, 7]:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        # Update date display label (do this first, before any potential errors)
        self.date_display.setText(self.selected_date.toString("dddd, MMMM d, yyyy"))

        # Update summary
        date_display = self.selected_date.toString("dddd, MMMM d, yyyy")
        self.summary_label.setText(
            f"{date_display} | "
            f"Present: {present_count} | "
            f"Absent: {absent_count} | "
            f"Late: {late_count}"
        )

    def toggle_month_lock(self):
        """Lock or unlock the current selected month"""
        month_key = f"{self.current_year}-{self.current_month:02d}"

        try:
            # Check if already locked
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            cursor.execute('SELECT locked_at FROM month_locks WHERE year = ? AND month = ?',
                          (self.current_year, self.current_month))
            lock_record = cursor.fetchone()
            conn.close()

            if lock_record:
                # Unlock
                reply = QMessageBox.question(
                    self, "Unlock Month",
                    f"Unlock {self.month_selector.currentText()} {self.current_year}?\n\n"
                    "This will allow edits to this month's data.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    conn = sqlite3.connect('attendance.db')
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM month_locks WHERE year = ? AND month = ?',
                                  (self.current_year, self.current_month))
                    conn.commit()
                    conn.close()

                    self.update_lock_button(False)
                    QMessageBox.information(self, "Unlocked", "Month has been unlocked.")
            else:
                # Lock
                reply = QMessageBox.question(
                    self, "Lock Month",
                    f"Lock {self.month_selector.currentText()} {self.current_year}?\n\n"
                    "This will:\n"
                    "• Copy data to locked database\n"
                    "• Prevent edits to this month\n"
                    "• Protect data from 'Clear Database'\n\n"
                    "Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.lock_month()
                    self.update_lock_button(True)
                    QMessageBox.information(self, "Locked", "Month has been locked successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle lock: {str(e)}")

    def lock_month(self):
        """Copy current month data to locked database"""
        import shutil
        from datetime import datetime

        # Get all active employees' attendance data for this month
        summaries = self.calculator.get_all_employees_summary(self.current_year, self.current_month)

        # Copy to locked database
        locked_db_path = 'locked_attendance.db'
        locked_conn = sqlite3.connect(locked_db_path)
        locked_cursor = locked_conn.cursor()

        # Create tables if not exist
        locked_cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_summaries (
                year INTEGER,
                month INTEGER,
                en_no TEXT,
                name TEXT,
                days_present INTEGER,
                days_absent INTEGER,
                days_half_day INTEGER,
                days_late INTEGER,
                days_missing_checkout INTEGER,
                total_hours REAL,
                total_days INTEGER,
                locked_at TEXT,
                PRIMARY KEY (year, month, en_no)
            )
        ''')

        locked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert data
        for summary in summaries:
            try:
                locked_cursor.execute('''
                    INSERT OR REPLACE INTO monthly_summaries
                    (year, month, en_no, name, days_present, days_absent, days_half_day,
                     days_late, days_missing_checkout, total_hours, total_days, locked_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.current_year, self.current_month, summary['en_no'], summary['name'],
                    summary['days_present'], summary['days_absent'], summary['days_half_day'],
                    summary['days_late'], summary['days_missing_checkout'], summary['total_hours'],
                    summary['total_days'], locked_at
                ))
            except Exception as e:
                print(f"Error inserting {summary['en_no']}: {e}")

        locked_conn.commit()
        locked_conn.close()

        # Mark month as locked in main database
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO month_locks (year, month, locked_at)
            VALUES (?, ?, ?)
        ''', (self.current_year, self.current_month, locked_at))
        conn.commit()
        conn.close()

    def update_lock_button(self, is_locked):
        """Update lock button appearance and text"""
        if is_locked:
            self.lock_button.setText("🔓 Unlock Month")
            self.lock_button.setStyleSheet("background-color: #e8f5e9; color: #2e7d32;")
        else:
            self.lock_button.setText("🔒 Lock Month")
            self.lock_button.setStyleSheet("")

    def check_month_locked(self):
        """Check if current month is locked and update UI"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT locked_at FROM month_locks WHERE year = ? AND month = ?',
                          (self.current_year, self.current_month))
            is_locked = cursor.fetchone() is not None
            conn.close()

            self.update_lock_button(is_locked)
            return is_locked
        except:
            return False

    def _clear_table_widgets(self):
        """Clear all cell widgets from the table"""
        for row in range(self.data_table.rowCount()):
            for col in range(self.data_table.columnCount()):
                widget = self.data_table.cellWidget(row, col)
                if widget:
                    self.data_table.removeCellWidget(row, col)
                    widget.deleteLater()

    def show_monthly_details(self, en_no, name):
        """Show dialog with detailed breakdown of flags for an employee's month"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QScrollArea

        # Get all daily records for this employee for the month
        daily_records = self.calculator.calculate_month(
            en_no, self.current_year, self.current_month
        )

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Attendance Details - {name} ({en_no})")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Title
        title = QLabel(f"<h2>{name} ({en_no})</h2>")
        title.setText(f"<b>{name}</b> ({en_no}) - {self.month_selector.currentText()} {self.current_year}")
        layout.addWidget(title)

        # Group by flag type
        absent_days = []
        late_days = []
        missing_checkout_days = []
        half_days = []
        present_days = []

        for record in daily_records:
            date_str = record['date']
            day_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A, %B %d")

            if record['status'] == 'Absent':
                absent_days.append(f"  • {day_name}")
            elif record['status'] == 'Half-day':
                half_days.append(f"  • {day_name} ({record['total_hours']:.1f} hrs)")

            if record['is_late']:
                late_days.append(f"  • {day_name} (First scan: {record['first_scan'].split(' ')[1]})")

            if record['missing_checkout']:
                missing_checkout_days.append(f"  • {day_name}")

            if record['status'] == 'Present':
                present_days.append(f"  • {day_name}: {record['total_hours']:.1f} hrs ({record['first_scan'].split(' ')[1]} - {record['last_scan'].split(' ')[1]})")

        # Build details text
        details = []

        if absent_days:
            details.append(f"<h3 style='color: #b22222;'>❌ Absent Days ({len(absent_days)})</h3>")
            details.append("<pre>" + "\n".join(absent_days) + "</pre>")

        if half_days:
            details.append(f"<h3 style='color: #daa520;'>⚠️ Half-Days ({len(half_days)})</h3>")
            details.append("<pre>" + "\n".join(half_days) + "</pre>")

        if late_days:
            details.append(f"<h3 style='color: #dc143c;'>⏰ Late Arrivals ({len(late_days)})</h3>")
            details.append("<pre>" + "\n".join(late_days) + "</pre>")

        if missing_checkout_days:
            details.append(f"<h3 style='color: #dc143c;'>❌ Missing Checkout ({len(missing_checkout_days)})</h3>")
            details.append("<pre>" + "\n".join(missing_checkout_days) + "</pre>")

        if present_days:
            details.append(f"<h3 style='color: #228b22;'>✓ Present Days ({len(present_days)})</h3>")
            details.append("<pre>" + "\n".join(present_days[:10]) + ("..." if len(present_days) > 10 else "") + "</pre>")

        if not details:
            details.append("<p><i>No attendance data for this month</i></p>")

        # Create text area with HTML
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setHtml("<br>".join(details))
        layout.addWidget(text_area)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _create_item(self, text):
        """Helper to create non-editable table item"""
        item = QTableWidgetItem(str(text))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item


class TimelineWidget(QWidget):
    """Custom widget that draws a timeline bar showing employee presence"""

    def __init__(self, first_scan, last_scan, day_start, day_end):
        super().__init__()
        self.first_scan = first_scan
        self.last_scan = last_scan
        self.day_start = day_start    # Earliest time on timeline
        self.day_end = day_end        # Latest time on timeline
        self.setMinimumHeight(30)
        self.setMaximumHeight(40)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(250, 250, 250))

        if self.first_scan == '-' or self.last_scan == '-':
            # No data - draw empty bar
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Data")
            return

        # Calculate time positions
        try:
            first_time = datetime.strptime(self.first_scan, "%Y-%m-%d %H:%M:%S")
            last_time = datetime.strptime(self.last_scan, "%Y-%m-%d %H:%M:%S")

            # Parse day boundaries (use same date as scans)
            scan_date = first_time.date()
            start_datetime = datetime.combine(scan_date, datetime.strptime(self.day_start, "%H:%M").time())
            end_datetime = datetime.combine(scan_date, datetime.strptime(self.day_end, "%H:%M").time())

            # Calculate pixel positions
            total_minutes = (end_datetime - start_datetime).total_seconds() / 60
            first_minutes = (first_time - start_datetime).total_seconds() / 60
            last_minutes = (last_time - start_datetime).total_seconds() / 60

            width = self.width()
            left_margin = 5
            right_margin = 5
            bar_width = width - left_margin - right_margin

            x1 = left_margin + (first_minutes / total_minutes) * bar_width
            x2 = left_margin + (last_minutes / total_minutes) * bar_width

            # Clamp values
            x1 = max(left_margin, min(width - right_margin, x1))
            x2 = max(left_margin, min(width - right_margin, x2))

            # Draw timeline background
            timeline_rect = QRect(left_margin, 18, bar_width, 6)
            painter.fillRect(timeline_rect, QColor(230, 230, 230))

            # Draw presence bar (green)
            if x2 > x1:
                presence_rect = QRect(int(x1), 15, int(x2 - x1), 12)
                painter.fillRect(presence_rect, QColor(76, 175, 80))

                # Draw start marker
                painter.setBrush(QColor(56, 142, 60))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(x1) - 3, 18, 6, 6)

                # Draw end marker
                painter.setBrush(QColor(56, 142, 60))
                painter.drawEllipse(int(x2) - 3, 18, 6, 6)

            # Draw time labels
            painter.setPen(QColor(100, 100, 100))
            painter.setFont(QFont("Arial", 7))

            # First scan time
            first_str = first_time.strftime("%H:%M")
            painter.drawText(int(x1), 12, first_str)

            # Last scan time
            last_str = last_time.strftime("%H:%M")
            painter.drawText(int(x2) - 25, 30, last_str)

        except Exception as e:
            # Error drawing - show message
            painter.setPen(QColor(200, 100, 100))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Error")
