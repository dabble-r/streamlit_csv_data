# ui/query_console.py
import streamlit as st
from typing import Dict, Any, List
from state.session import get_llm_config
from state.cache import add_cached_query, get_cached_queries, clear_cached_queries
from mcp.refactor_sql import nl_to_sql
from mcp.expand_queries import expand_sql_queries
from database.executor import run_query
from database.inspector import get_table_schema
from utils.validators import is_safe_sql, extract_executable_sql, validate_sql_identifiers
from utils.formatting import rows_to_arrow_safe_dataframe
from utils.error_messages import user_message_for_exception


def render_query_console(schema: Dict[str, str], table_name: str):
    st.subheader("Natural language query console")

    llm_config = get_llm_config()
    if llm_config is None:
        st.warning("Select an LLM provider and enter a valid API key first.")
        return

    user_query = st.text_input("Ask a question about the data")
    if st.button("Generate SQL", disabled=not user_query):
        try:
            base_sql = nl_to_sql(user_query, schema, llm_config, table_name)
            expansions = expand_sql_queries(user_query, schema, llm_config, n=5, table_name=table_name)

            cached_so_far = get_cached_queries()
            submission_index = len([q for q in cached_so_far if q.get("is_original", False)])
            add_cached_query("Original query", user_query, base_sql, submission_index=submission_index, is_original=True)
            if expansions:
                variant_nl = expansions[0]
                sql_variant = nl_to_sql(variant_nl, schema, llm_config, table_name)
                add_cached_query("Variant", variant_nl, sql_variant, submission_index=submission_index, is_original=False)

            cached_after = get_cached_queries()
            submission_ids = sorted(set(q["submission_index"] for q in cached_after), reverse=True)
            ordered_after = []
            for num, sid in enumerate(submission_ids, 1):
                group = [q for q in cached_after if q["submission_index"] == sid]
                group.sort(key=lambda q: (0 if q.get("is_original", False) else 1))
                for q in group:
                    kind = "Original" if q.get("is_original", False) else "Variant"
                    ordered_after.append((num, kind, q))
            new_labels = [f"{num}. {kind}" for num, kind, _ in ordered_after]
            if new_labels:
                st.session_state["cached_query_choice"] = new_labels[0]

            st.success("Queries generated and cached.")
        except Exception as e:
            st.error("Generation failed: " + user_message_for_exception(e))

    cached = get_cached_queries()
    if cached:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### Cached queries")
        with col2:
            if st.button("Clear cached queries", key="clear_cached_queries"):
                clear_cached_queries()
                st.rerun()
        submission_ids = sorted(set(q["submission_index"] for q in cached), reverse=True)
        ordered = []
        for num, sid in enumerate(submission_ids, 1):
            group = [q for q in cached if q["submission_index"] == sid]
            group.sort(key=lambda q: (0 if q.get("is_original", False) else 1))
            for q in group:
                kind = "Original" if q.get("is_original", False) else "Variant"
                ordered.append((num, kind, q))
        labels = [f"{num}. {kind}" for num, kind, _ in ordered]
        current_choice = st.session_state.get("cached_query_choice")
        if current_choice not in labels:
            st.session_state["cached_query_choice"] = labels[0]
        choice = st.selectbox("Select a query to run", labels, key="cached_query_choice")
        selected: Dict[str, Any] | None = None
        if choice in labels:
            idx = labels.index(choice)
            selected = ordered[idx][2]

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
                        db_schema = get_table_schema(table_name)
                        db_columns = {c["name"] for c in db_schema}
                        session_columns = set(schema.keys())

                        if not db_columns:
                            st.warning(
                                "No table found for the current session. Upload a CSV first, or the table name may have changed. "
                                "Clear cached queries and re-upload your data, then regenerate."
                            )
                        else:
                            if db_columns != session_columns:
                                st.warning(
                                    "The table structure in the database differs from the schema used when queries were generated. "
                                    f"Current table columns: {sorted(db_columns)}. Session schema had: {sorted(session_columns)}. "
                                    "Re-upload your data or clear cached queries and regenerate to avoid column errors."
                                )
                            valid_ids, missing = validate_sql_identifiers(executable, table_name, db_columns)
                            if not valid_ids:
                                missing_list = sorted(set(missing))
                                st.warning(
                                    f"The query references identifiers that are not in the current table: {missing_list}. "
                                    "The query may fail. Update the SQL or re-upload data and regenerate."
                                )

                        try:
                            rows = run_query(executable)
                            df = rows_to_arrow_safe_dataframe(rows)
                            st.caption("Result may include computed columns (e.g. aggregates) not in the original table.")
                            st.dataframe(df)
                            if not df.empty:
                                csv_bytes = df.to_csv(index=False).encode("utf-8")
                                st.download_button(
                                    "Export as CSV",
                                    data=csv_bytes,
                                    file_name="query_result.csv",
                                    mime="text/csv",
                                    key="export_query_csv",
                                )
                        except Exception as e:
                            err = user_message_for_exception(e).lower()
                            if "no such column" in err or "no such table" in err:
                                st.error(
                                    "Query failed: " + user_message_for_exception(e) + " "
                                    "The table structure may have changed. "
                                    "If the query uses aggregates or expressions, ensure column names in FROM/WHERE/GROUP BY/ORDER BY match the table; SELECT aliases are allowed. "
                                    "Otherwise clear cached queries, re-upload your data, and regenerate the query."
                                )
                            else:
                                st.error("Query failed: " + user_message_for_exception(e))