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
from state.session import init_session_state, set_llm_config, clear_llm_config, get_llm_config
from state.cache import clear_cached_queries
from ui.browse_students import render_browse_page
from ui.query_console import render_query_console
from utils.error_messages import user_message_for_exception


def main():
    st.set_page_config(page_title="CSV Data Explorer", layout="wide")
    init_session_state()

    # Rotating key for API key input so "Clear" resets the field without a persistent flag that could clear config on a later run (see tests/api_session_1.md)
    if "api_key_input_key" not in st.session_state:
        st.session_state["api_key_input_key"] = 0

    # Do not clear DB on first run: in multi-process deployments a new process would wipe the shared DB and drop data (see tests/csv_drop_1.md). DB is cleared only when the user uploads a new file (below).

    st.title("CSV Data Explorer")

    # Sidebar: LLM provider + API key
    st.sidebar.header("LLM Settings")
    providers = get_supported_providers()
    provider = st.sidebar.selectbox("LLM Provider", providers)
    api_key = st.sidebar.text_input("API Key", key=f"api_key_input_{st.session_state['api_key_input_key']}", type="password")
    st.sidebar.caption("Closing the browser ends the session and clears the key from server memory.")
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

    if get_llm_config() is not None:
        if st.sidebar.button("Clear API key", key="clear_api_key"):
            clear_llm_config()
            st.session_state["api_key_input_key"] = st.session_state.get("api_key_input_key", 0) + 1
            st.rerun()

    st.sidebar.header("Data")
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        last_processed = st.session_state.get("last_processed_file_name")
        if last_processed != uploaded_file.name:
            try:
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
            except Exception as e:
                st.sidebar.error("Upload failed: " + user_message_for_exception(e))

    table_name = st.session_state.get("table_name", "students")
    schema = st.session_state.get("schema", {})

    tab1, tab2 = st.tabs(["Browse", "Query"])
    with tab1:
        render_browse_page(table_name)
    with tab2:
        render_query_console(schema, table_name)


if __name__ == "__main__":
    main()