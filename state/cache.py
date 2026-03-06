# state/cache.py
import streamlit as st
from typing import Dict, Any, List


def add_cached_query(label: str, nl_query: str, sql_query: str):
    cached: List[Dict[str, Any]] = st.session_state.get("cached_queries", [])
    cached.append({"label": label, "nl": nl_query, "sql": sql_query})
    st.session_state["cached_queries"] = cached


def get_cached_queries() -> List[Dict[str, Any]]:
    return st.session_state.get("cached_queries", [])