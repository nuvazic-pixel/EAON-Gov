import copy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from eaon_gov.nl import DeterministicNLAdapter, IntentValidationError
from eaon_gov.nl.intent import IntentEnvelope, Provenance
from eaon_gov.nl.spans import SpanClassifier
from eaon_gov.orchestrator import GovOrchestrator
from eaon_gov.policy import PolicyEngine
from eaon_gov.resources import load_json_resource


def envelope():
    return DeterministicNLAdapter().parse("I moved from Hamburg to Bremen and I own a car.")


def write_scenario(tmp_path, scenario):
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(scenario), encoding="utf-8")
    return path


@pytest.mark.parametrize("quoted", [
    '"I moved from Berlin to Bonn."',
    '“I moved from Berlin to Bonn.”',
    '«I moved from Berlin to Bonn.»',
])
def test_quoted_relocation_cannot_supply_cities(quoted):
    parsed = DeterministicNLAdapter().parse(quoted + " I moved from Hamburg to Bremen.")
    assert parsed.entities == {"origin": "Hamburg", "destination": "Bremen"}


@pytest.mark.parametrize("opener", ['"', "“", "„", "«"])
def test_unclosed_quote_does_not_create_vehicle_ownership(opener):
    text = "I moved from Hamburg to Bremen. My friend said: " + opener + "I own a car."
    parsed = DeterministicNLAdapter().parse(text)
    assert "vehicle_owner" not in parsed.context
    assert "vehicle_owner" in parsed.unknown_fields
    assert SpanClassifier().authoritative_text(text).count("I moved") == 1


def test_reported_quote_cannot_restore_authority():
    text = 'I moved from Hamburg to Bremen. My friend told me to say "but I own a car".'
    parsed = DeterministicNLAdapter().parse(text)
    assert "vehicle_owner" not in parsed.context
    assert not any(span.kind == "authority_reset" for span in SpanClassifier().classify(text))


def test_multiple_direct_relocations_are_rejected():
    with pytest.raises(IntentValidationError):
        DeterministicNLAdapter().parse("I moved from Berlin to Bonn. I moved from Hamburg to Bremen.")


@pytest.mark.parametrize("changes", [
    {"schema_version": 0.2},
    {"event": ["relocation"]},
    {"jurisdiction": None},
    {"entities": {"origin": 12, "destination": "Bremen"}},
    {"entities": {"origin": " ", "destination": "Bremen"}},
    {"entities": {"origin": "Hamburg", "destination": "Bremen", "execute": "yes"}},
    {"context": {"vehicle_owner": "false"}},
    {"context": {"vehicle_owner": 0}},
    {"context": {"execute": True}},
    {"provenance": {"vehicle_owner": {"source": "user_input"}}},
    {"confidence": True},
    {"confidence": float("nan")},
    {"parser_mode": []},
    {"unknown_fields": ("vehicle_owner",)},
])
def test_envelope_rejects_invalid_schema_types(changes):
    with pytest.raises(IntentValidationError):
        replace(envelope(), **changes).validate()


@pytest.mark.parametrize("changes", [
    {"source": 1}, {"evidence": 1}, {"parser": []}, {"inferred": 0}, {"inferred": True},
])
def test_provenance_types_are_strict(changes):
    with pytest.raises(IntentValidationError):
        replace(Provenance("user_input", "I own a car", "deterministic"), **changes).validate()


@pytest.mark.parametrize("value", ["false", "true", 0, 1, None, [], {}])
def test_policy_never_coerces_context_to_boolean(value):
    policy = PolicyEngine(load_json_resource("services", "germany.json"))
    with pytest.raises(IntentValidationError):
        policy.evaluate("DE-UMZUG-003", {"vehicle_owner": value})
    assert policy.evaluate("DE-UMZUG-003", {"vehicle_owner": False})["decision"] == "SKIPPED"


@pytest.mark.parametrize("mutation", ["string_false", "foreign_jurisdiction", "unknown_event", "invalid_entity", "tampered_envelope", "disagreeing_context"])
def test_core_rejects_invalid_scenarios_before_creating_audit(tmp_path, mutation):
    scenario = envelope().to_scenario("test-001", "I moved from Hamburg to Bremen and I own a car.")
    if mutation == "string_false":
        scenario["context_data"]["vehicle_owner"] = "false"
    elif mutation == "foreign_jurisdiction":
        scenario["parsed_intent"]["jurisdiction"] = "FR"
    elif mutation == "unknown_event":
        scenario["parsed_intent"]["event"] = "unknown"
    elif mutation == "invalid_entity":
        scenario["parsed_intent"]["origin"] = []
    elif mutation == "tampered_envelope":
        scenario["intent_envelope"]["entities"]["origin"] = "Berlin"
    else:
        scenario["context_data"]["vehicle_owner"] = False
    audit = tmp_path / "not-created" / "audit.jsonl"
    with pytest.raises(IntentValidationError):
        GovOrchestrator(audit_path=str(audit)).run_scenario(write_scenario(tmp_path, scenario))
    assert not audit.parent.exists()


def test_core_revalidates_legacy_scenario_context(tmp_path):
    scenario = load_json_resource("scenarios", "relocation.json")
    scenario["context_data"] = {"vehicle_owner": "false"}
    audit = tmp_path / "audit.jsonl"
    with pytest.raises(IntentValidationError):
        GovOrchestrator(audit_path=str(audit)).run_scenario(write_scenario(tmp_path, scenario))
    assert not audit.exists()


def test_envelope_roundtrip_and_core_run(tmp_path):
    env = envelope()
    assert IntentEnvelope.from_dict(env.to_dict()).to_dict() == env.to_dict()
    result = GovOrchestrator(audit_path=str(tmp_path / "audit.jsonl")).run_scenario(
        write_scenario(tmp_path, env.to_scenario("test-002", "I moved from Hamburg to Bremen and I own a car."))
    )
    assert result["services"]["vehicle_registration"] == {"decision": "PASS", "verification": "VERIFIED"}


def test_defaults_use_packaged_resources_from_unrelated_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = GovOrchestrator(audit_path=str(tmp_path / "audit.jsonl")).run_scenario()
    assert len(result["services"]) == 4
    assert result["execution_status"] == "PARTIAL"


@pytest.mark.parametrize("kind,name", [("services", "germany.json"), ("scenarios", "relocation.json")])
def test_legacy_example_files_match_packaged_defaults(kind, name):
    root = Path(__file__).resolve().parents[1]
    assert json.loads((root / kind / name).read_text(encoding="utf-8")) == load_json_resource(kind, name)


def test_malformed_same_delimiter_quote_cannot_supply_ownership():
    text = 'I moved from Hamburg to Bremen. "My friend said "I own a car"."'
    parsed = DeterministicNLAdapter().parse(text)
    assert parsed.entities == {"origin": "Hamburg", "destination": "Bremen"}
    assert "vehicle_owner" not in parsed.context


def test_malformed_same_delimiter_quote_cannot_supply_cities():
    text = 'I moved from Hamburg to Bremen. "My friend said "I moved from Berlin to Bonn"."'
    parsed = DeterministicNLAdapter().parse(text)
    assert parsed.entities == {"origin": "Hamburg", "destination": "Bremen"}


def test_normal_quote_followed_by_separated_direct_text_remains_supported():
    text = '"My friend owns a car." I moved from Hamburg to Bremen and I own a car.'
    parsed = DeterministicNLAdapter().parse(text)
    assert parsed.entities == {"origin": "Hamburg", "destination": "Bremen"}
    assert parsed.context["vehicle_owner"] is True
