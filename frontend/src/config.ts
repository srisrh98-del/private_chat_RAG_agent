// In production (desktop app), same origin; in dev, backend on 8000
const API_BASE =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.PROD ? "" : "http://127.0.0.1:8000");

export function apiUrl(path: string, params?: Record<string, string>): string {
  const base = API_BASE || window.location.origin;
  const u = new URL(path, base);
  if (params) {
    Object.entries(params).forEach(([k, v]) => u.searchParams.set(k, v));
  }
  return u.toString();
}

export { API_BASE };
