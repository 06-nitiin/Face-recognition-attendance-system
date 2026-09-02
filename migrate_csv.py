import argparse
import csv
from datetime import datetime
from pathlib import Path

from attendance import AttendanceStore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import date-aware or legacy CSV attendance into SQLite."
    )
    parser.add_argument("csv_file", type=Path, help="Existing Attendance.csv file")
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("attendance.db"),
        help="SQLite database to create or update.",
    )
    return parser.parse_args()


def migrate(csv_path: Path, database_path: Path) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file does not exist: {csv_path}")

    store = AttendanceStore(database_path)
    imported = 0
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as file:
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
                    timestamp = datetime.strptime(
                        f"{date_value} {time_value}", "%Y-%m-%d %H:%M:%S"
                    )
                except ValueError:
                    print(f"Skipping row with invalid date/time: {row}")
                    continue

                if store.mark_present(name, timestamp):
                    imported += 1
    finally:
        store.close()

    return imported


def main() -> None:
    args = parse_args()
    try:
        imported = migrate(args.csv_file, args.database)
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Migration error: {error}") from error
    print(f"Imported {imported} attendance record(s) into {args.database}.")


if __name__ == "__main__":
    main()
