"""FAISS index build and load. Metadata in JSONL."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .config import INDEX_DIR, INDEX_FAISS, INDEX_META, DATA_DIR
from .pdf_processor import get_pdf_list, extract_text_and_chunks
from .ollama_client import embed, check_ollama


def _ensure_index_dir():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def build_index() -> tuple[int, int, list[str]]:
    """
    Build or rebuild FAISS index from data/docs.
    Returns (num_docs, num_chunks, list of warnings).
    """
    ok, msg = check_ollama()
    if not ok:
        raise RuntimeError(msg)

    _ensure_index_dir()
    pdfs = get_pdf_list()
    if not pdfs:
        return 0, 0, ["No PDFs found in data/docs/"]

    all_chunks = []
    warnings = []
    for p in pdfs:
        path = p["path"]
        try:
            _, chunks, warn = extract_text_and_chunks(path)
            all_chunks.extend(chunks)
            if warn:
                warnings.append(f"{p['name']}: {warn}")
        except Exception as e:
            warnings.append(f"{p['name']}: {e!s}")

    if not all_chunks:
        return len(pdfs), 0, warnings

    texts = [c["text"] for c in all_chunks]
    vectors = embed(texts)

    try:
        import faiss
        import numpy as np
    except ImportError:
        raise RuntimeError("faiss-cpu not installed. pip install faiss-cpu")

    dim = len(vectors[0])
    index = faiss.IndexFlatIP(dim)  # inner product for normalized vectors
    v = np.array(vectors, dtype="float32")
    # L2 normalize for cosine similarity via IP
    faiss.normalize_L2(v)
    index.add(v)

    faiss.write_index(index, str(INDEX_FAISS))
    with open(INDEX_META, "w") as f:
        for i, c in enumerate(all_chunks):
            rec = {"idx": i, "doc_id": c["doc_id"], "doc_name": c["doc_name"], "page": c["page"], "text": c["text"]}
            f.write(json.dumps(rec) + "\n")

    return len(pdfs), len(all_chunks), warnings


def load_index():
    """Load FAISS index and metadata. Returns (faiss_index, metadata_list) or (None, [])."""
    if not INDEX_FAISS.exists() or not INDEX_META.exists():
        return None, []

    import faiss
    index = faiss.read_index(str(INDEX_FAISS))
    meta = []
    with open(INDEX_META) as f:
        for line in f:
            line = line.strip()
            if line:
                meta.append(json.loads(line))
    return index, meta
