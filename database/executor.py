# database/executor.py
from typing import List, Dict, Any
from .connection import get_connection


def run_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Execute a read-only SQL query and return rows as dicts.
    """
    with get_connection() as conn:
        conn.row_factory = lambda cursor, row: {
            col[0]: row[idx] for idx, col in enumerate(cursor.description)
        }
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()