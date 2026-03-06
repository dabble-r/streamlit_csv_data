# ui/browse_students.py
import streamlit as st
from database.executor import run_query
from database.inspector import get_table_schema
from ui.components.dynamic_table import render_table


def render_browse_page(table_name: str):
    st.subheader("Browse Data")

    schema_info = get_table_schema(table_name)
    if not schema_info:
        st.info("No table schema found. Upload a CSV first.")
        return

    st.caption(f"Table: {table_name}")
    cols = [c["name"] for c in schema_info]

    selected_cols = st.multiselect("Columns to display", cols, default=cols)
    if not selected_cols:
        st.warning("Select at least one column.")
        return

    cols_sql = ", ".join(f'"{c}"' for c in selected_cols)
    sql = f'SELECT {cols_sql} FROM "{table_name}" LIMIT 200;'
    rows = run_query(sql)
    render_table(rows)