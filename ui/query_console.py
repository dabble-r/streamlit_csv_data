# ui/query_console.py
import streamlit as st
from typing import Dict, Any
from state.session import get_llm_config
from state.cache import add_cached_query, get_cached_queries
from mcp.refactor_sql import nl_to_sql
from mcp.expand_queries import expand_sql_queries
from database.executor import run_query
from utils.validators import is_safe_sql


def render_query_console(schema: Dict[str, str], table_name: str):
    st.subheader("Natural language query console")

    llm_config = get_llm_config()
    if llm_config is None:
        st.warning("Select an LLM provider and enter a valid API key first.")
        return

    user_query = st.text_input("Ask a question about the data")
    if st.button("Generate SQL and expansions", disabled=not user_query):
        base_sql = nl_to_sql(user_query, schema, llm_config)
        expansions = expand_sql_queries(user_query, schema, llm_config, n=5)

        add_cached_query("Original query", user_query, base_sql)
        for i, variant in enumerate(expansions, start=1):
            sql_variant = nl_to_sql(variant, schema, llm_config)
            add_cached_query(f"Variant {i}", variant, sql_variant)

        st.success("Queries generated and cached.")

    cached = get_cached_queries()
    if cached:
        st.markdown("### Cached queries")
        labels = [q["label"] for q in cached]
        choice = st.selectbox("Select a query to run", labels)
        selected: Dict[str, Any] | None = next((q for q in cached if q["label"] == choice), None)

        if selected:
            st.code(selected["sql"], language="sql")
            if not is_safe_sql(selected["sql"]):
                st.error("This query looks unsafe and will not be executed.")
            else:
                if st.button("Run selected query"):
                    rows = run_query(selected["sql"])
                    st.dataframe(rows)