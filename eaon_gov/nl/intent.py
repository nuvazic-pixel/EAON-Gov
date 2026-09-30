from dataclasses import dataclass, field
from typing import Any

class IntentValidationError(ValueError):
    pass

@dataclass(frozen=True)
class IntentEnvelope:
    schema_version: str
    event: str
    jurisdiction: str
    entities: dict[str, str]
    context: dict[str, Any]
    unknown_fields: tuple[str, ...] = field(default_factory=tuple)
    parser_mode: str = "deterministic"
    confidence: float = 1.0

    def validate(self) -> "IntentEnvelope":
        if self.schema_version != "0.2":
            raise IntentValidationError("Unsupported schema_version")
        if self.event not in {"relocation"}:
            raise IntentValidationError("Unsupported or unknown event")
        if self.jurisdiction != "DE":
            raise IntentValidationError("Unsupported jurisdiction")
        if not 0.0 <= self.confidence <= 1.0:
            raise IntentValidationError("confidence must be between 0 and 1")
        if not self.entities.get("origin") or not self.entities.get("destination"):
            raise IntentValidationError("origin and destination are required")
        return self

    def to_scenario(self, scenario_id: str, input_text: str) -> dict:
        self.validate()
        return {
            "scenario_id": scenario_id,
            "input_text": input_text,
            "parsed_intent": {
                "event": self.event,
                "jurisdiction": self.jurisdiction,
                **self.entities,
            },
            "context_data": dict(self.context),
            "intent_envelope": self.to_dict(),
        }

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "event": self.event,
            "jurisdiction": self.jurisdiction,
            "entities": dict(self.entities),
            "context": dict(self.context),
            "unknown_fields": list(self.unknown_fields),
            "parser": {"mode": self.parser_mode, "confidence": self.confidence},
        }
