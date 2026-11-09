#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from obs_lab.redact import redact_obj, redact_text
from obs_lab.cli import cmd_demo, cmd_summary
from obs_lab.summary import load_spans, aggregate


def main() -> int:
    assert "[REDACTED_PHONE]" in redact_text("call 13812345678 now")
    assert "sk-[REDACTED]" in redact_text("key=sk-abcdefghijklmnop")
    obj = redact_obj({"api_key": "secret", "model": "gpt-demo-small", "email": "a@b.com"})
    assert obj["api_key"] == "[REDACTED]"
    assert obj["model"] == "gpt-demo-small"
    assert obj["email"] == "[REDACTED_EMAIL]"

    out = ROOT / "out" / "smoke.jsonl"
    assert cmd_demo(out) == 0
    spans = load_spans(out)
    blob = "\n".join(json.dumps(s, ensure_ascii=False) for s in spans)
    assert "13812345678" not in blob
    report = aggregate(spans)
    assert report["n_spans"] >= 4
    assert report["total_cost_usd"] > 0
    assert cmd_summary(out) == 0
    print("smoke_check OK", report["n_spans"], report["total_cost_usd"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
