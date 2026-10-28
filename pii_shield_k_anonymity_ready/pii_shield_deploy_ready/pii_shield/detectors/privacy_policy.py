"""Policy recommendations and uncertainty prioritization for PII findings.

Actions are recommendations for review/UI. They do not silently rewrite source
text; actual redaction remains in the existing, auditable redaction pipeline.
"""
from __future__ import annotations

DIRECT_IDENTIFIER_TYPES = {
    "AADHAAR", "PAN", "GSTIN", "MOBILE", "EMAIL", "IFSC", "BANK_ACCOUNT",
    "CARD", "PASSPORT", "VOTER_ID", "DL", "VEHICLE_PLATE", "UPI_ID",
}
QUASI_TYPES = {"PERSON", "ADDRESS", "LOCATION", "DATE_OF_BIRTH", "DATE", "AGE", "ORGANIZATION"}


def recommend_actions(findings, privacy_risk: dict, profile: str = "balanced") -> list[dict]:
    """Return one action recommendation per finding without exposing matched values."""
    profile = profile if profile in {"strict", "balanced", "utility_preserving"} else "balanced"
    high_risk = privacy_risk.get("level") == "high" or privacy_risk.get("combination_warning", False)
    recommendations = []
    for finding in findings:
        kind = str(getattr(finding, "pii_type", "UNKNOWN"))
        confidence = float(getattr(finding, "confidence", 0.0))
        status = str(getattr(finding, "status", "pending"))
        if kind in DIRECT_IDENTIFIER_TYPES:
            action = "redact"
            reason = "Direct identifier category; default policy is to redact."
        elif profile == "strict":
            action = "redact"
            reason = "Strict profile masks detected personal or quasi-identifying entities."
        elif profile == "balanced" and high_risk:
            action = "redact_or_generalize"
            reason = "Contextual combination risk is elevated; redact or generalize after review."
        elif profile == "utility_preserving":
            action = "generalize_or_review"
            reason = "Preserve utility only if generalization does not leave a re-identification path."
        elif confidence < 0.75 or status in {"pending", "review"}:
            action = "human_review"
            reason = "Detection evidence is uncertain or has not been adjudicated."
        else:
            action = "redact_or_review"
            reason = "Detected personal entity; choose the least revealing safe transformation."
        recommendations.append({
            "type": kind,
            "start": int(getattr(finding, "start", -1)),
            "end": int(getattr(finding, "end", -1)),
            "confidence": round(confidence, 3),
            "detector": str(getattr(finding, "layer", "unknown")),
            "action": action,
            "reason": reason,
            "profile": profile,
        })
    return recommendations


def prioritize_review(findings, privacy_risk: dict, limit: int = 25) -> list[dict]:
    """Active-learning-inspired review order: uncertainty and privacy impact first.

    This prioritizes review examples; it does not train a model or claim a formal
    active-learning algorithm. Returned records contain no matched values.
    """
    risk_level = privacy_risk.get("level", "low")
    risk_bonus = {"low": 0.0, "medium": 0.08, "high": 0.16}.get(risk_level, 0.0)
    ranked = []
    for finding in findings:
        confidence = max(0.0, min(1.0, float(getattr(finding, "confidence", 0.0))))
        status = str(getattr(finding, "status", "pending"))
        uncertain = 1.0 - confidence
        pending_bonus = 0.2 if status in {"pending", "review"} else 0.0
        type_bonus = 0.12 if getattr(finding, "pii_type", "UNKNOWN") in DIRECT_IDENTIFIER_TYPES else 0.0
        priority = min(1.0, uncertain + pending_bonus + type_bonus + risk_bonus)
        if status in {"pending", "review"} or confidence < 0.8:
            ranked.append({
                "type": str(getattr(finding, "pii_type", "UNKNOWN")),
                "start": int(getattr(finding, "start", -1)),
                "end": int(getattr(finding, "end", -1)),
                "confidence": round(confidence, 3),
                "status": status,
                "priority": round(priority, 3),
                "selection_reason": "uncertainty + identifier impact + document context risk",
            })
    return sorted(ranked, key=lambda item: (-item["priority"], item["start"]))[:max(0, int(limit))]
