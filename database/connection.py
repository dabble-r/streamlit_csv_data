# database/connection.py
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def _db_path() -> Path:
    """Resolve data/app.db relative to project root (parent of database/)."""
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "app.db"


def clear_db() -> None:
    """Remove the database file so the app starts with a clean slate."""
    path = _db_path()
    if path.exists():
        path.unlink()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(_db_path()))
    try:
        yield conn
    finally:
        conn.close()