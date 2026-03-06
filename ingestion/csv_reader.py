# ingestion/csv_reader.py
from typing import Iterable, Dict, Any
import csv
import io


def read_csv(file_bytes: bytes, encoding: str = "utf-8") -> Iterable[Dict[str, Any]]:
    """
    Read a CSV file from raw bytes and yield rows as dicts.
    Handles basic irregularities but assumes flat, row-based data.
    """
    text = file_bytes.decode(encoding, errors="replace")
    buffer = io.StringIO(text)
    reader = csv.DictReader(buffer)

    for row in reader:
        yield dict(row)