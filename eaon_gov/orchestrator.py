import hashlib
import json
from pathlib import Path

from eaon_gov.action_gateway import ActionGateway
from eaon_gov.agents.buergeramt import BuergeramtAgent
from eaon_gov.agents.fahrzeug import FahrzeugAgent
from eaon_gov.agents.familienkasse import FamilienkasseAgent
from eaon_gov.agents.finanzamt import FinanzamtAgent
from eaon_gov.policy import PolicyEngine
from eaon_gov.state import StateManager
from eaon_gov.verifier import Verifier

class GovOrchestrator:
    def __init__(self, services_path: str = "services/germany.json", audit_path: str = "telemetry/audit.jsonl"):
        self.services_config = json.loads(Path(services_path).read_text(encoding="utf-8"))
        self.policy_engine = PolicyEngine(self.services_config)
        self.action_gateway = ActionGateway()
        self.verifier = Verifier()
        self.audit_path = audit_path
        self.agents = [BuergeramtAgent(), FinanzamtAgent(), FahrzeugAgent(), FamilienkasseAgent()]

    @staticmethod
    def _trace_id(scenario: dict) -> str:
        canonical = json.dumps(scenario, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return "gov-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

    def run_scenario(self, scenario_path: str):
        scenario = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
        intent = scenario.get("parsed_intent", {})
        event = intent.get("event")
        jurisdiction = intent.get("jurisdiction")
        state = StateManager(self._trace_id(scenario), self.audit_path)
        state.update_intent(event, jurisdiction)

        for agent in self.agents:
            claim = agent.process(intent)
            policy = self.policy_engine.evaluate(claim["rule_id"], intent)
            result = self.action_gateway.execute_action(agent.name, claim["action"], policy["decision"])
            verification = self.verifier.verify(policy["decision"], result)
            record = {
                **claim,
                "decision": policy["decision"],
                "missing": policy["missing"],
                "execution": result["execution"],
                "status": result["status"],
                "verification": verification
            }
            state.set_service(agent.service, {
                "decision": policy["decision"],
                "missing": policy["missing"],
                "execution": result["execution"],
                "verification": verification
            })
            state.add_claim(record)

        decisions = [x["decision"] for x in state.state["services"].values()]
        status = "COMPLETED" if all(x == "PASS" for x in decisions) else "PARTIAL"
        return state.finalize(status)
