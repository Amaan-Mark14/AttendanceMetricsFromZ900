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

---

## ✅ COMPLETED FEATURES (Current Status: ~75% MVP Complete)

### ✅ Phase 1: Foundation & Data Import
1. **USB Import Module** (`import_usb.py`)
   - Detect USB by predefined name (ATTENDANCE_USB)
   - Validate file structure (tab-separated format)
   - Import raw logs to SQLite with duplicate prevention
   - Show import summary with records imported/skipped
   - Debug data loading from debug.txt for testing

2. **Database Schema** (All in SQLite via `main.py`)
   - ✅ `raw_logs` - Imported scan data with soft delete (hidden flag)
   - ✅ `employees` - Employee records with work_schedule, is_locked flags
   - ✅ `shifts` - Shift definitions with times, grace period, min/max hours
   - ✅ `import_batches` - Import tracking
   - ✅ `month_locks` - Month locking records
   - ✅ `edit_history` - Complete audit trail
   - ✅ `locked_attendance.db` - Separate database for locked months

### ✅ Phase 2: Core Configuration
3. **Employee Management** (`employees.py`)
   - Auto-import employees from raw logs
   - Add/edit employees with custom shifts
   - Activate/deactivate employees
   - Lock/unlock employee configuration (prevents accidental changes)
   - Work schedule configuration (Mon-Sun checkboxes)
   - Shift configuration per employee (start, end, grace, min/max hours)

4. **Shift Management**
   - Create shifts with: start time, end time, grace period, minimum hours, maximum hours
   - Default Shift auto-created
   - Employee-specific shifts automatically created on config save

### ✅ Phase 3: Attendance Processing Engine
5. **Processing Logic** (`attendance_processor.py`)
   - **On-Demand Calculation** - No stored results, calculates from raw_logs when needed
   - First valid scan = IN, Last valid scan = OUT
   - Total hours calculation with max cap
   - Late detection (shift start + grace period)
   - Status determination: Present, Half-day, Absent, Holiday
   - Work schedule filtering (non-working days = Holiday)
   - Missing checkout detection (single scan days)
   - Per-employee shift rules application

### ✅ Phase 4: User Interface
6. **Monthly Summary View** (`attendance_dashboard.py`)
   - Employee list with monthly totals
   - Color-coded bold text: Present (green), Absent (red), Half-day (orange), Holidays (blue)
   - Late count, Missing checkout count, Total hours, Working days
   - Details button for per-employee breakdown
   - Lock/Unlock month button

7. **Daily Detail View** (`attendance_dashboard.py`)
   - Single day view for all active employees
   - Status with colors: Present (green), Absent (red), Half-day (orange), Holiday (purple)
   - **Timeline visualization** - Green bar showing employee presence duration
   - First scan, Last scan, Total hours, Flags
   - Day navigation (Previous/Next buttons)
   - Date picker for quick navigation

8. **Raw Logs Dashboard** (`dashboard.py`)
   - View all imported logs
   - Delete individual logs (soft delete with audit trail)
   - Edit log timestamps (with audit trail)
   - Add manual logs (with audit trail)

### ✅ Phase 5: Data Integrity & Reporting
9. **Individual Log Editing (Fully Audited)** (`dashboard.py`, `audit_tab.py`)
   - Edit timestamps → logged in edit_history
   - Delete logs → soft delete (hidden=1), logged in edit_history
   - Add manual logs → mode='Manual', logged in edit_history
   - All edits tracked: table_name, record_id, action, old_value, new_value, reason

10. **Administrative Controls**
    - ✅ **Lock Month** - Copies data to locked_attendance.db, prevents deletion
    - ✅ **Lock Employee** - Prevents configuration changes, preserves through database clear
    - ✅ **Clear Database** - Smart deletion that preserves:
      - Locked months (raw_logs protected)
      - Locked employees (employee + shift preserved)
    - ✅ **Audit Tab** - Three sub-tabs:
      - Edit History (color-coded: DELETE=red, INSERT=green, UPDATE=blue)
      - Deleted Logs (soft-deleted logs with Restore button)
      - Manual Logs (all mode='Manual' entries)

11. **Basic Reporting** (Partially Complete)
    - ✅ Monthly summary per employee
    - ✅ Holiday tracking (non-working days excluded from calculations)
    - ❌ Export to Excel/CSV (TODO)

12. **Basic Anomaly Detection** (Built into processing)
    - ✅ Missing checkout flag
    - ✅ Total hours capping (max_hours from shift)
    - ✅ Single scan days detected
    - ✅ Late arrivals detected
    - ❌ Scan outside shift window warning (TODO)
    - ❌ Excessive scans warning (TODO)

---

## Input File Format
Tab-separated format:
```
No	TMNo	EnNo	Name	GMNo	Mode	In/Out	Antipass	ProxyWork	DateTime
1	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-14 16:40:09
```

---

## Architecture Decisions Implemented

### 1. **On-Demand Calculation** (Critical)
- **Decision**: Do NOT store processed attendance results
- **Implementation**: `AttendanceCalculator` calculates from `raw_logs` when needed
- **Benefits**:
  - Single source of truth (raw_logs)
  - No sync issues between raw and processed data
  - Simplified edit handling (just edit raw log, recalculate)
  - Smaller database size

### 2. **Soft Delete Pattern**
- **Implementation**: `hidden` column in `raw_logs`
- **Benefits**:
  - Audit trail preserved
  - Logs can be restored
  - Edit history shows deletions

### 3. **Lock Pattern**
- **Month Lock**: Copies data to separate `locked_attendance.db`
  - Survives "Clear Database" operations
  - Prevents accidental deletion of finalized payroll data
- **Employee Lock**: `is_locked` flag in employees table
  - Prevents configuration changes
  - Preserves employee + shift through database clear

### 4. **Work Schedule**
- **Implementation**: 7-character string (Mon-Sun) like "1111110"
- **Benefits**:
  - Non-working days show as "Holiday" not "Absent"
  - Custom schedules per employee
  - Excluded from totals (total_days, total_hours)

---

## Current File Structure
```
AttendanceMetricsFromZ900/
├── main.py                    # Application entry point, DB init, tab management
├── attendance_processor.py    # Core calculation engine (on-demand)
├── attendance_dashboard.py    # Monthly/Daily views with timeline
├── employees.py               # Employee management with locking
├── audit_tab.py               # Edit history, deleted logs, manual logs
├── import_usb.py              # USB detection and import
├── dashboard.py               # Raw logs viewer with edit/delete
├── CLAUDE.md                  # This file
└── attendance.db              # SQLite database (created at runtime)
```

---

## Database Schema

### raw_logs
```sql
- id, import_batch_id, no, tm_no, en_no, name, gm_no, mode, in_out
- datetime, hidden (soft delete flag), created_at
```

### employees
```sql
- id, en_no (unique), name, gm_no
- shift_id (FK to shifts)
- is_active, is_locked, work_schedule (7-char string)
```

### shifts
```sql
- id, name (unique), start_time, end_time
- grace_period, minimum_hours, maximum_hours, is_active
```

### month_locks
```sql
- year, month (composite PK), locked_at
```

### edit_history
```sql
- id, table_name, record_id, action
- old_value, new_value, reason, edited_by, edited_at
```

### import_batches
```sql
- id, import_date, file_name, records_count, status
```

---

## Build & Run Commands
```bash
# Install dependencies
pip install PySide6

# Run development version
python main.py

# Build executable (TODO - test this)
pyinstaller --onefile --windowed --name "AttendanceSystem" main.py
```

---

## MVP Limitations (Accepted)
- Cannot detect early leaving without checkout scan
- Cannot verify physical presence duration (just first/last scan)
- Relies on clean raw export format
- Admin edits can override logic (but fully logged in edit_history)
- Timeline visualization uses day-wide range, not employee-specific shift boundaries (known limitation)

---

## 📋 NEXT STEPS (Priority Order)

### 1. **Export to Excel/CSV** (High Priority)
- Add export button to monthly summary
- Export to Excel with formatting
- Export to CSV for payroll integration
- Include all columns: En No, Name, Present, Absent, Holidays, Half-days, Late, Missing Checkout, Total Hours

### 2. **Calendar Grid View** (Medium Priority)
- Traditional calendar view showing all employees
- Each cell = P/A/H/L/MC status for that day
- Click cell → show daily details for that employee
- Heatmap coloring for attendance patterns

### 3. **Anomaly Warnings** (Low Priority)
- Show warnings for:
  - Scans outside shift window (early arrival, late departure)
  - Excessive scans in one day (>10 scans)
  - Duplicate timestamps
- Display in daily view with visual indicators

### 4. **Backup/Restore System** (Low Priority)
- Backup button → zip entire database
- Restore functionality
- Automatic backup before database clear
- Backup before locking month

### 5. **Testing & Packaging**
- End-to-end testing with real data
- PyInstaller packaging test
- Create installer (NSIS or Inno Setup)
- User documentation (README, quick start guide)

### 6. **Performance Optimization** (If Needed)
- Add indexes to raw_logs (en_no, datetime)
- Pagination for large datasets
- Lazy loading for monthly view
- Progress indicators for long operations

---

## Critical Design Decisions (Maintained)
1. **Audit Trail**: Every edit logged with who/when/why/what changed
2. **Shift-Based Logic**: All calculations based on assigned shift rules
3. **Offline-First**: No network dependencies, all data local
4. **Admin-Controlled**: Single admin concept for MVP
5. **Payroll-Ready Output**: Export format suitable for payroll processing

---

## Testing Data Requirements
- ✅ debug.txt for basic testing
- Need sample USB files with:
  - Normal attendance patterns
  - Late arrivals
  - Missing checkouts
  - Single scan days
  - Multiple rapid scans
  - Different shift assignments
  - Holiday scenarios (Sundays, custom schedules)