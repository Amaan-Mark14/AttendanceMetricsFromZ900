from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QHeaderView, QLabel, QComboBox,
                               QPushButton, QMessageBox, QTabWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import sqlite3
from datetime import datetime

class AuditTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title_label = QLabel("Audit Trail")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Sub-tabs for different audit views
        self.sub_tabs = QTabWidget()
        layout.addWidget(self.sub_tabs)

        # Edit History Tab
        self.edit_history_widget = QWidget()
        self.setup_edit_history_view()
        self.sub_tabs.addTab(self.edit_history_widget, "Edit History")

        # Soft Deleted Logs Tab
        self.deleted_logs_widget = QWidget()
        self.setup_deleted_logs_view()
        self.sub_tabs.addTab(self.deleted_logs_widget, "Deleted Logs")

        # Manual Logs Tab
        self.manual_logs_widget = QWidget()
        self.setup_manual_logs_view()
        self.sub_tabs.addTab(self.manual_logs_widget, "Manual Logs")

    def setup_edit_history_view(self):
        layout = QVBoxLayout()
        self.edit_history_widget.setLayout(layout)

        # Controls
        controls = QHBoxLayout()
        layout.addLayout(controls)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_edit_history)
        controls.addWidget(refresh_btn)

        controls.addStretch()

        self.edit_history_table = QTableWidget()
        self.edit_history_table.setAlternatingRowColors(True)
        self.edit_history_table.setColumnCount(7)
        self.edit_history_table.setHorizontalHeaderLabels([
            "Date/Time", "Table", "Record ID", "Action", "Old Value", "New Value", "Reason"
        ])
        layout.addWidget(self.edit_history_table)

        self.load_edit_history()

    def setup_deleted_logs_view(self):
        layout = QVBoxLayout()
        self.deleted_logs_widget.setLayout(layout)

        # Controls
        controls = QHBoxLayout()
        layout.addLayout(controls)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_deleted_logs)
        controls.addWidget(refresh_btn)

        restore_btn = QPushButton("Restore Selected")
        restore_btn.clicked.connect(self.restore_selected_log)
        controls.addWidget(restore_btn)

        controls.addStretch()

        self.deleted_logs_table = QTableWidget()
        self.deleted_logs_table.setAlternatingRowColors(True)
        self.deleted_logs_table.setColumnCount(6)
        self.deleted_logs_table.setHorizontalHeaderLabels([
            "En No", "Name", "Date/Time", "Mode", "Hidden Date", "Actions"
        ])
        self.deleted_logs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.deleted_logs_table)

        self.load_deleted_logs()

    def setup_manual_logs_view(self):
        layout = QVBoxLayout()
        self.manual_logs_widget.setLayout(layout)

        # Controls
        controls = QHBoxLayout()
        layout.addLayout(controls)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_manual_logs)
        controls.addWidget(refresh_btn)

        controls.addStretch()

        self.manual_logs_table = QTableWidget()
        self.manual_logs_table.setAlternatingRowColors(True)
        self.manual_logs_table.setColumnCount(6)
        self.manual_logs_table.setHorizontalHeaderLabels([
            "En No", "Name", "Date/Time", "Added At", "Mode", "Notes"
        ])
        layout.addWidget(self.manual_logs_table)

        self.load_manual_logs()

    def load_edit_history(self):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT edited_at, table_name, record_id, action, old_value, new_value, reason
                FROM edit_history
                ORDER BY edited_at DESC
                LIMIT 100
            ''')

            records = cursor.fetchall()
            conn.close()

            self.edit_history_table.setRowCount(len(records))

            for row_idx, record in enumerate(records):
                for col_idx, value in enumerate(record):
                    item = QTableWidgetItem(str(value) if value else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Color code by action
                    if col_idx == 3:  # Action column
                        if record[3] == 'DELETE':
                            item.setForeground(QColor(220, 20, 60))  # Crimson
                        elif record[3] == 'INSERT':
                            item.setForeground(QColor(34, 139, 34))  # Green
                        elif record[3] == 'UPDATE':
                            item.setForeground(QColor(0, 102, 204))  # Blue

                    self.edit_history_table.setItem(row_idx, col_idx, item)

            # Resize columns
            header = self.edit_history_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            for col in [4, 5, 6]:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load edit history: {str(e)}")

    def load_deleted_logs(self):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT en_no, name, datetime, mode, created_at, id
                FROM raw_logs
                WHERE hidden = 1
                ORDER BY created_at DESC
            ''')

            records = cursor.fetchall()
            conn.close()

            self.deleted_logs_table.setRowCount(len(records))

            for row_idx, record in enumerate(records):
                # Columns: En No, Name, Date/Time, Mode, Hidden Date, Actions
                for col_idx in range(5):
                    item = QTableWidgetItem(str(record[col_idx]) if record[col_idx] else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if col_idx == 1:  # Name
                        item.setForeground(QColor(178, 34, 34))  # Red for deleted
                    self.deleted_logs_table.setItem(row_idx, col_idx, item)

                # Store ID in last column for restore
                id_item = QTableWidgetItem(str(record[5]))
                self.deleted_logs_table.setItem(row_idx, 5, id_item)

            # Resize columns
            header = self.deleted_logs_table.horizontalHeader()
            for col in range(6):
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load deleted logs: {str(e)}")

    def restore_selected_log(self):
        selected_rows = self.deleted_logs_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a log to restore.")
            return

        reply = QMessageBox.question(
            self, "Restore Log",
            f"Restore {len(selected_rows)} selected log(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()

                for row in selected_rows:
                    row_idx = row.row()
                    log_id = self.deleted_logs_table.item(row_idx, 5).text()

                    cursor.execute('UPDATE raw_logs SET hidden = 0 WHERE id = ?', (log_id,))

                conn.commit()
                conn.close()

                self.load_deleted_logs()
                QMessageBox.information(self, "Success", f"Restored {len(selected_rows)} log(s)")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to restore: {str(e)}")

    def load_manual_logs(self):
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()

            # Manual logs are identified by mode = 'Manual'
            cursor.execute('''
                SELECT en_no, name, datetime, created_at, mode, id
                FROM raw_logs
                WHERE mode = 'Manual' AND hidden = 0
                ORDER BY created_at DESC
            ''')

            records = cursor.fetchall()
            conn.close()

            self.manual_logs_table.setRowCount(len(records))

            for row_idx, record in enumerate(records):
                for col_idx in range(5):
                    value = record[col_idx]
                    if col_idx == 4 and value == 'Manual':
                        value = "Manually Added"

                    item = QTableWidgetItem(str(value) if value else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    if col_idx == 4:  # Mode column
                        item.setForeground(QColor(34, 139, 34))  # Green for manual

                    self.manual_logs_table.setItem(row_idx, col_idx, item)

                # Store ID
                id_item = QTableWidgetItem(str(record[5]))
                self.manual_logs_table.setItem(row_idx, 5, id_item)

            # Resize columns
            header = self.manual_logs_table.horizontalHeader()
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            for col in [0, 2, 3, 4]:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load manual logs: {str(e)}")

    def load_data(self):
        """Reload all audit data"""
        self.load_edit_history()
        self.load_deleted_logs()
        self.load_manual_logs()
