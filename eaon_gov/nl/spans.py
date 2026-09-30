from dataclasses import dataclass
import re

@dataclass(frozen=True)
class TextSpan:
    text: str
    start: int
    end: int
    authoritative: bool
    kind: str

class SpanClassifier:
    """Deterministically separates direct, quoted, and narrow reported-speech spans."""

    QUOTE_PAIRS = {'"': '"', '«': '»', '„': '”', '“': '”'}
    REPORTED_PATTERNS = (
        re.compile(r"\bmy friend told me to\b", re.IGNORECASE),
        re.compile(r"\bprietenul meu a zis sa\b", re.IGNORECASE),
        re.compile(r"\bmein freund sagte,? ich soll\b", re.IGNORECASE),
    )

    def _reported_start(self, text: str, start: int) -> int | None:
        matches = [m.start() for pattern in self.REPORTED_PATTERNS if (m := pattern.search(text, start))]
        return min(matches) if matches else None

    def classify(self, text: str) -> tuple[TextSpan, ...]:
        spans = []
        buffer_start = 0
        i = 0
        while i < len(text):
            reported_at = self._reported_start(text, i)
            opener_at = next((j for j in range(i, len(text)) if text[j] in self.QUOTE_PAIRS), None)

            candidates = [x for x in (reported_at, opener_at) if x is not None]
            if not candidates:
                break
            boundary = min(candidates)

            if buffer_start < boundary:
                spans.append(TextSpan(text[buffer_start:boundary], buffer_start, boundary, True, "direct"))

            if reported_at is not None and boundary == reported_at:
                end = len(text)
                spans.append(TextSpan(text[reported_at:end], reported_at, end, False, "reported"))
                buffer_start = end
                i = end
                break

            opener = text[boundary]
            closer = self.QUOTE_PAIRS[opener]
            close_at = text.find(closer, boundary + 1)
            if close_at == -1:
                i = boundary + 1
                continue
            spans.append(TextSpan(text[boundary + 1:close_at], boundary + 1, close_at, False, "quoted"))
            i = close_at + 1
            buffer_start = i

        if buffer_start < len(text):
            spans.append(TextSpan(text[buffer_start:], buffer_start, len(text), True, "direct"))
        return tuple(span for span in spans if span.text)

    def authoritative_text(self, text: str) -> str:
        return " ".join(span.text for span in self.classify(text) if span.authoritative)
