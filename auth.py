import sqlite3
from datetime import datetime
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash


class AuthStore:
    """Stores local dashboard admins and an audit trail in SQLite."""

    def __init__(self, database_path: Path) -> None:
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            )"""
        )
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                created_at TEXT NOT NULL
            )"""
        )
        self.connection.commit()

    def create_admin(self, username: str, password: str) -> int:
        username = username.strip()
        if not username or len(password) < 8:
            raise ValueError("Username is required and password must be at least 8 characters.")
        try:
            cursor = self.connection.execute(
                """INSERT INTO admin_users
                (username, password_hash, created_at) VALUES (?, ?, ?)""",
                (username, generate_password_hash(password), datetime.now().isoformat(timespec="seconds")),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as error:
            self.connection.rollback()
            raise ValueError("That username already exists.") from error
        return cursor.lastrowid

    def authenticate(self, username: str, password: str) -> bool:
        row = self.connection.execute(
            "SELECT * FROM admin_users WHERE username=? COLLATE NOCASE AND is_active=1",
            (username.strip(),),
        ).fetchone()
        if row is None or not check_password_hash(row["password_hash"], password):
            return False
        self.connection.execute(
            "UPDATE admin_users SET last_login_at=? WHERE id=?",
            (datetime.now().isoformat(timespec="seconds"), row["id"]),
        )
        self.connection.commit()
        return True

    def audit(self, username: str, action: str, target: str = "") -> None:
        self.connection.execute(
            "INSERT INTO audit_logs (username, action, target, created_at) VALUES (?, ?, ?, ?)",
            (username, action, target, datetime.now().isoformat(timespec="seconds")),
        )
        self.connection.commit()

    def logs(self, limit: int = 100):
        return self.connection.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    def close(self) -> None:
        self.connection.close()
