"""
database.py – SQLite database connection helpers.

Uses the standard `sqlite3` module so no additional ORM is required
for the starter.  Switch to SQLAlchemy when the project grows.
"""

import sqlite3
from pathlib import Path

from app.config import DATABASE_URL

# Strip "sqlite:///" prefix to get the file path
_DB_PATH = DATABASE_URL.replace("sqlite:///", "")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory set to Row."""
    db_file = Path(_DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(schema_path: str = "database/schema.sql") -> None:
    """
    Initialise the database by executing the SQL schema file.

    Args:
        schema_path: Path to the SQL schema file relative to the project root.
    """
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with get_connection() as conn:
        conn.executescript(schema_file.read_text(encoding="utf-8"))
        conn.commit()
