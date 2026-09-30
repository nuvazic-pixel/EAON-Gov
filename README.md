# EAON-Gov

Deterministic Civic Orchestration and Policy Engine for EAON.

> AI proposes → Policy authorizes → Executor acts → Verifier proves → Audit remembers.

## v0.1 goal

A reproducible, simulation-only civic orchestration baseline for a German relocation life event.

- deterministic service discovery
- explicit `PASS / NEEDS_INPUT / REJECT / ERROR`
- no unauthorized execution
- verification before state commit
- JSONL audit trail
- deterministic SHA-256 state hash
- no LLM required

## Run

```bash
python -m pip install -e ".[dev]"
python run_demo.py
pytest -q
```

No real government service or API is contacted in v0.1.
