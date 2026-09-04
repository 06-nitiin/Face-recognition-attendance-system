import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from attendance import AttendanceStore
from corrections import CorrectionStore


class CorrectionStoreTests(unittest.TestCase):
    def test_void_and_restore_keep_original_attendance_record(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "attendance.db"
            attendance = AttendanceStore(database)
            attendance.register_person("Nitin")
            session = attendance.start_session("Math", "2026-09-04")
            attendance.mark_present("Nitin", session.id, datetime(2026, 9, 4, 9, 0))
            record_id = attendance.records()[0].id
            corrections = CorrectionStore(database)

            corrections.void_record(record_id, "Marked during a camera test", "admin")
            self.assertTrue(corrections.is_voided(record_id))
            self.assertEqual(attendance.records()[0].id, record_id)

            corrections.restore_record(record_id)
            self.assertFalse(corrections.is_voided(record_id))
            corrections.close()
            attendance.close()

    def test_reason_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            corrections = CorrectionStore(Path(directory) / "attendance.db")
            with self.assertRaises(ValueError):
                corrections.void_record(1, "", "admin")
            corrections.close()


if __name__ == "__main__":
    unittest.main()
