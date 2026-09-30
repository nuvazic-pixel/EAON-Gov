import json
from pathlib import Path
from eaon_gov.state import StateManager
from eaon_gov.policy import PolicyEngine
from eaon_gov.verifier import ClaimVerifier, ExecutionVerifier
from eaon_gov.action_gateway import ActionGateway
from eaon_gov.agents.buergeramt import BuergeramtAgent
from eaon_gov.agents.finanzamt import FinanzamtAgent
from eaon_gov.agents.fahrzeug import FahrzeugAgent
from eaon_gov.agents.familienkasse import FamilienkasseAgent

class GovOrchestrator:
    def __init__(self, services_path="services/germany.json", audit_path="telemetry/audit.jsonl"):
        self.services_config = json.loads(Path(services_path).read_text(encoding="utf-8"))
        self.audit_path = audit_path
        self.policy = PolicyEngine(self.services_config)
        self.claim_verifier = ClaimVerifier()
        self.execution_verifier = ExecutionVerifier()
        self.gateway = ActionGateway()
        self.agents = [BuergeramtAgent(), FinanzamtAgent(), FahrzeugAgent(), FamilienkasseAgent()]

    def run_scenario(self, scenario_path: str):
        scenario = json.loads(Path(scenario_path).read_text(encoding="utf-8"))
        state = StateManager(scenario, self.audit_path)
        trace_id = state.derive_trace_id(scenario)
        context = scenario.get("context_data", {})

        unresolved = False
        for agent in self.agents:
            claim = agent.process(state.intent)
            policy = self.policy.evaluate(claim["rule_id"], context)
            decision = policy["decision"]
            unresolved |= decision == "NEEDS_INPUT"
            claim_status = self.claim_verifier.verify(claim, decision)
            receipt = self.gateway.execute_action(agent.name, claim["action"], decision, claim_status)
            execution_status = self.execution_verifier.verify(receipt)
            verification = "VERIFIED" if execution_status == "VERIFIED" else ("PENDING" if execution_status == "DEFERRED" else ("NOT_APPLICABLE" if execution_status == "NOT_APPLICABLE" else "FAILED"))
            state.set_service_state(agent.service, decision, verification, policy["missing"])
            state.add_claim_audit({**claim, "decision": decision, "missing": policy["missing"], "claim_verification": claim_status, "execution": receipt["execution"], "execution_status": receipt["status"], "execution_verification": execution_status})

        final = state.finalize("PARTIAL" if unresolved else "COMPLETED")
        state_hash = state.compute_state_hash()
        state.write_audit(trace_id)
        return {"trace_id": trace_id, "state_hash": state_hash, **final}
