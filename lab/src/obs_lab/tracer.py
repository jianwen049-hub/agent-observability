from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Iterator

from obs_lab.redact import redact_obj
from obs_lab.spans import Span, new_id, now_ms

_current: ContextVar[Span | None] = ContextVar("obs_current_span", default=None)


class Tracer:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._trace_id = new_id()

    @property
    def trace_id(self) -> str:
        return self._trace_id

    def _write(self, span: Span) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(span.to_record(), ensure_ascii=False) + "\n")

    @contextmanager
    def span(self, name: str, **attrs: Any) -> Iterator[Span]:
        parent = _current.get()
        sp = Span(
            trace_id=self._trace_id,
            span_id=new_id(),
            parent_span_id=parent.span_id if parent else None,
            name=name,
            attrs=redact_obj(attrs),
            start_ms=now_ms(),
        )
        token = _current.set(sp)
        try:
            yield sp
        except Exception as e:
            sp.status = "error"
            sp.error = redact_obj(str(e))[:200]
            raise
        finally:
            sp.end_ms = now_ms()
            sp.attrs = redact_obj(sp.attrs)
            self._write(sp)
            _current.reset(token)

    def record_usage(self, tokens_in: int = 0, tokens_out: int = 0, cost_usd: float = 0.0) -> None:
        sp = _current.get()
        if sp is None:
            return
        sp.tokens_in += tokens_in
        sp.tokens_out += tokens_out
        sp.cost_usd += cost_usd


def current_span() -> Span | None:
    return _current.get()
