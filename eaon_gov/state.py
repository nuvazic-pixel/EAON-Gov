import hashlib
import json
from pathlib import Path

class StateManager:
    def __init__(self, scenario_data: dict, audit_path: str = "telemetry/audit.jsonl"):
        self.scenario_data = scenario_data
        self.scenario_id = scenario_data.get("scenario_id", "unknown")
        self.intent = scenario_data.get("parsed_intent", {})
        self.event = self.intent.get("event")
        self.jurisdiction = self.intent.get("jurisdiction")
        self.audit_path = Path(audit_path)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self.services = {}
        self.claims = []
        self.execution_status = "INITIALIZED"

    @staticmethod
    def derive_trace_id(scenario_data: dict) -> str:
        canonical = json.dumps(scenario_data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return "gov-trace-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    def set_service_state(self, service, decision, verification="PENDING", missing=None):
        self.services[service] = {"decision": decision, "verification": verification}
        if missing:
            self.services[service]["missing"] = missing

    def add_claim_audit(self, record):
        self.claims.append(record)

    def get_canonical_state(self):
        return {
            "event": self.event,
            "jurisdiction": self.jurisdiction,
            "services": self.services,
            "claims": sorted(self.claims, key=lambda x: x.get("rule_id", "")),
            "execution_status": self.execution_status,
        }

    def compute_state_hash(self):
        canonical = json.dumps(self.get_canonical_state(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def finalize(self, status):
        self.execution_status = status
        return self.get_canonical_state()

    def write_audit(self, trace_id):
        record = {"trace_id": trace_id, "scenario_id": self.scenario_id, "state_hash": self.compute_state_hash(), **self.get_canonical_state()}
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
