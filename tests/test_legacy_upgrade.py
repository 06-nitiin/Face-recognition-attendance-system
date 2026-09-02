import sqlite3
import tempfile
import unittest
from pathlib import Path

from attendance import AttendanceStore


class LegacyUpgradeTests(unittest.TestCase):
    def test_upgrades_milestone_7_database(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "attendance.db"
            connection = sqlite3.connect(database_path)
            connection.execute("""CREATE TABLE people (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                external_id TEXT UNIQUE, email TEXT, is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
            connection.execute("""CREATE TABLE attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT, person_id INTEGER,
                name TEXT NOT NULL, attendance_date TEXT NOT NULL,
                check_in_time TEXT NOT NULL, created_at TEXT NOT NULL,
                UNIQUE (name COLLATE NOCASE, attendance_date))""")
            connection.execute("INSERT INTO attendance (name, attendance_date, check_in_time, created_at) VALUES (?, ?, ?, ?)", ("Nitin", "2026-09-02", "09:00:00", "2026-09-02T09:00:00"))
            connection.commit()
            connection.close()

            store = AttendanceStore(database_path)
            self.assertEqual(len(store.list_sessions("2026-09-02")), 1)
            self.assertEqual(store.records()[0].person_id, 1)
            self.assertEqual(store.records()[0].session_id, 1)
            store.close()


if __name__ == "__main__":
    unittest.main()
