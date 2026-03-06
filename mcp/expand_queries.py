# mcp/expand_queries.py
from typing import List, Dict
from llm.client_factory import get_llm_client
from llm.settings import LLMConfig
from .prompt_templates import build_schema_prompt


def expand_sql_queries(
    base_nl_query: str,
    schema: Dict[str, str],
    config: LLMConfig,
    n: int = 5,
) -> List[str]:
    """
    Ask the LLM to propose up to n alternative NL queries (or SQL variants).
    For now, returns simple variations as placeholders.
    """
    client = get_llm_client(config)
    schema_prompt = build_schema_prompt(schema)
    prompt = (
        f"{schema_prompt}\n\n"
        f"User question: {base_nl_query}\n\n"
        f"Propose {n} alternative questions that might be useful follow-ups."
    )
    _ = client.generate(prompt)  # not used in dummy implementation

    return [f"{base_nl_query} (variant {i+1})" for i in range(n)]