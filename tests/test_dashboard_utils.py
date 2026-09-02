import unittest
from dataclasses import dataclass

from dashboard_utils import attendance_summary, filter_records


@dataclass
class FakeRecord:
    session_id: int
    attendance_date: str


class DashboardUtilsTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            FakeRecord(1, "2026-09-02"),
            FakeRecord(1, "2026-09-02"),
            FakeRecord(2, "2026-09-03"),
        ]

    def test_filters_by_session(self):
        self.assertEqual(len(filter_records(self.records, session_id=1)), 2)

    def test_filters_by_date(self):
        self.assertEqual(len(filter_records(self.records, session_date="2026-09-03")), 1)

    def test_summary_counts_records_dates_and_sessions(self):
        summary = attendance_summary(self.records)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["dates"], 2)
        self.assertEqual(summary["sessions"], 2)


if __name__ == "__main__":
    unittest.main()
