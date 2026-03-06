# utils/validators.py
import re
from typing import Dict, Set, Tuple, List


def is_safe_sql(sql: str) -> bool:
    """
    Very naive SQL safety check. Extend with real validation.
    """
    lowered = sql.lower()
    forbidden = ["drop ", "delete ", "update ", "alter "]
    return not any(word in lowered for word in forbidden)


def extract_executable_sql(raw: str, table_name: str | None = None) -> str:
    """
    Extract a single executable SQL statement from LLM output that may contain
    markdown code blocks or leading/trailing prose (e.g. "To answer your question...").
    If table_name is provided, replace common placeholders (your_table_name, etc.) with the real table name.
    """
    if not raw or not raw.strip():
        return ""
    text = raw.strip()

    # Extract from markdown code block if present
    if "```" in text:
        match = re.search(r"```(?:sql)?\s*\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)
        else:
            # Unclosed block: take after first ```
            idx = text.find("```")
            if idx >= 0:
                rest = text[idx + 3 :].strip()
                if rest.lower().startswith("sql"):
                    rest = rest[3:].lstrip("\n")
                text = rest
    text = text.strip()

    # Find the start of the first SQL statement (SELECT, WITH, PRAGMA, etc.)
    start = re.search(r"\b(SELECT|WITH|PRAGMA)\b", text, re.IGNORECASE)
    if start:
        text = text[start.start() :]
    # Take up to last semicolon, then strip (ignore trailing comments/prose)
    last_semi = text.rfind(";")
    if last_semi >= 0:
        text = text[: last_semi + 1]
    text = text.strip()

    # Replace placeholder table names with actual table name so execution succeeds
    if table_name:
        quoted = f'"{table_name}"'
        # Replace unquoted placeholder (word boundary)
        text = re.sub(r"\byour_table_name\b", quoted, text, flags=re.IGNORECASE)
        text = re.sub(r"\bthe_table_name\b", quoted, text, flags=re.IGNORECASE)
        # Replace quoted placeholders
        text = text.replace('"your_table_name"', quoted)
        text = text.replace("'your_table_name'", quoted)
        text = text.replace('"the_table_name"', quoted)
        text = text.replace("'the_table_name'", quoted)

    return text


def ensure_schema_not_empty(schema: Dict[str, str]) -> bool:
    return bool(schema)


def validate_sql_identifiers(
    sql: str,
    table_name: str,
    db_column_names: Set[str],
) -> Tuple[bool, List[str]]:
    """
    Check that double-quoted identifiers in the SQL exist in the DB (table or columns).
    Quoted identifiers that appear after AS (SELECT-list aliases) are allowed and not
    required to exist in the table, so aggregates/computed columns do not trigger warnings.
    Returns (all_valid, list_of_missing_identifiers).
    """
    valid = db_column_names | {table_name}
    quoted = re.findall(r'"([^"]+)"', sql)
    alias_match = re.findall(r"\bAS\s+\"([^\"]+)\"", sql, re.IGNORECASE)
    allowed_aliases = set(alias_match)
    valid_or_alias = valid | allowed_aliases
    missing = [x for x in quoted if x not in valid_or_alias]
    return (len(missing) == 0, missing)