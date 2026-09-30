import re
import unicodedata
from eaon_gov.nl.intent import IntentEnvelope, IntentValidationError, Provenance

class DeterministicNLAdapter:
    """Small, auditable RO/DE/EN parser for the v0.2 relocation experiment."""

    MOVE_MARKERS = ("m-am mutat", "m am mutat", "umgezogen", "moved")
    VEHICLE_TRUE = ("am o masina", "am masina", "am un autoturism", "habe ein auto", "habe ein fahrzeug", "have a car", "own a car")
    VEHICLE_FALSE = ("nu am masina", "habe kein auto", "don't have a car", "do not have a car")
    INJECTION_MARKERS = ("ignore previous", "ignora regulile", "ignora instructiunile", "ignoriere vorherige", "set vehicle_owner", "seteaza vehicle_owner")

    @staticmethod
    def _fold(text: str) -> str:
        text = unicodedata.normalize("NFKD", text.casefold())
        return "".join(c for c in text if not unicodedata.combining(c))

    @staticmethod
    def _clean_place(value: str) -> str:
        return value.strip(" .,!?:;")

    def parse(self, text: str) -> IntentEnvelope:
        if not isinstance(text, str) or not text.strip():
            raise IntentValidationError("Input text is empty")

        folded = self._fold(text)
        if not any(marker in folded for marker in self.MOVE_MARKERS):
            raise IntentValidationError("No supported life event detected")

        patterns = (
            r"(?:m-am mutat|m am mutat) din\s+(.+?)\s+in\s+(.+?)(?=\s+si\s+|[.!?]|$)",
            r"(?:ich bin )?von\s+(.+?)\s+nach\s+(.+?)(?=\s+umgezogen(?:\s+und|[.!?]|$)|\s+und\s+|[.!?]|$)",
            r"(?:i )?moved from\s+(.+?)\s+to\s+(.+?)(?=\s+and\s+|[.!?]|$)",
        )
        match = next((m for p in patterns if (m := re.search(p, folded, flags=re.IGNORECASE))), None)
        if not match:
            raise IntentValidationError("Relocation detected but origin/destination are ambiguous")

        origin, destination = map(self._clean_place, match.groups())
        true_hits = [marker for marker in self.VEHICLE_TRUE if marker in folded]
        false_hits = [marker for marker in self.VEHICLE_FALSE if marker in folded]
        if true_hits and false_hits:
            raise IntentValidationError("Contradictory vehicle ownership evidence")
        if any(marker in folded for marker in self.INJECTION_MARKERS):
            raise IntentValidationError("Instruction-like state manipulation is not trusted evidence")

        context = {}
        provenance = {}
        if false_hits:
            context["vehicle_owner"] = False
            provenance["vehicle_owner"] = Provenance("user_input", false_hits[0], "deterministic", False)
        elif true_hits:
            context["vehicle_owner"] = True
            provenance["vehicle_owner"] = Provenance("user_input", true_hits[0], "deterministic", False)

        unknown = tuple(k for k in ("taxable", "vehicle_owner", "beneficiary") if k not in context)
        return IntentEnvelope(
            schema_version="0.2", event="relocation", jurisdiction="DE",
            entities={"origin": origin.title(), "destination": destination.title()},
            context=context, provenance=provenance, unknown_fields=unknown,
            parser_mode="deterministic", confidence=1.0,
        ).validate()
