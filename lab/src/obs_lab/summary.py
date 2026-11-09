from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_spans(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def aggregate(spans: list[dict[str, Any]]) -> dict[str, Any]:
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for s in spans:
        by_name[s["name"]].append(s)

    def stats(items: list[dict[str, Any]]) -> dict[str, Any]:
        durs = [i.get("duration_ms") or 0 for i in items]
        costs = [float(i.get("cost_usd") or 0) for i in items]
        tin = sum(int(i.get("tokens_in") or 0) for i in items)
        tout = sum(int(i.get("tokens_out") or 0) for i in items)
        durs_sorted = sorted(durs)
        p50 = durs_sorted[len(durs_sorted) // 2] if durs_sorted else 0
        return {
            "n": len(items),
            "p50_ms": p50,
            "max_ms": max(durs) if durs else 0,
            "tokens_in": tin,
            "tokens_out": tout,
            "cost_usd": round(sum(costs), 6),
        }

    per_name = {k: stats(v) for k, v in sorted(by_name.items())}
    total_cost = round(sum(s.get("cost_usd") or 0 for s in spans), 6)
    total_ms = sum(s.get("duration_ms") or 0 for s in spans)
    return {"per_name": per_name, "total_cost_usd": total_cost, "sum_span_ms": total_ms, "n_spans": len(spans)}
