"""Retrieve chunks with oversampling, filter by selected docs, threshold, dedupe."""
from __future__ import annotations

from .config import (
    DEFAULT_TOP_K,
    OVERSAMPLE_FACTOR,
    RELEVANCE_THRESHOLD,
    MAX_CITATIONS_PER_PAGE,
)
from .ollama_client import embed
from .indexer import load_index
import numpy as np


def retrieve(
    query: str,
    selected_doc_ids: list[str] | None,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict]:
    """
    selected_doc_ids: None = all docs; else only these doc_ids.
    Returns list of {doc_id, doc_name, page, text, score} sorted by score, deduped.
    """
    index, meta = load_index()
    if index is None or not meta:
        return []

    # Oversample then filter
    k_oversample = min(top_k * OVERSAMPLE_FACTOR, index.ntotal)
    if k_oversample < 1:
        return []

    qv = embed([query])[0]
    qv = np.array([qv], dtype="float32")
    import faiss
    faiss.normalize_L2(qv)

    scores, indices = index.search(qv, k_oversample)
    scores = scores[0].tolist()
    indices = indices[0].tolist()

    # Filter by selected docs
    if selected_doc_ids is not None and len(selected_doc_ids) > 0:
        selected_set = set(selected_doc_ids)
        filtered = []
        for i, idx in enumerate(indices):
            if idx < 0 or idx >= len(meta):
                continue
            m = meta[idx]
            if m["doc_id"] in selected_set and scores[i] >= RELEVANCE_THRESHOLD:
                filtered.append((scores[i], m))
    else:
        filtered = []
        for i, idx in enumerate(indices):
            if idx < 0 or idx >= len(meta):
                continue
            m = meta[idx]
            if scores[i] >= RELEVANCE_THRESHOLD:
                filtered.append((scores[i], m))

    # Dedupe: max MAX_CITATIONS_PER_PAGE per (doc_id, page)
    seen = {}  # (doc_id, page) -> count
    result = []
    for score, m in filtered:
        key = (m["doc_id"], m["page"])
        seen[key] = seen.get(key, 0) + 1
        if seen[key] <= MAX_CITATIONS_PER_PAGE:
            result.append({
                "doc_id": m["doc_id"],
                "doc_name": m["doc_name"],
                "page": m["page"],
                "text": m["text"],
                "score": float(score),
            })
        if len(result) >= top_k:
            break

    return result
