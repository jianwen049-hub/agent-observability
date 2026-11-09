from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


def new_id() -> str:
    return uuid.uuid4().hex[:16]


def now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    attrs: dict[str, Any] = field(default_factory=dict)
    start_ms: int = 0
    end_ms: int | None = None
    status: str = "ok"
    error: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0

    def duration_ms(self) -> int | None:
        if self.end_ms is None:
            return None
        return self.end_ms - self.start_ms

    def to_record(self) -> dict[str, Any]:
        d = asdict(self)
        d["duration_ms"] = self.duration_ms()
        return d
