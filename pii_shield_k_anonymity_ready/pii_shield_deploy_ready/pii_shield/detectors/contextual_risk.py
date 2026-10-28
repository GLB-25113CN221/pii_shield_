"""Interpretable privacy-risk signals for combinations of quasi-identifiers.

Research-inspired components: quasi-identifier aggregation, lightweight relation
extraction, and span/category-only reporting. This is a heuristic, not a trained
re-identification attack or a calibrated probability of identifying a person.
"""
from __future__ import annotations
import re
from collections import Counter

# These patterns are intentionally broad indicators, not standalone PII recognizers.
# Language/script coverage is opportunistic; it must be evaluated per language.
QUASI_PATTERNS = {
    "age": re.compile(
        r"(?i)\b(?:aged?\s*\d{1,3}|\d{1,3}\s*(?:years? old|yrs? old)|"
        r"\d{1,3}[- ]year[- ]old|age\s*[:=]?\s*\d{1,3})\b|"
        r"उम्र\s*[:=]?\s*\d{1,3}|आयु\s*[:=]?\s*\d{1,3}|"
        r"বয়স\s*[:=]?\s*\d{1,3}|વય\s*[:=]?\s*\d{1,3}|"
        r"ವಯಸ್ಸು\s*[:=]?\s*\d{1,3}|പ്രായം\s*[:=]?\s*\d{1,3}|"
        r"वय\s*[:=]?\s*\d{1,3}|ବୟସ\s*[:=]?\s*\d{1,3}|"
        r"ਉਮਰ\s*[:=]?\s*\d{1,3}|வயது\s*[:=]?\s*\d{1,3}|వయస్సు\s*[:=]?\s*\d{1,3}"
    ),
    "occupation": re.compile(
        r"(?i)\b(?:teacher|doctor|nurse|principal|collector|police officer|"
        r"village head|professor|engineer|lawyer|journalist|surgeon|councillor)\b|"
        r"शिक्षक|डॉक्टर|अध्यापक|प्राध्यापक|चिकित्सक|শিক্ষক|ডাক্তার|શિક્ષક|ડૉક્ટર|"
        r"ಶಿಕ್ಷಕ|ವೈದ್ಯ|അധ്യാപകൻ|ഡോക്ടർ|शिक्षक|डॉक्टर|ଶିକ୍ଷକ|ଡାକ୍ତର|"
        r"ਅਧਿਆਪਕ|ਡਾਕਟਰ|ஆசிரியர்|மருத்துவர்|ఉపాధ్యాయుడు|వైద్యుడు"
    ),
    "specific_location": re.compile(
        r"(?i)\b(?:village|ward|sector\s*\d+|street|lane|colony|block\s*[A-Z0-9]+|"
        r"panchayat|tehsil|taluka|hamlet|small town)\b|"
        r"गांव|गाँव|मोहल्ला|सेक्टर\s*\d+|गली|वार्ड|পাড়া|গ্রাম|વોર્ડ|ગામ|"
        r"ವಾಡ್|ಗ್ರಾಮ|വാർഡ്|ഗ്രാമം|वॉर्ड|गाव|ପଞ୍ଚାୟତ|ଗ୍ରାମ|"
        r"ਪਿੰਡ|ਵਾਰਡ|கிராமம்|தெரு|வார்டு|గ్రామం|వీధి"
    ),
    "date_or_event": re.compile(
        r"(?i)\b(?:on\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|born on|received an award|"
        r"elected on|appointed on|joined on|retired on)\b|"
        r"जन्म|पुरस्कार मिला|नियुक्ति|জন্ম|পুরস্কার|નિયુક્તિ|જન્મ|"
        r"ಜನನ|ಪ್ರಶಸ್ತಿ|ജനനം|പുരസ്കാരം|जन्म|पुरस्कार|ଜନ୍ମ|ପୁରସ୍କାର|"
        r"ਜਨਮ|ਪੁਰਸਕਾਰ|பிறந்த|விருது|జననం|పురస్కారం"
    ),
    "relationship": re.compile(
        r"(?i)\b(?:father of|mother of|son of|daughter of|spouse of|wife of|husband of|"
        r"reports to|works for|works at|lives with|relative of|married to|sibling of)\b|"
        r"पुत्र|पुत्री|पत्नी|पति|पिता|माता|भाई|बहन|বাবা|মা|પિતા|માતા|"
        r"ತಂದೆ|ತಾಯಿ|അച്ഛൻ|അമ്മ|वडील|आई|ପିତା|ମାତା|ਪਿਤਾ|ਮਾਤਾ|"
        r"தந்தை|தாய்|కుమారుడు|కుమార్తె"
    ),
}

RELATION_PATTERNS = {
    "family_relation": re.compile(
        r"(?i)\b(?:father of|mother of|son of|daughter of|spouse of|wife of|husband of|"
        r"married to|sibling of|brother of|sister of)\b|पिता|माता|पुत्र|पुत्री|पत्नी|पति|"
        r"தந்தை|தாய்|కుమారుడు|కుమార్తె"
    ),
    "employment": re.compile(
        r"(?i)\b(?:works at|works for|employed by|reports to|manager of|employee of|"
        r"studies at|student at)\b|काम करता है|कार्यरत|नौकरी|வேலை செய்கிறார்|"
        r"పని చేస్తాడు|কাজ করেন"
    ),
    "residence": re.compile(
        r"(?i)\b(?:lives at|lives in|resides in|resident of|stays at|belongs to)\b|"
        r"निवासी|रहता है|निवास|वसति|வசிக்கிறார்|నివసిస్తున్నారు|বাস করেন"
    ),
    "association": re.compile(r"(?i)\b(?:member of|associated with|president of|director of)\b|सदस्य|अध्यक्ष"),
}


def extract_relationship_signals(text: str, findings=()) -> list[dict]:
    """Return privacy-safe relationship signals between adjacent detected entities.

    Entity values are deliberately excluded from returned records and logs. This
    is rule-based relation extraction, not a trained relation-extraction model.
    """
    spans = sorted(
        [f for f in findings if getattr(f, "end", 0) > getattr(f, "start", 0)],
        key=lambda f: f.start,
    )
    links = []
    seen = set()
    for left, right in zip(spans, spans[1:]):
        if right.start < left.end or right.start - left.end > 160:
            continue
        between = text[left.end:right.start]
        # Search a bounded window too, because NER spans may include a title or
        # a relation phrase can precede the first entity in natural language.
        window = text[max(0, left.start - 80):min(len(text), right.end + 80)]
        for label, pattern in RELATION_PATTERNS.items():
            if pattern.search(between) or pattern.search(window):
                record = (label, getattr(left, "pii_type", "UNKNOWN"), getattr(right, "pii_type", "UNKNOWN"))
                if record not in seen:
                    seen.add(record)
                    links.append({"relation": record[0], "source_type": record[1], "target_type": record[2]})
                break
    return links


def assess_privacy_risk(text: str, findings=()) -> dict:
    """Score direct PII + quasi-identifier co-occurrence with transparent evidence."""
    text = text or ""
    direct = Counter(getattr(f, "pii_type", "UNKNOWN") for f in findings)
    indicators = {name: len(pattern.findall(text)) for name, pattern in QUASI_PATTERNS.items()}
    active = sum(value > 0 for value in indicators.values())
    relations = extract_relationship_signals(text, findings)
    direct_count = sum(direct.values())
    # Explainable heuristic only; the constants are policy weights, not learned parameters.
    direct_weight = min(48, direct_count * 12)
    indicator_weight = min(30, sum(min(value, 2) for value in indicators.values()) * 6)
    combination_weight = min(21, max(0, active - 1) * 7)
    relation_weight = min(15, len(relations) * 5)
    score = min(100, direct_weight + indicator_weight + combination_weight + relation_weight)
    if active >= 3 or (active >= 2 and relations):
        level = "high"
    elif active >= 1 or direct_count >= 3 or relations:
        level = "medium"
    else:
        level = "low"
    return {
        "score": score,
        "level": level,
        "method": "interpretable heuristic; not a calibrated re-identification probability",
        "direct_identifier_categories": dict(direct),
        "quasi_identifier_indicator_counts": indicators,
        "active_quasi_identifier_categories": active,
        "score_components": {
            "direct_identifier_weight": direct_weight,
            "quasi_identifier_weight": indicator_weight,
            "combination_weight": combination_weight,
            "relationship_weight": relation_weight,
        },
        "combination_warning": active >= 2 or bool(relations),
        "relationship_signals": relations,
        "recommendation": (
            "High combination risk: consider generalizing quasi-identifiers and require human review" if level == "high" else
            "Review direct identifiers and contextual relationships" if direct_count or relations else
            "No strong heuristic signal; this does not prove the document is safe"
        ),
    }
