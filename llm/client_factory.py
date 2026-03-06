# llm/client_factory.py
from typing import Any
from .settings import LLMConfig


class DummyLLMClient:
    """
    Placeholder client that simulates LLM calls.
    Replace with real provider SDKs.
    """

    def __init__(self, config: LLMConfig):
        self.config = config

    def generate(self, prompt: str) -> str:
        return f"-- SQL generated for provider={self.config.provider}: {prompt}"


def get_llm_client(config: LLMConfig) -> Any:
    """
    Factory returning an LLM client based on provider.
    For now, returns a dummy client.
    """
    return DummyLLMClient(config)