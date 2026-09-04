import argparse
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path


def check_integrity(database_path: Path) -> bool:
    connection = sqlite3.connect(database_path)
    try:
        return connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        connection.close()


def backup_database(database_path: Path, output_path: Path) -> Path:
    if not database_path.exists():
        raise FileNotFoundError(f"Database does not exist: {database_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    if temporary_path.exists():
        temporary_path.unlink()
    source = sqlite3.connect(database_path)
    destination = sqlite3.connect(temporary_path)
    try:
        source.backup(destination)
        destination.commit()
    finally:
        destination.close()
        source.close()
    if not check_integrity(temporary_path):
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError("Backup failed SQLite integrity validation.")
    temporary_path.replace(output_path)
    return output_path


def restore_database(backup_path: Path, database_path: Path, safety_copy: Path | None = None) -> Path | None:
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup does not exist: {backup_path}")
    if not check_integrity(backup_path):
        raise RuntimeError("The backup failed SQLite integrity validation.")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        safety_copy = safety_copy or database_path.with_name(
            f"{database_path.stem}.before-restore-{datetime.now().strftime('%Y%m%d-%H%M%S')}{database_path.suffix}"
        )
        shutil.copy2(database_path, safety_copy)

    temporary_path = database_path.with_suffix(database_path.suffix + ".restore.tmp")
    temporary_path.unlink(missing_ok=True)
    source = sqlite3.connect(backup_path)
    destination = sqlite3.connect(temporary_path)
    try:
        source.backup(destination)
        destination.commit()
    finally:
        destination.close()
        source.close()
    if not check_integrity(temporary_path):
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError("Restored database failed SQLite integrity validation.")
    temporary_path.replace(database_path)
    return safety_copy


def main() -> None:
    parser = argparse.ArgumentParser(description="Back up or restore the attendance database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup")
    backup_parser.add_argument("--database", type=Path, default=Path("attendance.db"))
    backup_parser.add_argument("--output", type=Path, required=True)

    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument("--backup", type=Path, required=True)
    restore_parser.add_argument("--database", type=Path, default=Path("attendance.db"))
    restore_parser.add_argument("--safety-copy", type=Path)

    args = parser.parse_args()
    if args.command == "backup":
        path = backup_database(args.database, args.output)
        print(f"Backup created: {path}")
    else:
        safety_copy = restore_database(args.backup, args.database, args.safety_copy)
        print(f"Database restored from: {args.backup}")
        if safety_copy:
            print(f"Previous database saved to: {safety_copy}")


if __name__ == "__main__":
    main()
