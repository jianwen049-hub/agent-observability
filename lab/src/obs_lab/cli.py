from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from obs_lab.pricing import estimate_cost
from obs_lab.summary import aggregate, load_spans
from obs_lab.tracer import Tracer


def cmd_demo(out: Path) -> int:
    if out.exists():
        out.unlink()
    t = Tracer(out)
    with t.span("request.handle", route="demo"):
        with t.span("retrieve", top_k=3):
            time.sleep(0.01)
        with t.span("llm.chat", model="gpt-demo-small") as sp:
            time.sleep(0.02)
            tin, tout = 120, 40
            cost = estimate_cost("gpt-demo-small", tin, tout)
            t.record_usage(tin, tout, cost)
            sp.attrs["phone_should_redact"] = "13812345678"
        with t.span("tool.calculator", expression="1+1"):
            time.sleep(0.005)
        with t.span("llm.chat", model="gpt-demo-large") as sp:
            time.sleep(0.02)
            tin, tout = 400, 80
            cost = estimate_cost("gpt-demo-large", tin, tout)
            t.record_usage(tin, tout, cost)
    print(f"wrote {out}")
    return 0


def cmd_summary(path: Path) -> int:
    spans = load_spans(path)
    report = aggregate(spans)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="obs_lab")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo")
    d.add_argument("--out", type=Path, default=Path("out/demo.jsonl"))
    s = sub.add_parser("summary")
    s.add_argument("--trace", type=Path, required=True)
    args = p.parse_args(argv)
    if args.cmd == "demo":
        return cmd_demo(args.out)
    if args.cmd == "summary":
        return cmd_summary(args.trace)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
