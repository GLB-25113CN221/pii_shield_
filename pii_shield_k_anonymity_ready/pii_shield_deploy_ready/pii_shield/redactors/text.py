"""Span-based text redaction."""
from detectors.base import Finding

def _merge(findings):
    """Merge overlapping spans so two detectors hitting the same text (e.g. EMAIL + UPI_ID)
    never corrupt the output. The label of the first (leftmost, longest) finding is kept."""
    merged = []
    for f in sorted(findings, key=lambda x: (x.start, -(x.end - x.start))):
        if merged and f.start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], f.end)
        else:
            merged.append([f.start, f.end, f.pii_type])
    return merged

def redact_text(text: str, findings: list[Finding]) -> str:
    """Replace spans from right to left so offsets remain stable."""
    for start, end, kind in reversed(_merge(findings)):
        text = text[:start] + f"[{kind}_REDACTED]" + text[end:]
    return text
