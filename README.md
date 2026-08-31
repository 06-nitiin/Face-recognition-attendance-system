# Face Recognition Attendance System

A local webcam prototype that recognizes enrolled faces and records attendance in a CSV file.

# Date-aware attendance

This milestone keeps CSV storage but fixes the original attendance rule. A person can now be marked once per day instead of once forever.

# Attendance format

Records use this format:

## Plain Text


name,date,time
Nitin,2026-08-31,22:31:22



The date uses ISO format (YYYY-MM-DD), which makes records easier to sort and migrate into a database later.

Legacy file migration

If an existing local Attendance.csv uses the old format:

## Plain Text


name,time
Nitin,22:31:22



AttendanceStore automatically converts it to the new three-column format when the application starts. Because the old format did not save dates, migrated rows are assigned the date on which the migration runs. This limitation is documented and will disappear once attendance is moved to a database.

Run the application

Activate the virtual environment and run:

Bash


source .venv/bin/activate
python app.py



The webcam recognition behavior remains the same as Milestone 1. The application calls AttendanceStore.mark_present() for recognized faces, and the store prevents duplicates for the same name and date.

Run the tests

The tests use Python's built-in unittest module, so no additional test dependency is needed:

Bash


python -m unittest discover -s tests -v



The tests cover duplicate prevention, attendance across different days, case-insensitive names, legacy CSV migration, and invalid empty names.

Project structure

Plain Text


.
├── app.py
├── attendance.py
├── face_engine.py
├── Attendance.example.csv
├── Attendance.csv          # local runtime file, ignored by Git
├── Training_images/        # local face images, ignored by Git
└── tests/
    └── test_attendance.py



Current limitations

CSV is still a temporary storage solution. The next milestone will introduce SQLite, stronger constraints, person IDs, and a schema suitable for attendance sessions and reporting. This remains an educational prototype and should not be used for high-stakes decisions without validation, consent, and privacy safeguards.

