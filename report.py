import argparse
import csv
from pathlib import Path

from attendance import AttendanceStore


def parse_args():
    parser = argparse.ArgumentParser(description="Summarize or export attendance records.")
    parser.add_argument("--database", type=Path, default=Path("attendance.db"))
    parser.add_argument("--date", dest="session_date", help="Filter by YYYY-MM-DD.")
    parser.add_argument("--session-id", type=int)
    parser.add_argument("--output", type=Path, help="Optional CSV export path.")
    return parser.parse_args()


def export_csv(records, output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["attendance_id", "person_id", "name", "session_id", "date", "time"])
        for record in records:
            writer.writerow([record.id, record.person_id, record.name, record.session_id, record.attendance_date, record.time])


def main() -> None:
    args = parse_args()
    store = AttendanceStore(args.database)
    try:
        records = store.records(session_id=args.session_id, session_date=args.session_date)
        if args.output:
            export_csv(records, args.output)
            print(f"Exported {len(records)} record(s) to {args.output}.")
        else:
            print(f"Attendance records: {len(records)}")
            for record in records:
                print(f"{record.attendance_date} | session {record.session_id} | {record.name} | {record.time}")
    finally:
        store.close()


if __name__ == "__main__":
    main()
