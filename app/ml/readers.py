"""Turn an uploaded file into plain text. Falls back to OCR for scans and photos."""
import io
from pathlib import Path


def _ocr_image(img) -> str:
    try:
        import pytesseract
        return pytesseract.image_to_string(img)
    except Exception:
        raise ValueError("This looks like a scan or photo and OCR is not set up. "
                         "Install Tesseract (brew install tesseract) or upload a text-based file.")


def read_pdf(data: bytes) -> tuple[str, str]:
    import pdfplumber
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    if len(text.strip()) >= 30:
        return text, "pdf-text"
    try:  # scanned PDF -> rasterise pages and OCR them
        from pdf2image import convert_from_bytes
        pages = convert_from_bytes(data, dpi=200)
    except Exception:
        raise ValueError("This PDF has no selectable text (scanned). Install poppler and Tesseract to enable OCR.")
    return "\n".join(_ocr_image(p) for p in pages), "pdf-ocr"


def read_docx(data: bytes) -> tuple[str, str]:
    import docx
    d = docx.Document(io.BytesIO(data))
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            parts.append(" | ".join(c.text for c in row.cells))
    return "\n".join(parts), "docx"


def read_image(data: bytes) -> tuple[str, str]:
    from PIL import Image
    return _ocr_image(Image.open(io.BytesIO(data))), "image-ocr"


def extract_text(filename: str, data: bytes) -> tuple[str, str]:
    ext = Path(filename).suffix.lower()
    try:
        if ext == ".pdf":
            return read_pdf(data)
        if ext == ".docx":
            return read_docx(data)
        if ext in {".png", ".jpg", ".jpeg"}:
            return read_image(data)
        return data.decode("utf-8", errors="ignore"), "text"
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Could not read this file ({type(e).__name__}). Check that it is not corrupted or password-protected.")
