"""Chat logic: build context from retrieval, call LLM, abstain if weak evidence."""
from __future__ import annotations

from .retriever import retrieve
from .ollama_client import chat

SYSTEM = """You are a helpful assistant that answers questions using ONLY the provided context from PDF documents.
Rules:
- Base your answer only on the context below. Do not use external knowledge.
- Cite sources as (DocumentName, page N) when you use a specific fact.
- If the context does not contain enough information to answer, say exactly: "I don't have enough information in the selected documents."
- Be concise. Do not make up information."""


def build_context(hits: list[dict]) -> str:
    parts = []
    for h in hits:
        parts.append(f"[{h['doc_name']}, page {h['page']}]:\n{h['text']}")
    return "\n\n---\n\n".join(parts) if parts else ""


def has_enough_evidence(hits: list[dict], min_hits: int = 1, min_score: float = 0.0) -> bool:
    if len(hits) < min_hits:
        return False
    if min_score > 0 and not any(h["score"] >= min_score for h in hits):
        return False
    return True


def answer_question(
    question: str,
    selected_doc_ids: list[str] | None,
    top_k: int = 10,
) -> dict:
    """
    Returns {answer, citations, abstained}.
    citations: [{doc_id, doc_name, page, text, score}, ...]
    """
    hits = retrieve(question, selected_doc_ids, top_k=top_k)
    if not has_enough_evidence(hits):
        return {
            "answer": "I don't have enough information in the selected documents.",
            "citations": [],
            "abstained": True,
        }
    context = build_context(hits)
    answer = chat(question, SYSTEM, context)
    # If model didn't abstain but we want to detect it from text
    abstained = "don't have enough information" in answer.lower()
    return {
        "answer": answer,
        "citations": hits,
        "abstained": abstained,
    }
