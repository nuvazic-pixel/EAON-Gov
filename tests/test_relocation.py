from pathlib import Path
from eaon_gov.orchestrator import GovOrchestrator

def run(tmp_path: Path):
    return GovOrchestrator(audit_path=str(tmp_path / "audit.jsonl")).run_scenario("scenarios/relocation.json")

def test_relocation_safe_and_deterministic(tmp_path):
    first = run(tmp_path)
    second = run(tmp_path)
    services = first["services"]
    assert len(services) == 4
    assert services["residence_registration"] == {"decision": "PASS", "verification": "VERIFIED"}
    assert services["tax_address"]["decision"] == "NEEDS_INPUT"
    assert services["vehicle_registration"]["decision"] == "NEEDS_INPUT"
    assert services["family_services"]["decision"] == "NEEDS_INPUT"
    assert services["vehicle_registration"]["missing"] == ["vehicle_owner"]
    assert all(s["verification"] == "PENDING" for k, s in services.items() if k != "residence_registration")
    assert first["execution_status"] == "PARTIAL"
    assert first["state_hash"] == second["state_hash"]
    assert first["trace_id"] == second["trace_id"]
