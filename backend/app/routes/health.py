from fastapi import APIRouter
from .deps import ollama_status

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    ok, msg = ollama_status()
    return {"status": "ok" if ok else "degraded", "ollama": msg}
