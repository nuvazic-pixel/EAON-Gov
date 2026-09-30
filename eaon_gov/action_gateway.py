class ActionGateway:
    def execute_action(self, agent_name: str, action: str, decision: str, claim_verification: str) -> dict:
        if decision == "PASS" and claim_verification == "CLAIM_VERIFIED":
            return {"status": "SUCCESS", "execution": "SIMULATED", "agent": agent_name, "action": action}
        if decision == "NEEDS_INPUT":
            return {"status": "BLOCKED", "execution": "NOT_EXECUTED", "agent": agent_name, "action": action}
        if decision == "SKIPPED":
            return {"status": "SKIPPED", "execution": "NOT_EXECUTED", "agent": agent_name, "action": action}
        return {"status": "DENIED", "execution": "BLOCKED", "agent": agent_name, "action": action}
