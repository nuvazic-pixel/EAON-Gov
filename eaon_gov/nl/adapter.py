import re
import unicodedata
from eaon_gov.nl.intent import IntentEnvelope, IntentValidationError, Provenance

class DeterministicNLAdapter:
    """Small, auditable RO/DE/EN parser for the v0.2 relocation experiment."""

    MOVE_MARKERS = ("m-am mutat", "m am mutat", "umgezogen", "moved")
    VEHICLE_TRUE = ("am o masina", "am masina", "am un autoturism", "habe ein auto", "habe ein fahrzeug", "have a car", "own a car")
    VEHICLE_FALSE = ("nu am masina", "habe kein auto", "don't have a car", "do not have a car")

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
        context = {}
        if any(marker in folded for marker in self.VEHICLE_FALSE):
            context["vehicle_owner"] = False
        elif any(marker in folded for marker in self.VEHICLE_TRUE):
            context["vehicle_owner"] = True

        unknown = tuple(k for k in ("taxable", "vehicle_owner", "beneficiary") if k not in context)
        return IntentEnvelope(
            schema_version="0.2", event="relocation", jurisdiction="DE",
            entities={"origin": origin.title(), "destination": destination.title()},
            context=context, provenance=provenance, unknown_fields=unknown,
            parser_mode="deterministic", confidence=1.0,
        ).validate()
