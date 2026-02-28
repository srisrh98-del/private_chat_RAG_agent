from fastapi import APIRouter
from ..indexer import build_index

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reindex")
def reindex():
    try:
        num_docs, num_chunks, warnings = build_index()
        return {
            "num_docs": num_docs,
            "num_chunks": num_chunks,
            "warnings": warnings,
        }
    except RuntimeError as e:
        return {
            "num_docs": 0,
            "num_chunks": 0,
            "warnings": [str(e)],
        }
