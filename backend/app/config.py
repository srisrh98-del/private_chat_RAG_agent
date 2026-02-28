"""App configuration - all local-only, no API keys."""
import os
from pathlib import Path

# Paths (relative to project root when running from run.sh)
PROJECT_ROOT = Path(os.environ.get("CHAT_AGENT_ROOT", Path(__file__).resolve().parent.parent.parent))
DATA_DIR = PROJECT_ROOT / "data" / "docs"
INDEX_DIR = PROJECT_ROOT / "index_data"
INDEX_FAISS = INDEX_DIR / "index.faiss"
INDEX_META = INDEX_DIR / "metadata.jsonl"
# Built frontend (when running as single server for the desktop app)
STATIC_DIR = PROJECT_ROOT / "frontend" / "dist"

# Ollama - localhost only
OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.2:3b"  # Fast, fits 24GB; alternatives: mistral:7b, phi3:mini

# Chunking
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

# Retrieval
DEFAULT_TOP_K = 10
OVERSAMPLE_FACTOR = 2  # retrieve more then filter by selected docs
RELEVANCE_THRESHOLD = 0.0  # tune; higher = stricter
MAX_CITATIONS_PER_PAGE = 2  # dedupe: max citations from same (doc, page)

# Server
HOST = "127.0.0.1"
PORT = 8000
DEBUG_LOG_PROMPTS = os.environ.get("CHAT_AGENT_DEBUG", "").lower() in ("1", "true", "yes")

# CORS - frontend dev port
CORS_ORIGINS = ["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:3000", "http://localhost:3000"]
