# ingestion/pipeline.py
from typing import List, Dict, Any, Tuple
from .csv_reader import read_csv
from .row_normalizer import collect_all_keys, normalize_rows
from .nested_field_filter import drop_nested_fields
from .pii_detection import detect_pii_columns
from .pii_hashing import apply_pii_hashing
from .type_inference import infer_schema
from .schema_builder import normalize_column_name


def run_ingestion_pipeline(file_bytes: bytes) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Full ingestion pipeline:
    - read CSV
    - drop nested fields
    - normalize rows (missing/extra columns)
    - detect + hash PII
    - infer schema
    Returns (clean_rows, schema).
    """
    raw_rows = list(read_csv(file_bytes))
    if not raw_rows:
        return [], {}

    # Drop nested fields
    flat_rows = [drop_nested_fields(r) for r in raw_rows]

    # Normalize rows
    all_keys = list(collect_all_keys(flat_rows))
    normalized_rows = list(normalize_rows(flat_rows, all_keys))

    # Detect PII columns from first row
    pii_cols = detect_pii_columns(normalized_rows[0])

    # Apply PII hashing
    hashed_rows = [apply_pii_hashing(r, pii_cols) for r in normalized_rows]

    # Infer schema
    schema = infer_schema(hashed_rows)

    # Normalize column names so DB and LLM use same identifiers (avoids e.g. Director_ as function)
    # Resolve collisions (e.g. "Director" and "Director " -> director, director_2)
    seen: Dict[str, int] = {}
    col_mapping: Dict[str, str] = {}
    for col in schema:
        base = normalize_column_name(col)
        if base in seen:
            seen[base] += 1
            final = f"{base}_{seen[base]}"
        else:
            seen[base] = 1
            final = base
        col_mapping[col] = final
    norm_schema = {col_mapping[col]: typ for col, typ in schema.items()}
    norm_rows = [{col_mapping[k]: v for k, v in row.items()} for row in hashed_rows]

    return norm_rows, norm_schema