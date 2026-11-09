"""Demo-only token prices (USD per 1K tokens)."""
from __future__ import annotations

PRICE_PER_1K = {
    "gpt-demo-small": {"in": 0.0001, "out": 0.0002},
    "gpt-demo-large": {"in": 0.0010, "out": 0.0020},
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    p = PRICE_PER_1K.get(model, PRICE_PER_1K["gpt-demo-small"])
    return (tokens_in / 1000.0) * p["in"] + (tokens_out / 1000.0) * p["out"]
