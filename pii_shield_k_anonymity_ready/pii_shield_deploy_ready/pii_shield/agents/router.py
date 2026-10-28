"""Input router agent."""
from pathlib import Path
def route(filename: str, data: bytes) -> dict:
    ext=Path(filename).suffix.lower()
    if ext in {".png",".jpg",".jpeg",".webp",".bmp"}: kind="image"
    elif ext==".pdf": kind="pdf"
    elif ext==".docx": kind="docx"
    elif ext==".csv": kind="csv"
    elif ext==".txt": kind="text"
    else: kind="unsupported"
    return {"kind":kind,"size_bytes":len(data),"tool": {"image":"ocr_image","pdf":"pdf_text_layer","docx":"docx_parser","csv":"csv_reader","text":"utf8_reader"}.get(kind,"reject")}
