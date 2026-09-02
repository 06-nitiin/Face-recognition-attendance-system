import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class AttendanceRecord:
    id: int
    name: str
    attendance_date: str
    time: str
    created_at: str


class AttendanceStore:
    """SQLite-backed attendance storage with one record per person per day."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def mark_present(self, name: str, now: datetime | None = None) -> bool:
        """Record attendance once per person per day.

        Returns True when a new row is inserted and False when the database
        uniqueness rule rejects a duplicate for the same person and date.
        """
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Attendance name cannot be empty.")

        timestamp = now or datetime.now()
        attendance_date = timestamp.date().isoformat()
        attendance_time = timestamp.strftime("%H:%M:%S")
        created_at = timestamp.isoformat(timespec="seconds")

        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO attendance
                (name, attendance_date, check_in_time, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (clean_name, attendance_date, attendance_time, created_at),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def records(self) -> list[AttendanceRecord]:
        rows = self.connection.execute(
            """
            SELECT id, name, attendance_date, check_in_time, created_at
            FROM attendance
            ORDER BY attendance_date DESC, check_in_time DESC, name COLLATE NOCASE
            """
        ).fetchall()
        return [
            AttendanceRecord(
                id=row["id"],
                name=row["name"],
                attendance_date=row["attendance_date"],
                time=row["check_in_time"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def close(self) -> None:
        self.connection.close()

    def _initialize_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                attendance_date TEXT NOT NULL,
                check_in_time TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (name COLLATE NOCASE, attendance_date)
            )
            """
        )
        self.connection.commit()
