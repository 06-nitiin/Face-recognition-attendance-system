Face Recognition Attendance System

A local webcam prototype that recognizes enrolled faces and records one attendance entry per person in a CSV file.

This repository is being revived incrementally. Milestone 1 focuses on making the original prototype reliable and understandable. SQLite, date-aware attendance, enrollment, and a dashboard will be introduced in later milestones.

# Features

Real-time face recognition through a webcam.
One image per enrolled person.
Configurable camera index.
Configurable recognition tolerance.
Safe handling of missing or invalid training images.
Unknown-face labeling.
Duplicate prevention within the current attendance file.
Graceful camera and window cleanup.


# Requirements

Python 3.10 or newer.
A working webcam.
Native build support may be required by face-recognition and its dlib dependency, depending on your operating system.

# Setup

Clone the repository and enter its directory:

Bash


git clone https://github.com/06-nitiin/Face-recognition-attendance-system.git
cd Face-recognition-attendance-system



Create and activate a virtual environment:

Bash
python -m venv .venv

On macOS/Linux:
Bash
source .venv/bin/activate

On Windows PowerShell:
Plain Text
.venv\Scripts\Activate.ps1


Install dependencies:
Bash

python -m pip install --upgrade pip
python -m pip install -r requirements.txt


Add training images

Place one clear image containing exactly one face inside Training_images/.

The filename becomes the recognized name. For example:

Plain Text


Training_images/
├── Alice.jpg
└── Bob.png



Use front-facing, well-lit images. Do not commit personal face images or real attendance data to a public repository. The .gitignore file excludes them by default.

Run

Start the application with the default camera:

Bash


python app.py



Use a different camera and a stricter recognition threshold when needed:

Bash


python app.py --camera 1 --tolerance 0.45



Lower tolerance values are stricter. If the value is too low, valid faces may be labeled unknown; if it is too high, false matches become more likely.

Press q in the camera window to stop the application.

Output

The prototype writes records to Attendance.csv using this temporary format:

Plain Text


name,time
Alice,09:15:22



This storage format is intentionally temporary. The next milestone will introduce date-aware attendance rules, followed by SQLite storage.

Project structure

Plain Text


.
├── app.py              # Command-line application and webcam loop
├── attendance.py       # CSV attendance storage
├── face_engine.py      # Face loading, encoding, and recognition
├── Training_images/    # Local enrollment images; ignored by Git
├── Attendance.csv      # Local runtime data; ignored by Git
├── requirements.txt
└── .gitignore



Limitations

This is an educational prototype. It does not yet include authentication, liveness detection, a database, date-aware sessions, an enrollment interface, reporting, or protection against spoofing. Face recognition can produce false positives and false negatives, so this system should not be used for high-stakes decisions without proper validation and safeguards.

