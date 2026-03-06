# ingestion/nested_field_filter.py
from typing import Dict, Any


def is_nested_value(value: Any) -> bool:
    """
    Return True if the value looks like nested JSON (dict, list, or JSON-like string).
    """
    if isinstance(value, (dict, list)):
        return True

    if isinstance(value, str):
        stripped = value.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            return True

    return False


def drop_nested_fields(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Drop any fields whose value appears to be nested JSON-like data.
    """
    return {k: v for k, v in row.items() if not is_nested_value(v)}