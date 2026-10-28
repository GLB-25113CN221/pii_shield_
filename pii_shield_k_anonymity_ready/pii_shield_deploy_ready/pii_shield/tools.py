"""Explicit callable tool registry used by the Planner and document handlers."""
import io
from PIL import Image, ImageOps, ImageEnhance
from detectors.identifiers import detect_identifiers
from ner.multilingual import detect_ner
from redactors.text import redact_text
from ocr.engine import ocr_image

def extract_text(data, kind):
    if kind in ('txt','csv'): return data.decode('utf-8-sig',errors='replace')
    if kind=='pdf':
        import fitz
        doc=fitz.open(stream=data,filetype='pdf'); return '\n'.join(p.get_text() for p in doc)
    if kind=='docx':
        from redactors.docx import docx_text
        return docx_text(data)
    return ''
def rasterize_pdf(data, dpi=220):
    import fitz
    doc=fitz.open(stream=data,filetype='pdf'); out=[]
    for page in doc: out.append(Image.frombytes('RGB',[page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False).width,page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False).height],page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False).samples))
    return out
def ocr_page(image, language='eng+hin'):
    img=ImageOps.grayscale(image); img=ImageEnhance.Contrast(img).enhance(1.8); img=img.resize((img.width*2,img.height*2))
    # pytesseract boxes are in processed coordinates; caller maps boxes if needed.
    return ocr_image(img,language)
def detect_names_addresses(text): return detect_ner(text)
def validate_candidate(text, finding):
    from agents.context_reviewer import review
    return review(text,finding)
def verify_output(text):
    from agents.red_team import inspect
    return inspect(text)

def redact_image_boxes(image, boxes):
    from redactors.image import redact_image
    return redact_image(image, boxes)

def redact_pdf(data, detector=None):
    from redactors.pdf import redact_pdf as fn
    return fn(data, detector or (lambda t: detect_identifiers(t)+detect_names_addresses(t)))

def redact_docx(data, detector=None):
    from redactors.docx import redact_docx as fn
    return fn(data, detector or (lambda t: detect_identifiers(t)+detect_names_addresses(t)))

def tool_registry():
    return {"extract_text":extract_text,"ocr_page":ocr_page,"rasterize_pdf":rasterize_pdf,
            "detect_identifiers":detect_identifiers,"detect_names_addresses":detect_names_addresses,
            "validate_candidate":validate_candidate,"redact_text":redact_text,
            "redact_image_boxes":redact_image_boxes,"redact_pdf":redact_pdf,
            "redact_docx":redact_docx,"verify_output":verify_output}

def redact_scanned_pdf(data, detector=None, language='eng+hin'):
    """Rasterize scanned PDF, OCR at 2x scale, redact matching word boxes, rebuild image-only PDF."""
    import fitz
    from redactors.image import redact_image
    from PIL import ImageOps, ImageEnhance
    src=fitz.open(stream=data,filetype='pdf'); dst=fitz.open()
    for page in src:
        pix=page.get_pixmap(matrix=fitz.Matrix(2.5,2.5),alpha=False)
        image=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        proc=ImageOps.grayscale(image); proc=ImageEnhance.Contrast(proc).enhance(1.8); proc=proc.resize((proc.width*2,proc.height*2))
        try: text,words=ocr_image(proc,language)
        except Exception as exc: raise RuntimeError('Scanned PDF OCR unavailable. Install Tesseract and eng+hin language packs.') from exc
        fs=(detector or (lambda x: detect_identifiers(x)+detect_names_addresses(x)))(text)
        boxes=[]; cursor=0
        for w in words:
            start=text.find(w['text'],cursor); end=start+len(w['text']) if start>=0 else -1
            if start>=0 and any(f.start<end and f.end>start for f in fs):
                x0,y0,x1,y1=w['box']; boxes.append((x0/2-3,y0/2-3,x1/2+3,y1/2+3))
                cursor=end
        clean=redact_image(image,boxes)
        b=io.BytesIO(); clean.save(b,format='PNG')
        outpage=dst.new_page(width=page.rect.width,height=page.rect.height); outpage.insert_image(outpage.rect,stream=b.getvalue())
    dst.set_metadata({}); result=dst.tobytes(garbage=4,deflate=True); src.close(); dst.close(); return result
