import sqlite3
from pathlib import Path


class RosterStore:
    """Stores expected people for sessions and derives present/absent status."""

    def __init__(self, database_path: Path) -> None:
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("""CREATE TABLE IF NOT EXISTS session_roster (
            session_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, person_id))""")
        self.connection.commit()

    def add_person(self, session_id: int, person_id: int) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO session_roster (session_id, person_id) VALUES (?, ?)",
            (session_id, person_id),
        )
        self.connection.commit()

    def add_all(self, session_id: int, person_ids: list[int]) -> int:
        before = self.connection.total_changes
        self.connection.executemany(
            "INSERT OR IGNORE INTO session_roster (session_id, person_id) VALUES (?, ?)",
            [(session_id, person_id) for person_id in person_ids],
        )
        self.connection.commit()
        return self.connection.total_changes - before

    def remove_person(self, session_id: int, person_id: int) -> None:
        self.connection.execute(
            "DELETE FROM session_roster WHERE session_id=? AND person_id=?",
            (session_id, person_id),
        )
        self.connection.commit()

    def roster(self, session_id: int) -> list[int]:
        rows = self.connection.execute(
            "SELECT person_id FROM session_roster WHERE session_id=? ORDER BY person_id",
            (session_id,),
        ).fetchall()
        return [row["person_id"] for row in rows]

    def close(self) -> None:
        self.connection.close()
