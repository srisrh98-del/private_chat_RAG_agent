"""PDF text extraction and page rendering using PyMuPDF. Local only."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from .config import CHUNK_SIZE, CHUNK_OVERLAP, DATA_DIR


def _ensure_fitz():
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is not installed. pip install pymupdf")


def get_pdf_list() -> list[dict]:
    """List PDFs in data/docs. Returns [{id, name, path}, ...]."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for i, p in enumerate(sorted(DATA_DIR.glob("**/*.pdf"))):
        try:
            rel = p.relative_to(DATA_DIR)
        except ValueError:
            rel = p.name
        out.append({
            "id": str(rel),
            "name": p.name,
            "path": str(p),
        })
    return out


def extract_text_and_chunks(pdf_path: str) -> tuple[str, list[dict], Optional[str]]:
    """
    Extract text and build chunks with page numbers.
    Returns (full_text, chunks, warning).
    chunks: [{text, page, doc_id}, ...]
    warning: set if low text (possible scanned PDF).
    """
    _ensure_fitz()
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    try:
        rel = path.relative_to(DATA_DIR)
    except ValueError:
        rel = path.name
    doc_id = str(rel)

    doc = fitz.open(pdf_path)
    try:
        num_pages = len(doc)
        full_text = ""
        chunks = []
        for page_num in range(num_pages):
            page = doc[page_num]
            text = page.get_text()
            full_text += text + "\n"
            # Chunk by size + overlap
            start = 0
            while start < len(text):
                end = min(start + CHUNK_SIZE, len(text))
                snippet = text[start:end].strip()
                if snippet:
                    chunks.append({
                        "text": snippet,
                        "page": page_num + 1,
                        "doc_id": doc_id,
                        "doc_name": path.name,
                    })
                start = end - CHUNK_OVERLAP if end < len(text) else len(text)
    finally:
        doc.close()

    # Low text heuristic (scanned PDF)
    total_chars = sum(len(c["text"]) for c in chunks)
    warning = None
    if num_pages > 0 and total_chars / num_pages < 50:
        warning = "Low text extracted; this PDF may be scanned. Consider OCR for v2."

    return full_text, chunks, warning


def render_page_to_png(pdf_path: str, page_num: int, dpi: int = 150) -> bytes:
    """Render a single PDF page to PNG bytes. page_num is 1-based."""
    _ensure_fitz()
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    doc = fitz.open(pdf_path)
    if page_num < 1 or page_num > len(doc):
        doc.close()
        raise ValueError(f"Page {page_num} out of range (1..{len(doc)})")
    page = doc[page_num - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes


def resolve_pdf_path(doc_id: str) -> Path:
    """Resolve doc_id to absolute path. Prevents path traversal."""
    # doc_id is relative to DATA_DIR, no ".." allowed
    safe = Path(doc_id)
    if ".." in safe.parts or safe.is_absolute():
        raise ValueError("Invalid doc_id")
    full = (DATA_DIR / safe).resolve()
    if not str(full).startswith(str(DATA_DIR.resolve())):
        raise ValueError("Invalid doc_id: path traversal")
    if not full.suffix.lower() == ".pdf":
        raise ValueError("Not a PDF")
    return full
