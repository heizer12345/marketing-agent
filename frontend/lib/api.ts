import type { MemoryState } from "./types";

const API = "/api/v2";

async function jsonFetch<T = any>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export const api = {
  memoryState: () => jsonFetch<MemoryState>(`${API}/memory/state`),
  savePersona: (persona: Record<string, any>, name = "sourcy") =>
    jsonFetch(`${API}/setup/persona`, { method: "POST", body: JSON.stringify({ name, persona }) }),
  saveDesignSystem: (design_system: Record<string, any>, name = "sourcy") =>
    jsonFetch(`${API}/setup/design-system`, { method: "POST", body: JSON.stringify({ name, design_system }) }),
  uploadAsset: async (file: File, asset_type = "logo", tag = "") => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("asset_type", asset_type);
    fd.append("tag", tag);
    const r = await fetch(`${API}/setup/upload-asset`, { method: "POST", body: fd, credentials: "include" });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json() as Promise<{ ok: boolean; url: string; asset_type: string; tag: string }>;
  },
  homeRefresh: () => jsonFetch<{ seed_prompt: string; agents_to_dispatch: string[] }>(`${API}/home/refresh`),
  homeSnapshot: (force = false) =>
    jsonFetch<{
      snapshot: {
        status?: string;
        generated_at?: number;
        elapsed_seconds?: number;
        kpis: Array<{ label: string; value: string | number; delta_pct?: number; source: string }>;
        insights: Array<{ text: string; severity: "urgent" | "important" | "info"; source: string }>;
        top_movers: Array<{ text: string; kind?: string; source: string }>;
        alerts: Array<{ text: string; severity: "urgent" | "important" | "info"; source: string }>;
        recommendations?: Array<{ text: string; priority: "high" | "medium" | "low"; source: string }>;
      };
      dashboard: null | { url: string; generated_at: number; size_kb: number };
      stale: boolean;
      refreshing: boolean;
    }>(`${API}/home/snapshot${force ? "?force=true" : ""}`),
  homeForceRefresh: () => jsonFetch<{ ok: boolean; queued: boolean }>(`${API}/home/refresh`, { method: "POST" }),
  library: (type: string) =>
    jsonFetch<{
      type: string;
      count: number;
      items: Array<{
        name: string;
        path: string;
        size_bytes: number;
        modified: number;
        ext: string;
        from_session?: { ticket_id: string; ticket_title: string };
      }>;
    }>(`${API}/library/${type}`),

  sessionArtifacts: (ticket_id: string) =>
    jsonFetch<{
      ticket_id: string;
      ticket_title: string | null;
      count: number;
      artifacts: Array<{ url: string; name: string; kind: "image" | "html" | "doc"; ext: string; created_at?: string }>;
    }>(`${API}/sessions/${ticket_id}/artifacts`),
  dispatch: (action_id: string, body: {
    selected_findings?: any[];
    selected_agents?: string[];
    channel?: string;
    subject?: string;
    customer_name?: string;
    ticket_id?: string;
  }) =>
    jsonFetch<{ ok: boolean; target_skill?: string; seed_prompt?: string; error?: string }>(
      `${API}/dispatch/${action_id}`,
      { method: "POST", body: JSON.stringify(body) },
    ),

  // Legacy ticket API (the existing FastAPI endpoints we re-use for ticket-scoped WS)
  createTicket: (title: string, created_by: string) =>
    jsonFetch<{ id: string }>(`/api/tickets`, { method: "POST", body: JSON.stringify({ title, created_by }) }),
};
