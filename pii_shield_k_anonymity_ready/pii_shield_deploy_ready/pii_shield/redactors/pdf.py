"""True PDF redaction using PyMuPDF. Text layer redactions remove underlying text."""
try:
    import pymupdf as fitz      # modern name (PyMuPDF >= 1.24.3)
except ImportError:             # older PyMuPDF
    import fitz

def redact_pdf(data: bytes, detector):
    """Redact detected text spans with PDF redaction annotations, then save sanitized PDF."""
    doc=fitz.open(stream=data,filetype="pdf")
    for page in doc:
        words=page.get_text("words")
        findings=detector(page.get_text())
        for f in findings:
            needle=(f.value or "").strip()
            if not needle: continue
            # search_for handles multi-word values (e.g. a full name); fall back to single-word match
            rects=page.search_for(needle)
            if not rects:
                rects=[fitz.Rect(w[:4]) for w in words if needle in w[4]]
            for r in rects: page.add_redact_annot(r,fill=(0,0,0))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS)
    doc.set_metadata({})
    return doc.tobytes(garbage=4,deflate=True,clean=True)

def pdf_text(data: bytes) -> str:
    """Extract the text layer of a PDF (empty for scanned PDFs)."""
    doc=fitz.open(stream=data,filetype="pdf")
    return "\n".join(p.get_text() for p in doc)
