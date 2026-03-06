# ui/main.py
import streamlit as st
from ingestion.pipeline import run_ingestion_pipeline
from database.loader import load_rows_into_table
from database.inspector import get_tables
from llm.providers import get_supported_providers
from llm.key_validation import validate_key
from state.session import init_session_state, set_llm_config
from ui.browse_students import render_browse_page
from ui.query_console import render_query_console


def main():
    st.set_page_config(page_title="Early Literacy Data Explorer", layout="wide")
    init_session_state()

    st.title("Early Literacy Data Explorer")

    # Sidebar: LLM provider + API key
    st.sidebar.header("LLM Settings")
    providers = get_supported_providers()
    provider = st.sidebar.selectbox("LLM Provider", providers)
    api_key = st.sidebar.text_input("API Key", type="password")

    if api_key:
        valid, message = validate_key(provider, api_key)
        st.sidebar.caption(message)
        if valid:
            set_llm_config(provider, api_key)

    st.sidebar.header("Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        bytes_data = uploaded_file.read()
        rows, schema = run_ingestion_pipeline(bytes_data)
        if not rows:
            st.error("No rows found after ingestion.")
        else:
            st.session_state["rows"] = rows
            st.session_state["schema"] = schema
            table_name = st.session_state["table_name"]
            load_rows_into_table(table_name, rows, schema)
            st.sidebar.success("Data ingested and loaded into database.")

    table_name = st.session_state.get("table_name", "students")
    schema = st.session_state.get("schema", {})

    tab1, tab2 = st.tabs(["Browse", "Query"])
    with tab1:
        render_browse_page(table_name)
    with tab2:
        render_query_console(schema, table_name)


if __name__ == "__main__":
    main()