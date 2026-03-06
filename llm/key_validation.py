# llm/key_validation.py
from typing import Tuple

INVISIBLE_CHARS = [
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u00a0",  # non-breaking space
    "\u00ad",  # soft hyphen
]

PROVIDER_PATTERNS = {
    "OpenAI": {
        "prefix": "sk-",
        "min_len": 40,
        "max_len": 100,
    },
    "Anthropic": {
        "prefix": "sk-ant-",
        "min_len": 60,
        "max_len": 120,
    },
    "Mistral": {
        "prefix": "mistral-",
        "min_len": 30,
        "max_len": 80,
    },
    "Gemini": {
        "prefix": "AIza",
        "min_len": 30,
        "max_len": 60,
    },
}


def contains_invisible_chars(key: str) -> bool:
    return any(char in key for char in INVISIBLE_CHARS)


def validate_key(provider: str, key: str) -> Tuple[bool, str]:
    """
    Returns (is_valid, message).
    """
    raw_key = key
    stripped_key = key.strip()

    if raw_key != stripped_key:
        return False, "Your key contains leading or trailing whitespace."

    if contains_invisible_chars(key):
        return False, "Your key contains invisible characters. Try retyping it."

    pattern = PROVIDER_PATTERNS.get(provider)
    if pattern:
        if not key.startswith(pattern["prefix"]):
            return False, f"{provider} keys typically start with '{pattern['prefix']}'."

        if not (pattern["min_len"] <= len(key) <= pattern["max_len"]):
            return False, f"This key length looks unusual for {provider}. Double-check for missing characters."

    return True, "Key format looks valid."