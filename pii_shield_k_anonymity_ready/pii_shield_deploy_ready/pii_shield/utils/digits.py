"""Indic digit normalization. Preserve original strings separately for redaction."""
import unicodedata

def normalize_digits(value: str) -> str:
    """Convert Unicode decimal digits to ASCII without changing other characters."""
    return "".join(str(unicodedata.digit(ch)) if ch.isdecimal() else ch for ch in value)
