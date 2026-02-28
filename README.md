# Chat Agent (Private PDF Reader)

Desktop-style app to chat with your PDF documents. **Runs fully offline** after setup: no API keys, no external inference or embeddings.

## Stack

- **Backend:** FastAPI on `127.0.0.1:8000`
- **Frontend:** React (Vite) on `127.0.0.1:5173`
- **LLM + embeddings:** Ollama (localhost)
- **Vector store:** FAISS (local files in `index_data/`)
- **PDFs:** PyMuPDF (text + page images)

## Install (macOS, Apple Silicon)

### 1. Ollama

```bash
brew install ollama
ollama serve   # or run Ollama app; keep it running
ollama pull nomic-embed-text
ollama pull llama3.2:3b
```

Other chat options (pick one): `ollama pull mistral:7b` or `ollama pull phi3:mini`.

### 2. Python (backend)

```bash
cd /path/to/chat-agent
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

Run backend from project root so `data/` and `index_data/` resolve:

```bash
export CHAT_AGENT_ROOT=/path/to/chat-agent
cd backend && python -c "from app.main import app"  # sanity check
```

### 3. Node (frontend)

```bash
cd frontend
npm install
```

## Run

**One command (from project root):**

```bash
chmod +x run.sh
./run.sh
```

Or manually:

```bash
export CHAT_AGENT_ROOT="$(pwd)"
cd backend && ../backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
# In another terminal:
cd frontend && npm run dev
```

Then open **http://127.0.0.1:5173**.

## Desktop app (double-click to run)

The app opens in **its own window** (not Safari or Chrome), with the server starting automatically.

1. **One-time:** Build the frontend and create the desktop app:
   ```bash
   chmod +x build-app.sh
   ./build-app.sh
   ```
2. **Use it:** Double-click **Chat Agent.app** in the project folder. A “Starting server…” message appears, then the Chat Agent window opens with the full UI.
3. **Important:** Keep **Chat Agent.app** inside the `chat-agent` project folder (it needs the `backend`, `data`, and `frontend` folders). You can drag a copy to Applications; that copy still needs the project folder to exist (e.g. `~/chat-agent`).

To quit: close the Chat Agent window; the server stops automatically. No Terminal window is shown.

## Usage

1. Put PDFs in **`data/docs/`** (create the folder if needed).
2. In the app, click **Build / Rebuild index**. Wait for “X docs, Y chunks”.
3. Optionally **select specific PDFs** (multi-select). If none selected, search is across all.
4. Type a question and **Send**. Answers include citations (doc name + page + snippet).
5. Use **Open page** on a citation to view the PDF page image; **Download PNG** to save it.
6. **Clear chat** resets the conversation (in-session only).

## API (localhost)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health + Ollama status |
| GET | `/pdfs` | List PDFs in `data/docs/` |
| POST | `/chat` | Body: `{ "question", "selected_docs"?, "top_k"? }` |
| GET | `/page?doc=...&page=N` | PNG bytes for cited page |
| POST | `/admin/reindex` | Rebuild FAISS index |

## Testing checklist

- [ ] **Health:** `curl http://127.0.0.1:8000/health` → `{"status":"ok","ollama":"ok"}` (or degraded if Ollama not running).
- [ ] **PDFs:** Add a PDF to `data/docs/`, then `curl http://127.0.0.1:8000/pdfs` → list includes the file.
- [ ] **Reindex:** POST to `/admin/reindex` → `num_docs` ≥ 1, `num_chunks` ≥ 1.
- [ ] **Chat:** POST to `/chat` with `{"question":"What is this document about?"}` → `answer` and optional `citations`.
- [ ] **Abstain:** Ask something unrelated → answer contains “I don’t have enough information”.
- [ ] **Page:** `curl "http://127.0.0.1:8000/page?doc=your.pdf&page=1" -o out.png` → valid PNG.
- [ ] **Path traversal:** `curl "http://127.0.0.1:8000/page?doc=../etc/passwd&page=1"` → 400.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| **Ollama not running** | Start with `ollama serve` or open Ollama app. Check `curl http://127.0.0.1:11434/api/tags`. |
| **Model missing** | `ollama pull nomic-embed-text` and `ollama pull llama3.2:3b` (or your chosen chat model). |
| **CORS errors in browser** | Backend allows `http://127.0.0.1:5173` and `localhost:5173`. Use one of these for the frontend. |
| **Index missing / empty** | Put PDFs in `data/docs/`, click “Build / Rebuild index”, wait for completion. |
| **Scanned PDF (no text)** | v1 uses text only. You’ll see a warning after indexing. For v2, consider Tesseract OCR. |
| **Backend “module not found”** | Run uvicorn from `backend` with `CHAT_AGENT_ROOT` set to project root: `cd backend && CHAT_AGENT_ROOT=/path/to/chat-agent uvicorn app.main:app --host 127.0.0.1 --port 8000`. |

## Folder structure

```
chat-agent/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── pdf_processor.py
│   │   ├── indexer.py
│   │   ├── retriever.py
│   │   ├── chat.py
│   │   ├── ollama_client.py
│   │   └── routes/
│   ├── requirements.txt
│   └── venv/                 # after install
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   └── config.ts
│   └── package.json
├── data/
│   └── docs/                 # put PDFs here
├── index_data/               # FAISS + metadata (created on first index)
├── run.sh
├── install.sh
└── README.md
```

## v2 ideas

- Incremental indexing (only new/changed PDFs).
- Optional local password / multi-user.
- Streaming chat responses.
- Section-aware chunking.
- Reranking (local cross-encoder).
- Hybrid search (BM25 + vectors).
- Package as desktop app (Tauri/Electron).
