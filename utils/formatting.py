# utils/formatting.py
from typing import List, Dict, Any

import pandas as pd


def rows_to_table(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Placeholder for any formatting needed before displaying rows.
    """
    return rows


def rows_to_arrow_safe_dataframe(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Build a DataFrame from rows and coerce mixed-type (object) columns to string
    so Streamlit/PyArrow serialization does not fail.
    """
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).replace("nan", "").replace("None", "")
    return df