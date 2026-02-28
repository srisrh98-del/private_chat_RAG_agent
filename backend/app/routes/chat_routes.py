from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ..chat import answer_question
from ..config import DEFAULT_TOP_K

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    selected_docs: Optional[list[str]] = None  # doc_id list; empty or null = all
    top_k: int = DEFAULT_TOP_K


@router.post("/chat")
def chat(req: ChatRequest):
    selected = req.selected_docs if req.selected_docs else None
    top_k = max(1, min(50, req.top_k))
    result = answer_question(req.question, selected, top_k=top_k)
    return result
