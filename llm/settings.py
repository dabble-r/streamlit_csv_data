# llm/settings.py
from dataclasses import dataclass


@dataclass
class LLMConfig:
    provider: str
    api_key: str