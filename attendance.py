import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Person:
    id: int
    name: str
    external_id: str | None
    email: str | None
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AttendanceRecord:
    id: int
    person_id: int
    name: str
    attendance_date: str
    time: str
    created_at: str


class AttendanceStore:
    """SQLite storage for people and one attendance record per person per day."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialize_schema()

    def register_person(
        self,
        name: str,
        external_id: str | None = None,
        email: str | None = None,
    ) -> Person:
        clean_name = name.strip()
        clean_external_id = external_id.strip() if external_id else None
        clean_email = email.strip() if email else None
        if not clean_name:
            raise ValueError("Person name cannot be empty.")

        now = datetime.now().isoformat(timespec="seconds")
        existing = self._person_by_name(clean_name)
        if existing:
            self.connection.execute(
                """
                UPDATE people
                SET external_id = ?, email = ?, updated_at = ?
                WHERE id = ?
                """,
                (clean_external_id, clean_email, now, existing.id),
            )
            self.connection.commit()
            return self.get_person(existing.id)

        try:
            cursor = self.connection.execute(
                """
                INSERT INTO people (name, external_id, email, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                """,
                (clean_name, clean_external_id, clean_email, now, now),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as error:
            self.connection.rollback()
            raise ValueError(
                "A person with this name or external ID already exists."
            ) from error
        return self.get_person(cursor.lastrowid)

    def get_person(self, person_id: int) -> Person:
        row = self.connection.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Person {person_id} does not exist.")
        return self._person_from_row(row)

    def list_people(self, active_only: bool = False) -> list[Person]:
        query = "SELECT * FROM people"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name COLLATE NOCASE"
        rows = self.connection.execute(query).fetchall()
        return [self._person_from_row(row) for row in rows]

    def set_person_active(self, person_id: int, active: bool) -> None:
        self.connection.execute(
            "UPDATE people SET is_active = ?, updated_at = ? WHERE id = ?",
            (int(active), datetime.now().isoformat(timespec="seconds"), person_id),
        )
        self.connection.commit()

    def mark_present(self, name: str, now: datetime | None = None) -> bool:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Attendance name cannot be empty.")

        person = self._person_by_name(clean_name) or self.register_person(clean_name)
        if not person.is_active:
            return False

        timestamp = now or datetime.now()
        attendance_date = timestamp.date().isoformat()
        attendance_time = timestamp.strftime("%H:%M:%S")
        created_at = timestamp.isoformat(timespec="seconds")
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO attendance
                (person_id, name, attendance_date, check_in_time, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (person.id, person.name, attendance_date, attendance_time, created_at),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def records(self) -> list[AttendanceRecord]:
        rows = self.connection.execute(
            """
            SELECT id, person_id, name, attendance_date, check_in_time, created_at
            FROM attendance
            ORDER BY attendance_date DESC, check_in_time DESC, name COLLATE NOCASE
            """
        ).fetchall()
        return [
            AttendanceRecord(
                id=row["id"],
                person_id=row["person_id"],
                name=row["name"],
                attendance_date=row["attendance_date"],
                time=row["check_in_time"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def close(self) -> None:
        self.connection.close()

    def _person_by_name(self, name: str) -> Person | None:
        row = self.connection.execute(
            "SELECT * FROM people WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        return self._person_from_row(row) if row else None

    @staticmethod
    def _person_from_row(row: sqlite3.Row) -> Person:
        return Person(
            id=row["id"], name=row["name"], external_id=row["external_id"],
            email=row["email"], is_active=bool(row["is_active"]),
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def _initialize_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                external_id TEXT UNIQUE,
                email TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER,
                name TEXT NOT NULL,
                attendance_date TEXT NOT NULL,
                check_in_time TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (name COLLATE NOCASE, attendance_date),
                FOREIGN KEY (person_id) REFERENCES people(id)
            )
            """
        )
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(attendance)")
        }
        if "person_id" not in columns:
            self.connection.execute("ALTER TABLE attendance ADD COLUMN person_id INTEGER")

        old_rows = self.connection.execute(
            "SELECT id, name FROM attendance WHERE person_id IS NULL"
        ).fetchall()
        for row in old_rows:
            person = self._person_by_name(row["name"]) or self.register_person(row["name"])
            self.connection.execute(
                "UPDATE attendance SET person_id = ? WHERE id = ?",
                (person.id, row["id"]),
            )
        self.connection.commit()
