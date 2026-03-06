# llm/settings.py
"""
LLM provider and API key configuration.
SECURITY: Do not log, print, or persist LLMConfig or any object containing api_key.
Use config.safe_repr() for debug output; __repr__ redacts the key by default.
"""
from dataclasses import dataclass


@dataclass
class LLMConfig:
    provider: str
    api_key: str

    def safe_repr(self) -> str:
        """Return a string safe for logs or debug; api_key is redacted."""
        return f"LLMConfig(provider={self.provider!r}, api_key='***')"

    def __repr__(self) -> str:
        """Redact api_key so accidental logging or print() does not expose it."""
        return self.safe_repr()