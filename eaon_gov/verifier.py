class Verifier:
    def verify(self, decision: str, action_result: dict) -> str:
        execution = action_result.get("execution")
        if decision == "PASS":
            return "VERIFIED" if execution == "SIMULATED" else "FAILED"
        if decision == "NEEDS_INPUT":
            return "VERIFIED" if execution == "NONE" else "FAILED"
        return "VERIFIED" if execution == "SIMULATION_DENIED" else "FAILED"
