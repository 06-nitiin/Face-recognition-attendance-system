import unittest
from dataclasses import dataclass

from analytics import build_analytics


@dataclass
class Record:
    name: str
    session_id: int
    attendance_date: str


@dataclass
class Person:
    is_active: bool


@dataclass
class Session:
    id: int
    name: str


class AnalyticsTests(unittest.TestCase):
    def test_calculates_people_sessions_and_daily_totals(self):
        records = [Record("Nitin", 1, "2026-09-02"), Record("Nitin", 2, "2026-09-02"), Record("Asha", 1, "2026-09-03")]
        result = build_analytics(records, [Person(True), Person(False)], [Session(1, "Math"), Session(2, "Physics")])
        self.assertEqual(result["total_records"], 3)
        self.assertEqual(result["active_people"], 1)
        self.assertEqual(result["people_totals"], [("Nitin", 2), ("Asha", 1)])
        self.assertEqual(result["session_totals"], [("Math", 2), ("Physics", 1)])
        self.assertEqual(result["daily_totals"], [("2026-09-03", 1), ("2026-09-02", 2)])

    def test_empty_data_is_supported(self):
        result = build_analytics([])
        self.assertEqual(result["total_records"], 0)
        self.assertEqual(result["people_totals"], [])
        self.assertEqual(result["session_totals"], [])


if __name__ == "__main__":
    unittest.main()
