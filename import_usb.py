import csv
import sqlite3
from pathlib import Path
from datetime import datetime
import platform

class USBImporter:
    def __init__(self, usb_name, file_name):
        self.usb_name = 'SONY'
        self.file_name = 'ALOG_001.txt'
        self.db_path = 'attendance.db'

    def find_usb_drive(self):
        system = platform.system()

        if system == "Windows":
            return self._find_windows_usb()
        elif system == "Darwin":  # macOS
            return self._find_macos_usb()
        elif system == "Linux":
            return self._find_linux_usb()
        else:
            raise Exception(f"Unsupported operating system: {system}")

    def _find_windows_usb(self):
        import win32api
        import win32file

        drives = []
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            try:
                drive_path = f"{letter}:\\"
                if Path(drive_path).exists():
                    drive_name = win32api.GetVolumeInformation(drive_path)[0]
                    if drive_name == self.usb_name:
                        return drive_path
            except Exception:
                continue

        return None

    def _find_macos_usb(self):
        volumes_path = Path("/Volumes")
        if volumes_path.exists():
            for volume in volumes_path.iterdir():
                if volume.name == self.usb_name:
                    return str(volume)
        return None

    def _find_linux_usb(self):
        media_path = Path("/media")
        if media_path.exists():
            for user in media_path.iterdir():
                for device in user.iterdir():
                    if device.name == self.usb_name:
                        return str(device)

        mount_path = Path("/mnt")
        if mount_path.exists():
            for device in mount_path.iterdir():
                if device.name == self.usb_name:
                    return str(device)

        return None

    def import_from_usb(self):
        try:
            usb_path = self.find_usb_drive()
            if not usb_path:
                return {
                    "success": False,
                    "error": f"USB drive '{self.usb_name}' not found. Please insert the USB drive."
                }

            file_path = Path(usb_path) / self.file_name
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File '{self.file_name}' not found on USB drive."
                }

            return self._parse_and_import_file(file_path)

        except Exception as e:
            return {
                "success": False,
                "error": f"Error accessing USB drive: {str(e)}"
            }

    def _parse_and_import_file(self, file_path):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            import_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute('''
                INSERT INTO import_batches (import_date, file_name, records_count, status)
                VALUES (?, ?, ?, ?)
            ''', (import_time, str(file_path), 0, 'processing'))

            batch_id = cursor.lastrowid
            conn.commit()

            records_imported = 0
            duplicates_skipped = 0

            # Try multiple encodings
            content = None
            encodings = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                return {
                    "success": False,
                    "error": "Unable to read file. Tried encodings: utf-8, utf-16, latin-1, cp1252"
                }

            files_content = content.split('File ')

            parsed_data = []

            for file_section in files_content:
                if not file_section.strip():
                    continue

                lines = file_section.strip().split('\n')
                if len(lines) < 2:
                    continue

                header_line = lines[0]
                if not header_line.strip():
                    continue

                headers = [h.strip() for h in header_line.split('\t')]

                for line in lines[1:]:
                    if not line.strip():
                        continue

                    values = line.strip().split('\t')

                    if len(values) < 10:
                        continue

                    try:
                        # Debug: print first few records to check parsing
                        if records_imported < 3:
                            print(f"DEBUG - Line values: {values}")
                            print(f"DEBUG - Length: {len(values)}")

                        record = {
                            'no': int(values[0]) if values[0].strip() else 0,
                            'tm_no': int(values[1]) if values[1].strip() else 0,
                            'en_no': values[2].strip() if len(values) > 2 else '',
                            'name': values[3].strip() if len(values) > 3 else '',
                            'gm_no': int(values[4]) if len(values) > 4 and values[4].strip() else 0,
                            'mode': values[5].strip() if len(values) > 5 else '',
                            'in_out': values[6].strip() if len(values) > 6 else '',
                            'antipass': int(values[7]) if len(values) > 7 and values[7].strip() else 0,
                            'proxy_work': int(values[8]) if len(values) > 8 and values[8].strip() else 0,
                            'datetime': values[9].strip() if len(values) > 9 else ''
                        }

                        if records_imported < 3:
                            print(f"DEBUG - Parsed record: {record}")

                        cursor.execute('''
                            SELECT id FROM raw_logs
                            WHERE no = ? AND tm_no = ? AND en_no = ? AND datetime = ?
                        ''', (record['no'], record['tm_no'], record['en_no'], record['datetime']))

                        if cursor.fetchone():
                            duplicates_skipped += 1
                        else:
                            cursor.execute('''
                                INSERT INTO raw_logs (
                                    import_batch_id, no, tm_no, en_no, name, gm_no,
                                    mode, in_out, antipass, proxy_work, datetime
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                batch_id, record['no'], record['tm_no'], record['en_no'],
                                record['name'], record['gm_no'], record['mode'],
                                record['in_out'], record['antipass'], record['proxy_work'],
                                record['datetime']
                            ))
                            records_imported += 1

                    except (ValueError, IndexError) as e:
                        continue

            cursor.execute('''
                UPDATE import_batches
                SET records_count = ?, status = ?
                WHERE id = ?
            ''', (records_imported, 'completed', batch_id))

            conn.commit()
            conn.close()

            return {
                "success": True,
                "records_imported": records_imported,
                "duplicates_skipped": duplicates_skipped,
                "import_time": import_time,
                "batch_id": batch_id
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error parsing file: {str(e)}"
            }