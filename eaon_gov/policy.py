class PolicyEngine:
    def __init__(self, rules_config: dict):
        self.rules = rules_config.get("rules", {})

    def evaluate(self, rule_id: str, context: dict) -> dict:
        rule = self.rules.get(rule_id)
        if not rule:
            return {"decision": "REJECT", "missing": []}
        if rule.get("condition") == "always_required":
            return {"decision": "PASS", "missing": []}

        required = rule.get("requires", [])
        missing = [key for key in required if key not in context]
        if missing:
            return {"decision": "NEEDS_INPUT", "missing": missing}
        return {"decision": "PASS" if all(bool(context[k]) for k in required) else "SKIPPED", "missing": []}
