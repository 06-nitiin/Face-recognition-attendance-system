import sqlite3
from datetime import datetime
from pathlib import Path


class CorrectionStore:
    """Stores reversible administrative voids without deleting attendance history."""

    def __init__(self, database_path: Path) -> None:
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("""CREATE TABLE IF NOT EXISTS attendance_corrections (
            record_id INTEGER PRIMARY KEY,
            status TEXT NOT NULL CHECK(status = 'voided'),
            reason TEXT NOT NULL,
            corrected_by TEXT NOT NULL,
            corrected_at TEXT NOT NULL)""")
        self.connection.commit()

    def void_record(self, record_id: int, reason: str, corrected_by: str) -> None:
        reason = reason.strip()
        corrected_by = corrected_by.strip()
        if not reason:
            raise ValueError("A correction reason is required.")
        if not corrected_by:
            raise ValueError("The correcting administrator is required.")
        self.connection.execute(
            """INSERT INTO attendance_corrections
            (record_id, status, reason, corrected_by, corrected_at)
            VALUES (?, 'voided', ?, ?, ?)
            ON CONFLICT(record_id) DO UPDATE SET
                status='voided', reason=excluded.reason,
                corrected_by=excluded.corrected_by, corrected_at=excluded.corrected_at""",
            (record_id, reason, corrected_by, datetime.now().isoformat(timespec="seconds")),
        )
        self.connection.commit()

    def restore_record(self, record_id: int) -> None:
        self.connection.execute("DELETE FROM attendance_corrections WHERE record_id=?", (record_id,))
        self.connection.commit()

    def is_voided(self, record_id: int) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM attendance_corrections WHERE record_id=? AND status='voided'",
            (record_id,),
        ).fetchone()
        return row is not None

    def statuses(self) -> dict[int, sqlite3.Row]:
        rows = self.connection.execute(
            "SELECT * FROM attendance_corrections ORDER BY corrected_at DESC"
        ).fetchall()
        return {row["record_id"]: row for row in rows}

    def close(self) -> None:
        self.connection.close()
