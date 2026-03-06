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
from utils.query_import_export import build_export_text, parse_import_file, group_parsed_by_label_prefix


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

    # Import queries: hidden by default in expander
    st.markdown("---")
    with st.expander("Import queries", expanded=False):
        if "import_uploader_key" not in st.session_state:
            st.session_state["import_uploader_key"] = 0
        import_file = st.file_uploader(
            "Import queries from file",
            type=["txt", "md", "sql"],
            key=f"import_queries_file_{st.session_state['import_uploader_key']}",
        )
        if import_file is not None:
            # Process only when this file is "new" so we don't re-read exhausted stream on rerun (see tests/upload_query_1.md)
            file_id = (import_file.name, getattr(import_file, "size", 0))
            if file_id != st.session_state.get("last_imported_file_id"):
                try:
                    content = import_file.read().decode("utf-8", errors="replace")
                    parsed = parse_import_file(content)
                    if parsed:
                        # Group by label prefix (e.g. "1. Original" + "1. Variant" -> one group) and assign next free display number
                        groups = group_parsed_by_label_prefix(parsed)
                        existing = get_cached_queries()
                        existing_sids = {q["submission_index"] for q in existing}
                        next_sid = (min(existing_sids) - 1) if existing_sids else 0
                        num_existing_groups = len(existing_sids) if existing_sids else 0
                        for group_idx, group in enumerate(groups):
                            display_num = num_existing_groups + 1 + group_idx
                            for i, p in enumerate(group):
                                stored_label = f"{display_num}. Original" if i == 0 else f"{display_num}. Variant"
                                add_cached_query(
                                    stored_label,
                                    p["nl"],
                                    p["sql"],
                                    submission_index=next_sid,
                                    is_original=(i == 0),
                                )
                            next_sid -= 1
                        st.session_state["last_imported_file_id"] = file_id
                        st.success(f"Imported {len(parsed)} queries ({len(groups)} groups).")
                        st.rerun()
                    else:
                        st.warning("No queries found in the file. Use the export format: ## Title, TITLE: ..., NL: ..., SQL: ...")
                except Exception as e:
                    st.error("Import failed: " + user_message_for_exception(e))

    cached = get_cached_queries()

    # Only Cached queries title and select dropdown always visible; rest mostly hidden (expander)
    st.markdown("### Cached queries")
    if not cached:
        st.selectbox(
            "Select a query to run",
            options=["— No cached queries (generate or import to add) —"],
            key="cached_query_choice",
            disabled=True,
        )
        st.caption("Generate SQL from a natural language question above, or import a cached query file below.")
    else:
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

        # Include in export + Clear: hidden by default in expander
        with st.expander("Cached query options (export / clear)", expanded=False):
            if st.button("Clear cached queries", key="clear_cached_queries"):
                clear_cached_queries()
                st.session_state.pop("last_imported_file_id", None)
                st.session_state["import_uploader_key"] = st.session_state.get("import_uploader_key", 0) + 1
                st.rerun()
            st.caption("Include in export:")
            for i in range(len(ordered)):
                st.checkbox(labels[i], value=True, key=f"export_include_{i}")
            to_export = [
                {"label": labels[i], "nl": ordered[i][2]["nl"], "sql": ordered[i][2]["sql"]}
                for i in range(len(ordered))
                if st.session_state.get(f"export_include_{i}", True)
            ]
            if to_export:
                export_bytes = build_export_text(to_export).encode("utf-8")
                st.download_button(
                    "Export selected",
                    data=export_bytes,
                    file_name="cached_queries_export.txt",
                    mime="text/plain",
                    key="export_selected_queries",
                )

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