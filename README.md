# EAON-Gov

Deterministic Civic Orchestration and Policy Engine for EAON.

> **Natural language is untrusted input. Structured intent is validated input. Policy remains sovereign.**

> AI proposes → Policy authorizes → Claim verifies → Executor acts → Execution verifies → State commits → Audit remembers.

## v0.1 baseline

A reproducible, simulation-only civic orchestration baseline for a German relocation life event.

- deterministic service discovery
- explicit `PASS / NEEDS_INPUT / REJECT / SKIPPED`
- no unauthorized execution
- claim and execution verification
- JSONL audit trail
- deterministic SHA-256 trace/state hashes
- no LLM required

## v0.2 candidate — Natural Language Edge

The first v0.2 layer is deliberately deterministic and auditable. `DeterministicNLAdapter` accepts a small RO/DE/EN relocation grammar and emits one validated `IntentEnvelope`. Ambiguous or unsupported input is rejected rather than guessed.

```text
Citizen text → DeterministicNLAdapter → IntentEnvelope → validation gate → deterministic v0.1 core
                                      ↘ future LLMAdapter must obey the same contract
```

The LLM adapter will be interchangeable parsing infrastructure. It will not receive policy or execution authority.

## Run

```bash
python -m pip install -e ".[dev]"
python run_demo.py
pytest -q
```

No real government service or API is contacted in v0.1/v0.2 simulation work.
