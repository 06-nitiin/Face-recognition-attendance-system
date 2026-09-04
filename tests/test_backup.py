import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from attendance import AttendanceStore
from backup import backup_database, check_integrity, restore_database


class BackupTests(unittest.TestCase):
    def test_backup_and_restore_preserve_attendance_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "attendance.db"
            backup = root / "backups" / "attendance.db"
            restored = root / "restored.db"

            store = AttendanceStore(database)
            store.register_person("Nitin")
            session = store.start_session("Math", "2026-09-04")
            store.mark_present("Nitin", session.id, datetime(2026, 9, 4, 9, 0))
            store.close()

            backup_database(database, backup)
            self.assertTrue(check_integrity(backup))
            restore_database(backup, restored)

            restored_store = AttendanceStore(restored)
            self.assertEqual(len(restored_store.records()), 1)
            self.assertEqual(restored_store.records()[0].name, "Nitin")
            restored_store.close()

    def test_restore_makes_safety_copy_of_existing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "attendance.db"
            backup = root / "backup.db"
            safety_copy = root / "before-restore.db"

            store = AttendanceStore(database)
            store.register_person("Original")
            store.close()
            backup_database(database, backup)

            store = AttendanceStore(database)
            store.register_person("Temporary")
            store.close()
            result = restore_database(backup, database, safety_copy)

            self.assertEqual(result, safety_copy)
            restored_store = AttendanceStore(database)
            self.assertEqual([person.name for person in restored_store.list_people()], ["Original"])
            restored_store.close()
            safety_store = AttendanceStore(safety_copy)
            self.assertEqual({person.name for person in safety_store.list_people()}, {"Original", "Temporary"})
            safety_store.close()


if __name__ == "__main__":
    unittest.main()
