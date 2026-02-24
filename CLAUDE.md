# Attendance Management System - Development Guide

## Project Overview
Desktop attendance system that processes biometric fingerprint logs from standalone Z900 device into payroll-ready attendance records. Fully offline Windows .exe application.

## Core Purpose
Transform raw fingerprint scan logs → structured, shift-based attendance records with audit trail

## MVP Stack
- **Language**: Python
- **UI Framework**: PySide6 (Qt Desktop)
- **Database**: SQLite (local)
- **Packaging**: PyInstaller → .exe
- **Environment**: Fully offline, no cloud/web

## MVP Feature Scope

### Phase 1: Foundation & Data Import
1. USB Import Module
   - Detect USB by predefined name
   - Validate file structure (tab-separated format shown in Attendance formats.md)
   - Import raw logs to SQLite
   - Prevent duplicate imports
   - Show import summary

2. Database Schema
   - Employees table
   - Shifts table
   - RawLogs table
   - ProcessedAttendance table
   - EditHistory table
   - ImportBatches table

### Phase 2: Core Configuration
3. Employee Management
   - Add/edit employees (ID, Name, Assigned shift, Status)
   - Activate/deactivate employees

4. Shift Management
   - Create shifts with: start time, end time, grace period, minimum hours for "Present", maximum shift cap

### Phase 3: Attendance Processing Engine
5. Processing Logic (Critical)
   - Group logs per employee per day
   - Collapse scans within X minutes
   - First valid scan = IN, Last valid scan = OUT
   - Auto-close shifts if checkout missing
   - Cap maximum working hours
   - Calculate: total hours, late flag, half-day flag, absent flag, missing checkout flag
   - Run after import or manual recalculation

### Phase 4: User Interface
6. Month View (Essential)
   - Calendar grid view per employee
   - Daily status: P/A/H/L/MC + total hours
   - Click date → detailed daily log view

7. Daily Detail View
   - Raw logs, processed IN/OUT times, total hours, flags triggered

8. Dashboard (Simple)
   - Total employees, present/absent/late/missing checkout counts today

### Phase 5: Data Integrity & Reporting
9. Individual Log Editing (Audited)
   - Edit timestamps, add manual logs, delete logs
   - Every edit stored in EditHistory with: old value, new value, date, admin username, reason

10. Administrative Controls
    - Recalculate button (reprocess after edits)
    - Lock month feature (prevent edits after payroll finalization)
    - Data backup button
    - Import log history viewer

11. Basic Reporting
    - Monthly summary: employee ID, name, days present/absent, late count, total hours, overtime
    - Export to Excel/CSV

12. Basic Anomaly Detection
    - Missing checkout
    - Total hours > max cap
    - Only one scan in day
    - Scan outside shift window
    - Excessive scans in one day

## Input File Format
Tab-separated format (from Attendance formats.md):
```
No	TMNo	EnNo	Name	GMNo	Mode	In/Out	Antipass	ProxyWork	DateTime
1	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-14 16:40:09
```

## MVP Limitations (Accepted)
- Cannot detect early leaving without scan
- Cannot verify physical presence duration
- Relies on clean raw export format
- Admin edits can override logic (but fully logged)

## Development Phases

### Phase 1: Foundation (Weeks 1-2)
- Set up project structure
- Implement SQLite database schema
- Create USB import module
- Basic employee/shift management UI

### Phase 2: Processing Engine (Weeks 3-4)
- Build attendance processing algorithm
- Implement shift logic application
- Create recalculation engine
- Test with sample data

### Phase 3: UI Development (Weeks 5-6)
- Month view calendar interface
- Daily detail view
- Dashboard
- Log editing interface with audit trail

### Phase 4: Reporting & Admin (Weeks 7-8)
- Export functionality
- Month locking mechanism
- Backup system
- Import history viewer
- Basic anomaly detection

### Phase 5: Testing & Packaging (Week 9)
- End-to-end testing
- PyInstaller packaging
- User documentation
- Bug fixes

## Critical Design Decisions
1. **Audit Trail**: Every edit must be logged with who/when/why/what changed
2. **Shift-Based Logic**: All calculations based on assigned shift rules
3. **Offline-First**: No network dependencies, all data local
4. **Admin-Controlled**: Single admin user concept for MVP
5. **Payroll-Ready Output**: Export format suitable for payroll processing

## Testing Data Requirements
- Sample USB files with various scenarios:
  - Normal attendance patterns
  - Late arrivals
  - Missing checkouts
  - Single scan days
  - Multiple rapid scans
  - Different shift assignments

## Build & Run Commands
```bash
# Install dependencies
pip install PySide6 sqlite3 pyinstaller

# Run development version
python main.py

# Build executable
pyinstaller --onefile --windowed main.py
```

## Key Files Structure
```
attendance_system/
├── main.py                 # Application entry point
├── database/
│   ├── schema.py          # Database schema definition
│   └── migrations.py      # Database migrations
├── processing/
│   ├── attendance_engine.py  # Core processing logic
│   └── shift_manager.py      # Shift rule application
├── ui/
│   ├── main_window.py     # Main application window
│   ├── month_view.py      # Calendar view
│   ├── daily_view.py      # Daily detail view
│   └── dashboard.py       # Dashboard
├── import/
│   └── usb_import.py      # USB detection and import
├── export/
│   └── report_export.py   # Excel/CSV export
└── config/
    └── settings.py        # Application configuration
```