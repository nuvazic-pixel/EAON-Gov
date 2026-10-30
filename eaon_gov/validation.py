"""Validation shared by the deterministic core and the optional NL edge."""

CONTEXT_FIELDS = frozenset({"taxable", "vehicle_owner", "beneficiary"})


class IntentValidationError(ValueError):
    pass


def validate_context(context: dict) -> None:
    if type(context) is not dict:
        raise IntentValidationError("context must be an object")
    for key, value in context.items():
        if type(key) is not str or key not in CONTEXT_FIELDS:
            raise IntentValidationError("Unsupported context field")
        if type(value) is not bool:
            raise IntentValidationError(f"{key} must be a boolean")


def validate_entities(entities: dict) -> None:
    if type(entities) is not dict or set(entities) != {"origin", "destination"}:
        raise IntentValidationError("Exactly origin and destination are required")
    if any(type(value) is not str or not value.strip() for value in entities.values()):
        raise IntentValidationError("origin and destination must be non-empty strings")


def validate_scenario(scenario: dict) -> None:
    """Accept typed v0.1 scenarios and revalidate v0.2 envelopes before any effects."""
    if type(scenario) is not dict:
        raise IntentValidationError("scenario must be an object")
    if "scenario_id" in scenario and (
        type(scenario["scenario_id"]) is not str or not scenario["scenario_id"].strip()
    ):
        raise IntentValidationError("scenario_id must be a non-empty string")
    intent = scenario.get("parsed_intent")
    if type(intent) is not dict or set(intent) != {"event", "jurisdiction", "origin", "destination"}:
        raise IntentValidationError("Invalid parsed_intent fields")
    if type(intent["event"]) is not str or intent["event"] != "relocation":
        raise IntentValidationError("Unsupported event")
    if type(intent["jurisdiction"]) is not str or intent["jurisdiction"] != "DE":
        raise IntentValidationError("Unsupported jurisdiction")
    validate_entities({key: intent[key] for key in ("origin", "destination")})
    context = scenario.get("context_data", {})
    validate_context(context)
    if "input_text" in scenario and type(scenario["input_text"]) is not str:
        raise IntentValidationError("input_text must be a string")
    if "intent_envelope" in scenario:
        from eaon_gov.nl.intent import IntentEnvelope

        envelope = IntentEnvelope.from_dict(scenario["intent_envelope"])
        expected = {"event": envelope.event, "jurisdiction": envelope.jurisdiction, **envelope.entities}
        if expected != intent or envelope.context != context:
            raise IntentValidationError("Scenario and intent envelope disagree")
