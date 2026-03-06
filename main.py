# ui/main.py
import streamlit as st
from ingestion.pipeline import run_ingestion_pipeline
from ingestion.schema_builder import filename_to_table_name
from database.loader import load_rows_into_table
from database.inspector import get_tables
from database.connection import clear_db
from llm.providers import get_supported_providers
from llm.key_validation import validate_key
from llm.litellm_client import validate_key_with_litellm
from state.session import init_session_state, set_llm_config
from state.cache import clear_cached_queries
from ui.browse_students import render_browse_page
from ui.query_console import render_query_console


def main():
    st.set_page_config(page_title="CSV Data Explorer", layout="wide")
    init_session_state()

    # Clear DB once per session when the app first loads
    if st.session_state.get("db_cleared") is not True:
        clear_db()
        st.session_state["db_cleared"] = True

    st.title("Early Literacy Data Explorer")

    # Sidebar: LLM provider + API key
    st.sidebar.header("LLM Settings")
    providers = get_supported_providers()
    provider = st.sidebar.selectbox("LLM Provider", providers)
    api_key = st.sidebar.text_input("API Key", type="password")
    submit_key = st.sidebar.button("Submit", key="api_key_submit")

    if submit_key and api_key:
        valid, message = validate_key(provider, api_key)
        st.sidebar.caption(message)
        if valid:
            api_valid, api_message = validate_key_with_litellm(provider, api_key)
            st.sidebar.caption(api_message)
            if api_valid:
                set_llm_config(provider, api_key)
                st.sidebar.success("API key saved and validated.")
            else:
                st.sidebar.error("Key rejected by provider. Fix the key and try again.")

    st.sidebar.header("Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        last_processed = st.session_state.get("last_processed_file_name")
        if last_processed != uploaded_file.name:
            bytes_data = uploaded_file.read()
            rows, schema = run_ingestion_pipeline(bytes_data)
            if not rows:
                st.error("No rows found after ingestion.")
            else:
                clear_db()
                clear_cached_queries()
                table_name = filename_to_table_name(uploaded_file.name)
                st.session_state["table_name"] = table_name
                st.session_state["rows"] = rows
                st.session_state["schema"] = schema
                st.session_state["last_processed_file_name"] = uploaded_file.name
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