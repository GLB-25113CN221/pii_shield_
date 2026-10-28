"""Multilingual NER: AI4Bharat IndicNER (11 languages) plus label heuristics.

IndicNER is optional at runtime because Hugging Face access is gated. Accept the
model conditions and authenticate before enabling downloads; document contents
are never sent to Hugging Face by this module.
"""
import os
import re
from functools import lru_cache
from detectors.base import Finding

# Field-label heuristics are a fallback, not a substitute for NER. Include labels
# for the 11 IndicNER languages: as, bn, gu, hi, kn, ml, mr, or, pa, ta, te.
LABELS = [
 r"(?:नाम|पिता का नाम|जन्म तिथि|पता|आधार संख्या|पैन)\s*[:：-]?\s*([^\n,;]{2,70})",
 r"(?:नाव|वडिलांचे नाव|जन्मतारीख|पत्ता)\s*[:：-]?\s*([^\n,;]{2,70})",
 r"(?:பெயர்|தந்தையின் பெயர்|பிறந்த தேதி|முகவரி)\s*[:：-]?\s*([^\n,;]{2,70})",
 r"(?<![A-Za-z])(?:name|father'?s name|date of birth|dob|address)\s*[:：-]\s*([^\n,;]{2,70})",
 r"(?:নাম|জন্ম তারিখ|ঠিকানা)\s*[:：-]?\s*([^\n,;]{2,70})",
 r"(?:పేరు|చిరునామా|పుట్టిన తేదీ|ಹೆಸರು|ವಿಳಾಸ|പേര്|വിലാസം|નામ|સરનામું|ਨਾਮ|ਪਤਾ|ନାମ|ଠିକଣା|নাম|ঠিকানা)\s*[:：-]?\s*([^\n,;]{2,70})",
 r"(?:নাম|ঠিকানা|জন্ম তারিখ|নাম|ঠিকানা)\s*[:：-]?\s*([^\n,;]{2,70})",
]

@lru_cache(maxsize=2)
def _load_indicner(model: str, allow_download: bool):
    """Load IndicNER. Downloads require an explicit environment opt-in.

    The cache is keyed by configuration so changing the environment before a
    subsequent call can retry loading instead of caching a stale failure.
    """
    try:
        from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
        tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=not allow_download)
        model_obj = AutoModelForTokenClassification.from_pretrained(model, local_files_only=not allow_download)
        return pipeline("token-classification", model=model_obj, tokenizer=tokenizer,
                        aggregation_strategy="simple")
    except Exception:
        return None

def _get_indicner():
    model = os.getenv("PII_NER_MODEL", "ai4bharat/IndicNER")
    allow_download = os.getenv("PII_NER_ALLOW_DOWNLOAD", "false").lower() in {"1", "true", "yes"}
    return _load_indicner(model, allow_download)

@lru_cache(maxsize=1)
def _load_spacy():
    """Optional English fallback; never downloads a model automatically."""
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        return None

def _kind_from_label(label):
    label = str(label or "").upper().replace("B-", "").replace("I-", "")
    if label in {"PER", "PERSON", "PERSON_NAME"} or "PERSON" in label:
        return "PERSON"
    if label in {"LOC", "LOCATION", "GPE", "ADDRESS", "FAC"} or "LOC" in label or "GPE" in label:
        return "ADDRESS" if label in {"ADDRESS", "FAC"} else "LOCATION"
    if label in {"ORG", "ORGANIZATION", "COMPANY"} or "ORG" in label:
        return "ORGANIZATION"
    return None

def detect_ner(text: str) -> list[Finding]:
    """Find entities with IndicNER when available, plus multilingual label rules."""
    out=[]
    for pattern in LABELS:
        for m in re.finditer(pattern, text, re.I):
            label = text[m.start():m.start(1)].lower()
            address_markers = ("पता", "पत्ता", "முகவரி", "address", "ঠিকানা", "చిరునామా", "ವಿಳಾಸ", "വിലാസം", "સરનામું", "ਪਤਾ", "ଠିକଣା")
            date_markers = ("जन्म", "பிறந்த", "date", "dob", "জন্ম", "పుట్టిన", "जन्मतारीख")
            kind = "ADDRESS" if any(x in label for x in address_markers) else ("DATE_OF_BIRTH" if any(x in label for x in date_markers) else "PERSON")
            out.append(Finding(kind, m.start(1), m.end(1), .72, m.group(1), "label_heuristic", "pending"))

    ner = _get_indicner()
    if ner is not None:
        try:
            # Chunk at sentence/newline boundaries to avoid the transformer token limit.
            # Keep offsets by processing each line independently.
            offset = 0
            for line in text.splitlines(keepends=True):
                body = line.rstrip("\r\n")
                if body.strip():
                    for ent in ner(body[:12000]):
                        kind = _kind_from_label(ent.get("entity_group", ent.get("entity", "")))
                        start, end = int(ent.get("start", -1)), int(ent.get("end", -1))
                        if kind and 0 <= start < end <= len(body):
                            out.append(Finding(kind, offset + start, offset + end,
                                               float(ent.get("score", .6)), text[offset + start:offset + end],
                                               "ai4bharat_indicner", "pending"))
                offset += len(line)
        except Exception:
            pass

    nlp = _load_spacy()
    if nlp is not None:
        try:
            for ent in nlp(text[:100000]).ents:
                if ent.label_ in {"PERSON", "GPE", "LOC", "ORG", "FAC"}:
                    kind = "PERSON" if ent.label_ == "PERSON" else ("ORGANIZATION" if ent.label_ == "ORG" else "LOCATION")
                    out.append(Finding(kind, ent.start_char, ent.end_char, .68, ent.text, "spacy_en_fallback", "pending"))
        except Exception:
            pass
    # De-duplicate exact span/type pairs, preserving the highest-confidence finding.
    best = {}
    for f in out:
        key = (f.pii_type, f.start, f.end)
        if key not in best or f.confidence > best[key].confidence:
            best[key] = f
    return sorted(best.values(), key=lambda f: (f.start, f.end))

def ner_status() -> dict:
    """Safe status for UI/reporting; does not expose document text."""
    if _get_indicner() is not None:
        return {"model": os.getenv("PII_NER_MODEL", "ai4bharat/IndicNER"), "status": "loaded", "languages": ["Assamese", "Bengali", "Gujarati", "Hindi", "Kannada", "Malayalam", "Marathi", "Odia", "Punjabi", "Tamil", "Telugu"]}
    return {"model": os.getenv("PII_NER_MODEL", "ai4bharat/IndicNER"), "status": "not loaded; using label heuristics and optional English fallback", "languages": []}
