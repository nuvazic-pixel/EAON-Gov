class FinanzamtAgent:
    name = "finanzamt"
    service = "tax_address"

    def process(self, context: dict) -> dict:
        return {"agent": self.name, "service": self.service, "action": "evaluate_tax_address", "claim": "tax_address_transfer_requires_context", "source": "simulated://goettingen/finanzamt", "confidence": 1.0, "rule_id": "DE-UMZUG-002"}
