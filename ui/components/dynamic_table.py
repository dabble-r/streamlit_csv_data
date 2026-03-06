# ui/components/dynamic_table.py
from typing import List, Dict, Any
import streamlit as st
from utils.formatting import rows_to_table, rows_to_arrow_safe_dataframe


def render_table(rows: List[Dict[str, Any]]):
    if not rows:
        st.info("No data to display.")
        return
    table = rows_to_table(rows)
    st.dataframe(rows_to_arrow_safe_dataframe(table))