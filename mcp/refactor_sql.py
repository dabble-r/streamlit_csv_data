# mcp/refactor_sql.py
from typing import Dict
from llm.client_factory import get_llm_client
from llm.settings import LLMConfig
from .prompt_templates import build_schema_prompt


def nl_to_sql(
    user_query: str,
    schema: Dict[str, str],
    config: LLMConfig,
    table_name: str = "data",
) -> str:
    """
    Use the selected LLM provider to turn a natural language query
    into a SQL query for the given table and schema.
    """
    client = get_llm_client(config)
    schema_prompt = build_schema_prompt(schema, table_name)
    prompt = f"{schema_prompt}\n\nUser question: {user_query}\n\nSQL:"
    sql = client.generate(prompt)
    return sql