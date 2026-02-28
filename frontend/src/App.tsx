import { useState, useEffect, useCallback } from "react";
import { fetchPdfs, chat, reindex, health, pageImageUrl, type PdfItem, type Citation } from "./api";
import "./App.css";

type Message = {
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
  abstained?: boolean;
};

function App() {
  const [pdfs, setPdfs] = useState<PdfItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [indexStats, setIndexStats] = useState<{ docs: number; chunks: number } | null>(null);
  const [pageModal, setPageModal] = useState<{ docId: string; docName: string; page: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [healthMsg, setHealthMsg] = useState<string>("");

  const loadPdfs = useCallback(async () => {
    try {
      const list = await fetchPdfs();
      setPdfs(list);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load PDFs");
    }
  }, []);

  useEffect(() => {
    loadPdfs();
    health().then((h) => setHealthMsg(h.ollama)).catch(() => setHealthMsg("Backend unreachable"));
  }, [loadPdfs]);

  const togglePdf = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    if (selectedIds.size === pdfs.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(pdfs.map((p) => p.id)));
  };

  const handleReindex = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await reindex();
      setIndexStats({ docs: res.num_docs, chunks: res.num_chunks });
      if (res.warnings.length) setError(res.warnings.join("; "));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reindex failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    setError(null);
    try {
      const selected = selectedIds.size > 0 ? Array.from(selectedIds) : null;
      const res = await chat(q, selected, 10);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: res.answer,
          citations: res.citations,
          abstained: res.abstained,
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chat failed");
      setMessages((m) => [...m, { role: "assistant", text: "Sorry, something went wrong." }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Chat Agent</h1>
        <span className="health" title={healthMsg}>
          {healthMsg === "ok" ? "● Ready" : `○ ${healthMsg.slice(0, 40)}…`}
        </span>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <div className="sidebar-section">
            <h2>Documents</h2>
            <button type="button" className="btn secondary" onClick={loadPdfs}>
              Refresh list
            </button>
            {pdfs.length > 0 && (
              <button type="button" className="btn secondary" onClick={selectAll}>
                {selectedIds.size === pdfs.length ? "Deselect all" : "Select all"}
              </button>
            )}
            <ul className="pdf-list">
              {pdfs.map((p) => (
                <li key={p.id} className={selectedIds.has(p.id) ? "selected" : ""}>
                  <label>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(p.id)}
                      onChange={() => togglePdf(p.id)}
                    />
                    <span className="pdf-name">{p.name}</span>
                  </label>
                </li>
              ))}
            </ul>
            {pdfs.length === 0 && <p className="muted">Place PDFs in data/docs/</p>}
            <p className="muted selection-hint">
              {selectedIds.size === 0
                ? "Search across all PDFs"
                : `${selectedIds.size} selected`}
            </p>
          </div>
          <div className="sidebar-section">
            <h2>Index</h2>
            <button
              type="button"
              className="btn primary"
              onClick={handleReindex}
              disabled={loading}
            >
              {loading ? "Building…" : "Build / Rebuild index"}
            </button>
            {indexStats && (
              <p className="stats">
                {indexStats.docs} docs, {indexStats.chunks} chunks
              </p>
            )}
          </div>
        </aside>

        <main className="main">
          {error && (
            <div className="banner error" role="alert">
              {error}
            </div>
          )}
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                <div className="message-text">{msg.text}</div>
                {msg.citations && msg.citations.length > 0 && (
                  <ul className="citations">
                    {msg.citations.map((c, j) => (
                      <li key={j} className="citation">
                        <span className="cite-label">
                          {c.doc_name}, p.{c.page}
                        </span>
                        <span className="cite-snippet">{c.text.slice(0, 120)}…</span>
                        <button
                          type="button"
                          className="btn link"
                          onClick={() =>
                            setPageModal({ docId: c.doc_id, docName: c.doc_name, page: c.page })
                          }
                        >
                          Open page
                        </button>
                        <a
                          href={pageImageUrl(c.doc_id, c.page)}
                          download={`${c.doc_name}_p${c.page}.png`}
                          className="btn link"
                        >
                          Download PNG
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
          <div className="chat-input-row">
            <input
              type="text"
              className="chat-input"
              placeholder="Ask a question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              disabled={loading}
            />
            <button
              type="button"
              className="btn primary"
              onClick={handleSend}
              disabled={loading || !input.trim()}
            >
              {loading ? "…" : "Send"}
            </button>
            <button type="button" className="btn secondary" onClick={clearChat}>
              Clear chat
            </button>
          </div>
        </main>
      </div>

      {pageModal && (
        <div
          className="modal-overlay"
          onClick={() => setPageModal(null)}
          role="dialog"
          aria-modal="true"
          aria-label="Cited page"
        >
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                {pageModal.docName} — Page {pageModal.page}
              </h3>
              <button type="button" className="btn icon" onClick={() => setPageModal(null)}>
                ×
              </button>
            </div>
            <img
              src={pageImageUrl(pageModal.docId, pageModal.page)}
              alt={`Page ${pageModal.page}`}
              className="page-image"
            />
            <a
              href={pageImageUrl(pageModal.docId, pageModal.page)}
              download={`${pageModal.docName}_p${pageModal.page}.png`}
              className="btn primary"
            >
              Download page as PNG
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
