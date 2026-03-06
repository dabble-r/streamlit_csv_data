# database/loader.py
from typing import List, Dict, Any
from .connection import get_connection
from ingestion.schema_builder import build_create_table_sql, normalize_column_name


def load_rows_into_table(
    table_name: str,
    rows: List[Dict[str, Any]],
    schema: Dict[str, str],
) -> None:
    """
    Create table (if needed) and insert rows.
    """
    if not rows:
        return

    create_sql = build_create_table_sql(table_name, schema)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(create_sql)

        columns = list(schema.keys())
        norm_cols = [normalize_column_name(c) for c in columns]
        quoted_cols = [f'"{c}"' for c in norm_cols]
        placeholders = ", ".join(["?"] * len(columns))
        insert_sql = f'INSERT INTO "{table_name}" ({", ".join(quoted_cols)}) VALUES ({placeholders})'

        for row in rows:
            values = [row.get(col) for col in columns]
            cur.execute(insert_sql, values)

        conn.commit()