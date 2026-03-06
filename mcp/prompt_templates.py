# mcp/prompt_templates.py
from typing import Dict, List


def build_schema_prompt(schema: Dict[str, str], table_name: str = "data") -> str:
    """
    Build a textual description of the current DB schema for the LLM.
    Includes exact table name and column names so generated SQL uses valid identifiers.
    """
    lines = [
        f"You are generating SQLite SQL. The table name is: \"{table_name}\".",
        "Use only these columns (use the exact quoted names in your SQL):",
    ]
    for col, col_type in schema.items():
        lines.append(f"  - \"{col}\" ({col_type})")
    lines.append("")
    lines.append(
        "Rules: Use double-quoted identifiers for the table and every column "
        "(e.g. SELECT \"column\" FROM \"table\"). Output only one SQL statement, no explanation or markdown."
    )
    return "\n".join(lines)


def build_pick_best_variant_prompt(variants: List[str]) -> str:
    """Ask the LLM to pick the single best question from a list of variants."""
    lines = ["Consider these alternative questions:", ""]
    for i, v in enumerate(variants, 1):
        lines.append(f"{i}. {v}")
    lines.append("")
    lines.append(
        "Which single question is the best (most useful and clear)? "
        "Reply with only that one question, nothing else."
    )
    return "\n".join(lines)