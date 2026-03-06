# ingestion/row_normalizer.py
from typing import Iterable, Dict, Any, List, Set


def collect_all_keys(rows: Iterable[Dict[str, Any]]) -> Set[str]:
    """
    Collect the union of all keys across rows.
    """
    keys: Set[str] = set()
    for row in rows:
        keys.update(row.keys())
    return keys


def normalize_rows(
    rows: Iterable[Dict[str, Any]],
    all_keys: List[str],
) -> Iterable[Dict[str, Any]]:
    """
    Ensure each row has all keys in all_keys, filling missing with None.
    Extra keys are kept if present in all_keys.
    """
    for row in rows:
        normalized = {key: row.get(key, None) for key in all_keys}
        yield normalized