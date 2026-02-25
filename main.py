import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QTextEdit,
                               QMessageBox, QTabWidget)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import sqlite3
from pathlib import Path
from import_usb import USBImporter
from dashboard import Dashboard
from attendance_dashboard import AttendanceDashboard
from employees import EmployeeManager
from audit_tab import AuditTab

class USBImportThread(QThread):
    finished = Signal(dict)

    def __init__(self, usb_name, file_name):
        super().__init__()
        self.usb_name = usb_name
        self.file_name = file_name

    def run(self):
        try:
            importer = USBImporter(self.usb_name, self.file_name)
            result = importer.import_from_usb()
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "error": str(e)})

class AttendanceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attendance Management System")

        self.init_database()
        self.setup_ui()

    def init_database(self):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_date TEXT,
                file_name TEXT,
                records_count INTEGER,
                status TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_batch_id INTEGER,
                no INTEGER,
                tm_no INTEGER,
                en_no TEXT,
                name TEXT,
                gm_no INTEGER,
                mode TEXT,
                in_out TEXT,
                antipass INTEGER,
                proxy_work INTEGER,
                datetime TEXT,
                hidden INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (import_batch_id) REFERENCES import_batches(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                grace_period INTEGER DEFAULT 15,
                minimum_hours REAL DEFAULT 4.0,
                maximum_hours REAL DEFAULT 12.0,
                is_active INTEGER DEFAULT 1
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                en_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                gm_no INTEGER,
                shift_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shift_id) REFERENCES shifts(id)
            )
        ''')

        # Create default shift if none exists
        cursor.execute('SELECT COUNT(*) FROM shifts')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO shifts (name, start_time, end_time, grace_period, minimum_hours, maximum_hours)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('Default Shift', '09:00', '18:00', 15, 4.0, 12.0))

        # Add hidden column to raw_logs if it doesn't exist (for existing databases)
        try:
            cursor.execute("SELECT hidden FROM raw_logs LIMIT 1")
        except:
            cursor.execute('ALTER TABLE raw_logs ADD COLUMN hidden INTEGER DEFAULT 0')

        # Add work_schedule column to employees if it doesn't exist
        try:
            cursor.execute("SELECT work_schedule FROM employees LIMIT 1")
        except:
            cursor.execute('ALTER TABLE employees ADD COLUMN work_schedule TEXT DEFAULT "1111110"')

        # Add is_locked column to employees if it doesn't exist
        try:
            cursor.execute("SELECT is_locked FROM employees LIMIT 1")
        except:
            cursor.execute('ALTER TABLE employees ADD COLUMN is_locked INTEGER DEFAULT 0')

        # Create month_locks table for month locking feature
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS month_locks (
                year INTEGER,
                month INTEGER,
                locked_at TEXT,
                PRIMARY KEY (year, month)
            )
        ''')

        # Create edit_history table for audit trail
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                record_id INTEGER,
                action TEXT,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                edited_by TEXT,
                edited_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        title_label = QLabel("Attendance Management System")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        import_widget = QWidget()
        import_layout = QVBoxLayout()
        import_widget.setLayout(import_layout)

        self.read_button = QPushButton("📁 Read from USB")
        self.read_button.setMinimumHeight(50)
        button_font = QFont()
        button_font.setPointSize(12)
        self.read_button.setFont(button_font)
        self.read_button.clicked.connect(self.read_from_usb)
        import_layout.addWidget(self.read_button)

        import_layout.addSpacing(20)

        self.status_label = QLabel("Status: Ready to import")
        self.status_label.setAlignment(Qt.AlignCenter)
        import_layout.addWidget(self.status_label)

        import_layout.addSpacing(10)

        buttons_layout = QHBoxLayout()
        import_layout.addLayout(buttons_layout)

        self.clear_button = QPushButton("🗑️ Clear Database")
        self.clear_button.setStyleSheet("background-color: #fee; color: #c00;")
        self.clear_button.clicked.connect(self.clear_database)
        buttons_layout.addWidget(self.clear_button)

        self.debug_button = QPushButton("🐛 Load Debug Data")
        self.debug_button.setStyleSheet("background-color: #eef; color: #006;")
        self.debug_button.clicked.connect(self.load_debug_data)
        buttons_layout.addWidget(self.debug_button)

        buttons_layout.addStretch()

        import_layout.addSpacing(10)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        import_layout.addWidget(self.log_text)

        self.tab_widget.addTab(import_widget, "USB Import")

        self.employee_manager = EmployeeManager()
        self.tab_widget.addTab(self.employee_manager, "Employees")

        self.attendance_dashboard = AttendanceDashboard(employee_manager=self.employee_manager)
        self.tab_widget.addTab(self.attendance_dashboard, "Attendance")

        self.dashboard = Dashboard()
        self.tab_widget.addTab(self.dashboard, "Raw Logs")

        self.audit_tab = AuditTab()
        self.tab_widget.addTab(self.audit_tab, "Audit")

    def read_from_usb(self):
        USB_NAME = "ATTENDANCE_USB"  # configurable
        FILE_NAME = "attendance.txt"  # configurable

        self.read_button.setEnabled(False)
        self.status_label.setText("Status: Searching for USB drive...")
        self.log_text.append("Starting USB import process...")

        self.import_thread = USBImportThread(USB_NAME, FILE_NAME)
        self.import_thread.finished.connect(self.on_import_finished)
        self.import_thread.start()

    def on_import_finished(self, result):
        self.read_button.setEnabled(True)

        if result["success"]:
            self.status_label.setText(f"Status: Import completed successfully!")
            self.log_text.append(f"✓ Imported {result['records_imported']} records")
            self.log_text.append(f"✓ Skipped {result['duplicates_skipped']} duplicates")

            QMessageBox.information(self, "Import Complete",
                                   f"Successfully imported {result['records_imported']} attendance records.")

            self.dashboard.load_data()
            self.attendance_dashboard.load_data()
            self.employee_manager.load_employees()
        else:
            self.status_label.setText("Status: Import failed")
            self.log_text.append(f"✗ Error: {result.get('error', 'Unknown error')}")

            QMessageBox.critical(self, "Import Failed",
                                f"Failed to import attendance records.\nError: {result.get('error', 'Unknown error')}")

    def log_message(self, message):
        self.log_text.append(message)

    def clear_database(self):
        reply = QMessageBox.question(
            self, "Clear Database",
            "Are you sure you want to clear all data?\n\nThis will delete:\n"
            "• All imported attendance records (except locked months)\n"
            "• All import history\n"
            "• All employees (except locked employees)\n"
            "• All shifts (except default)\n\n"
            "Locked months and locked employees will be preserved.\n\n"
            "This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()

                # Check for locked months
                cursor.execute('SELECT year, month FROM month_locks')
                locked_months = cursor.fetchall()

                if locked_months:
                    # Build list of protected year-month periods
                    protected_periods = [f"{year}-{month:02d}" for year, month in locked_months]
                    locked_list = "\n".join([f"{m[1]}/{m[0]}" for m in locked_months])

                    QMessageBox.warning(
                        self, "Locked Months Detected",
                        f"The following months are LOCKED and will be preserved:\n{locked_list}\n\n"
                        "Only unlocked data will be cleared."
                    )

                    # Delete logs NOT in protected periods
                    # Build the NOT IN clause dynamically
                    placeholders = ','.join(['?' for _ in protected_periods])
                    cursor.execute(f'''
                        DELETE FROM raw_logs
                        WHERE strftime('%Y-%m', datetime) NOT IN ({placeholders})
                    ''', protected_periods)
                else:
                    # No locks, delete all logs
                    cursor.execute("DELETE FROM raw_logs")

                # Check for locked employees
                cursor.execute('SELECT en_no, name, shift_id FROM employees WHERE is_locked = 1')
                locked_employees = cursor.fetchall()

                if locked_employees:
                    locked_list = "\n".join([f"{e[0]} - {e[1]}" for e in locked_employees])
                    QMessageBox.warning(
                        self, "Locked Employees Detected",
                        f"The following employees are LOCKED and will be preserved:\n{locked_list}\n\n"
                        "Only unlocked employees will be deleted."
                    )

                    # Delete only unlocked employees
                    cursor.execute("DELETE FROM employees WHERE is_locked = 0")

                    # Get shift IDs used by locked employees
                    locked_shift_ids = [e[2] for e in locked_employees if e[2]]
                else:
                    # No locked employees, delete all
                    cursor.execute("DELETE FROM employees")
                    locked_shift_ids = []

                # Delete shifts NOT used by locked employees and not the default shift
                if locked_shift_ids:
                    placeholders = ','.join(['?' for _ in locked_shift_ids])
                    cursor.execute(f"DELETE FROM shifts WHERE name != 'Default Shift' AND id NOT IN ({placeholders})", locked_shift_ids)
                else:
                    cursor.execute("DELETE FROM shifts WHERE name != 'Default Shift'")

                # Always delete import batches (they don't affect locked data)
                cursor.execute("DELETE FROM import_batches")

                conn.commit()
                conn.close()

                self.log_text.append("🗑️ Database cleared successfully (locked months & employees preserved)")
                self.status_label.setText("Status: Database cleared")

                # Refresh employees first (they may need to be auto-imported)
                self.employee_manager.load_employees()
                # Then refresh dashboard (which will also check if employees need importing)
                self.dashboard.load_data()
                self.attendance_dashboard.load_data()

                QMessageBox.information(self, "Database Cleared",
                                       "Data has been cleared.\n\nLocked months and locked employees were preserved.")

            except Exception as e:
                error_msg = f"Failed to clear database: {str(e)}"
                self.log_text.append(f"✗ {error_msg}")
                QMessageBox.critical(self, "Error", error_msg)

    def load_debug_data(self):
        try:
            debug_file = Path("debug.txt")
            if not debug_file.exists():
                QMessageBox.warning(self, "File Not Found",
                                   "debug.txt not found in the program folder.\n\n"
                                   "Please create a debug.txt file with attendance data for testing.")
                return

            self.status_label.setText("Status: Loading debug data...")
            self.log_text.append("🐛 Starting debug data import...")

            from import_usb import USBImporter
            importer = USBImporter("", "")  # USB name not needed for debug file

            result = importer._parse_and_import_file(debug_file)

            if result["success"]:
                self.status_label.setText("Status: Debug data loaded successfully")
                self.log_text.append(f"✓ Loaded {result['records_imported']} debug records")
                self.log_text.append(f"✓ Skipped {result['duplicates_skipped']} duplicates")

                self.dashboard.load_data()
                self.attendance_dashboard.load_data()

                QMessageBox.information(self, "Debug Data Loaded",
                                       f"Successfully loaded {result['records_imported']} debug records.")
            else:
                self.status_label.setText("Status: Debug data import failed")
                self.log_text.append(f"✗ Error: {result.get('error', 'Unknown error')}")
                QMessageBox.critical(self, "Import Failed",
                                    f"Failed to load debug data.\nError: {result.get('error', 'Unknown error')}")

        except Exception as e:
            error_msg = f"Failed to load debug data: {str(e)}"
            self.log_text.append(f"✗ {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)

def main():
    app = QApplication(sys.argv)
    window = AttendanceWindow()
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()