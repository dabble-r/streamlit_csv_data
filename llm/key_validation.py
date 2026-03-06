# llm/key_validation.py
from typing import Tuple

INVISIBLE_CHARS = [
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u00a0",  # non-breaking space
    "\u00ad",  # soft hyphen
]

# Lengths are per provider docs / common usage; kept permissive to avoid false rejections.
# OpenAI: sk- (51 chars typical), sk-proj- (longer); we accept a wide range.
PROVIDER_PATTERNS = {
    "OpenAI": {
        "prefixes": ("sk-", "sk-proj-"),  # standard and project keys
        "min_len": 40,
        "max_len": 256,
    },
    "Anthropic": {
        "prefixes": ("sk-ant-",),
        "min_len": 60,
        "max_len": 120,
    },
    "Mistral": {
        "prefixes": ("mistral-",),
        "min_len": 30,
        "max_len": 80,
    },
    "Gemini": {
        "prefixes": ("AIza",),
        "min_len": 30,
        "max_len": 60,
    },
}


def _key_matches_prefix(key: str, pattern: dict) -> bool:
    prefixes = pattern.get("prefixes", (pattern.get("prefix"),))
    return any(key.startswith(p) for p in prefixes)


def contains_invisible_chars(key: str) -> bool:
    return any(char in key for char in INVISIBLE_CHARS)


def validate_key(provider: str, key: str) -> Tuple[bool, str]:
    """
    Returns (is_valid, message).
    Validates format/prefix and length only; does not call the API.
    For OpenAI, length is advisory only (accept key if prefix matches).
    """
    raw_key = key
    stripped_key = key.strip()

    if raw_key != stripped_key:
        return False, "Your key contains leading or trailing whitespace."

    if contains_invisible_chars(key):
        return False, "Your key contains invisible characters. Try retyping it."

    pattern = PROVIDER_PATTERNS.get(provider)
    if pattern:
        if not _key_matches_prefix(key, pattern):
            prefixes = pattern["prefixes"]
            hint = ", ".join(f"'{p}'" for p in prefixes)
            return False, f"{provider} keys typically start with {hint}."

        min_len = pattern["min_len"]
        max_len = pattern["max_len"]
        if not (min_len <= len(key) <= max_len):
            # OpenAI: accept anyway and warn (key formats/lengths vary).
            if provider == "OpenAI":
                return True, (
                    f"Key length is outside the usual range ({min_len}–{max_len} chars). "
                    "Saved; try the Query tab."
                )
            return False, (
                f"Key length is outside the usual range for {provider} "
                f"({min_len}–{max_len} characters)."
            )

    return True, "Key format looks valid."