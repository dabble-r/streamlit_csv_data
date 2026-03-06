# utils/query_import_export.py
"""
Export cached queries to text/markdown and parse imported query files.
Format matches tests/export_cached_queries_1.md (## N. Label, NL: ..., SQL: ...).
"""
import re
from typing import Dict, Any, List


def build_export_text(queries: List[Dict[str, Any]]) -> str:
    """
    Build a single text/markdown string from a list of cached query dicts.
    Format: for each query, section with ## title, TITLE:, NL:, SQL: so the file
    is recognizable and round-trip importable. Each dict must have "label", "nl", "sql".
    """
    lines = ["# Cached queries export", ""]
    for q in queries:
        title = q.get("label", "Query")
        nl = q.get("nl", "")
        sql = (q.get("sql") or "").strip()
        lines.append(f"## {title}")
        lines.append(f"TITLE: {title}")
        lines.append(f"NL: {nl}")
        lines.append("SQL:")
        lines.append(sql)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def parse_import_file(content: str) -> List[Dict[str, str]]:
    """
    Parse file content (export format) into a list of {label, nl, sql}.
    Recognizes: ## Title, optional TITLE: ..., NL: ..., SQL: ... (multiline).
    Each section becomes one cached-query item. Returns empty list if no valid sections.
    """
    if not content or not content.strip():
        return []

    raw_sections = re.split(r"^\s*##\s+", content.strip(), flags=re.MULTILINE)
    result: List[Dict[str, str]] = []

    for block in raw_sections:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        if not lines:
            continue
        # Title: first line of block, or TITLE: line if present
        label = lines[0].strip()
        nl = ""
        sql_parts: List[str] = []
        in_sql = False
        for i in range(1, len(lines)):
            line = lines[i]
            if line.strip().upper().startswith("TITLE:"):
                label = line.split(":", 1)[1].strip() if ":" in line else label
                in_sql = False
            elif line.strip().upper().startswith("NL:"):
                nl = line.split(":", 1)[1].strip() if ":" in line else ""
                in_sql = False
            elif line.strip().upper().startswith("SQL:"):
                in_sql = True
                rest = line.split(":", 1)[1].strip() if ":" in line else ""
                if rest:
                    sql_parts.append(rest)
            elif in_sql:
                sql_parts.append(line)
        sql = "\n".join(sql_parts).strip()
        if label and (nl or sql):
            result.append({"label": label, "nl": nl, "sql": sql})
    return result


def group_parsed_by_label_prefix(parsed: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
    """
    Group parsed items by the numeric prefix in the label (e.g. "1. Original" and "1. Variant" -> same group).
    Preserves order; items without a "N." prefix are each their own group.
    Returns list of groups, each group a list of {label, nl, sql}.
    """
    if not parsed:
        return []

    def prefix(label: str) -> int | None:
        m = re.match(r"^(\d+)\.\s*", label.strip())
        return int(m.group(1)) if m else None

    groups: List[List[Dict[str, str]]] = []
    current_prefix: int | None = None
    current_group: List[Dict[str, str]] = []

    for p in parsed:
        pnum = prefix(p["label"])
        if pnum is not None and pnum == current_prefix:
            current_group.append(p)
        else:
            if current_group:
                groups.append(current_group)
            current_prefix = pnum
            current_group = [p]
    if current_group:
        groups.append(current_group)
    return groups
