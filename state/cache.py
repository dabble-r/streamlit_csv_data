# state/cache.py
import streamlit as st
from typing import Dict, Any, List


def add_cached_query(label: str, nl_query: str, sql_query: str, submission_index: int | None = None, is_original: bool = False):
    cached: List[Dict[str, Any]] = st.session_state.get("cached_queries", [])
    if submission_index is None:
        submission_index = len([q for q in cached if q.get("is_original", False)])
    cached.append({
        "label": label,
        "nl": nl_query,
        "sql": sql_query,
        "submission_index": submission_index,
        "is_original": is_original,
    })
    st.session_state["cached_queries"] = cached


def get_cached_queries() -> List[Dict[str, Any]]:
    return st.session_state.get("cached_queries", [])


def clear_cached_queries():
    """Remove all cached queries (e.g. after uploading new data with a new schema)."""
    st.session_state["cached_queries"] = []