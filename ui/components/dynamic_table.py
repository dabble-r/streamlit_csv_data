# ui/components/dynamic_table.py
from typing import List, Dict, Any
import streamlit as st
from utils.formatting import rows_to_table


def render_table(rows: List[Dict[str, Any]]):
    if not rows:
        st.info("No data to display.")
        return
    table = rows_to_table(rows)
    st.dataframe(table)