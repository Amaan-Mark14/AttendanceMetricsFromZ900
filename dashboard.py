from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QHeaderView, QLabel, QComboBox,
                               QPushButton, QLineEdit)
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

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or employee number...")
        self.search_input.textChanged.connect(self.load_data)
        controls_layout.addWidget(self.search_input)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_data)
        controls_layout.addWidget(self.refresh_button)

        self.records_table = QTableWidget()
        self.records_table.setColumnCount(5)
        self.records_table.setHorizontalHeaderLabels([
            "No", "En No", "Name", "Mode", "Date/Time"
        ])

        header = self.records_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

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
                SELECT no, en_no, name, mode, datetime
                FROM raw_logs
                WHERE 1=1
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

            query += ' ORDER BY datetime DESC'

            cursor.execute(query, params)
            records = cursor.fetchall()

            self.records_table.setRowCount(len(records))

            for row_idx, record in enumerate(records):
                for col_idx, value in enumerate(record):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.records_table.setItem(row_idx, col_idx, item)

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