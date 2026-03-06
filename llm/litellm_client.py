# llm/litellm_client.py
"""
LiteLLM integration: API key validation and completion.
Maps app provider names to LiteLLM model names and delegates completion.
"""
from typing import Tuple

from .settings import LLMConfig

# Map app provider names to LiteLLM model identifiers (used for validation and completion).
# Use small/fast models for validation and default generation.
LITELLM_MODEL = {
    "OpenAI": "gpt-4o-mini",
    "Anthropic": "claude-3-5-haiku-20241022",
    "Mistral": "mistral/mistral-small-latest",
    "Gemini": "gemini/gemini-1.5-flash",
}


def validate_key_with_litellm(provider: str, api_key: str) -> Tuple[bool, str]:
    """
    Validate an API key by calling LiteLLM's check_valid_key (or a minimal completion).
    Returns (is_valid, message).
    """
    try:
        from litellm import check_valid_key
    except ImportError:
        try:
            import litellm  # noqa: F401
        except ImportError:
            return False, "LiteLLM is not installed. Run: pip install litellm"
        return _validate_via_completion(provider, api_key)

    model = LITELLM_MODEL.get(provider)
    if not model:
        return False, f"Unknown provider: {provider}"

    try:
        valid = check_valid_key(model=model, api_key=api_key)
        if valid:
            return True, "Key validated with provider."
        return False, "Invalid key or insufficient permissions."
    except Exception as e:
        return False, f"Validation failed: {getattr(e, 'message', str(e))}"


def _validate_via_completion(provider: str, api_key: str) -> Tuple[bool, str]:
    """Fallback: validate by running a minimal completion when check_valid_key is unavailable."""
    import litellm

    model = LITELLM_MODEL.get(provider)
    if not model:
        return False, f"Unknown provider: {provider}"
    try:
        litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "Say OK"}],
            api_key=api_key,
        )
        return True, "Key validated with provider."
    except Exception as e:
        msg = getattr(e, "message", str(e))
        if "auth" in msg.lower() or "invalid" in msg.lower() or "401" in msg or "403" in msg:
            return False, "Invalid key or insufficient permissions."
        return False, f"Validation failed: {msg}"


def completion_with_config(config: LLMConfig, prompt: str) -> str:
    """
    Run a single completion using LiteLLM with the given config.
    Returns the assistant message content.
    """
    import litellm

    model = LITELLM_MODEL.get(config.provider)
    if not model:
        raise ValueError(f"Unknown provider: {config.provider}")

    messages = [{"role": "user", "content": prompt}]
    response = litellm.completion(
        model=model,
        messages=messages,
        api_key=config.api_key,
    )
    choice = response.choices[0]
    return (choice.message.content or "").strip()
