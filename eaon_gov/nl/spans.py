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
    """Separates direct text from quotes and a narrow reported-speech grammar."""

    QUOTE_PAIRS = {'"': '"', '«': '»', '„': '”', '“': '”'}
    REPORTED_PATTERNS = (
        re.compile(r"\bmy friend told me to\b", re.IGNORECASE),
        re.compile(r"\bprietenul meu a zis s[ăa]\b", re.IGNORECASE),
        re.compile(r"\bmein freund sagte,? ich soll\b", re.IGNORECASE),
    )
    AUTHORITY_RESETS = (
        re.compile(r"\bbut\b", re.IGNORECASE),
        re.compile(r"\bdar\b", re.IGNORECASE),
        re.compile(r"\binsa\b|\bînsă\b", re.IGNORECASE),
        re.compile(r"\baber\b", re.IGNORECASE),
    )

    def _reported_start(self, text: str, start: int) -> int | None:
        matches = [m.start() for pattern in self.REPORTED_PATTERNS if (m := pattern.search(text, start))]
        return min(matches) if matches else None

    def _quote_end(self, text: str, start: int) -> int | None:
        closers = [self.QUOTE_PAIRS[text[start]]]
        for index in range(start + 1, len(text)):
            char = text[index]
            if char == closers[-1]:
                # Adjacent word text makes a same-delimiter nested/malformed
                # quote ambiguous. Keep the remaining material protected.
                if len(closers) == 1 and index + 1 < len(text) and text[index + 1].isalnum():
                    return None
                closers.pop()
                if not closers:
                    return index
            elif char in self.QUOTE_PAIRS:
                closers.append(self.QUOTE_PAIRS[char])
        return None

    def _reported_reset(self, text: str, start: int):
        index = start
        while index < len(text):
            if text[index] in self.QUOTE_PAIRS:
                end = self._quote_end(text, index)
                if end is None:
                    return None
                index = end + 1
                continue
            match = next((m for pattern in self.AUTHORITY_RESETS if (m := pattern.match(text, index))), None)
            if match:
                return match
            index += 1
        return None

    def classify(self, text: str) -> tuple[TextSpan, ...]:
        spans = []
        buffer_start = 0
        index = 0
        while index < len(text):
            reported_at = self._reported_start(text, index)
            opener_at = next((j for j in range(index, len(text)) if text[j] in self.QUOTE_PAIRS), None)
            candidates = [position for position in (reported_at, opener_at) if position is not None]
            if not candidates:
                break
            boundary = min(candidates)
            if buffer_start < boundary:
                spans.append(TextSpan(text[buffer_start:boundary], buffer_start, boundary, True, "direct"))
            if reported_at is not None and boundary == reported_at:
                reset = self._reported_reset(text, reported_at)
                end = reset.start() if reset else len(text)
                spans.append(TextSpan(text[reported_at:end], reported_at, end, False, "reported"))
                if reset:
                    spans.append(TextSpan(text[reset.start():reset.end()], reset.start(), reset.end(), False, "authority_reset"))
                    buffer_start = index = reset.end()
                    continue
                buffer_start = index = end
                break

            close_at = self._quote_end(text, boundary)
            if close_at is None:
                spans.append(TextSpan(text[boundary + 1:], boundary + 1, len(text), False, "unclosed_quote"))
                buffer_start = index = len(text)
                break
            spans.append(TextSpan(text[boundary + 1:close_at], boundary + 1, close_at, False, "quoted"))
            buffer_start = index = close_at + 1
        if buffer_start < len(text):
            spans.append(TextSpan(text[buffer_start:], buffer_start, len(text), True, "direct"))
        return tuple(span for span in spans if span.text)

    def authoritative_text(self, text: str) -> str:
        return " ".join(span.text for span in self.classify(text) if span.authoritative)
