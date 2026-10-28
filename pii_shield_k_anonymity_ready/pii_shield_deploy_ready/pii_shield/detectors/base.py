"""Common detector contract. Findings retain spans so original-script text can be redacted."""
from dataclasses import dataclass, asdict
@dataclass
class Finding:
    pii_type: str
    start: int
    end: int
    confidence: float
    value: str
    layer: str = "regex"
    status: str = "high"
    def public(self):
        """Safe representation: never expose the matched value."""
        return {"type": self.pii_type, "start": self.start, "end": self.end,
                "confidence": self.confidence, "layer": self.layer, "status": self.status}
