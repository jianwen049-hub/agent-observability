from __future__ import annotations

import re
from typing import Any

_PHONE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+")
_SK = re.compile(r"sk-[A-Za-z0-9]{10,}")
_SENSITIVE_KEYS = re.compile(r"(?i)pass(word)?|secret|token|api[_-]?key|authorization")


def redact_text(text: str) -> str:
    text = _PHONE.sub("[REDACTED_PHONE]", text)
    text = _EMAIL.sub("[REDACTED_EMAIL]", text)
    text = _BEARER.sub(r"\1[REDACTED_TOKEN]", text)
    text = _SK.sub("sk-[REDACTED]", text)
    return text


def redact_obj(obj: Any, *, key: str | None = None) -> Any:
    if key and _SENSITIVE_KEYS.search(key):
        return "[REDACTED]"
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {k: redact_obj(v, key=str(k)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_obj(v) for v in obj]
    return obj
