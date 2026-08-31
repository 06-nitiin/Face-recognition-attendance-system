import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class AttendanceRecord:
    name: str
    attendance_date: str
    time: str


class AttendanceStore:
    HEADER = ["name", "date", "time"]
    LEGACY_HEADER = ["name", "time"]

    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.csv_path.touch(exist_ok=True)
        self._migrate_legacy_file()

    def mark_present(self, name: str, now: datetime | None = None) -> bool:
        if not name.strip():
            raise ValueError("Attendance name cannot be empty.")

        timestamp = now or datetime.now()
        attendance_date = timestamp.date().isoformat()
        attendance_time = timestamp.strftime("%H:%M:%S")
        records = self._read_records()

        already_present = any(
            record.name.casefold() == name.casefold()
            and record.attendance_date == attendance_date
            for record in records
        )
        if already_present:
            return False

        with self.csv_path.open("a", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([name.strip(), attendance_date, attendance_time])
        return True

    def records(self) -> list[AttendanceRecord]:
        return self._read_records()

    def _read_records(self) -> list[AttendanceRecord]:
        records: list[AttendanceRecord] = []
        with self.csv_path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                if not row or not any(cell.strip() for cell in row):
                    continue
                if [cell.strip().lower() for cell in row] == self.HEADER:
                    continue
                if [cell.strip().lower() for cell in row] == self.LEGACY_HEADER:
                    continue
                if len(row) == 3:
                    records.append(
                        AttendanceRecord(
                            name=row[0].strip(),
                            attendance_date=row[1].strip(),
                            time=row[2].strip(),
                        )
                    )
        return records

    def _migrate_legacy_file(self) -> None:
        with self.csv_path.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.reader(file))

        non_empty_rows = [row for row in rows if any(cell.strip() for cell in row)]
        if not non_empty_rows:
            self._write_records([])
            return

        header = [cell.strip().lower() for cell in non_empty_rows[0]]
        if header != self.LEGACY_HEADER:
            return

        today = date.today().isoformat()
        migrated: list[AttendanceRecord] = []
        for row in non_empty_rows[1:]:
            if len(row) >= 2 and row[0].strip():
                migrated.append(
                    AttendanceRecord(
                        name=row[0].strip(), attendance_date=today, time=row[1].strip()
                    )
                )
        self._write_records(migrated)

    def _write_records(self, records: list[AttendanceRecord]) -> None:
        with self.csv_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(self.HEADER)
            writer.writerows(
                [record.name, record.attendance_date, record.time]
                for record in records
            )
