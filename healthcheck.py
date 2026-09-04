import argparse
import importlib.util
import sqlite3
from pathlib import Path

from config import ProjectConfig

REQUIRED_TABLES = {"people", "sessions", "attendance", "session_roster", "admin_users", "audit_logs", "attendance_corrections"}
REQUIRED_MODULES = {"cv2": "opencv-python", "face_recognition": "face-recognition", "flask": "Flask"}


def check_database(database: Path) -> list[str]:
    if not database.exists():
        return [f"Database missing: {database}"]
    connection = sqlite3.connect(database)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        connection.close()
    problems = []
    if integrity != "ok":
        problems.append(f"SQLite integrity check failed: {integrity}")
    missing = REQUIRED_TABLES - tables
    if missing:
        problems.append("Missing database tables: " + ", ".join(sorted(missing)))
    return problems


def check_project(config: ProjectConfig) -> tuple[list[str], list[str]]:
    problems = check_database(config.database)
    warnings = []
    if not config.training_dir.exists():
        problems.append(f"Training directory missing: {config.training_dir}")
    elif not any(config.training_dir.glob("*.jpg")):
        warnings.append(f"No .jpg enrollment images found in {config.training_dir}")
    for module, package in REQUIRED_MODULES.items():
        if importlib.util.find_spec(module) is None:
            problems.append(f"Missing dependency: install {package}")
    try:
        config.validate()
    except ValueError as error:
        problems.append(str(error))
    return problems, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Check attendance project readiness.")
    parser.add_argument("--database", type=Path, default=None)
    parser.add_argument("--training-dir", type=Path, default=None)
    args = parser.parse_args()
    config = ProjectConfig.from_environment()
    if args.database:
        config = ProjectConfig(**{**config.__dict__, "database": args.database})
    if args.training_dir:
        config = ProjectConfig(**{**config.__dict__, "training_dir": args.training_dir})
    problems, warnings = check_project(config)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        raise SystemExit(1)
    print("Project health check passed.")


if __name__ == "__main__":
    main()
