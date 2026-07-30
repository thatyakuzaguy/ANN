"""Shared secret redaction for persisted skill evidence."""

from __future__ import annotations

import re


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)([\"']?(?:api[_-]?key|secret|token|password|credential|private[_-]?key)"
    r"[\"']?\s*[:=]\s*)[\"']?[^\s,}\]\"']{8,}[\"']?"
)
_KNOWN_TOKEN = re.compile(
    r"(?i)\b(?:gh[opsu]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})\b"
)


def redact_sensitive_text(text: str) -> tuple[str, bool]:
    """Replace secret-like assignments and known token formats in text."""

    redacted = False

    def replace_assignment(match: re.Match[str]) -> str:
        nonlocal redacted
        redacted = True
        return f'{match.group(1)}"[REDACTED_SECRET]"'

    safe = _SECRET_ASSIGNMENT.sub(replace_assignment, text)
    if _KNOWN_TOKEN.search(safe):
        redacted = True
        safe = _KNOWN_TOKEN.sub("[REDACTED_SECRET]", safe)
    return safe, redacted
