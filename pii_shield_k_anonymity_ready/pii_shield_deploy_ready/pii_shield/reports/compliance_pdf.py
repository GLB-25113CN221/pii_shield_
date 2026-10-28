"""Generate a category/count-only compliance report."""
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
def make_report(report: dict) -> bytes:
    buf=BytesIO(); c=canvas.Canvas(buf,pagesize=letter); y=750
    c.setTitle("PII Shield India - Sanitization Report")
    lines=["PII Shield India — Sanitization Report","",f"Document ID: {report.get('document_id','not assigned')}",
           f"File type: {report.get('file_type','unknown')}",f"Language: {report.get('language','auto')}",
           f"Verification: {report.get('verification_status','not run')}",f"Risk score: {report.get('risk_score',0)}/100",
           "Detected categories and counts (no raw PII):"]
    lines += [f"  {k}: {v}" for k,v in report.get("counts",{}).items()] or ["  No findings recorded"]
    lines += ["","Safeguards: data minimization; masking/obfuscation; local-first review; audit retention.",
              "Legal note: This technical report is not a certification of DPDP Act/Rules compliance.",
              "DPDP Act 2023: assess security safeguards under Section 8(5); applicable Rules and commencement dates require legal review."]
    for line in lines:
        c.drawString(48,y,line[:110]); y-=20
        if y<50: c.showPage(); y=750
    c.save(); return buf.getvalue()
