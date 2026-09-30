import hashlib
import json
from pathlib import Path

class StateManager:
    def __init__(self, trace_id: str, audit_path: str = "telemetry/audit.jsonl"):
        self.trace_id = trace_id
        self.audit_path = Path(audit_path)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self.state = {
            "trace_id": trace_id,
            "event": None,
            "jurisdiction": None,
            "services": {},
            "claims": [],
            "execution_status": "INITIALIZED"
        }

    def update_intent(self, event: str, jurisdiction: str):
        self.state["event"] = event
        self.state["jurisdiction"] = jurisdiction

    def set_service(self, service: str, data: dict):
        self.state["services"][service] = data

    def add_claim(self, claim: dict):
        self.state["claims"].append(claim)
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"trace_id": self.trace_id, **claim}, ensure_ascii=False, sort_keys=True) + "\n")

    def finalize(self, status: str):
        self.state["execution_status"] = status
        canonical = json.dumps(self.state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.state["state_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return self.state
