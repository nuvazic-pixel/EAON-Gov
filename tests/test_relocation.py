from pathlib import Path
from eaon_gov.orchestrator import GovOrchestrator

def run(tmp_path: Path):
    return GovOrchestrator(audit_path=str(tmp_path / "audit.jsonl")).run_scenario("scenarios/relocation.json")

def test_relocation_safe_and_deterministic(tmp_path):
    first = run(tmp_path)
    second = run(tmp_path)

    assert len(first["services"]) == 4
    assert first["services"]["residence_registration"]["decision"] == "PASS"
    assert first["services"]["tax_address"]["decision"] == "NEEDS_INPUT"
    assert first["services"]["vehicle_registration"]["decision"] == "NEEDS_INPUT"
    assert first["services"]["family_services"]["decision"] == "NEEDS_INPUT"
    assert all(s["verification"] == "VERIFIED" for s in first["services"].values())
    assert all(s["execution"] != "SIMULATED" for k, s in first["services"].items() if k != "residence_registration")
    assert first["state_hash"] == second["state_hash"]
