"""Regex + validator detectors for common Indian identifiers."""
import re
from detectors.base import Finding
from utils.digits import normalize_digits
from utils.verhoeff import verhoeff_valid
from utils.luhn import luhn_valid

PATTERNS = {
 "PAN": re.compile(r"(?<![A-Z0-9])[A-Z]{5}[0-9]{4}[A-Z](?![A-Z0-9])", re.I),
 "IFSC": re.compile(r"(?<![A-Z0-9])[A-Z]{4}0[A-Z0-9]{6}(?![A-Z0-9])", re.I),
 "MOBILE": re.compile(r"(?<!\d)(?:\+?91[- ]?)?[6-9](?:[\s-]?\d){9}(?!\d)"),
 "EMAIL": re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?!\w)"),
 "CARD": re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
 "GSTIN": re.compile(r"(?<![A-Z0-9])(?:0[1-9]|[1-2]\d|3[0-8])[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z](?![A-Z0-9])", re.I),
 "PASSPORT": re.compile(r"(?<![A-Z0-9])[A-Z][0-9]{7}(?![A-Z0-9])", re.I),
 "VEHICLE_PLATE": re.compile(r"(?<![A-Z0-9])[A-Z]{2}[ -]?[0-9]{1,2}[ -]?[A-Z]{1,3}[ -]?[0-9]{4}(?![A-Z0-9])", re.I),
 "VOTER_ID": re.compile(r"(?<![A-Z0-9])[A-Z]{3}[0-9]{7}(?![A-Z0-9])", re.I),
 "UPI_ID": re.compile(r"(?<![\w.-])[A-Za-z0-9._-]{2,}@[A-Za-z][A-Za-z0-9]{1,}(?![\w-]|\.[A-Za-z])"),  # handle has no dot, so emails are not double-counted
 "PIN_CODE": re.compile(r"(?<!\d)[1-9]\d{5}(?!\d)"),
 "DL": re.compile(r"(?<![A-Z0-9])[A-Z]{2}[- ]?\d{2}[- ]?\d{4}\d{7,}(?![A-Z0-9])", re.I),
}
def detect_identifiers(text: str) -> list[Finding]:
    """Detect validated identifiers; offsets always refer to original text."""
    normalized = normalize_digits(text)
    out=[]
    for kind, pat in PATTERNS.items():
        for m in pat.finditer(normalized):
            value=m.group()
            ok=True
            if kind=="PAN": ok=value[3].upper() in "ABCFGHJLPT"
            elif kind=="MOBILE":
                digits=re.sub(r"\D", "", value)
                if digits.startswith("91") and len(digits)==12: digits=digits[2:]
                ok=len(digits)==10 and digits[0] in "6789"
            elif kind=="CARD":
                digits=re.sub(r"\D","",value); ok=13 <= len(digits) <= 19 and luhn_valid(digits)
            elif kind=="GSTIN": ok=value[:2].isdigit() and 1 <= int(value[:2]) <= 38
            elif kind=="PIN_CODE": ok=len(value)==6
            if ok:
                # Unicode decimal digits normally occupy one code point, so offsets align.
                out.append(Finding(kind,m.start(),m.end(),.99,text[m.start():m.end()]))
    # Aadhaar: 12 digits, not beginning 0/1, valid Verhoeff checksum.
    # Accept spaces/hyphens and normalized Hindi digits. Checksum on compact digits.
    for m in re.finditer(r"(?<!\d)[2-9](?:[\d\s-]{10,18})\d(?!\d)", normalized):
        raw=m.group(); digits=re.sub(r"[\s-]", "", raw)
        if len(digits)==12 and verhoeff_valid(digits):
            out.append(Finding("AADHAAR",m.start(),m.end(),.995,text[m.start():m.end()]))
    # OCR-confused Aadhaar candidates: correct O/o→0, I/l→1, S/s→5 only when
    # the resulting compact 12-digit value passes Verhoeff. Keep original span.
    for m in re.finditer(r"(?<![A-Za-z0-9])[2-9OolISs](?:[0-9OolISs\s-]{10,22})[0-9OolISs](?![A-Za-z0-9])", normalized):
        raw=m.group(); compact=re.sub(r"[\s-]", "", raw).translate(str.maketrans({"O":"0","o":"0","I":"1","l":"1","S":"5","s":"5"}))
        if len(compact)==12 and compact[0] in "23456789" and verhoeff_valid(compact):
            if not any(f.pii_type=="AADHAAR" and f.start==m.start() and f.end==m.end() for f in out):
                out.append(Finding("AADHAAR",m.start(),m.end(),.86,text[m.start():m.end()],"ocr_checksum"))
    # Bank account: intentionally review-only due to broad formats.
    for m in re.finditer(r"(?i)(?:account|a/c|bank account|खाता)\s*(?:no\.?|number|संख्या)?\s*[:#-]?\s*(\d{9,18})", normalized):
        out.append(Finding("BANK_ACCOUNT",m.start(1),m.end(1),.78,text[m.start(1):m.end(1)],status="pending"))
    # Add Presidio's custom PatternRecognizer pipeline for complementary context-aware
    # matching. Existing validated matches win exact-span duplicates.
    try:
        from detectors.presidio_pipeline import detect_with_presidio
        presidio_findings, _presidio_path = detect_with_presidio(text)
        existing={(f.pii_type, f.start, f.end) for f in out}
        for f in presidio_findings:
            key=(f.pii_type, f.start, f.end)
            # Do not duplicate a finding already validated by the local rules.
            if key not in existing:
                out.append(f); existing.add(key)
    except Exception:
        pass
    # Dates and name/address labels are handled as heuristic findings by multilingual layer.
    return _dedupe(out)
def _dedupe(items):
    seen=set(); result=[]
    for f in sorted(items,key=lambda x:(x.start, -(x.end-x.start))):
        key=(f.pii_type,f.start,f.end)
        if key not in seen: seen.add(key); result.append(f)
    return result
