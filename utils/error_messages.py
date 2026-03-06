# utils/error_messages.py
"""
Sanitize exception messages for display in the UI.
Strips file paths, line numbers, and raw code references so users see clear, safe messages.
"""
import re


def sanitize_error_message(message: str) -> str:
    """
    Remove file paths, line numbers, and traceback noise from an error message.
    Returns a short, user-safe string suitable for st.error() or captions.
    """
    if not message or not isinstance(message, str):
        return "An error occurred."
    text = message.strip()

    # Remove "File \"...\", line N" or 'File "...", line N' (Python traceback)
    text = re.sub(r'File\s+["\'][^"\']+["\']\s*,\s*line\s+\d+.*', '', text, flags=re.IGNORECASE)
    # Remove standalone path-like segments (Unix/Windows)
    text = re.sub(r'[/\\][a-zA-Z0-9_\-./\\]+\.py[\w.]*', '', text)
    text = re.sub(r'[A-Za-z]:\\[^\s]+', '', text)
    text = re.sub(r'/home/[^\s]+', '', text)
    text = re.sub(r'/tmp/[^\s]+', '', text)
    # Collapse multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip().strip(':,;')
    if not text:
        return "An error occurred."
    # Limit length so one-line display stays readable
    if len(text) > 400:
        text = text[:397] + "..."
    return text


def user_message_for_exception(exc: BaseException) -> str:
    """
    Build a user-facing message from an exception. Uses sanitized str(exc)
    and does not include file paths or tracebacks.
    """
    msg = getattr(exc, "message", None) or str(exc)
    return sanitize_error_message(msg)
