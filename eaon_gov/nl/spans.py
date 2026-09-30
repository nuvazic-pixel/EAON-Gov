from dataclasses import dataclass

@dataclass(frozen=True)
class TextSpan:
    text: str
    start: int
    end: int
    authoritative: bool
    kind: str

class SpanClassifier:
    """Deterministically separates direct user text from explicitly quoted text."""

    QUOTE_PAIRS = {'"': '"', '«': '»', '„': '”'}

    def classify(self, text: str) -> tuple[TextSpan, ...]:
        spans = []
        buffer_start = 0
        i = 0
        while i < len(text):
            opener = text[i]
            closer = self.QUOTE_PAIRS.get(opener)
            if closer is None:
                i += 1
                continue
            close_at = text.find(closer, i + 1)
            if close_at == -1:
                i += 1
                continue
            if buffer_start < i:
                spans.append(TextSpan(text[buffer_start:i], buffer_start, i, True, "direct"))
            spans.append(TextSpan(text[i + 1:close_at], i + 1, close_at, False, "quoted"))
            i = close_at + 1
            buffer_start = i
        if buffer_start < len(text):
            spans.append(TextSpan(text[buffer_start:], buffer_start, len(text), True, "direct"))
        return tuple(span for span in spans if span.text)

    def authoritative_text(self, text: str) -> str:
        return " ".join(span.text for span in self.classify(text) if span.authoritative)
