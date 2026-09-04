# Face Recognition Attendance System

A local webcam-based attendance system built with Python. The application recognizes enrolled faces, confirms identities across consecutive video frames, records attendance in SQLite, organizes attendance into named sessions, and provides a protected local dashboard for administration and reporting.

This project is intended for local educational and prototype use. It is not designed to be exposed directly to the public internet or used as a production biometric system without additional security, privacy, reliability, and compliance work.

## Features

| Area | Current functionality |
|---|---|
| Recognition | Local webcam face recognition using enrolled image samples |
| Enrollment | Guided capture of multiple face samples for each person |
| Confirmation | Requires consecutive recognition frames before recording attendance |
| Preview | Horizontally mirrored webcam preview |
| Storage | SQLite database with people, sessions, attendance, administrators, rosters, and audit logs |
| Attendance | Prevents duplicate attendance for the same person in the same session |
| Sessions | Supports named class or work sessions |
| Dashboard | Protected local Flask dashboard |
| Administration | Admin login, logout, person activation, and deactivation |
| Rosters | Expected attendees with present and absent status |
| Analytics | Totals by person, session, and date |
| Reports | Filtered attendance display and CSV export |

## Project structure

```text
Face-recognition-attendance-system/
├── app.py
├── attendance.py
├── auth.py
├── analytics.py
├── create_admin.py
├── dashboard.py
├── dashboard_utils.py
├── enroll.py
├── enrollment_utils.py
├── face_engine.py
├── migrate_csv.py
├── report.py
├── roster.py
├── requirements.txt
├── requirements-dashboard.txt
├── templates/
│   ├── analytics.html
│   ├── attendance.html
│   ├── base.html
│   ├── dashboard.html
│   ├── login.html
│   ├── people.html
│   ├── sessions.html
│   └── session_roster.html
├── static/
│   └── styles.css
├── tests/
│   ├── test_attendance.py
│   ├── test_analytics.py
│   ├── test_auth.py
│   ├── test_dashboard_utils.py
│   ├── test_enroll.py
│   ├── test_enrollment_utils.py
│   ├── test_legacy_upgrade.py
│   ├── test_people.py
│   ├── test_recognition_state.py
│   ├── test_roster.py
│   └── test_sessions.py
├── Training_images/
└── attendance.db
```

Runtime data such as `attendance.db`, face images, and generated reports should remain local and should not be committed to the repository.

## Requirements

The project requires Python 3.10 or newer. Python 3.11 or 3.12 is recommended because some older face-recognition dependencies may not yet provide smooth support for the newest Python releases.

The main application uses:

- `face-recognition` for face encodings and comparisons.
- `opencv-python` for camera capture and display.
- `numpy` for numerical processing.
- `face-recognition-models` for the pretrained recognition models.

The dashboard additionally uses Flask.

## Installation

Clone the repository and enter its directory:

```bash
git clone https://github.com/06-nitiin/Face-recognition-attendance-system.git
cd Face-recognition-attendance-system
```

Create and activate a virtual environment:

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the main dependencies:

```bash
python -m pip install -r requirements.txt
```

Install the dashboard dependency:

```bash
python -m pip install -r requirements-dashboard.txt
```

If the face-recognition model package is missing, install it inside the active virtual environment:

```bash
python -m pip install face-recognition-models==0.3.0
```

Use the same Python environment for every command. On macOS, `python` may not exist outside a virtual environment, while `python3` may point to a different installation. After activation, verify the interpreter:

```bash
which python
python --version
python -m pip --version
```

## Enroll a person

Create the training directory if it does not exist:

```bash
mkdir -p Training_images
```

Enroll a person with a name:

```bash
python enroll.py "Nitin" --force
```

Enrollment captures five samples by default. During enrollment:

1. Keep exactly one face in the camera view.
2. Wait for the `READY` message.
3. Press `s` to save a sample.
4. Repeat until all requested samples are captured.
5. Press `q` to cancel.

Enroll with optional metadata:

```bash
python enroll.py "Nitin" \
  --person-id STU-001 \
  --email nitin@example.com \
  --force
```

The `--force` option replaces existing samples for the same person. Use it when you want to recapture enrollment images.

To capture a different number of samples:

```bash
python enroll.py "Nitin" --samples 3 --force
```

Enrollment samples are stored locally using names similar to:

```text
Training_images/Nitin__1.jpg
Training_images/Nitin__2.jpg
Training_images/Nitin__3.jpg
```

## Run face recognition

Start the attendance application:

```bash
python app.py
```

Start it with a named session:

```bash
python app.py --session-name "Math Class"
```

The application creates a new session for each run. It displays a mirrored camera preview and confirms a recognized person across consecutive frames before attempting to record attendance.

Useful options include:

```bash
python app.py --confirm-frames 5 --cooldown 10
```

The default values are five confirmation frames and a ten-second session cooldown.

Press `q` in the camera window to exit. `Ctrl+C` in the terminal is also handled cleanly.

The terminal may display a warning similar to:

```text
pkg_resources is deprecated as an API
```

This is a dependency warning from `face_recognition_models`. It does not mean that recognition failed if the application continues to run.

## Create an administrator account

Create a local dashboard administrator:

```bash
python create_admin.py admin
```

The command prompts for the password without displaying it. Passwords must contain at least eight characters.

Passwords are stored as hashes rather than plain text.

## Start the protected dashboard

Generate a Flask secret key once:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Save it in your Zsh configuration on macOS or Linux:

```bash
echo 'export DASHBOARD_SECRET_KEY="paste-your-generated-key-here"' >> ~/.zshrc
source ~/.zshrc
```

Verify that the variable is available:

```bash
echo "$DASHBOARD_SECRET_KEY"
```

Start the dashboard:

```bash
python dashboard.py
```

Open the local dashboard at:

```text
http://127.0.0.1:5000
```

The dashboard requires the administrator credentials created with `create_admin.py`.

The secret key must not be committed to GitHub. It is used to sign Flask login sessions. Reusing the same key means you do not need to generate a new one for every dashboard launch.

## Dashboard pages

| Page | URL | Purpose |
|---|---|---|
| Overview | `/` | Counts, recent attendance, and recent admin activity |
| People | `/people` | Registered people and active/inactive controls |
| Sessions | `/sessions` | Named session history |
| Attendance | `/attendance` | Attendance records with date and session filters |
| Analytics | `/analytics` | Totals by person, session, and date |
| Session roster | `/sessions/<id>/roster` | Expected attendees and present/absent status |
| CSV export | `/attendance/export` | Download filtered attendance records |

## Manage a session roster

1. Start a named session with `app.py`.
2. Open the dashboard.
3. Open the **Sessions** page.
4. Select **Manage roster** beside a session.
5. Select the people expected to attend.
6. Select **Save roster**.

The roster page compares the selected people with attendance records for that session.

A person appears as:

- **Present** when they are on the roster and have an attendance record for that session.
- **Absent** when they are on the roster but do not have an attendance record.
- **Not on roster** when they are not expected for that session.

Roster configuration is optional. Existing recognition and attendance behavior continues to work without a roster.

## Generate reports

Print all attendance records:

```bash
python report.py
```

Filter by date:

```bash
python report.py --date 2026-09-02
```

Filter by session ID:

```bash
python report.py --session-id 5
```

Export records to CSV:

```bash
python report.py --output attendance-report.csv
```

The dashboard also provides a filtered CSV export button.

## Import older CSV data

The CSV migration utility supports common formats with either two or three columns.

Import a CSV file:

```bash
python migrate_csv.py Attendance.csv
```

Use a named imported session:

```bash
python migrate_csv.py Attendance.csv --session-name "Imported attendance"
```

The utility preserves valid rows and skips malformed rows with a message.

## Database

The SQLite database is normally stored at:

```text
attendance.db
```

The database includes these logical areas:

| Table | Purpose |
|---|---|
| `people` | Registered person metadata |
| `sessions` | Named attendance sessions |
| `attendance` | Attendance records linked to people and sessions |
| `session_roster` | Expected people for each session |
| `admin_users` | Hashed dashboard administrator credentials |
| `audit_logs` | Administrative activity history |

The application upgrades older database structures automatically where supported. Do not delete `attendance.db` unless you intentionally want to remove local attendance history.

Inspect tables:

```bash
sqlite3 attendance.db ".tables"
```

Inspect people:

```bash
sqlite3 attendance.db "SELECT id, name, external_id, email, is_active FROM people;"
```

Inspect linked attendance:

```bash
sqlite3 attendance.db "
SELECT people.name, sessions.name, sessions.session_date, attendance.check_in_time
FROM attendance
JOIN people ON people.id = attendance.person_id
JOIN sessions ON sessions.id = attendance.session_id;
"
```

## Testing

Run the complete test suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

The tests cover:

- Attendance uniqueness.
- Date-aware storage.
- SQLite migration.
- Person metadata.
- Session behavior.
- Roster behavior.
- Present and absent status.
- Recognition confirmation.
- Session cooldown.
- Dashboard filtering.
- Analytics calculations.
- Password hashing.
- Authentication.
- Audit logging.

A successful run ends with:

```text
OK
```

## Privacy and security

Face images and biometric encodings are sensitive personal data. Obtain appropriate consent before enrolling anyone.

Keep these files private:

```text
Training_images/
attendance.db
Attendance.csv
*.csv
.env
```

Do not commit real face images, attendance records, passwords, secret keys, or personal metadata to GitHub.

The local dashboard should bind to `127.0.0.1` during development. Do not use the Flask development server as a public production server.

The current system provides basic local authentication. It does not yet provide all controls expected of a production biometric system, such as strong role separation, rate limiting, CSRF protection, encrypted biometric storage, consent management, retention policies, or regulatory compliance workflows.

## Troubleshooting

### `python: command not found`

Use `python3`, or activate the virtual environment:

```bash
source .venv/bin/activate
```

Then use:

```bash
python app.py
```

### `ModuleNotFoundError: No module named 'cv2'`

Install the dependencies inside the active virtual environment:

```bash
python -m pip install -r requirements.txt
```

### Missing `face_recognition_models`

Install the model package inside the active virtual environment:

```bash
python -m pip install face-recognition-models==0.3.0
```

### Camera cannot open

Check macOS camera permissions:

```text
System Settings → Privacy & Security → Camera
```

Enable access for the terminal or application that launches Python.

You can try another camera index:

```bash
python app.py --camera 1
```

### Dashboard redirects to login

Confirm that:

- The admin account exists.
- The dashboard is using the expected database.
- The browser is not blocking local cookies.
- `DASHBOARD_SECRET_KEY` is set consistently.

### Dashboard says `no such table`

Start the dashboard or initialize the database through Python using the repository's active virtual environment. The updated storage layer creates and upgrades the required tables automatically.

### Attendance already recorded

This means the person has already been recorded for the current session. It is normal duplicate-prevention behavior.

## License

Add the license that you choose for this project before distributing it publicly. If no license is present, normal copyright restrictions apply.

## References

[1]: https://github.com/06-nitiin/Face-recognition-attendance-system "Face Recognition Attendance System repository"
[2]: https://docs.python.org/3/library/venv.html "Python virtual environment documentation"
[3]: https://flask.palletsprojects.com/ "Flask documentation"
[4]: https://opencv.org/ "OpenCV project"
[5]: https://github.com/ageitgey/face_recognition "face_recognition project"
[6]: https://www.sqlite.org/docs.html "SQLite documentation"


## Operational maintenance

The system includes local tools for correcting records, backing up the database, and checking project readiness before use.

### Correct an attendance record

Administrators can void an incorrect attendance record from the protected dashboard. Voiding does not delete the original row. It creates a separate correction record containing the reason, administrator, and correction time.

A voided record can be restored from the dashboard. Active CSV exports exclude voided records.

The correction history can be inspected with:

```bash
sqlite3 attendance.db "
SELECT record_id, status, reason, corrected_by, corrected_at
FROM attendance_corrections
ORDER BY corrected_at DESC;
"
```

### Back up the database

Create a local backup before database changes:

```bash
mkdir -p backups
python backup.py backup \
  --database attendance.db \
  --output "backups/attendance-$(date +%Y-%m-%d-%H%M%S).db"
```

Validate a backup:

```bash
python -c "from backup import check_integrity; from pathlib import Path; print(check_integrity(Path('backups/attendance-backup.db')))"
```

A valid backup prints:

```text
True
```

Restore to a separate test database before replacing the active database:

```bash
python backup.py restore \
  --backup backups/attendance-backup.db \
  --database restored-attendance.db
```

The restore command creates a safety copy automatically when replacing an existing database. Do not restore over `attendance.db` unless you intentionally want to replace its current contents.

Keep database backups private. They may contain biometric-related metadata, attendance history, administrator records, and personal information.

### Health check

Run the project health check from the repository root:

```bash
python healthcheck.py
```

A successful check prints:

```text
Project health check passed.
```

The health check verifies SQLite integrity, required database tables, required Python packages, the training-image directory, and configuration values. It checks for these tables:

```text
people
sessions
attendance
session_roster
admin_users
audit_logs
attendance_corrections
```

Run the final automated test suite with:

```bash
python -m unittest discover -s tests -v
```

A successful test run ends with:

```text
OK
```

### Centralized configuration

The optional `config.py` module reads configuration from environment variables:

| Variable | Default | Purpose |
|---|---:|---|
| `ATTENDANCE_DATABASE` | `attendance.db` | SQLite database path |
| `ATTENDANCE_TRAINING_DIR` | `Training_images` | Enrollment-image directory |
| `ATTENDANCE_CAMERA` | `0` | Camera index |
| `ATTENDANCE_TOLERANCE` | `0.5` | Face comparison tolerance |
| `ATTENDANCE_CONFIRM_FRAMES` | `5` | Required consecutive confirmation frames |
| `ATTENDANCE_COOLDOWN` | `10` | Recognition cooldown in seconds |
| `DASHBOARD_HOST` | `127.0.0.1` | Local dashboard host |
| `DASHBOARD_PORT` | `5000` | Local dashboard port |
| `DASHBOARD_SECRET_KEY` | None | Flask session-signing secret |

Use `.env.example` as a reference. Do not commit a real secret key or a file containing real environment values.

## Current completion status

The project currently supports the complete local workflow:

```text
Enroll a person
    ↓
Capture multiple face samples
    ↓
Recognize faces through the webcam
    ↓
Confirm identities across frames
    ↓
Create a named attendance session
    ↓
Record attendance in SQLite
    ↓
Manage rosters and present/absent status
    ↓
Review analytics and export reports
    ↓
Correct records without deleting history
    ↓
Protect administration with login and audit logs
    ↓
Back up and validate the database
```

The application is complete as a local educational prototype. Further work would be optional product development rather than required functionality, such as deployment architecture, stronger production security, encrypted biometric storage, advanced reporting, mobile access, or integration with an institutional identity system.
