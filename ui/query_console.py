# ui/query_console.py
import streamlit as st
from typing import Dict, Any, List
from state.session import get_llm_config
from state.cache import add_cached_query, get_cached_queries, clear_cached_queries
from mcp.refactor_sql import nl_to_sql
from mcp.expand_queries import expand_sql_queries
from database.executor import run_query
from utils.validators import is_safe_sql, extract_executable_sql
from utils.formatting import rows_to_arrow_safe_dataframe


def render_query_console(schema: Dict[str, str], table_name: str):
    st.subheader("Natural language query console")

    llm_config = get_llm_config()
    if llm_config is None:
        st.warning("Select an LLM provider and enter a valid API key first.")
        return

    user_query = st.text_input("Ask a question about the data")
    if st.button("Generate SQL", disabled=not user_query):
        base_sql = nl_to_sql(user_query, schema, llm_config, table_name)
        expansions = expand_sql_queries(user_query, schema, llm_config, n=5, table_name=table_name)

        cached_so_far = get_cached_queries()
        submission_index = len([q for q in cached_so_far if q.get("is_original", False)])
        add_cached_query("Original query", user_query, base_sql, submission_index=submission_index, is_original=True)
        if expansions:
            variant_nl = expansions[0]
            sql_variant = nl_to_sql(variant_nl, schema, llm_config, table_name)
            add_cached_query("Variant", variant_nl, sql_variant, submission_index=submission_index, is_original=False)

        st.success("Queries generated and cached.")

    cached = get_cached_queries()
    if cached:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### Cached queries")
        with col2:
            if st.button("Clear cached queries", key="clear_cached_queries"):
                clear_cached_queries()
                st.rerun()
        labels = [q["label"] for q in cached]
        choice = st.selectbox("Select a query to run", labels, key="cached_query_choice")
        selected: Dict[str, Any] | None = next((q for q in cached if q["label"] == choice), None)

        if selected:
            st.caption("Edit the SQL below if needed (e.g. replace placeholders like your_table_name), then run.")
            sql_to_run = st.text_area(
                "SQL",
                value=selected["sql"],
                height=200,
                key=f"sql_edit_{choice}",
                label_visibility="collapsed",
            )
            if not is_safe_sql(sql_to_run):
                st.error("This query looks unsafe and will not be executed.")
            else:
                if st.button("Run selected query"):
                    executable = extract_executable_sql(sql_to_run, table_name=table_name)
                    if not executable:
                        st.error("No executable SQL found. Ensure the query contains a SELECT or WITH statement.")
                    else:
                        rows = run_query(executable)
                        st.dataframe(rows_to_arrow_safe_dataframe(rows))