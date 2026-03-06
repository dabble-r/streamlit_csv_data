# ingestion/pii_hashing.py
from typing import Dict, Any, Set
import hashlib


def hash_pii_value(value: str, salt: str = "literacy-app") -> str:
    """
    Deterministically hash a PII value into a 5-digit numeric string.
    """
    digest = hashlib.sha256((salt + value).encode()).hexdigest()
    return str(int(digest, 16))[:5]


def apply_pii_hashing(
    row: Dict[str, Any],
    pii_columns: Set[str],
    salt: str = "literacy-app",
) -> Dict[str, Any]:
    """
    Replace PII values in specified columns with 5-digit hashes.
    """
    new_row = dict(row)
    for col in pii_columns:
        value = new_row.get(col)
        if value is None:
            continue
        if not isinstance(value, str):
            value = str(value)
        new_row[col] = hash_pii_value(value, salt=salt)
    return new_row