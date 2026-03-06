# database/connection.py
import sqlite3
from contextlib import contextmanager
from typing import Iterator


DB_PATH = "data/app.db"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()