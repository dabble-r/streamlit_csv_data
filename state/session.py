# state/session.py
"""
Session state for the Streamlit app.
SECURITY: Do not log or persist objects containing api_key (e.g. llm_config).
Use LLMConfig.safe_repr() or redact before any debug output.
"""
import streamlit as st
from typing import Dict, Any, List
from llm.settings import LLMConfig


def init_session_state():
    if "rows" not in st.session_state:
        st.session_state["rows"]: List[Dict[str, Any]] = []
    if "schema" not in st.session_state:
        st.session_state["schema"]: Dict[str, str] = {}
    if "table_name" not in st.session_state:
        st.session_state["table_name"] = "table_name"
    if "llm_config" not in st.session_state:
        st.session_state["llm_config"] = None
    if "cached_queries" not in st.session_state:
        st.session_state["cached_queries"] = []  # list of dicts: {label, nl, sql}


def set_llm_config(provider: str, api_key: str):
    st.session_state["llm_config"] = LLMConfig(provider=provider, api_key=api_key)


def clear_llm_config():
    """Remove the stored API key from session state. Key is cleared from server memory for this session."""
    st.session_state["llm_config"] = None


def get_llm_config() -> LLMConfig | None:
    return st.session_state.get("llm_config")