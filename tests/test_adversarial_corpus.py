import json
from pathlib import Path
import pytest
from eaon_gov.nl import DeterministicNLAdapter, IntentValidationError

CASES = json.loads(Path("tests/corpus/nl_adversarial_v02.json").read_text(encoding="utf-8"))

@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_adversarial_corpus(case):
    parser = DeterministicNLAdapter()
    if case["expect"] == "reject":
        with pytest.raises(IntentValidationError):
            parser.parse(case["text"])
        return

    env = parser.parse(case["text"])
    if case["expect"] == "unknown":
        assert "vehicle_owner" in env.unknown_fields
        assert "vehicle_owner" not in env.context
        assert "vehicle_owner" not in env.provenance
        return

    assert env.context["vehicle_owner"] is case["vehicle_owner"]
    proof = env.provenance["vehicle_owner"]
    assert proof.source == "user_input"
    assert proof.inferred is False
    assert proof.evidence
