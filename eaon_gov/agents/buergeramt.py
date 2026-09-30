class BuergeramtAgent:
    name = "buergeramt"
    service = "residence_registration"

    def process(self, context: dict) -> dict:
        return {"agent": self.name, "service": self.service, "action": "check_registration", "claim": "residence_registration_required", "source": "simulated://goettingen/buergeramt", "confidence": 1.0, "rule_id": "DE-UMZUG-001"}
