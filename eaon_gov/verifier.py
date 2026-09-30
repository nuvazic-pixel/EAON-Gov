class ClaimVerifier:
    def verify(self, claim_packet: dict, decision: str) -> str:
        if decision == "PASS":
            source = claim_packet.get("source", "")
            confidence = claim_packet.get("confidence", 0.0)
            return "CLAIM_VERIFIED" if confidence >= 1.0 and source.startswith("simulated://") else "CLAIM_FAILED"
        if decision == "NEEDS_INPUT":
            return "PENDING_INPUT"
        if decision == "SKIPPED":
            return "NOT_APPLICABLE"
        return "CLAIM_FAILED"

class ExecutionVerifier:
    def verify(self, receipt: dict) -> str:
        status, execution = receipt.get("status"), receipt.get("execution")
        if status == "SUCCESS" and execution == "SIMULATED":
            return "VERIFIED"
        if status == "BLOCKED" and execution == "NOT_EXECUTED":
            return "DEFERRED"
        if status == "SKIPPED" and execution == "NOT_EXECUTED":
            return "NOT_APPLICABLE"
        return "FAILED"
