import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from attendance import AttendanceStore


class AttendanceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "attendance.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_marks_person_once_per_day(self) -> None:
        store = AttendanceStore(self.database_path)
        self.assertTrue(
            store.mark_present("Nitin", datetime(2026, 8, 31, 9, 15, 22))
        )
        self.assertFalse(
            store.mark_present("Nitin", datetime(2026, 8, 31, 14, 30, 10))
        )
        self.assertEqual(len(store.records()), 1)
        store.close()

    def test_allows_same_person_on_a_new_day(self) -> None:
        store = AttendanceStore(self.database_path)
        self.assertTrue(store.mark_present("Nitin", datetime(2026, 8, 31, 9, 0)))
        self.assertTrue(store.mark_present("Nitin", datetime(2026, 9, 1, 9, 0)))
        self.assertEqual(len(store.records()), 2)
        store.close()

    def test_database_enforces_case_insensitive_uniqueness(self) -> None:
        store = AttendanceStore(self.database_path)
        timestamp = datetime(2026, 8, 31, 9, 0)
        self.assertTrue(store.mark_present("Nitin", timestamp))
        self.assertFalse(store.mark_present("nitin", timestamp))
        store.close()

    def test_database_file_contains_expected_table(self) -> None:
        store = AttendanceStore(self.database_path)
        store.close()

        connection = sqlite3.connect(self.database_path)
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        connection.close()

        self.assertIn(("attendance",), tables)

    def test_rejects_empty_names(self) -> None:
        store = AttendanceStore(self.database_path)
        with self.assertRaises(ValueError):
            store.mark_present("   ")
        store.close()


if __name__ == "__main__":
    unittest.main()
