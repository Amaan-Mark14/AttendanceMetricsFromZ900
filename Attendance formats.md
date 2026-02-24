File 1 
No	TMNo	EnNo	Name	GMNo	Mode	In/Out	Antipass	ProxyWork	DateTime
1	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-14 16:40:09
2	1	00000004	t	1	FP	DutyOff	0	0	2026-02-14 16:41:11
3	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-24 16:15:10
4	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-24 16:25:56
5	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-24 16:38:59

File 2 
No	TMNo	EnNo	Name	GMNo	Mode	In/Out	Antipass	ProxyWork	DateTime
1	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-14 16:40:09
2	1	00000004	t	1	FP	DutyOff	0	0	2026-02-14 16:41:11
3	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-24 16:15:10
4	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-24 16:25:56
5	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-24 16:38:59
6	1	00000001	amaan	1	FP	DutyOff	0	0	2026-02-24 17:22:16
7	1	00000004	t	1	FP	DutyOff	0	0	2026-02-24 17:22:24


Project Summary

This project is a desktop attendance management system that processes biometric fingerprint logs exported from a standalone device and converts them into structured, payroll-ready attendance records.

The biometric device only verifies identity and records timestamps. This software becomes the intelligence layer that:

Interprets raw scan logs

Applies shift rules

Calculates working hours

Detects anomalies

Generates monthly attendance summaries


It is designed to operate fully offline as a Windows .exe application, importing data via USB and storing all records locally.


---

Core Purpose

Transform unstructured fingerprint scan logs into:

Daily attendance records

Monthly summaries

Payroll-ready hour calculations

Behavioral flags (late, missing checkout, anomalies)


While maintaining auditability and administrative control.


---

Functional Requirements

1. Data Import

Detect USB with predefined name

Validate log file structure

Import and store raw logs

Prevent duplicate imports

Log import batches



---

2. Employee Management

Add/edit employees

Assign shifts

Activate/deactivate employees



---

3. Shift Configuration

Define shift start/end time

Define grace period

Set minimum hours for “Present”

Set maximum shift cap



---

4. Attendance Processing Engine

Group logs per employee per day

Determine first scan (IN)

Determine last scan (OUT)

Auto-close shifts if checkout missing

Cap maximum working hours

Mark Present / Half-day / Absent

Flag Late arrivals

Flag Missing checkout



---

5. Manual Log Editing (Audited)

Edit timestamps

Add missing entries

Delete incorrect entries

Store full edit history (who, when, what changed, reason)



---

6. Month View Interface

Calendar view per employee

Display daily status and total hours

Click date to view detailed logs



---

7. Reporting

Monthly attendance summary

Total hours worked

Days present / absent

Late count

Missing checkout count

Export to Excel/CSV



---

8. Basic Anomaly Detection

Excessive working hours

Single scan days

Multiple rapid scans

Scan outside shift window

Repeated missing checkouts



---

9. Administrative Controls

Recalculate attendance after edits

Lock finalized months

Database backup

Import history tracking



---

System Characteristics

Fully offline

Single executable deployment

SQLite local database

Payroll-supportive logic

Audit-compliant

Designed to reduce gaming within hardware limitations



---

What It Does Not Do

Does not enforce physical presence

Does not track building entry/exit

Does not prevent early leaving without scan

Does not replace access control hardware



---

Final Definition

A controlled, auditable attendance analytics system that converts raw biometric timestamp logs into structured, shift-based attendance records suitable for HR and payroll use.


Below is a clean MVP outline including your additions and only what is realistically necessary for a strong first version.

This assumes:

Offline

USB import

Shift-based logic

Payroll-ready hours calculation

Admin-operated system



---

✅ MVP OBJECTIVE

A stable desktop app that:

Imports biometric logs from USB

Applies shift logic

Calculates daily/monthly attendance

Allows controlled manual corrections

Generates payroll-ready summaries

Flags basic anomalies



---

1️⃣ Core Stack (MVP)

Python

PySide6 (Qt Desktop UI)

SQLite (local DB)

PyInstaller → .exe packaging


No cloud. No web. Fully offline.


---

2️⃣ MVP FEATURE OUTLINE


---

A. USB Import Module

Features:

Detect USB by name

Detect expected file name

Validate file structure

Import raw logs

Prevent duplicate imports

Show import summary:

Rows imported

Duplicates skipped

Errors detected



Required for MVP:

Yes.


---

B. Employee Management

Features:

Add employee

Edit employee

Assign shift

Activate / deactivate employee


Minimum fields:

Employee ID

Name

Assigned shift

Status



---

C. Shift Management

Features:

Create shift

Define:

Start time

End time

Grace period

Minimum hours for "Present"

Maximum shift cap




---

D. Attendance Processing Engine

Daily per employee:

Collapse scans within X minutes

First valid scan = IN

Last valid scan = OUT

Auto close if no OUT

Cap maximum hours

Calculate:

Total hours

Late flag

Half-day flag

Absent flag

Missing checkout flag



This runs:

After import

Or when month recalculated



---

E. Month View (Your Requirement)

Calendar Grid View

For selected employee:

Each date shows:

P = Present

A = Absent

H = Half day

L = Late

MC = Missing checkout

Total hours


Clicking a date:

Opens detailed daily log


This is essential for payroll clarity.


---

F. Individual Log Editing (Your Requirement)

This must be controlled and auditable.

Allowed Actions:

Edit timestamp

Add manual log

Delete log


Critical MVP Rule:

Every edit must:

Be stored in Edit History table

Record:

Old value

New value

Date edited

Admin username

Reason



Without edit audit trail, payroll credibility is lost.


---

G. Daily Detail View

For selected employee + date:

Show:

Raw logs

Processed IN time

Processed OUT time

Total hours

Flags triggered



---

H. Dashboard (Simple MVP Version)

Overview screen:

Total employees

Present today

Absent today

Late today

Missing checkout today


No advanced analytics yet.


---

I. Reports (Basic)

Export monthly:

Employee ID

Name

Days present

Days absent

Late count

Total hours

Overtime hours (if defined)


Export to:

Excel

CSV


PDF optional in MVP.


---

J. Basic Anomaly Flags (MVP Level)

Detect:

Missing checkout

Total hours > max cap

Only one scan in day

Scan outside shift window

More than X scans in one day


Just flag. No scoring system yet.


---

3️⃣ Database Tables (MVP)

Employees

Shifts

RawLogs

ProcessedAttendance

EditHistory

ImportBatches

Keep it clean and minimal.


---

4️⃣ What Else Should Be in MVP?

These are small but important additions:


---

1. Recalculate Button

If admin edits logs → system must reprocess that day/month.


---

2. Lock Month Feature

After payroll is finalized:

Lock month

Prevent edits unless unlocked by admin


Critical for integrity.


---

3. Data Backup Button

Manual backup of database file.


---

4. Import Log History

Show:

When imports happened

How many records

From which file



---

5️⃣ What NOT To Include in MVP

Avoid:

Role-based login (add later)

Department analytics

Compliance scoring

Real-time syncing

Cloud

Advanced charts

Biometric integration


Keep MVP stable and controlled.


---

6️⃣ Realistic MVP Scope Summary

MVP Includes:

✔ USB import
✔ Shift system
✔ Daily attendance calculation
✔ Month calendar view
✔ Individual log editing (audited)
✔ Basic anomaly flags
✔ Monthly report export
✔ Recalculation engine
✔ Month locking

That is a complete, usable HR attendance tool.


---

7️⃣ MVP Limitations (Accept These)

Cannot detect early leaving without scan

Cannot verify physical presence duration

Relies on clean raw export format

Admin edits can override logic (but logged)



---

8️⃣ Complexity Level

This MVP is:

Medium complexity
Very manageable
Professional-grade if structured well


---

If you want next, I can:

Define exact attendance calculation rules formally

Or design the database schema structure cleanly

Or outline UI layout screens in detail