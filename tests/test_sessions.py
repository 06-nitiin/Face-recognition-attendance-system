import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from attendance import AttendanceStore
from report import export_csv


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "attendance.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_records_are_unique_per_person_per_session(self):
        store = AttendanceStore(self.database_path)
        person = store.register_person("Nitin")
        session = store.start_session("Math class", "2026-09-02")
        self.assertTrue(store.mark_present("Nitin", session.id, datetime(2026, 9, 2, 9, 0)))
        self.assertFalse(store.mark_present("Nitin", session.id, datetime(2026, 9, 2, 9, 1)))
        self.assertEqual(store.records(session_id=session.id)[0].person_id, person.id)
        store.close()

    def test_same_person_can_attend_two_sessions_same_day(self):
        store = AttendanceStore(self.database_path)
        store.register_person("Nitin")
        first = store.start_session("Math", "2026-09-02")
        second = store.start_session("Physics", "2026-09-02")
        self.assertTrue(store.mark_present("Nitin", first.id, datetime(2026, 9, 2, 9, 0)))
        self.assertTrue(store.mark_present("Nitin", second.id, datetime(2026, 9, 2, 10, 0)))
        self.assertEqual(len(store.records()), 2)
        store.close()

    def test_report_exports_records(self):
        store = AttendanceStore(self.database_path)
        store.register_person("Nitin")
        session = store.start_session("Math", "2026-09-02")
        store.mark_present("Nitin", session.id, datetime(2026, 9, 2, 9, 0))
        output = Path(self.temp_dir.name) / "report.csv"
        export_csv(store.records(), output)
        store.close()
        with output.open(newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))
        self.assertEqual(rows[0][-2:], ["date", "time"])
        self.assertEqual(rows[1][2], "Nitin")


if __name__ == "__main__":
    unittest.main()
