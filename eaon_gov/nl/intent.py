import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

class IntentValidationError(ValueError):
    pass

@dataclass(frozen=True)
class Provenance:
    source: str
    evidence: str
    parser: str
    inferred: bool = False

    def validate(self) -> "Provenance":
        if self.source != "user_input":
            raise IntentValidationError("Unsupported provenance source")
        if self.inferred:
            raise IntentValidationError("Inferred facts cannot cross the deterministic security gate")
        if not self.evidence.strip():
            raise IntentValidationError("Direct user evidence is required")
        return self

    def to_dict(self) -> dict:
        return {"source": self.source, "evidence": self.evidence, "parser": self.parser, "inferred": self.inferred}

@dataclass(frozen=True)
class IntentEnvelope:
    schema_version: str
    event: str
    jurisdiction: str
    entities: dict[str, str]
    context: dict[str, Any]
    provenance: dict[str, Provenance] = field(default_factory=dict)
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
        for key in self.context:
            if key not in self.provenance:
                raise IntentValidationError(f"Missing provenance for context field: {key}")
            self.provenance[key].validate()
        return self

    def canonical_payload(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "event": self.event,
            "jurisdiction": self.jurisdiction,
            "entities": dict(sorted(self.entities.items())),
            "context": dict(sorted(self.context.items())),
            "provenance": {k: self.provenance[k].to_dict() for k in sorted(self.provenance)},
            "unknown_fields": sorted(self.unknown_fields),
            "parser": {"mode": self.parser_mode, "confidence": self.confidence},
        }

    def fingerprint(self) -> str:
        canonical = json.dumps(self.canonical_payload(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_scenario(self, scenario_id: str, input_text: str) -> dict:
        self.validate()
        return {
            "scenario_id": scenario_id,
            "input_text": input_text,
            "parsed_intent": {"event": self.event, "jurisdiction": self.jurisdiction, **self.entities},
            "context_data": dict(self.context),
            "intent_envelope": self.to_dict(),
        }

    def to_dict(self) -> dict:
        payload = self.canonical_payload()
        payload["schema_fingerprint"] = self.fingerprint()
        return payload
