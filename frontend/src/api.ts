import { apiUrl } from "./config";

export type PdfItem = { id: string; name: string; path: string };

export async function fetchPdfs(): Promise<PdfItem[]> {
  const r = await fetch(apiUrl("/pdfs"));
  if (!r.ok) throw new Error("Failed to list PDFs");
  return r.json();
}

export async function chat(
  question: string,
  selectedDocs: string[] | null,
  topK: number = 10
): Promise<{ answer: string; citations: Citation[]; abstained: boolean }> {
  const r = await fetch(apiUrl("/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      selected_docs: selectedDocs?.length ? selectedDocs : null,
      top_k: topK,
    }),
  });
  if (!r.ok) throw new Error("Chat request failed");
  return r.json();
}

export type Citation = {
  doc_id: string;
  doc_name: string;
  page: number;
  text: string;
  score: number;
};

export function pageImageUrl(docId: string, page: number): string {
  return apiUrl("/page", { doc: docId, page: String(page) });
}

export async function reindex(): Promise<{
  num_docs: number;
  num_chunks: number;
  warnings: string[];
}> {
  const r = await fetch(apiUrl("/admin/reindex"), { method: "POST" });
  if (!r.ok) throw new Error("Reindex failed");
  return r.json();
}

export async function health(): Promise<{ status: string; ollama: string }> {
  const r = await fetch(apiUrl("/health"));
  if (!r.ok) throw new Error("Health check failed");
  return r.json();
}
