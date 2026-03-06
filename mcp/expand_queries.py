# mcp/expand_queries.py
import re
from typing import List, Dict
from llm.client_factory import get_llm_client
from llm.settings import LLMConfig
from .prompt_templates import build_schema_prompt, build_pick_best_variant_prompt


def _parse_numbered_variants(text: str, n: int = 5) -> List[str]:
    """Extract up to n numbered items (1. ... 2. ...) from LLM response."""
    variants: List[str] = []
    pattern = re.compile(r"^\s*\d+[.)]\s*(.+)$", re.MULTILINE | re.IGNORECASE)
    for m in pattern.finditer(text):
        variants.append(m.group(1).strip())
        if len(variants) >= n:
            break
    return variants


def expand_sql_queries(
    base_nl_query: str,
    schema: Dict[str, str],
    config: LLMConfig,
    n: int = 5,
    table_name: str = "data",
) -> List[str]:
    """
    Ask the LLM to brainstorm n alternative NL queries, then ask it to pick the single best one.
    Returns a list with one element: the best variant (or [base_nl_query] on fallback).
    """
    client = get_llm_client(config)
    schema_prompt = build_schema_prompt(schema, table_name)

    prompt1 = (
        f"{schema_prompt}\n\n"
        f"User question: {base_nl_query}\n\n"
        f"Braistorm exactly {n} relevant alternative questions. "
        f"Number them 1 through {n}, one per line (e.g. '1. First question')."
    )
    raw_variants = client.generate(prompt1)
    variants = _parse_numbered_variants(raw_variants, n)

    if not variants:
        return [base_nl_query]

    prompt2 = build_pick_best_variant_prompt(variants)
    best = client.generate(prompt2).strip()
    if "\n" in best:
        best = best.split("\n")[0].strip()
    if not best:
        best = variants[0]
    return [best]