"""Ollama client - localhost only, no proxy/env for API keys."""
from __future__ import annotations

import json
import requests
from typing import Optional

from .config import OLLAMA_BASE, EMBED_MODEL, CHAT_MODEL, DEBUG_LOG_PROMPTS


def _session() -> requests.Session:
    s = requests.Session()
    s.trust_env = False  # do not use HTTP_PROXY for Ollama
    s.headers.update({"Content-Type": "application/json"})
    return s


def check_ollama() -> tuple[bool, str]:
    """Returns (ok, message)."""
    try:
        r = _session().get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        if r.status_code != 200:
            return False, f"Ollama returned {r.status_code}"
        data = r.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        has_embed = any(EMBED_MODEL in n for n in models)
        has_chat = any(CHAT_MODEL in n or CHAT_MODEL.split(":")[0] in n for n in models)
        if not has_embed:
            return False, f"Embedding model '{EMBED_MODEL}' not found. Run: ollama pull {EMBED_MODEL}"
        if not has_chat:
            return False, f"Chat model '{CHAT_MODEL}' not found. Run: ollama pull {CHAT_MODEL}"
        return True, "ok"
    except requests.RequestException as e:
        return False, f"Cannot reach Ollama at {OLLAMA_BASE}: {e}"


def embed(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a list of texts. Local only."""
    if not texts:
        return []
    out = []
    # Ollama embed API often takes one at a time or batch
    for t in texts:
        r = _session().post(
            f"{OLLAMA_BASE}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": t},
            timeout=120,
        )
        r.raise_for_status()
        out.append(r.json()["embedding"])
    return out


def chat(user_message: str, system_prompt: str, context: str) -> str:
    """Single turn completion. No streaming for v1. Returns assistant text."""
    body = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }
    if context:
        body["messages"][1]["content"] = f"Context from documents:\n\n{context}\n\nUser question: {user_message}"

    if DEBUG_LOG_PROMPTS:
        print("[DEBUG] system:", system_prompt[:200], "...")
        print("[DEBUG] user (with context):", body["messages"][1]["content"][:500], "...")

    r = _session().post(f"{OLLAMA_BASE}/api/chat", json=body, timeout=180)
    r.raise_for_status()
    data = r.json()
    return data.get("message", {}).get("content", "").strip()
