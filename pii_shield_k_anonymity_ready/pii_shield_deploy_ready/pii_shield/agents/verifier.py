"""Verifier agent: re-run detection on output text, ignoring our own [XXX_REDACTED] tokens."""
import re
from detectors.identifiers import detect_identifiers
from ner.multilingual import detect_ner

TOKEN = re.compile(r"\[[A-Z_]+_REDACTED\]")

def residual_findings(text: str):
    """Detect PII in text after masking existing redaction tokens (same length, so offsets stay valid)."""
    masked = TOKEN.sub(lambda m: "#" * len(m.group()), text)
    found = detect_identifiers(masked) + detect_ner(masked)
    # a label followed only by '#' (an already-redacted value) is not a leak
    return [f for f in found if set(masked[f.start:f.end]) - {"#", " "}]

def verify_text(text: str):
    findings = residual_findings(text)
    return {"verified": len(findings) == 0,
            "residual_types": sorted({f.pii_type for f in findings}),
            "residual_count": len(findings)}
