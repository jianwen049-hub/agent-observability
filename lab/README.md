# obs_lab — in-process JSONL tracer

```bash
cd lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python3 scripts/smoke_check.py
python3 -m obs_lab.cli demo
python3 -m obs_lab.cli summary --trace out/demo.jsonl
```
