"""
PDF and text file extraction utilities.
"""
import io
import pdfplumber


def extract_text_from_pdf(file_bytes: bytes, max_chars: int = 8000) -> str:
    """Extract plain text from a PDF byte string."""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
        full = " ".join(pages_text)
        return full[:max_chars]
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def extract_text_from_txt(file_bytes: bytes, max_chars: int = 8000) -> str:
    """Decode plain text from uploaded TXT file bytes."""
    return file_bytes.decode("utf-8", errors="ignore")[:max_chars]


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Auto-detect file type and extract text."""
    fn = filename.lower()
    if fn.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    return extract_text_from_txt(file_bytes)
