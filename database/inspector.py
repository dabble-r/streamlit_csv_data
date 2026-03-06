# database/inspector.py
from typing import List, Dict, Any
from .connection import get_connection


def get_tables() -> List[str]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [r[0] for r in cur.fetchall()]


def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """
    Return a list of columns with name and type.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f'PRAGMA table_info("{table_name}");')
        rows = cur.fetchall()
        return [
            {"cid": r[0], "name": r[1], "type": r[2], "notnull": r[3], "default": r[4], "pk": r[5]}
            for r in rows
        ]