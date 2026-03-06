# utils/validators.py
from typing import Dict


def is_safe_sql(sql: str) -> bool:
    """
    Very naive SQL safety check. Extend with real validation.
    """
    lowered = sql.lower()
    forbidden = ["drop ", "delete ", "update ", "alter "]
    return not any(word in lowered for word in forbidden)


def ensure_schema_not_empty(schema: Dict[str, str]) -> bool:
    return bool(schema)