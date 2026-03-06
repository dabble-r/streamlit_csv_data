# ui/components/query_dropdown.py
from typing import List, Dict, Any
import streamlit as st


def render_query_dropdown(cached_queries: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not cached_queries:
        st.info("No cached queries yet.")
        return None

    labels = [q["label"] for q in cached_queries]
    choice = st.selectbox("Choose a cached query", labels)
    for q in cached_queries:
        if q["label"] == choice:
            return q
    return None