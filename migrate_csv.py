import argparse
import csv
from datetime import datetime
from pathlib import Path

from attendance import AttendanceStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Import CSV attendance into SQLite.")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--database", type=Path, default=Path("attendance.db"))
    parser.add_argument("--session-name", default="Imported CSV attendance")
    args = parser.parse_args()
    if not args.csv_file.exists():
        raise SystemExit(f"CSV file does not exist: {args.csv_file}")

    store = AttendanceStore(args.database)
    session = None
    imported = 0
    try:
        with args.csv_file.open("r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                if not row or not any(cell.strip() for cell in row):
                    continue
                normalized = [cell.strip().lower() for cell in row]
                if normalized in (["name", "date", "time"], ["name", "time"]):
                    continue
                if len(row) == 3:
                    name, date_value, time_value = [cell.strip() for cell in row]
                elif len(row) == 2:
                    name, time_value = [cell.strip() for cell in row]
                    date_value = datetime.now().date().isoformat()
                else:
                    print(f"Skipping malformed row: {row}")
                    continue
                try:
                    timestamp = datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    print(f"Skipping row with invalid date/time: {row}")
                    continue
                if session is None or session.session_date != date_value:
                    session = store.start_session(args.session_name, date_value)
                if store.mark_present(name, session_id=session.id, now=timestamp):
                    imported += 1
    finally:
        store.close()
    print(f"Imported {imported} attendance record(s) into {args.database}.")


if __name__ == "__main__":
    main()
