import type { MemoryState } from "./types";
import { apiUrl } from "./backendUrl";

const API = "/api/v2";

function v2(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return apiUrl(`/api/v2${p}`);
}

/** Drill-down detail for Home briefing cards (alerts, recommendations). */
export type BriefingDetail = {
  cause: string;
  evidence: string;
  pages: string[];
  suggestion: string;
  next_step: string;
};

export type BriefingItem = {
  text: string;
  severity?: "urgent" | "important" | "info";
  priority?: "high" | "medium" | "low";
  source: string;
  detail?: BriefingDetail;
};

export type KpiTrendPoint = { date: string; raw_date?: string; value: number };
export type KpiTrendDriver = { label: string; current: number; previous: number; change_pct: number };
export type KpiTrendResponse = {
  kpi_key: string;
  label: string;
  source: string;
  series: KpiTrendPoint[];
  delta_pct?: number | null;
  total_current?: number | null;
  unit?: string;
  drivers: KpiTrendDriver[];
  explanation: string;
  explanation_bullets?: string[];
  related_insights?: string[];
  error?: string | null;
};

async function jsonFetch<T = any>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!r.ok) {
    const restartHint = r.status === 404 ? " Restart the backend: python main.py" : "";
    throw new Error(`${r.status} ${r.statusText}.${restartHint}`);
  }
  return r.json();
}

export const api = {
  memoryState: () => jsonFetch<MemoryState>(v2("/memory/state")),
  savePersona: (persona: Record<string, any>, name = "sourcy") =>
    jsonFetch(v2("/setup/persona"), { method: "POST", body: JSON.stringify({ name, persona }) }),
  saveDesignSystem: (design_system: Record<string, any>, name = "sourcy") =>
    jsonFetch(v2("/setup/design-system"), { method: "POST", body: JSON.stringify({ name, design_system }) }),
  uploadAsset: async (file: File, asset_type = "logo", tag = "") => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("asset_type", asset_type);
    fd.append("tag", tag);
    const r = await fetch(v2("/setup/upload-asset"), { method: "POST", body: fd, credentials: "include" });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json() as Promise<{ ok: boolean; url: string; asset_type: string; tag: string }>;
  },
  homeRefresh: () => jsonFetch<{ seed_prompt: string; agents_to_dispatch: string[] }>(v2("/home/refresh")),
  homeSnapshot: (force = false) =>
    jsonFetch<{
      snapshot: {
        status?: string;
        generated_at?: number;
        elapsed_seconds?: number;
        kpis: Array<{ label: string; value: string | number; delta_pct?: number; source: string }>;
        insights: Array<{ text: string; severity: "urgent" | "important" | "info"; source: string; detail?: BriefingDetail }>;
        top_movers: Array<{ text: string; kind?: string; source: string }>;
        alerts: Array<BriefingItem & { severity: "urgent" | "important" | "info" }>;
        recommendations?: Array<BriefingItem & { priority: "high" | "medium" | "low" }>;
      };
      dashboard: null | { url: string; generated_at: number; size_kb: number };
      stale: boolean;
      refreshing: boolean;
    }>(v2(`/home/snapshot${force ? "?force=true" : ""}`)),
  homeForceRefresh: () => jsonFetch<{ ok: boolean; queued: boolean }>(v2("/home/refresh"), { method: "POST" }),
  kpiTrend: (label: string, source: string) =>
    jsonFetch<KpiTrendResponse>(
      v2(`/home/kpi-trend?${new URLSearchParams({ label, source })}`),
    ),
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
    }>(v2(`/library/${type}`)),

  sessionArtifacts: (ticket_id: string) =>
    jsonFetch<{
      ticket_id: string;
      ticket_title: string | null;
      count: number;
      artifacts: Array<{ url: string; name: string; kind: "image" | "html" | "doc"; ext: string; created_at?: string }>;
    }>(v2(`/sessions/${ticket_id}/artifacts`)),
  dispatch: (action_id: string, body: {
    selected_findings?: any[];
    selected_agents?: string[];
    channel?: string;
    subject?: string;
    customer_name?: string;
    ticket_id?: string;
  }) =>
    jsonFetch<{ ok: boolean; target_skill?: string; seed_prompt?: string; error?: string }>(
      v2(`/dispatch/${action_id}`),
      { method: "POST", body: JSON.stringify(body) },
    ),

  // Legacy ticket API (the existing FastAPI endpoints we re-use for ticket-scoped WS)
  createTicket: (title: string, created_by: string) =>
    jsonFetch<{ id: string }>(apiUrl("/api/tickets"), { method: "POST", body: JSON.stringify({ title, created_by }) }),
};
