const BASE = import.meta.env.VITE_API_URL ?? "";

export interface Source {
  n: number;
  file_name: string;
  source: string;
  area: string;
  doc_type?: string;
  version?: string;
  page?: number;
  score: number;
  snippet: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  no_info: boolean;
  status: string;
  session_id: string;
}

export async function sendChat(
  message: string,
  sessionId: string,
  areas: string,
): Promise<ChatResponse> {
  const r = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-User-Areas": areas },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!r.ok) {
    const detail = (await r.json().catch(() => null))?.detail;
    throw new Error(detail ?? `HTTP ${r.status}`);
  }
  return r.json();
}

export const getAreas = (): Promise<{ areas: string[] }> =>
  fetch(`${BASE}/api/areas`).then((r) => r.json());

export interface ComplianceResult {
  file_name: string;
  verdict: "cumple" | "parcial" | "no_cumple" | "indeterminado";
  report: string;
  sources: Source[];
}

export async function checkCompliance(file: File, areas: string): Promise<ComplianceResult> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("areas", areas);
  const r = await fetch(`${BASE}/api/compliance`, {
    method: "POST",
    headers: { "X-User-Areas": areas },
    body: fd,
  });
  if (!r.ok) {
    const detail = (await r.json().catch(() => null))?.detail;
    throw new Error(detail ?? `HTTP ${r.status}`);
  }
  return r.json();
}
