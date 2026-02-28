from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..pdf_processor import get_pdf_list, render_page_to_png, resolve_pdf_path

router = APIRouter(tags=["pdfs"])


@router.get("/pdfs")
def list_pdfs():
    return get_pdf_list()


@router.get("/page")
def get_page(doc: str, page: int):
    """Returns PNG image of the cited page. Path traversal safe."""
    if page < 1:
        raise HTTPException(400, "page must be >= 1")
    try:
        path = resolve_pdf_path(doc)
    except ValueError as e:
        raise HTTPException(400, str(e))
    try:
        png_bytes = render_page_to_png(str(path), page)
    except FileNotFoundError:
        raise HTTPException(404, "PDF not found")
    except ValueError as e:
        raise HTTPException(400, str(e))
    return Response(content=png_bytes, media_type="image/png")
