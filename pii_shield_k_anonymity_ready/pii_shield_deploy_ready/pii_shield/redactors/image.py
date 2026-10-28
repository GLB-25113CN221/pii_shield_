"""Image redaction and metadata stripping."""
from PIL import Image, ImageDraw
def redact_image(image: Image.Image, boxes: list[tuple[int,int,int,int]]) -> Image.Image:
    """Draw opaque black boxes and return a fresh RGB image without EXIF metadata."""
    out=image.convert("RGB").copy()
    draw=ImageDraw.Draw(out)
    for box in boxes: draw.rectangle(box,fill="black")
    return out
