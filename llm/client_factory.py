# llm/client_factory.py
from typing import Any
from .settings import LLMConfig
from .litellm_client import completion_with_config


class LiteLLMClient:
    """LLM client backed by LiteLLM; uses provider + api_key from config."""

    def __init__(self, config: LLMConfig):
        self.config = config

    def generate(self, prompt: str) -> str:
        return completion_with_config(self.config, prompt)


def get_llm_client(config: LLMConfig) -> Any:
    """Factory returning an LLM client. Uses LiteLLM for completion."""
    return LiteLLMClient(config)