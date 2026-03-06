# ingestion/schema_builder.py
import re
from typing import Dict


def filename_to_table_name(filename: str) -> str:
    """
    Derive a SQL-friendly table name from an uploaded filename.
    Example: "MovieDatabaseData.csv" -> "movie_database_data"
    """
    name = filename.strip()
    if name.lower().endswith(".csv"):
        name = name[:-4]
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    name = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name)
    name = name.lower().strip("_")
    name = re.sub(r"_+", "_", name)
    return name or "table"


def normalize_column_name(name: str) -> str:
    """
    Normalize column names to SQL-friendly identifiers: lowercase, single underscores,
    no leading/trailing underscores (avoids names like Director_ that SQLite can treat as functions).
    """
    if not name or not name.strip():
        return "column"
    name = name.strip()
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    name = name.strip("_")
    name = re.sub(r"_+", "_", name)
    name = name.lower()
    return name or "column"


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