import tempfile
import unittest
from pathlib import Path

from auth import AuthStore


class AuthStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = AuthStore(Path(self.temp_dir.name) / "attendance.db")

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_password_is_hashed_and_authentication_works(self):
        self.store.create_admin("admin", "correct horse")
        row = self.store.connection.execute("SELECT password_hash FROM admin_users").fetchone()
        self.assertNotEqual(row["password_hash"], "correct horse")
        self.assertTrue(self.store.authenticate("admin", "correct horse"))
        self.assertFalse(self.store.authenticate("admin", "wrong password"))

    def test_short_password_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.create_admin("admin", "short")

    def test_audit_log_is_written(self):
        self.store.audit("admin", "person_deactivated", "person:1")
        logs = self.store.logs()
        self.assertEqual(logs[0]["action"], "person_deactivated")


if __name__ == "__main__":
    unittest.main()
