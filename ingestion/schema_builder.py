# ingestion/schema_builder.py
from typing import Dict


def normalize_column_name(name: str) -> str:
    """
    Normalize column names to be SQL-friendly (simple heuristic).
    """
    name = name.strip()
    name = name.replace(" ", "_")
    return name


def build_create_table_sql(table_name: str, schema: Dict[str, str]) -> str:
    """
    Build a CREATE TABLE statement from a schema dict {col: type}.
    """
    cols = []
    for col, col_type in schema.items():
        norm = normalize_column_name(col)
        cols.append(f'"{norm}" {col_type}')
    cols_sql = ", ".join(cols)
    return f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_sql});'