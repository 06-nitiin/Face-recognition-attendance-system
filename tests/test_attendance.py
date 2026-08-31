import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from attendance import AttendanceStore


class AttendanceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "Attendance.csv"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_marks_person_once_per_day(self) -> None:
        store = AttendanceStore(self.csv_path)
        morning = datetime(2026, 8, 31, 9, 15, 22)
        later = datetime(2026, 8, 31, 14, 30, 10)

        self.assertTrue(store.mark_present("Nitin", morning))
        self.assertFalse(store.mark_present("Nitin", later))
        self.assertEqual(len(store.records()), 1)

    def test_allows_same_person_on_a_new_day(self) -> None:
        store = AttendanceStore(self.csv_path)

        self.assertTrue(store.mark_present("Nitin", datetime(2026, 8, 31, 9, 0)))
        self.assertTrue(store.mark_present("Nitin", datetime(2026, 9, 1, 9, 0)))
        self.assertEqual(len(store.records()), 2)

    def test_names_are_compared_case_insensitively(self) -> None:
        store = AttendanceStore(self.csv_path)
        timestamp = datetime(2026, 8, 31, 9, 0)

        self.assertTrue(store.mark_present("Nitin", timestamp))
        self.assertFalse(store.mark_present("nitin", timestamp))

    def test_migrates_legacy_two_column_file(self) -> None:
        with self.csv_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["name", "time"])
            writer.writerow(["Nitin", "09:00:00"])

        store = AttendanceStore(self.csv_path)
        rows = self.csv_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(rows[0], "name,date,time")
        self.assertEqual(len(store.records()), 1)
        self.assertEqual(store.records()[0].name, "Nitin")

    def test_rejects_empty_names(self) -> None:
        store = AttendanceStore(self.csv_path)

        with self.assertRaises(ValueError):
            store.mark_present("   ")


if __name__ == "__main__":
    unittest.main()
