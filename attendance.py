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

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def mark_present(self, name: str, now: datetime | None = None) -> bool:
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
            
        )
        self.connection.commit()
