from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QHeaderView, QLabel, QPushButton,
                               QSpinBox, QTimeEdit, QComboBox, QLineEdit, QMessageBox,
                               QDialog, QFormLayout, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sqlite3
from datetime import datetime

class EmployeeManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_employees()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title_label = QLabel("Employee Management")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Controls
        controls_layout = QHBoxLayout()
        layout.addLayout(controls_layout)

        self.auto_import_btn = QPushButton("Auto-Import from Logs")
        self.auto_import_btn.clicked.connect(self.auto_import_employees)
        controls_layout.addWidget(self.auto_import_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_employees)
        controls_layout.addWidget(self.refresh_btn)

        controls_layout.addStretch()

        # Employee table
        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(10)
        self.employees_table.setHorizontalHeaderLabels([
            "En No", "Name", "Start Time", "End Time", "Grace (min)", "Min Hours", "Status", "Lock", "Toggle", "Configure"
        ])

        header = self.employees_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.employees_table.setAlternatingRowColors(True)
        self.employees_table.setSortingEnabled(True)
        layout.addWidget(self.employees_table)

        # Stats
        self.stats_label = QLabel("Total Employees: 0")
        self.stats_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.stats_label)

    def load_employees(self):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            query = '''
                SELECT e.en_no, e.name, s.start_time, s.end_time,
                       s.grace_period, s.minimum_hours, e.is_active, e.is_locked, e.id
                FROM employees e
                LEFT JOIN shifts s ON e.shift_id = s.id
                ORDER BY e.is_locked ASC, e.is_active DESC, CAST(e.en_no AS INTEGER)
            '''

            cursor.execute(query)
            employees = cursor.fetchall()

            self.employees_table.setRowCount(len(employees))

            for row_idx, employee in enumerate(employees):
                for col_idx, value in enumerate(employee):
                    if col_idx == 6:  # Status column
                        status_text = "Active" if value else "Inactive"
                        item = QTableWidgetItem(status_text)
                    else:
                        item = QTableWidgetItem(str(value) if value else "")

                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.employees_table.setItem(row_idx, col_idx, item)

                # Add lock button
                employee_id = employee[8]
                is_locked = employee[7]
                en_no = employee[0]

                lock_btn = QPushButton("🔓" if is_locked else "🔒")
                lock_btn.setStyleSheet("background-color: #fff3cd;" if is_locked else "")
                lock_btn.setToolTip("Lock employee configuration")
                lock_btn.clicked.connect(lambda checked, emp_id=employee_id, en_no=en_no:
                                        self.toggle_employee_lock(emp_id, en_no))
                self.employees_table.setCellWidget(row_idx, 7, lock_btn)

                # Add toggle button for active/inactive
                is_active = employee[6]

                toggle_btn = QPushButton("Deactivate" if is_active else "Activate")
                if is_active:
                    toggle_btn.setStyleSheet("background-color: #fee; color: #c00;")
                else:
                    toggle_btn.setStyleSheet("background-color: #efe; color: #060;")

                toggle_btn.clicked.connect(lambda checked, emp_id=employee_id, en_no=en_no:
                                           self.toggle_employee_status(emp_id, en_no))
                self.employees_table.setCellWidget(row_idx, 8, toggle_btn)

                # Add configure button
                configure_btn = QPushButton("Configure")
                if is_locked:
                    configure_btn.setEnabled(False)
                    configure_btn.setText("Locked")
                    configure_btn.setStyleSheet("color: #999;")
                configure_btn.clicked.connect(lambda checked, en_no=en_no: self.configure_employee(en_no))
                self.employees_table.setCellWidget(row_idx, 9, configure_btn)

            conn.close()

            self.stats_label.setText(f"Total Employees: {len(employees)}")

        except Exception as e:
            self.stats_label.setText(f"Error: {str(e)}")

    def auto_import_employees(self):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            # Get unique employees from raw logs
            cursor.execute('''
                SELECT DISTINCT en_no, name, gm_no
                FROM raw_logs
                WHERE en_no IS NOT NULL AND en_no != ''
                ORDER BY name
            ''')

            raw_employees = cursor.fetchall()

            # Get existing employees
            cursor.execute('SELECT en_no FROM employees')
            existing_en_nos = set(row[0] for row in cursor.fetchall())

            imported_count = 0
            skipped_count = 0

            # Get default shift ID
            cursor.execute('SELECT id FROM shifts WHERE name = ?', ('Default Shift',))
            default_shift = cursor.fetchone()
            shift_id = default_shift[0] if default_shift else None

            for en_no, name, gm_no in raw_employees:
                if en_no not in existing_en_nos:
                    try:
                        cursor.execute('''
                            INSERT INTO employees (en_no, name, gm_no, shift_id)
                            VALUES (?, ?, ?, ?)
                        ''', (en_no, name, gm_no, shift_id))
                        imported_count += 1
                    except Exception as e:
                        skipped_count += 1
                else:
                    skipped_count += 1

            conn.commit()
            conn.close()

            self.load_employees()

            message = f"Auto-import complete:\n• Imported: {imported_count} new employees\n• Skipped: {skipped_count} existing employees"
            QMessageBox.information(self, "Import Complete", message)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import employees: {str(e)}")

    def toggle_employee_status(self, employee_id, en_no):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            cursor.execute('SELECT is_active FROM employees WHERE id = ?', (employee_id,))
            result = cursor.fetchone()

            if result:
                current_status = result[0]
                new_status = 0 if current_status else 1

                cursor.execute('UPDATE employees SET is_active = ? WHERE id = ?', (new_status, employee_id))
                conn.commit()
                conn.close()

                self.load_employees()

                status_text = "activated" if new_status else "deactivated"
                QMessageBox.information(self, "Success", f"Employee {en_no} has been {status_text}.")
            else:
                conn.close()
                QMessageBox.warning(self, "Error", "Employee not found.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle status: {str(e)}")

    def toggle_employee_lock(self, employee_id, en_no):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            cursor.execute('SELECT is_locked FROM employees WHERE id = ?', (employee_id,))
            result = cursor.fetchone()

            if result:
                current_lock = result[0]
                new_lock = 1 if current_lock == 0 else 0

                if new_lock:
                    reply = QMessageBox.question(
                        self, "Lock Employee",
                        f"Lock employee {en_no}?\n\n"
                        "This will:\n"
                        "• Prevent configuration changes\n"
                        "• Keep shift settings safe\n\n"
                        "Continue?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )

                    if reply != QMessageBox.StandardButton.Yes:
                        conn.close()
                        return

                cursor.execute('UPDATE employees SET is_locked = ? WHERE id = ?', (new_lock, employee_id))
                conn.commit()
                conn.close()

                self.load_employees()

                status_text = "locked" if new_lock else "unlocked"
                QMessageBox.information(self, "Success", f"Employee {en_no} has been {status_text}.")
            else:
                conn.close()
                QMessageBox.warning(self, "Error", "Employee not found.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle lock: {str(e)}")

    def configure_employee(self, en_no):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT e.en_no, e.name, e.shift_id, s.start_time, s.end_time,
                       s.grace_period, s.minimum_hours, s.maximum_hours, e.work_schedule
                FROM employees e
                LEFT JOIN shifts s ON e.shift_id = s.id
                WHERE e.en_no = ?
            ''', (en_no,))

            employee_data = cursor.fetchone()
            conn.close()

            if employee_data:
                dialog = EmployeeConfigDialog(employee_data, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.load_employees()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure employee: {str(e)}")

class EmployeeConfigDialog(QDialog):
    def __init__(self, employee_data, parent=None):
        super().__init__(parent)
        self.employee_data = employee_data
        self.en_no = employee_data[0]
        self.parent_window = parent
        self.setWindowTitle(f"Configure Employee - {employee_data[1]}")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Employee info
        info_label = QLabel(f"Employee: {self.employee_data[1]} ({self.employee_data[0]})")
        info_font = QFont()
        info_font.setBold(True)
        info_label.setFont(info_font)
        layout.addWidget(info_label)

        # Form layout
        form_layout = QFormLayout()
        layout.addLayout(form_layout)

        # Start time
        self.start_time = QTimeEdit()
        if self.employee_data[3]:
            self.start_time.setTime(datetime.strptime(self.employee_data[3], "%H:%M").time())
        form_layout.addRow("Shift Start Time:", self.start_time)

        # End time
        self.end_time = QTimeEdit()
        if self.employee_data[4]:
            self.end_time.setTime(datetime.strptime(self.employee_data[4], "%H:%M").time())
        form_layout.addRow("Shift End Time:", self.end_time)

        # Grace period
        self.grace_period = QSpinBox()
        self.grace_period.setRange(0, 60)
        self.grace_period.setValue(self.employee_data[5] if self.employee_data[5] else 15)
        self.grace_period.setSuffix(" min")
        form_layout.addRow("Grace Period:", self.grace_period)

        # Minimum hours
        self.min_hours = QSpinBox()
        self.min_hours.setRange(1, 12)
        self.min_hours.setValue(int(self.employee_data[6] if self.employee_data[6] else 4))
        self.min_hours.setSuffix(" hours")
        form_layout.addRow("Minimum Hours:", self.min_hours)

        # Maximum hours
        self.max_hours = QSpinBox()
        self.max_hours.setRange(4, 24)
        self.max_hours.setValue(int(self.employee_data[7] if self.employee_data[7] else 12))
        self.max_hours.setSuffix(" hours")
        form_layout.addRow("Maximum Hours:", self.max_hours)

        # Work Schedule
        schedule_label = QLabel("Work Schedule (select working days):")
        schedule_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(schedule_label)

        schedule_layout = QHBoxLayout()
        layout.addLayout(schedule_layout)

        self.day_checkboxes = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # Get current schedule
        current_schedule = self.employee_data[8] if len(self.employee_data) > 8 else '1111110'
        if not current_schedule:
            current_schedule = '1111110'

        for idx, day in enumerate(days):
            checkbox = QCheckBox(day)
            checkbox.setChecked(current_schedule[idx] == '1')
            self.day_checkboxes[idx] = checkbox
            schedule_layout.addWidget(checkbox)

        layout.addStretch()

        # Buttons
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_configuration)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

    def save_configuration(self):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            start_time = self.start_time.time().toString("HH:mm")
            end_time = self.end_time.time().toString("HH:mm")
            grace_period = self.grace_period.value()
            min_hours = float(self.min_hours.value())
            max_hours = float(self.max_hours.value())

            # Build work schedule string (7 chars, one for each day Mon-Sun)
            schedule = ''.join(['1' if self.day_checkboxes[idx].isChecked() else '0'
                               for idx in range(7)])

            # Create or update shift for this employee
            shift_name = f"{self.en_no}_Shift"

            cursor.execute('''
                INSERT OR REPLACE INTO shifts (name, start_time, end_time, grace_period, minimum_hours, maximum_hours)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (shift_name, start_time, end_time, grace_period, min_hours, max_hours))

            # Get shift ID
            cursor.execute('SELECT id FROM shifts WHERE name = ?', (shift_name,))
            shift_id = cursor.fetchone()[0]

            # Update employee with new shift and work schedule
            cursor.execute('''
                UPDATE employees SET shift_id = ?, work_schedule = ? WHERE en_no = ?
            ''', (shift_id, schedule, self.en_no))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", "Employee configuration saved successfully!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {str(e)}")