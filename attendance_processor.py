import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

class AttendanceCalculator:
    """
    Calculates attendance metrics on-demand from raw logs.
    No storage - just calculation logic applied when needed.
    """

    def __init__(self, db_path='attendance.db'):
        self.db_path = db_path

    def calculate_day(self, en_no, date):
        """
        Calculate attendance for a single employee on a single day.

        Returns:
            dict with attendance data or None if no logs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get employee work schedule first
        cursor.execute('''
            SELECT work_schedule
            FROM employees
            WHERE en_no = ?
        ''', (en_no,))

        emp_result = cursor.fetchone()
        work_schedule = emp_result[0] if emp_result and emp_result[0] else '1111110'

        # Check if this day is a working day
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        day_of_week = date_obj.weekday()  # Monday=0, Sunday=6

        # If not a working day, return Holiday record
        if work_schedule[day_of_week] == '0':
            conn.close()
            return {
                'employee_id': None,
                'en_no': en_no,
                'date': date,
                'first_scan': None,
                'last_scan': None,
                'total_hours': 0.0,
                'status': 'Holiday',
                'is_late': 0,
                'missing_checkout': 0,
                'scan_count': 0,
                'shift_start': None,
                'shift_end': None
            }

        # Get all logs for this employee on this date
        cursor.execute('''
            SELECT datetime, mode
            FROM raw_logs
            WHERE en_no = ? AND DATE(datetime) = ? AND hidden = 0
            ORDER BY datetime
        ''', (en_no, date))

        logs = cursor.fetchall()

        if not logs:
            conn.close()
            # Return absent record for working days
            return {
                'employee_id': None,
                'en_no': en_no,
                'date': date,
                'first_scan': None,
                'last_scan': None,
                'total_hours': 0.0,
                'status': 'Absent',
                'is_late': 0,
                'missing_checkout': 0,
                'scan_count': 0,
                'shift_start': None,
                'shift_end': None
            }

        # Get employee shift information
        cursor.execute('''
            SELECT e.id, s.start_time, s.end_time, s.grace_period,
                   s.minimum_hours, s.maximum_hours
            FROM employees e
            LEFT JOIN shifts s ON e.shift_id = s.id
            WHERE e.en_no = ?
        ''', (en_no,))

        shift_info = cursor.fetchone()
        conn.close()

        # Parse shift info
        if not shift_info or not shift_info[1]:
            # Use default shift values
            employee_id = shift_info[0] if shift_info else None
            shift_start = "09:00"
            shift_end = "18:00"
            grace_period = 15  # minutes
            min_hours = 4.0
            max_hours = 12.0
        else:
            employee_id, shift_start, shift_end, grace_period, min_hours, max_hours = shift_info

        # Extract times
        first_scan = logs[0][0]
        last_scan = logs[-1][0]

        # Calculate total hours
        first_time = datetime.strptime(first_scan, "%Y-%m-%d %H:%M:%S")
        last_time = datetime.strptime(last_scan, "%Y-%m-%d %H:%M:%S")
        total_hours = (last_time - first_time).total_seconds() / 3600

        # Apply cap
        total_hours = min(total_hours, max_hours)

        # Determine flags
        is_late = self._check_if_late(first_scan, shift_start, grace_period)
        missing_checkout = 1 if len(logs) == 1 else 0

        # Determine status
        status = self._determine_status(total_hours, min_hours, len(logs))

        return {
            'employee_id': employee_id,
            'en_no': en_no,
            'date': date,
            'first_scan': first_scan,
            'last_scan': last_scan,
            'total_hours': round(total_hours, 2),
            'status': status,
            'is_late': is_late,
            'missing_checkout': missing_checkout,
            'scan_count': len(logs),
            'shift_start': shift_start,
            'shift_end': shift_end
        }

    def calculate_month(self, en_no, year, month):
        """
        Calculate attendance for an entire month.

        Args:
            en_no: Employee enrollment number
            year: Year (e.g., 2026)
            month: Month (1-12)

        Returns:
            list of daily attendance dicts
        """
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]

        results = []
        for day in range(1, days_in_month + 1):
            date = f"{year}-{month:02d}-{day:02d}"
            daily = self.calculate_day(en_no, date)
            # Always append (even if absent), now calculate_day returns a record not None
            results.append(daily)

        return results

    def calculate_month_summary(self, en_no, year, month):
        """
        Calculate monthly summary stats for an employee.

        Returns:
            dict with totals: days_present, days_absent, days_late, total_hours, etc.
        """
        daily_records = self.calculate_month(en_no, year, month)

        # Filter out None values (non-working days)
        daily_records = [d for d in daily_records if d is not None]

        if not daily_records:
            return None

        summary = {
            'en_no': en_no,
            'year': year,
            'month': month,
            'days_present': sum(1 for d in daily_records if d['status'] in ['Present', 'Half-day']),
            'days_absent': sum(1 for d in daily_records if d['status'] == 'Absent'),
            'days_half_day': sum(1 for d in daily_records if d['status'] == 'Half-day'),
            'days_holiday': sum(1 for d in daily_records if d['status'] == 'Holiday'),
            'days_late': sum(1 for d in daily_records if d['is_late']),
            'days_missing_checkout': sum(1 for d in daily_records if d['missing_checkout']),
            'total_hours': round(sum(d['total_hours'] for d in daily_records if d['status'] != 'Holiday'), 2),
            'total_days': sum(1 for d in daily_records if d['status'] != 'Holiday')
        }

        return summary

    def _check_if_late(self, first_scan, shift_start, grace_period):
        """
        Check if first scan is after shift start + grace period.
        """
        try:
            scan_time = datetime.strptime(first_scan, "%Y-%m-%d %H:%M:%S")
            shift_time = datetime.strptime(shift_start, "%H:%M").replace(
                year=scan_time.year, month=scan_time.month, day=scan_time.day
            )

            # Add grace period
            grace_deadline = shift_time + timedelta(minutes=grace_period)

            return 1 if scan_time > grace_deadline else 0
        except:
            return 0

    def _determine_status(self, total_hours, min_hours, scan_count):
        """
        Determine attendance status based on hours and scans.
        """
        if scan_count == 0:
            return 'Absent'
        elif total_hours < (min_hours / 2):  # Less than half minimum = absent
            return 'Absent'
        elif total_hours < min_hours:  # Below minimum but above half = half-day
            return 'Half-day'
        else:
            return 'Present'

    def get_all_employees_summary(self, year, month):
        """
        Get monthly summary for all active employees.

        Returns:
            list of summary dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT en_no, name FROM employees WHERE is_active = 1 ORDER BY en_no')
        employees = cursor.fetchall()
        conn.close()

        summaries = []
        for en_no, name in employees:
            summary = self.calculate_month_summary(en_no, year, month)
            if summary:
                summary['name'] = name
                summaries.append(summary)

        return summaries


# Demo/test function
if __name__ == "__main__":
    calc = AttendanceCalculator()

    # Test single day
    print("=" * 60)
    print("SINGLE DAY CALCULATION")
    print("=" * 60)
    result = calc.calculate_day("00000001", "2026-02-24")
    if result:
        print(f"Employee: {result['en_no']}")
        print(f"Date: {result['date']}")
        print(f"First Scan: {result['first_scan']}")
        print(f"Last Scan: {result['last_scan']}")
        print(f"Total Hours: {result['total_hours']}")
        print(f"Status: {result['status']}")
        print(f"Late: {'Yes' if result['is_late'] else 'No'}")
        print(f"Missing Checkout: {'Yes' if result['missing_checkout'] else 'No'}")
        print(f"Scans: {result['scan_count']}")

    # Test monthly summary
    print("\n" + "=" * 60)
    print("MONTHLY SUMMARY")
    print("=" * 60)
    summary = calc.calculate_month_summary("00000001", 2026, 2)
    if summary:
        print(f"Employee: {summary['en_no']}")
        print(f"Period: {summary['year']}-{summary['month']:02d}")
        print(f"Days Present: {summary['days_present']}")
        print(f"Days Absent: {summary['days_absent']}")
        print(f"Half Days: {summary['days_half_day']}")
        print(f"Days Late: {summary['days_late']}")
        print(f"Missing Checkouts: {summary['days_missing_checkout']}")
        print(f"Total Hours: {summary['total_hours']}")
