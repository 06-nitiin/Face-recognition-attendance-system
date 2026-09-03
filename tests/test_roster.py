import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from attendance import AttendanceStore
from roster import RosterStore


class RosterTests(unittest.TestCase):
    def test_roster_is_unique_and_supports_present_status(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "attendance.db"
            attendance = AttendanceStore(database)
            nitin = attendance.register_person("Nitin")
            asha = attendance.register_person("Asha")
            session = attendance.start_session("Math", "2026-09-03")
            roster = RosterStore(database)
            roster.add_person(session.id, nitin.id)
            roster.add_person(session.id, nitin.id)
            roster.add_person(session.id, asha.id)
            self.assertEqual(roster.roster(session.id), [nitin.id, asha.id])
            self.assertTrue(attendance.mark_present("Nitin", session.id, datetime(2026, 9, 3, 9, 0)))
            records = {record.person_id for record in attendance.records(session.id)}
            self.assertEqual(records, {nitin.id})
            roster.close()
            attendance.close()

    def test_remove_person_from_roster(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "attendance.db"
            attendance = AttendanceStore(database)
            person = attendance.register_person("Nitin")
            session = attendance.start_session("Math", "2026-09-03")
            roster = RosterStore(database)
            roster.add_person(session.id, person.id)
            roster.remove_person(session.id, person.id)
            self.assertEqual(roster.roster(session.id), [])
            roster.close()
            attendance.close()


if __name__ == "__main__":
    unittest.main()
