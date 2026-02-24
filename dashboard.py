from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QHeaderView, QLabel, QComboBox,
                               QPushButton, QLineEdit, QDialog, QFormLayout,
                               QDateTimeEdit, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sqlite3
from datetime import datetime

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        title_label = QLabel("Attendance Records Dashboard")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        controls_layout = QHBoxLayout()
        layout.addLayout(controls_layout)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Records", "Today", "This Week", "This Month"])
        self.filter_combo.currentTextChanged.connect(self.load_data)
        controls_layout.addWidget(QLabel("Filter:"))
        controls_layout.addWidget(self.filter_combo)

        controls_layout.addStretch()

        self.add_log_btn = QPushButton("+ Add Log")
        self.add_log_btn.clicked.connect(self.add_manual_log)
        controls_layout.addWidget(self.add_log_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or employee number...")
        self.search_input.textChanged.connect(self.load_data)
        controls_layout.addWidget(self.search_input)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_data)
        controls_layout.addWidget(self.refresh_button)

        self.records_table = QTableWidget()
        self.records_table.setColumnCount(6)
        self.records_table.setHorizontalHeaderLabels([
            "No", "En No", "Name", "Mode", "Date/Time", "Actions"
        ])

        header = self.records_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.records_table.setAlternatingRowColors(True)
        self.records_table.setSortingEnabled(True)
        layout.addWidget(self.records_table)

        self.stats_label = QLabel("Total Records: 0")
        self.stats_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.stats_label)

    def load_data(self):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            query = '''
                SELECT id, no, en_no, name, mode, datetime
                FROM raw_logs
                WHERE hidden = 0
            '''

            params = []

            search_text = self.search_input.text().strip()
            if search_text:
                query += ' AND (name LIKE ? OR en_no LIKE ?)'
                params.extend([f'%{search_text}%', f'%{search_text}%'])

            filter_type = self.filter_combo.currentText()
            if filter_type == "Today":
                query += ' AND DATE(datetime) = DATE("now")'
            elif filter_type == "This Week":
                query += ' AND datetime >= DATE("now", "-7 days")'
            elif filter_type == "This Month":
                query += ' AND strftime("%Y-%m", datetime) = strftime("%Y-%m", "now")'

            query += ' ORDER BY datetime DESC, CAST(en_no AS INTEGER)'

            cursor.execute(query, params)
            records = cursor.fetchall()

            self.records_table.setRowCount(len(records))

            for row_idx, record in enumerate(records):
                # Skip the ID column (col 0) when displaying
                for col_idx, value in enumerate(record[1:], start=0):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.records_table.setItem(row_idx, col_idx, item)

                # Add delete button
                delete_btn = QPushButton("🗑️")
                delete_btn.setStyleSheet("color: #c00;")
                delete_btn.clicked.connect(lambda checked, log_id=record[0]: self.hide_log(log_id))
                self.records_table.setCellWidget(row_idx, 5, delete_btn)

            conn.close()

            self.stats_label.setText(f"Total Records: {len(records)}")

        except Exception as e:
            self.stats_label.setText(f"Error loading data: {str(e)}")

    def view_record_details(self, record_id):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM raw_logs WHERE id = ?
            ''', (record_id,))

            record = cursor.fetchone()
            conn.close()

            if record:
                details = f"""
Record Details:
--------------
ID: {record[0]}
Import Batch ID: {record[1]}
No: {record[2]}
TM No: {record[3]}
En No: {record[4]}
Name: {record[5]}
GM No: {record[6]}
Mode: {record[7]}
In/Out: {record[8]}
Antipass: {record[9]}
Proxy Work: {record[10]}
Date/Time: {record[11]}
Created At: {record[12]}
                """

                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Record Details", details.strip())

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to load record details: {str(e)}")

    def hide_log(self, log_id):
        try:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, "Hide Log",
                "Are you sure you want to hide this log entry?\n\n"
                "This will mark it as hidden (soft delete). It won't appear in views\n"
                "and won't be re-imported with new data.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE raw_logs SET hidden = 1 WHERE id = ?', (log_id,))
                conn.commit()
                conn.close()
                self.load_data()

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to hide log: {str(e)}")

    def add_manual_log(self):
        try:
            dialog = ManualLogDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add manual log: {str(e)}")

class ManualLogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Manual Log Entry")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        form_layout = QFormLayout()
        layout.addLayout(form_layout)

        # Get unique employees for dropdown
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT en_no, name FROM raw_logs WHERE hidden = 0 ORDER BY name')
            employees = cursor.fetchall()
            conn.close()
        except:
            employees = []

        # Employee dropdown
        self.employee_combo = QComboBox()
        for en_no, name in employees:
            self.employee_combo.addItem(f"{name} ({en_no})", en_no)
        form_layout.addRow("Employee:", self.employee_combo)

        # Date/Time picker
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_edit.setDateTime(datetime.now())
        form_layout.addRow("Date/Time:", self.datetime_edit)

        # Buttons
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)

        save_btn = QPushButton("Save Log")
        save_btn.clicked.connect(self.save_log)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

    def save_log(self):
        try:
            en_no = self.employee_combo.currentData()
            if not en_no:
                QMessageBox.warning(self, "Error", "Please select an employee")
                return

            # Get employee name from raw_logs
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT name, gm_no FROM raw_logs WHERE en_no = ? LIMIT 1', (en_no,))
            employee_data = cursor.fetchone()

            if not employee_data:
                QMessageBox.warning(self, "Error", "Employee not found in database")
                conn.close()
                return

            name, gm_no = employee_data
            datetime_str = self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")

            # Insert manual log
            cursor.execute('''
                INSERT INTO raw_logs (import_batch_id, no, tm_no, en_no, name, gm_no, mode, in_out, antipass, proxy_work, datetime, hidden)
                VALUES (NULL, NULL, 1, ?, ?, ?, 'Manual', 'DutyOff', 0, 0, ?, 0)
            ''', (en_no, name, gm_no, datetime_str))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", "Manual log entry added successfully!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save manual log: {str(e)}")