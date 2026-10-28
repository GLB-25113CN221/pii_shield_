"""Presidio-compatible recognizers for Indian identifiers.

Uses Presidio PatternRecognizer components and, when an English spaCy model is
installed, the AnalyzerEngine pipeline. If the NLP model is absent, it falls
back to running the same custom PatternRecognizer objects directly; it never
silently claims the full AnalyzerEngine ran.
"""
from __future__ import annotations
import re
from functools import lru_cache
from detectors.base import Finding

# Conservative high-value patterns. Existing project validators remain the
# source of truth for checksums/format-specific validation.
_RECOGNIZERS = {
    "PAN": (r"(?<![A-Z0-9])[A-Z]{3}[ABCFGHJLPT][A-Z][0-9]{4}[A-Z](?![A-Z0-9])", ["PAN", "permanent account number", "tax id"]),
    "IFSC": (r"(?<![A-Z0-9])[A-Z]{4}0[A-Z0-9]{6}(?![A-Z0-9])", ["IFSC", "bank branch", "bank code"]),
    "GSTIN": (r"(?<![A-Z0-9])(?:0[1-9]|[1-2][0-9]|3[0-8])[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z](?![A-Z0-9])", ["GSTIN", "GST number", "GSTIN number"]),
    "MOBILE": (r"(?<!\d)(?:\+?91[- ]?)?[6-9]\d{9}(?!\d)", ["mobile", "phone", "contact number", "मोबाइल", "फोन", "தொலைபேசி"]),
    "EMAIL": (r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?!\w)", ["email", "e-mail", "ईमेल"]),
    "AADHAAR_CANDIDATE": (r"(?<!\d)[2-9](?:[\d\s-]{10,18})\d(?!\d)", ["aadhaar", "aadhar", "आधार", "uid"]),
    "BANK_ACCOUNT_CANDIDATE": (r"(?i)(?:account|a/c|bank account|खाता|கணக்கு)\s*(?:no\.?|number|संख्या)?\s*[:#-]?\s*\d{9,18}", ["account number", "bank account", "खाता संख्या"]),
    "UPI_ID": (r"(?<![\w.-])[A-Za-z0-9._-]{2,}@[A-Za-z][A-Za-z0-9]{1,}(?![\w-]|\.[A-Za-z])", ["UPI", "UPI ID", "VPA", "payment address"]),
    "VOTER_ID": (r"(?<![A-Z0-9])[A-Z]{3}[0-9]{7}(?![A-Z0-9])", ["voter id", "EPIC", "मतदाता पहचान पत्र"]),
    "PASSPORT": (r"(?<![A-Z0-9])[A-Z][0-9]{7}(?![A-Z0-9])", ["passport", "passport number", "पासपोर्ट"]),
}

@lru_cache(maxsize=1)
def _presidio_components():
    """Create custom Presidio PatternRecognizers once; safe if package absent."""
    try:
        from presidio_analyzer import Pattern, PatternRecognizer
        result = {}
        for entity, (regex, context) in _RECOGNIZERS.items():
            result[entity] = PatternRecognizer(
                supported_entity=entity,
                patterns=[Pattern(name=f"india_{entity.lower()}", regex=regex, score=0.72)],
                context=context,
                supported_language="en",
            )
        return result
    except Exception:
        return {}

@lru_cache(maxsize=1)
def _analyzer_engine():
    """Try the Presidio AnalyzerEngine with the small English spaCy model."""
    try:
        import spacy
        spacy.load("en_core_web_sm")
        from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        })
        nlp_engine = provider.create_engine()
        registry = RecognizerRegistry(supported_languages=["en"])
        # Start from Presidio's predefined recognizers, but invoke only this
        # intentionally small subset below (not every country-specific recognizer).
        try:
            registry.load_predefined_recognizers(supported_language="en")
        except Exception:
            pass
        for recognizer in _presidio_components().values():
            registry.add_recognizer(recognizer)
        return AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=["en"])
    except Exception:
        return None

def detect_with_presidio(text: str) -> tuple[list[Finding], str]:
    """Return custom recognizer results and the actual path used.

    AnalyzerEngine is used when its NLP dependency is installed. Otherwise the
    exact same Presidio PatternRecognizer objects are invoked directly, avoiding
    an implicit model download or a failure of the rest of the app.
    """
    if not text:
        return [], "unavailable"
    recognizers = _presidio_components()
    if not recognizers:
        return [], "unavailable (presidio-analyzer not installed)"
    results = []
    engine = _analyzer_engine()
    if engine is not None:
        try:
            # Custom regex recognizers work on Indian scripts too; language='en'
            # selects the configured recognizer registry, not a translation step.
            selected_entities = list(_RECOGNIZERS) + ["EMAIL_ADDRESS", "CREDIT_CARD", "PHONE_NUMBER", "IP_ADDRESS", "URL"]
            category_map = {"EMAIL_ADDRESS": "EMAIL", "CREDIT_CARD": "CARD", "PHONE_NUMBER": "MOBILE"}
            for item in engine.analyze(text=text, language="en", entities=selected_entities):
                start, end = int(item.start), int(item.end)
                if 0 <= start < end <= len(text):
                    entity_type = category_map.get(str(item.entity_type), str(item.entity_type))
                    results.append(Finding(entity_type, start, end,
                                           float(item.score), text[start:end],
                                           "presidio_analyzer", "pending"))
            return _dedupe(results), "Presidio AnalyzerEngine + custom Indian recognizers"
        except Exception:
            pass
    for entity, recognizer in recognizers.items():
        before = len(results)
        try:
            for item in recognizer.analyze(text=text, entities=[entity], nlp_artifacts=None):
                start, end = int(item.start), int(item.end)
                if 0 <= start < end <= len(text):
                    results.append(Finding(str(item.entity_type), start, end,
                                           float(item.score), text[start:end],
                                           "presidio_pattern", "pending"))
        except Exception:
            pass
        # Some Presidio versions expect NLP artifacts for context enhancement.
        # Preserve the configured Presidio patterns even when that optional NLP
        # dependency is absent; context boosts are only applied by AnalyzerEngine.
        if len(results) == before:
            regex, _context = _RECOGNIZERS[entity]
            try:
                for match in re.finditer(regex, text, re.I):
                    results.append(Finding(entity, match.start(), match.end(), .62,
                                           match.group(), "presidio_pattern_fallback", "pending"))
            except re.error:
                pass
    return _dedupe(results), "Presidio PatternRecognizer fallback (NLP model unavailable)"

def _dedupe(items):
    seen = set(); out = []
    for f in items:
        key = (f.pii_type, f.start, f.end)
        if key not in seen:
            seen.add(key); out.append(f)
    return out

def presidio_status() -> str:
    """Describe whether Presidio's full AnalyzerEngine or fallback is available."""
    if not _presidio_components():
        return "unavailable (presidio-analyzer not installed)"
    if _analyzer_engine() is not None:
        return "Presidio AnalyzerEngine + built-in selected recognizers + custom Indian recognizers"
    return "Presidio PatternRecognizer fallback (spaCy model/AnalyzerEngine unavailable)"
