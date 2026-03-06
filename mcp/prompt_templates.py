# mcp/prompt_templates.py
from typing import Dict


def build_schema_prompt(schema: Dict[str, str]) -> str:
    """
    Build a textual description of the current DB schema for the LLM.
    """
    lines = ["You are given a SQL table with the following columns:"]
    for col, col_type in schema.items():
        lines.append(f"- {col} ({col_type})")
    lines.append("Generate a SQL query that answers the user's question.")
    return "\n".join(lines)