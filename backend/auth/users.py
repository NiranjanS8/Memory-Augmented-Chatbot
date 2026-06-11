import hashlib
import os
import sqlite3
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel


class User(BaseModel):
    id: str
    email: str
    display_name: str
    created_at: datetime


class AuthStore:
    """SQLite-backed user store with PBKDF2 password hashing."""

    def __init__(self, db_path: str = "users.db"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def register(self, email: str, password: str, display_name: str = "") -> User:
        """Create a new user. Raises ValueError if email already exists."""
        existing = self._conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            raise ValueError(f"Email already registered: {email}")

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        password_hash = _hash_password(password)

        self._conn.execute(
            "INSERT INTO users (id, email, display_name, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, display_name or email.split("@")[0], password_hash, now.isoformat()),
        )
        self._conn.commit()

        return User(id=user_id, email=email, display_name=display_name or email.split("@")[0], created_at=now)

    def login(self, email: str, password: str) -> User:
        """Authenticate a user. Raises ValueError on bad credentials."""
        row = self._conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        if not row:
            raise ValueError("Invalid email or password")

        if not _verify_password(password, row["password_hash"]):
            raise ValueError("Invalid email or password")

        return User(
            id=row["id"],
            email=row["email"],
            display_name=row["display_name"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def close(self) -> None:
        self._conn.close()

    def get_by_id(self, user_id: str) -> User | None:
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return None
        return User(
            id=row["id"],
            email=row["email"],
            display_name=row["display_name"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


def _hash_password(password: str) -> str:
    """PBKDF2-SHA256 with random salt, 260k iterations."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=260_000)
    return f"{salt.hex()}:{dk.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, dk_hex = stored_hash.split(":")
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=260_000)
    return dk.hex() == dk_hex
