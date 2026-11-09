# agent-observability — Traces, Redaction, Cost×Latency

> Open technical lab on **in-process tracing for LLM / Agent calls**: spans, PII redaction, and linking token cost with latency. Chinese deep-dives cite real lab paths.

**Author:** 马健文 / Evans Owen ([jianwen049-hub](https://github.com/jianwen049-hub))

| | |
|---|---|
| **Lab** | [`lab/`](./lab/) — JSONL tracer + summary CLI + smoke check |
| **Blog** | [`docs/blog/`](./docs/blog/) |
| **Bio** | [`PROFILE.md`](./PROFILE.md) |

## Reading guide (EN)

1. Read posts 01 → 02 → 03 under `docs/blog/`.
2. Run offline:

```bash
cd lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python3 scripts/smoke_check.py
python3 -m obs_lab.cli demo
python3 -m obs_lab.cli summary --trace lab/out/demo.jsonl
```

## 中文简介

Agent 一复杂，出问题就像黑盒。本仓用**进程内 JSONL tracer**把 span、脱敏、成本与延迟打到同一条时间线，配套中文深拆。

## License

MIT — see [`LICENSE`](./LICENSE).
