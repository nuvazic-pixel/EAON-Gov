class ActionGateway:
    def execute_action(self, agent_name: str, action: str, decision: str) -> dict:
        if decision == "NEEDS_INPUT":
            return {"status": "NOT_EXECUTED", "execution": "NONE"}
        if decision != "PASS":
            return {"status": "BLOCKED", "execution": "SIMULATION_DENIED"}
        return {"status": "SUCCESS", "execution": "SIMULATED"}
