# state/session.py
import streamlit as st
from typing import Dict, Any, List
from llm.settings import LLMConfig


def init_session_state():
    if "rows" not in st.session_state:
        st.session_state["rows"]: List[Dict[str, Any]] = []
    if "schema" not in st.session_state:
        st.session_state["schema"]: Dict[str, str] = {}
    if "table_name" not in st.session_state:
        st.session_state["table_name"] = "students"
    if "llm_config" not in st.session_state:
        st.session_state["llm_config"] = None
    if "cached_queries" not in st.session_state:
        st.session_state["cached_queries"] = []  # list of dicts: {label, nl, sql}


def set_llm_config(provider: str, api_key: str):
    st.session_state["llm_config"] = LLMConfig(provider=provider, api_key=api_key)


def get_llm_config() -> LLMConfig | None:
    return st.session_state.get("llm_config")