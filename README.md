# EAON-Gov

Deterministic Civic Orchestration and Policy Engine for EAON.

> Natural language is untrusted input. Structured intent is validated input. Policy remains sovereign.

AI proposes → Policy authorizes → Claim verifies → Executor acts → Execution verifies → State commits → Audit remembers.

## Status

The package version remains **0.1.0**. The **v0.2 candidate** adds a deterministic RO/DE/EN relocation parser and an `IntentEnvelope` with schema version `0.2`; this is not a released v0.2 package.

This is an independent, simulation-only prototype. Four fixed civic agents evaluate a German relocation scenario; no government API is contacted and no real action is performed. EAON integration and an LLM adapter remain future work.

## Input and validation

`DeterministicNLAdapter` extracts supported facts only from authoritative text. Quoted and narrowly recognized reported speech cannot supply those facts; an unclosed quote protects the remaining text. A closing quote immediately followed by a letter or digit is treated conservatively as ambiguous and also protects the remaining text. Multiple direct relocation statements are rejected as ambiguous. The grammar is intentionally limited, not a general solution to natural-language trust.

The core revalidates every scenario before creating audit state. It accepts only the supported event/jurisdiction, non-empty origin/destination strings, and actual JSON booleans for `taxable`, `vehicle_owner`, and `beneficiary`. Strings such as `"false"` are rejected, including direct policy calls. A supplied v0.2 envelope is revalidated and must agree with the scenario and its fingerprint.

Legacy v0.1 structured scenarios remain supported; their caller supplies trusted structured facts. Provenance and fingerprints establish consistency, not identity or authenticity. They are not authorization credentials.

## Run

```bash
python -m pip install -e ".[dev]"
python -m eaon_gov
pytest -q
```

`python run_demo.py` remains available in a source checkout. Installed defaults resolve through package resources, so `GovOrchestrator().run_scenario()` works from any current directory. Explicit `services_path` and `scenario_path` overrides remain supported.

Canonical bundled simulation data live in `eaon_gov/data/`. The top-level `services/` and `scenarios/` files remain compatibility examples, with a regression test preventing drift. Audit JSONL is written to the caller-selected path (default: `telemetry/audit.jsonl` in the current directory).

Tests cover deterministic state/trace hashes, NL positive/negative cases, protected spans, strict schema and policy types, core validation before side effects, and resource loading outside the source directory.

CI also builds a wheel, installs it without dependencies in a separate environment, and runs `scripts/smoke_installed.py` from outside the checkout on Python 3.10, 3.11, and 3.12. The smoke check verifies the installed import, bundled defaults, all four services, and matching temporary audit state.
