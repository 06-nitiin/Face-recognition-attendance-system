import tempfile
import unittest
from pathlib import Path

from attendance import AttendanceStore
from auth import AuthStore
from corrections import CorrectionStore
from healthcheck import check_database
from roster import RosterStore
from config import ProjectConfig


class ReleaseReadinessTests(unittest.TestCase):
    def test_configuration_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            ProjectConfig(tolerance=0).validate()
        with self.assertRaises(ValueError):
            ProjectConfig(confirm_frames=0).validate()

    def test_health_check_accepts_initialized_database(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "attendance.db"
            store = AttendanceStore(database)
            store.close()
            AuthStore(database).close()
            RosterStore(database).close()
            CorrectionStore(database).close()
            self.assertEqual(check_database(database), [])

    def test_health_check_reports_missing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(check_database(Path(directory) / "missing.db"))


if __name__ == "__main__":
    unittest.main()
