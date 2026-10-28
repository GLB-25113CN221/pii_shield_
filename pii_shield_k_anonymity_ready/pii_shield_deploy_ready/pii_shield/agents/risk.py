"""Transparent heuristic risk scoring; not a legal determination."""
def risk_score(findings):
    weights={"AADHAAR":25,"BANK_ACCOUNT":22,"PAN":15,"CARD":20,"PASSPORT":15,"MOBILE":8,"EMAIL":5,"PERSON":5,"ADDRESS":8}
    score=min(100,sum(weights.get(f.pii_type,4) for f in findings))
    if not findings: explanation="No supported PII patterns were detected; this is not proof of zero risk."
    elif score>=70: explanation="High risk: multiple or high-impact identifiers were detected."
    elif score>=35: explanation="Moderate risk: review the detected categories and verification status."
    else: explanation="Lower estimated risk, but probabilistic detectors can miss PII."
    return score,explanation
