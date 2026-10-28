"""OCR with bounding boxes using pytesseract; gracefully reports missing language packs."""
from PIL import Image
def ocr_image(image: Image.Image, language: str = "eng"):
    """Return text and word boxes. Install Tesseract and requested language packs."""
    import pytesseract
    data=pytesseract.image_to_data(image,lang=language,output_type=pytesseract.Output.DICT)
    words=[]; lines=[]
    for i,word in enumerate(data["text"]):
        if word.strip():
            x,y,w,h=[int(data[k][i]) for k in ("left","top","width","height")]
            words.append({"text":word,"box":(x,y,x+w,y+h),"confidence":float(data["conf"][i]) if data["conf"][i] not in ("-1","") else 0})
            lines.append(word)
    return " ".join(lines), words
