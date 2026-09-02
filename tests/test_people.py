import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from attendance import AttendanceStore


class PeopleMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "attendance.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_registers_person_with_metadata(self) -> None:
        store = AttendanceStore(self.database_path)
        person = store.register_person("Nitin Bhardwaj", "STU-001", "nitin@example.com")
        self.assertEqual(person.name, "Nitin Bhardwaj")
        self.assertEqual(person.external_id, "STU-001")
        self.assertEqual(person.email, "nitin@example.com")
        self.assertTrue(person.is_active)
        store.close()

    def test_attendance_links_to_person(self) -> None:
        store = AttendanceStore(self.database_path)
        person = store.register_person("Nitin")
        self.assertTrue(store.mark_present("Nitin", datetime(2026, 9, 2, 9, 0)))
        record = store.records()[0]
        self.assertEqual(record.person_id, person.id)
        store.close()

    def test_recognition_name_reuses_existing_person(self) -> None:
        store = AttendanceStore(self.database_path)
        person = store.register_person("Nitin", "STU-001")
        store.mark_present("nitin", datetime(2026, 9, 2, 9, 0))
        self.assertEqual(store.records()[0].person_id, person.id)
        self.assertEqual(len(store.list_people()), 1)
        store.close()

    def test_inactive_person_is_not_marked(self) -> None:
        store = AttendanceStore(self.database_path)
        person = store.register_person("Nitin")
        store.set_person_active(person.id, False)
        self.assertFalse(store.mark_present("Nitin", datetime(2026, 9, 2, 9, 0)))
        self.assertEqual(store.records(), [])
        store.close()

    def test_existing_database_gets_people_links(self) -> None:
        connection = sqlite3.connect(self.database_path)
        connection.execute(
            """CREATE TABLE attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                attendance_date TEXT NOT NULL,
                check_in_time TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE (name COLLATE NOCASE, attendance_date)
            )"""
        )
        connection.execute(
            "INSERT INTO attendance (name, attendance_date, check_in_time, created_at) VALUES (?, ?, ?, ?)",
            ("Nitin", "2026-09-01", "09:00:00", "2026-09-01T09:00:00"),
        )
        connection.commit()
        connection.close()

        store = AttendanceStore(self.database_path)
        self.assertEqual(len(store.list_people()), 1)
        self.assertEqual(store.records()[0].person_id, 1)
        store.close()


if __name__ == "__main__":
    unittest.main()
