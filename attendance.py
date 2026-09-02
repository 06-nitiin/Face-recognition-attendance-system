import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
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
class AttendanceSession:
    id: int
    name: str
    session_date: str
    started_at: str
    ended_at: str | None


@dataclass(frozen=True)
class AttendanceRecord:
    id: int
    person_id: int
    session_id: int
    name: str
    attendance_date: str
    time: str
    created_at: str


class AttendanceStore:
    """SQLite storage for people, sessions, and attendance records."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialize_schema()

    def register_person(self, name, external_id=None, email=None) -> Person:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Person name cannot be empty.")
        clean_external_id = external_id.strip() if external_id else None
        clean_email = email.strip() if email else None
        now = datetime.now().isoformat(timespec="seconds")
        existing = self._person_by_name(clean_name)
        if existing:
            self.connection.execute(
                "UPDATE people SET external_id=?, email=?, updated_at=? WHERE id=?",
                (clean_external_id, clean_email, now, existing.id),
            )
            self.connection.commit()
            return self.get_person(existing.id)
        try:
            cursor = self.connection.execute(
                """INSERT INTO people
                (name, external_id, email, is_active, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)""",
                (clean_name, clean_external_id, clean_email, now, now),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as error:
            self.connection.rollback()
            raise ValueError("A person with this name or external ID already exists.") from error
        return self.get_person(cursor.lastrowid)

    def get_person(self, person_id: int) -> Person:
        row = self.connection.execute("SELECT * FROM people WHERE id=?", (person_id,)).fetchone()
        if row is None:
            raise ValueError(f"Person {person_id} does not exist.")
        return self._person_from_row(row)

    def list_people(self, active_only=False) -> list[Person]:
        query = "SELECT * FROM people"
        if active_only:
            query += " WHERE is_active=1"
        rows = self.connection.execute(query + " ORDER BY name COLLATE NOCASE").fetchall()
        return [self._person_from_row(row) for row in rows]

    def set_person_active(self, person_id: int, active: bool) -> None:
        self.connection.execute(
            "UPDATE people SET is_active=?, updated_at=? WHERE id=?",
            (int(active), datetime.now().isoformat(timespec="seconds"), person_id),
        )
        self.connection.commit()

    def start_session(self, name: str, session_date: str | None = None) -> AttendanceSession:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Session name cannot be empty.")
        session_date = session_date or date.today().isoformat()
        started_at = datetime.now().isoformat(timespec="seconds")
        cursor = self.connection.execute(
            "INSERT INTO sessions (name, session_date, started_at) VALUES (?, ?, ?)",
            (clean_name, session_date, started_at),
        )
        self.connection.commit()
        return self.get_session(cursor.lastrowid)

    def get_session(self, session_id: int) -> AttendanceSession:
        row = self.connection.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        if row is None:
            raise ValueError(f"Session {session_id} does not exist.")
        return AttendanceSession(row["id"], row["name"], row["session_date"], row["started_at"], row["ended_at"])

    def list_sessions(self, session_date: str | None = None) -> list[AttendanceSession]:
        if session_date:
            rows = self.connection.execute(
                "SELECT * FROM sessions WHERE session_date=? ORDER BY started_at DESC", (session_date,)
            ).fetchall()
        else:
            rows = self.connection.execute("SELECT * FROM sessions ORDER BY started_at DESC").fetchall()
        return [AttendanceSession(row["id"], row["name"], row["session_date"], row["started_at"], row["ended_at"]) for row in rows]

    def end_session(self, session_id: int) -> None:
        self.connection.execute(
            "UPDATE sessions SET ended_at=? WHERE id=?",
            (datetime.now().isoformat(timespec="seconds"), session_id),
        )
        self.connection.commit()

    def mark_present(self, name: str, session_id: int | None = None, now: datetime | None = None) -> bool:
        # Preserve the Milestone 3-7 calling style: mark_present(name, datetime).
        if isinstance(session_id, datetime) and now is None:
            now = session_id
            session_id = None
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Attendance name cannot be empty.")
        timestamp = now or datetime.now()
        if session_id is None:
            session = self._default_session(timestamp.date().isoformat())
            session_id = session.id
        session = self.get_session(session_id)
        person = self._person_by_name(clean_name) or self.register_person(clean_name)
        if not person.is_active:
            return False
        cursor = self.connection.execute(
            """INSERT OR IGNORE INTO attendance
            (person_id, session_id, name, attendance_date, check_in_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (person.id, session.id, person.name, session.session_date,
             timestamp.strftime("%H:%M:%S"), timestamp.isoformat(timespec="seconds")),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def records(self, session_id: int | None = None, session_date: str | None = None) -> list[AttendanceRecord]:
        query = "SELECT * FROM attendance"
        values = []
        conditions = []
        if session_id is not None:
            conditions.append("session_id=?")
            values.append(session_id)
        if session_date is not None:
            conditions.append("attendance_date=?")
            values.append(session_date)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY attendance_date DESC, check_in_time DESC, name COLLATE NOCASE"
        rows = self.connection.execute(query, values).fetchall()
        return [AttendanceRecord(row["id"], row["person_id"], row["session_id"], row["name"], row["attendance_date"], row["check_in_time"], row["created_at"]) for row in rows]

    def close(self) -> None:
        self.connection.close()

    def _default_session(self, session_date: str) -> AttendanceSession:
        row = self.connection.execute(
            "SELECT id FROM sessions WHERE name=? AND session_date=? ORDER BY id LIMIT 1",
            ("Default session", session_date),
        ).fetchone()
        return self.get_session(row["id"]) if row else self.start_session("Default session", session_date)

    def _person_by_name(self, name: str) -> Person | None:
        row = self.connection.execute("SELECT * FROM people WHERE name=? COLLATE NOCASE", (name,)).fetchone()
        return self._person_from_row(row) if row else None

    @staticmethod
    def _person_from_row(row: sqlite3.Row) -> Person:
        return Person(row["id"], row["name"], row["external_id"], row["email"], bool(row["is_active"]), row["created_at"], row["updated_at"])

    def _initialize_schema(self) -> None:
        self.connection.execute("""CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE COLLATE NOCASE,
            external_id TEXT UNIQUE, email TEXT, is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            session_date TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT)""")
        self.connection.commit()
        self._ensure_attendance_table()
        self._link_old_attendance_people()

    def _ensure_attendance_table(self) -> None:
        table = self.connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='attendance'").fetchone()
        if table is None:
            self._create_attendance_table()
            return
        columns = {row["name"] for row in self.connection.execute("PRAGMA table_info(attendance)")}
        if "person_id" not in columns:
            self.connection.execute("ALTER TABLE attendance ADD COLUMN person_id INTEGER")
        if "session_id" not in columns:
            self.connection.execute("ALTER TABLE attendance ADD COLUMN session_id INTEGER")
        self.connection.commit()
        has_new_constraint = "person_id, session_id" in (table["sql"] or "")
        if not has_new_constraint:
            self._rebuild_attendance_table()

    def _create_attendance_table(self) -> None:
        self.connection.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT, person_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL, name TEXT NOT NULL, attendance_date TEXT NOT NULL,
            check_in_time TEXT NOT NULL, created_at TEXT NOT NULL,
            UNIQUE (person_id, session_id),
            FOREIGN KEY (person_id) REFERENCES people(id),
            FOREIGN KEY (session_id) REFERENCES sessions(id))""")
        self.connection.commit()

    def _rebuild_attendance_table(self) -> None:
        old_rows = self.connection.execute("SELECT * FROM attendance").fetchall()
        for row in old_rows:
            session = self._default_session(row["attendance_date"])
            if row["session_id"] is None:
                self.connection.execute("UPDATE attendance SET session_id=? WHERE id=?", (session.id, row["id"]))
        self.connection.commit()
        self.connection.execute("PRAGMA foreign_keys=OFF")
        self.connection.execute("ALTER TABLE attendance RENAME TO attendance_legacy")
        self._create_attendance_table()
        rows = self.connection.execute("SELECT * FROM attendance_legacy").fetchall()
        for row in rows:
            person_id = row["person_id"]
            if person_id is None:
                person = self._person_by_name(row["name"]) or self.register_person(row["name"])
                person_id = person.id
            self.connection.execute("""INSERT OR IGNORE INTO attendance
                (id, person_id, session_id, name, attendance_date, check_in_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (row["id"], person_id, row["session_id"], row["name"], row["attendance_date"], row["check_in_time"], row["created_at"]))
        self.connection.execute("DROP TABLE attendance_legacy")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.commit()

    def _link_old_attendance_people(self) -> None:
        rows = self.connection.execute("SELECT id, name FROM attendance WHERE person_id IS NULL").fetchall()
        for row in rows:
            person = self._person_by_name(row["name"]) or self.register_person(row["name"])
            self.connection.execute("UPDATE attendance SET person_id=? WHERE id=?", (person.id, row["id"]))
        self.connection.commit()
