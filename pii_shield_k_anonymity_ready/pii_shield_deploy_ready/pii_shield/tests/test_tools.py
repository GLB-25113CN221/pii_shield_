from io import BytesIO
from PIL import Image
import fitz
from tools import extract_text, rasterize_pdf, detect_names_addresses, verify_output, redact_scanned_pdf
from detectors.identifiers import detect_identifiers
from redactors.text import redact_text
from redactors.docx import redact_docx, docx_text
from docx import Document

def test_extract_text(): assert 'hello' in extract_text(b'hello','txt')
def test_detect_names(): assert detect_names_addresses('Name: Priya Sharma')
def test_validate_and_verify_tool(): assert verify_output('nothing personal')['verified']
def test_redact_text():
    t='email demo.user@example.com'; f=detect_identifiers(t); assert 'demo.user@example.com' not in redact_text(t,f)
def test_rasterize_pdf():
    d=fitz.open(); p=d.new_page(); p.insert_text((40,40),'hello'); data=d.tobytes(); d.close(); assert len(rasterize_pdf(data))==1
def test_redact_docx():
    d=Document(); d.add_paragraph('Email demo.user@example.com'); b=BytesIO(); d.save(b); out=redact_docx(b.getvalue(),lambda t:detect_identifiers(t)); assert 'demo.user@example.com' not in docx_text(out)
def test_ocr_tool_preprocessing_import():
    from tools import ocr_page
    im=Image.new('RGB',(120,40),'white')
    # OCR may require external Tesseract; test graceful call surface only.
    assert callable(ocr_page)
def test_scanned_pdf_requires_ocr_readable_error():
    d=fitz.open(); d.new_page(); data=d.tobytes(); d.close()
    # May run when Tesseract is installed; if not, a readable RuntimeError is expected.
    try: out=redact_scanned_pdf(data,lambda t:[]); assert out.startswith(b'%PDF')
    except RuntimeError as e: assert 'Tesseract' in str(e)

def test_native_tool_registry_complete():
    from tools import tool_registry
    expected={'extract_text','ocr_page','rasterize_pdf','detect_identifiers','detect_names_addresses','validate_candidate','redact_text','redact_image_boxes','redact_pdf','redact_docx','verify_output'}
    assert expected <= set(tool_registry())

def test_aadhaar_plain_spaced_hyphen_hindi_digits():
    from detectors.identifiers import detect_identifiers
    assert any(f.pii_type=='AADHAAR' for f in detect_identifiers('234567890124'))
    assert any(f.pii_type=='AADHAAR' for f in detect_identifiers('2345 6789 0124'))
    assert any(f.pii_type=='AADHAAR' for f in detect_identifiers('2345-6789-0124'))
    assert any(f.pii_type=='AADHAAR' for f in detect_identifiers('२३४५ ६७८९ ०१२४'))

def test_synthetic_evaluation_runs():
    from evaluation import evaluate
    result=evaluate('rule-only')
    assert result['synthetic_samples'] >= 10 and result['metrics']
