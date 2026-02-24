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
        self.setGeometry(100, 100, 600, 400)

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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (import_batch_id) REFERENCES import_batches(id)
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

        self.last_import_label = QLabel("Last import: Never")
        self.last_import_label.setAlignment(Qt.AlignCenter)
        import_layout.addWidget(self.last_import_label)

        import_layout.addSpacing(20)

        buttons_layout = QHBoxLayout()
        import_layout.addLayout(buttons_layout)

        self.clear_button = QPushButton("🗑️ Clear Database")
        self.clear_button.setStyleSheet("background-color: #fee; color: #c00;")
        self.clear_button.clicked.connect(self.clear_database)
        buttons_layout.addWidget(self.clear_button)

        buttons_layout.addStretch()

        import_layout.addSpacing(10)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        import_layout.addWidget(self.log_text)

        self.tab_widget.addTab(import_widget, "USB Import")

        self.dashboard = Dashboard()
        self.tab_widget.addTab(self.dashboard, "Dashboard")

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
            self.last_import_label.setText(f"Last import: {result['import_time']}")

            QMessageBox.information(self, "Import Complete",
                                   f"Successfully imported {result['records_imported']} attendance records.")

            self.dashboard.load_data()
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
            "• All imported attendance records\n"
            "• All import history\n\nThis action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()

                cursor.execute("DELETE FROM raw_logs")
                cursor.execute("DELETE FROM import_batches")

                conn.commit()
                conn.close()

                self.log_text.append("🗑️ Database cleared successfully")
                self.status_label.setText("Status: Database cleared")
                self.last_import_label.setText("Last import: Never")

                self.dashboard.load_data()

                QMessageBox.information(self, "Database Cleared",
                                       "All data has been successfully deleted from the database.")

            except Exception as e:
                error_msg = f"Failed to clear database: {str(e)}"
                self.log_text.append(f"✗ {error_msg}")
                QMessageBox.critical(self, "Error", error_msg)

def main():
    app = QApplication(sys.argv)
    window = AttendanceWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()