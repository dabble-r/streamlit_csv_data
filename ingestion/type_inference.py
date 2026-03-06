# ingestion/type_inference.py
from typing import Dict, Any, Iterable


def infer_type_for_column(values: Iterable[Any]) -> str:
    """
    Infer a simple SQL type for a column based on sample values.
    Returns one of: INTEGER, REAL, TEXT.
    """
    has_float = False
    has_int = False

    for v in values:
        if v is None or v == "":
            continue
        try:
            int(v)
            has_int = True
            continue
        except (ValueError, TypeError):
            pass
        try:
            float(v)
            has_float = True
            continue
        except (ValueError, TypeError):
            pass
        return "TEXT"

    if has_float and not has_int:
        return "REAL"
    if has_int and not has_float:
        return "INTEGER"
    if has_int and has_float:
        return "REAL"
    return "TEXT"


def infer_schema(rows: Iterable[Dict[str, Any]]) -> Dict[str, str]:
    """
    Infer SQL types for each column from a collection of rows.
    """
    rows = list(rows)
    if not rows:
        return {}

    columns = rows[0].keys()
    schema: Dict[str, str] = {}

    for col in columns:
        values = [row.get(col) for row in rows]
        schema[col] = infer_type_for_column(values)

    return schema