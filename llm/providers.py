# llm/providers.py
from typing import List


def get_supported_providers() -> List[str]:
    return ["OpenAI", "Anthropic", "Mistral", "Gemini"]