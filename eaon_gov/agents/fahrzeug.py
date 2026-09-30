class FahrzeugAgent:
    name = "fahrzeug"
    service = "vehicle_registration"

    def process(self, context: dict) -> dict:
        return {"agent": self.name, "service": self.service, "action": "check_vehicle_re_registration", "claim": "vehicle_registration_update_conditional", "source": "simulated://kfz-zulassung/goettingen", "rule_id": "DE-UMZUG-003"}
