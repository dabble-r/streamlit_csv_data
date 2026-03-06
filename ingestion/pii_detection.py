# ingestion/pii_detection.py
from typing import Dict, Any, Set
import re

PII_NAME_HINTS = ["name", "student", "first", "last"]
PII_ID_HINTS = ["id", "student_id", "sis"]
PII_CONTACT_HINTS = ["email", "phone", "mobile", "contact"]


def detect_pii_columns(sample_row: Dict[str, Any]) -> Set[str]:
    """
    Heuristic detection of PII columns based on column names.
    """
    pii_cols: Set[str] = set()
    for col in sample_row.keys():
        lower = col.lower()
        if any(h in lower for h in PII_NAME_HINTS + PII_ID_HINTS + PII_CONTACT_HINTS):
            pii_cols.add(col)
    return pii_cols


EMAIL_REGEX = re.compile(r".+@.+\..+")


def is_pii_value(value: Any) -> bool:
    """
    Optional value-based heuristic (not strictly needed if name-based is enough).
    """
    if not isinstance(value, str):
        return False
    if EMAIL_REGEX.match(value):
        return True
    return False