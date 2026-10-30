import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any
from eaon_gov.validation import (
    CONTEXT_FIELDS, IntentValidationError, validate_context, validate_entities,
)


@dataclass(frozen=True)
class Provenance:
    source: str
    evidence: str
    parser: str
    inferred: bool = False

    def validate(self) -> "Provenance":
        if type(self.source) is not str or self.source != "user_input":
            raise IntentValidationError("Unsupported provenance source")
        if type(self.inferred) is not bool or self.inferred:
            raise IntentValidationError("Inferred facts cannot cross the deterministic security gate")
        if type(self.evidence) is not str or not self.evidence.strip():
            raise IntentValidationError("Direct user evidence is required")
        if type(self.parser) is not str or not self.parser.strip():
            raise IntentValidationError("A parser name is required")
        return self

    def to_dict(self) -> dict:
        return {"source": self.source, "evidence": self.evidence, "parser": self.parser, "inferred": self.inferred}

    @classmethod
    def from_dict(cls, payload: dict) -> "Provenance":
        if type(payload) is not dict or set(payload) != {"source", "evidence", "parser", "inferred"}:
            raise IntentValidationError("Invalid provenance fields")
        return cls(**payload).validate()


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
        if type(self.schema_version) is not str or self.schema_version != "0.2":
            raise IntentValidationError("Unsupported schema_version")
        if type(self.event) is not str or self.event != "relocation":
            raise IntentValidationError("Unsupported or unknown event")
        if type(self.jurisdiction) is not str or self.jurisdiction != "DE":
            raise IntentValidationError("Unsupported jurisdiction")
        if type(self.confidence) not in (int, float) or not math.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise IntentValidationError("confidence must be a finite number between 0 and 1")
        if type(self.parser_mode) is not str or not self.parser_mode.strip():
            raise IntentValidationError("A parser mode is required")
        validate_entities(self.entities)
        validate_context(self.context)
        if type(self.provenance) is not dict or set(self.provenance) != set(self.context):
            raise IntentValidationError("Exactly one provenance record per context field is required")
        for proof in self.provenance.values():
            if not isinstance(proof, Provenance):
                raise IntentValidationError("Invalid provenance record")
            proof.validate()
        if type(self.unknown_fields) is not tuple or any(
            type(key) is not str or key not in CONTEXT_FIELDS for key in self.unknown_fields
        ):
            raise IntentValidationError("Invalid unknown_fields")
        if len(set(self.unknown_fields)) != len(self.unknown_fields) or set(self.unknown_fields) & set(self.context):
            raise IntentValidationError("unknown_fields must be unique and absent from context")
        return self

    def canonical_payload(self) -> dict:
        self.validate()
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

    @classmethod
    def from_dict(cls, payload: dict) -> "IntentEnvelope":
        required = {"schema_version", "event", "jurisdiction", "entities", "context", "provenance", "unknown_fields", "parser"}
        if type(payload) is not dict or not required <= set(payload) or set(payload) - required - {"schema_fingerprint"}:
            raise IntentValidationError("Invalid intent envelope fields")
        parser = payload["parser"]
        if type(parser) is not dict or set(parser) != {"mode", "confidence"}:
            raise IntentValidationError("Invalid parser fields")
        if type(payload["provenance"]) is not dict or type(payload["unknown_fields"]) is not list:
            raise IntentValidationError("Invalid provenance or unknown_fields")
        envelope = cls(
            schema_version=payload["schema_version"], event=payload["event"],
            jurisdiction=payload["jurisdiction"], entities=payload["entities"], context=payload["context"],
            provenance={key: Provenance.from_dict(value) for key, value in payload["provenance"].items()},
            unknown_fields=tuple(payload["unknown_fields"]), parser_mode=parser["mode"], confidence=parser["confidence"],
        ).validate()
        if "schema_fingerprint" in payload and (
            type(payload["schema_fingerprint"]) is not str or payload["schema_fingerprint"] != envelope.fingerprint()
        ):
            raise IntentValidationError("Intent envelope fingerprint mismatch")
        return envelope
