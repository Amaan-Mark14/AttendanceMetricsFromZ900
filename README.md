# Attendance Management System

A complete desktop attendance system that transforms raw biometric fingerprint logs from Z900 devices into payroll-ready attendance records. Fully offline Windows application with comprehensive reporting and audit capabilities.

## Overview

This application processes biometric scan data to calculate accurate attendance records based on configurable shifts and work schedules. It provides detailed dashboards, export functionality, and maintains a complete audit trail of all modifications.

## Key Features

### Core Functionality

* **Automated Attendance Processing**
  * Processes raw fingerprint scan logs into structured attendance data
  * Configurable shift definitions with grace periods and hour limits
  * Automatic detection of late arrivals, missing checkouts, and half-days
  * Support for custom work schedules per employee

* **Comprehensive Dashboard**
  * Monthly summary view with employee totals and statistics
  * Daily detail view with timeline visualization
  * Raw logs viewer with search and filter capabilities
  * Color-coded attendance status for easy identification

* **Employee Management**
  * Auto-import employees from scan logs
  * Custom shift assignment per employee
  * Work schedule configuration (Mon-Sun)
  * Employee activation and deactivation
  * Lock employee configurations to prevent accidental changes

* **Data Import & Integration**
  * USB drive import from Z900 devices
  * Debug data loading for testing
  * Duplicate detection and prevention
  * Support for tab-separated log files

* **Advanced Reporting**
  * Export to Excel with three comprehensive sheets:
    * Monthly Summary: Employee totals with attendance breakdown
    * Raw Logs: Complete scan data for the month
    * Daily Details: Day-by-day records with conditional formatting
  * Color-coded cells for visual analysis (Present/Absent/Late flags)
  * Custom file naming and location selection

* **Data Integrity & Security**
  * Complete audit trail of all changes
  * Month locking to protect finalized payroll data
  * Employee locking to preserve critical configurations
  * Soft delete pattern for recoverable records
  * Smart database clear that preserves locked data

## System Requirements

* **Operating System**: Windows 10 or higher
* **Disk Space**: 50 MB for application, additional space for databases
* **Permissions**: Read/write access to application folder
* **USB Import**: Removable drive named "ATTENDANCE_USB" (optional)

## Installation

### Option 1: Using Executable (Recommended)

1. Download `AttendanceSystem.exe` from the `dist` folder
2. Place the executable in your desired location
3. Double-click to run the application
4. No additional installation required

### Option 2: From Source

1. Install Python 3.8 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Usage Guide

### Getting Started

1. **Import Data**
   * Insert USB drive named "ATTENDANCE_USB" with attendance.txt file
   * Click "Read from USB" to import scan logs
   * Or use "Load Debug Data" for testing with debug.txt file

2. **Configure Employees**
   * Go to "Employees" tab
   * Employees are auto-imported from scan logs
   * Configure work schedules and shifts per employee
   * Lock employee configurations when finalized

3. **View Attendance**
   * Use "Attendance" tab for monthly summaries and daily details
   * Select month/year and choose between Monthly Summary or Daily Details view
   * Click "View" button for detailed employee breakdown

4. **Export Reports**
   * In the Attendance tab, select desired month
   * Click "Export to Excel" button
   * Choose file location and name
   * Excel file will contain three sheets with formatted data

### Managing Raw Logs

* Access "Raw Logs" tab to view all imported scan data
* Edit individual log timestamps with full audit trail
* Delete erroneous logs (soft delete with recovery option)
* Add manual logs for missing attendance records

### Data Protection

* **Lock Month**: Prevents changes to finalized monthly data
* **Lock Employee**: Protects employee configuration from accidental changes
* **Clear Database**: Removes unlocked data while preserving locked months/employees

## Input File Format

The system expects tab-separated attendance logs in the following format:

```
No	TMNo	EnNo	Name	GMNo	Mode	In/Out	Antipass	ProxyWork	DateTime
1	1	00000001	John Doe	1	FP	DutyOff	0	0	2026-02-14 16:40:09
```

## File Structure

* **USB Import Tab**: Data import and database management
* **Employees Tab**: Employee configuration and shift management
* **Attendance Tab**: Monthly summaries, daily details, and Excel export
* **Raw Logs Tab**: Individual scan log management
* **Audit Tab**: Complete history of all changes and deleted records

## Database Management

* **Automatic Creation**: Database is created automatically on first run
* **Location**: `attendance.db` in application folder
* **Locked Data**: Separate `locked_attendance.db` for protected months
* **Backup**: Regular manual backup recommended before database operations

## Troubleshooting

### Import Issues
* Ensure USB drive is named exactly "ATTENDANCE_USB"
* Verify attendance.txt file exists and is properly formatted
* Check that file is tab-separated with correct headers

### Data Display Issues
* Use "Refresh" button to reload data after imports
* Check employee activation status in Employees tab
* Verify work schedule configuration for proper holiday calculation

### Performance Issues
* For large datasets, consider locking old months to improve performance
* Use "Clear Database" to remove old unlocked data
* Regular database maintenance recommended

## Technical Details

### Attendance Calculation Logic

* **First Scan** = Check-in time
* **Last Scan** = Check-out time
* **Late Detection** = First scan after shift start + grace period
* **Half-day** = Total hours < minimum shift hours
* **Missing Checkout** = Only one scan in a day
* **Holiday** = Non-working day per employee schedule

### Data Protection Features

* **Soft Delete**: Removed logs are hidden, not deleted
* **Audit Trail**: Every change is logged with timestamp and reason
* **Lock Mechanisms**: Protected data survives database clearing
* **Transaction Safety**: Database operations use ACID compliance

## Support & Maintenance

### Regular Maintenance Tasks
* Lock completed payroll months
* Backup database before major operations
* Clear old unlocked data periodically
* Review audit logs for data integrity

### Best Practices
* Always lock months before finalizing payroll
* Use employee locking for critical configurations
* Regular backups of database files
* Test imports with debug data before production use

## Application Architecture

* **Language**: Python 3.8+
* **UI Framework**: PySide6 (Qt6)
* **Database**: SQLite
* **Export Library**: openpyxl
* **Packaging**: PyInstaller

## Limitations

* Cannot detect early leaving without checkout scan
* Physical presence duration based on first/last scan only
* Requires clean tab-separated input format
* Timeline visualization uses day-wide range (not shift-specific)
* Single admin user model for MVP

## Future Enhancements

Potential additions for future versions:
* Calendar grid view with attendance patterns
* Enhanced anomaly detection and warnings
* Automated backup and restore system
* Performance optimizations for large datasets
* Multi-user support with permissions

## License and Distribution

This is a proprietary attendance management system intended for internal organizational use. Personal usage allowed. All rights reserved.

## Version Information

* **Current Version**: 1.0.0 (MVP Release)
* **Release Date**: February 2026
* **Status**: Production Ready
* **Executable Size**: ~48 MB standalone

---

**Note**: This application is designed for offline use and does not require internet connectivity or cloud services. All data remains local on the machine where it is installed.