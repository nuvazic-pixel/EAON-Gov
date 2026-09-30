class FamilienkasseAgent:
    name = "familienkasse"
    service = "family_services"

    def process(self, context: dict) -> dict:
        return {"agent": self.name, "service": self.service, "action": "evaluate_family_benefits", "claim": "family_services_address_check", "source": "simulated://arbeitsagentur/familienkasse", "rule_id": "DE-UMZUG-004"}
