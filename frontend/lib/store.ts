import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ChatSession, Finding, SubAgent, SuggestedAction, WSEvent } from "./types";

const newId = () => Math.random().toString(36).slice(2, 10);

type State = {
  sessions: ChatSession[];
  activeSessionId: string | null;
  expandedSubagentIds: Record<string, boolean>; // per-session: sessionId|subId
  selectedSubagentIds: Record<string, Record<string, boolean>>; // sessionId → subId → selected
  activeCitation: string | null;

  newSession: (title: string, opts?: { seedPrompt?: string }) => ChatSession;
  setActive: (id: string) => void;
  updateActiveTitle: (title: string) => void;
  consumeSeedPrompt: (sessionId: string) => string | null;
  handleEvent: (sessionId: string, ev: WSEvent) => void;
  closeSession: (sessionId: string, status: ChatSession["status"], error?: string) => void;
  toggleSubExpand: (sessionId: string, subId: string) => void;
  toggleSubSelect: (sessionId: string, subId: string) => void;
  setActiveCitation: (ref: string | null) => void;
  clearSelected: (sessionId: string) => void;
  /** Optimistically show planner state immediately on user send. */
  markSubmitting: (sessionId: string, prompt: string) => void;
  /** Delete a chat session entirely — both local and backend. */
  deleteSession: (sessionId: string) => void;
  /** Bulk-purge backend tickets that have no messages (empty 'New chat'). */
  cleanupEmptyTickets: () => Promise<number>;
  /** Merge any backend tickets that aren't already in the local store.
   * Used on /chat mount so server-side runs (scripts, other devices) show up. */
  hydrateFromBackend: () => Promise<void>;
  /** Replace a session's artifact/messages from a backend fetch — used when the
   * user opens a session we hydrated from backend (no live planner state). */
  rehydrateSessionFromBackend: (sessionId: string) => Promise<void>;
};

const blankSession = (title: string): ChatSession => ({
  id: newId(),
  title,
  created_at: Date.now(),
  subagents: [],
  artifact: { markdown: "", citation_refs: [], suggested_actions: [], complete: false },
  status: "idle",
});

export const useChatStore = create<State>()(persist((set, get) => ({
  sessions: [],
  activeSessionId: null,
  expandedSubagentIds: {},
  selectedSubagentIds: {},
  activeCitation: null,

  newSession: (title, opts) => {
    const s = blankSession(title);
    if (opts?.seedPrompt) s.pendingSeedPrompt = opts.seedPrompt;
    set((st) => ({ sessions: [s, ...st.sessions], activeSessionId: s.id }));
    return s;
  },

  consumeSeedPrompt: (sessionId) => {
    let prompt: string | null = null;
    set((st) => ({
      sessions: st.sessions.map((s) => {
        if (s.id !== sessionId) return s;
        prompt = s.pendingSeedPrompt || null;
        if (!prompt) return s;
        return { ...s, pendingSeedPrompt: undefined };
      }),
    }));
    return prompt;
  },

  setActive: (id) => set({ activeSessionId: id, activeCitation: null }),

  updateActiveTitle: (title) => set((st) => ({
    sessions: st.sessions.map((s) => (s.id === st.activeSessionId ? { ...s, title } : s)),
  })),

  handleEvent: (sessionId, ev) => {
    set((st) => {
      const idx = st.sessions.findIndex((s) => s.id === sessionId);
      if (idx === -1) return st;
      const s = { ...st.sessions[idx] };

      switch (ev.type) {
        case "stream_start":
          s.status = "running";
          break;
        case "planner_started":
          s.planner = { id: ev.id, name: ev.name, prompt: ev.prompt, text: "" };
          s.status = "running";
          break;
        case "stream_delta": {
          // Legacy event — append the streaming text to the planner card so the
          // user sees live progress even when no sub-agents fire (simple prompts).
          if (s.planner) {
            s.planner = { ...s.planner, text: s.planner.text + (ev.data ?? "") };
          }
          break;
        }
        case "agent_switch": {
          // Promote agent transitions in the legacy stream into running planner status.
          if (s.planner) s.planner = { ...s.planner, name: ev.agent };
          break;
        }
        case "tool_status": {
          // Surface as the planner's current activity hint (no text injection).
          if (s.planner) {
            (s.planner as any).activity = ev.label ?? ev.tool ?? "Working…";
          }
          break;
        }
        case "subagent_started": {
          const sub: SubAgent = {
            id: ev.id, letter: ev.letter, name: ev.name,
            parent_id: ev.parent_id, text: "", findings: [], status: "running",
          };
          // Avoid duplicate (re-entry case).
          if (!s.subagents.find((x) => x.id === sub.id)) s.subagents = [...s.subagents, sub];
          break;
        }
        case "subagent_delta": {
          if (ev.is_planner && s.planner) {
            s.planner = { ...s.planner, text: s.planner.text + ev.delta };
          } else {
            s.subagents = s.subagents.map((a) =>
              a.id === ev.id ? { ...a, text: a.text + ev.delta } : a
            );
          }
          break;
        }
        case "subagent_finished": {
          s.subagents = s.subagents.map((a) =>
            a.id === ev.id ? { ...a, findings: ev.findings ?? [], status: "finished" } : a
          );
          break;
        }
        case "artifact_chunk": {
          // Backend currently emits ONE artifact_chunk with the full final output.
          // Replace, don't append, so we don't double-write the text.
          s.artifact = {
            ...s.artifact,
            markdown: ev.markdown ?? "",
            citation_refs: Array.from(new Set([...s.artifact.citation_refs, ...(ev.citation_refs ?? [])])),
          };
          break;
        }
        case "artifact_complete": {
          s.artifact = {
            ...s.artifact,
            suggested_actions: ev.suggested_actions ?? [],
            citation_refs: ev.citation_refs ?? s.artifact.citation_refs,
            elapsed_seconds: ev.elapsed_seconds,
            complete: true,
          };
          s.status = "complete";
          break;
        }
        case "stream_end":
          if (s.status !== "error") s.status = "complete";
          // Fallback — if no artifact_chunk fired, promote the streamed planner
          // text into the artifact so the user sees the answer.
          if (!s.artifact.markdown && s.planner?.text) {
            s.artifact = { ...s.artifact, markdown: s.planner.text, complete: true };
          }
          break;
        case "error":
          s.status = "error";
          s.error = (ev as any).message || (ev as any).data || "unknown error";
          break;
      }

      const next = [...st.sessions];
      next[idx] = s;
      return { sessions: next };
    });
  },

  closeSession: (sessionId, status, error) => {
    set((st) => ({
      sessions: st.sessions.map((s) => (s.id === sessionId ? { ...s, status, error } : s)),
    }));
  },

  toggleSubExpand: (sessionId, subId) => set((st) => {
    const k = `${sessionId}|${subId}`;
    return { expandedSubagentIds: { ...st.expandedSubagentIds, [k]: !st.expandedSubagentIds[k] } };
  }),

  toggleSubSelect: (sessionId, subId) => set((st) => {
    const cur = st.selectedSubagentIds[sessionId] || {};
    return { selectedSubagentIds: { ...st.selectedSubagentIds, [sessionId]: { ...cur, [subId]: !cur[subId] } } };
  }),

  setActiveCitation: (ref) => set({ activeCitation: ref }),

  clearSelected: (sessionId) => set((st) => ({
    selectedSubagentIds: { ...st.selectedSubagentIds, [sessionId]: {} },
  })),

  markSubmitting: (sessionId, prompt) => set((st) => ({
    sessions: st.sessions.map((s) => {
      if (s.id !== sessionId) return s;
      // Show a planner card immediately so the user sees feedback. The backend's
      // planner_started event will overwrite this with the real agent name.
      return {
        ...s,
        status: "running",
        planner: s.planner ?? {
          id: "pending",
          name: "Planner",
          prompt,
          text: "",
          activity: "Connecting to the planner…",
        },
        artifact: { markdown: "", citation_refs: [], suggested_actions: [], complete: false },
        subagents: [],
      };
    }),
  })),

  deleteSession: (sessionId) => {
    // Fire backend delete (best-effort) before removing from local state so the
    // ticket disappears from /api/tickets next hydrate pass.
    const s = get().sessions.find((x) => x.id === sessionId);
    if (s?.ticket_id) {
      fetch(`/api/tickets/${s.ticket_id}`, { method: "DELETE", credentials: "include" })
        .catch(() => { /* ignore — local removal still happens */ });
    }
    set((st) => {
      const next = st.sessions.filter((x) => x.id !== sessionId);
      const nextActive = st.activeSessionId === sessionId
        ? (next[0]?.id ?? null)
        : st.activeSessionId;
      return { sessions: next, activeSessionId: nextActive };
    });
  },

  cleanupEmptyTickets: async () => {
    try {
      const r = await fetch("/api/v2/cleanup/empty-tickets", { method: "POST", credentials: "include" });
      if (r.ok) {
        const data = await r.json();
        // Remove any local sessions whose ticket_id got deleted.
        const deleted = new Set<string>(data.deleted_ticket_ids ?? []);
        set((st) => ({
          sessions: st.sessions.filter((s) => !s.ticket_id || !deleted.has(s.ticket_id)),
        }));
        return data.deleted_count ?? 0;
      }
    } catch { /* ignore */ }
    return 0;
  },

  hydrateFromBackend: async () => {
    try {
      // First, ask the server to reap stuck jobs older than 10 min so we don't
      // pull a 'running' status that's actually dead.
      try {
        await fetch("/api/v2/cleanup/stuck-jobs", { method: "POST", credentials: "include" });
      } catch { /* best-effort */ }

      const tickets = await fetchJSON<Array<{
        id: string; title: string; status: string; created_at: string; updated_at?: string;
      }>>("/api/tickets");
      set((st) => {
        const byTicket: Record<string, typeof tickets[number]> = {};
        tickets.forEach((t) => { byTicket[t.id] = t; });

        // (a) Update status of EXISTING sessions to match backend. Fixes
        // stuck 'running' rows when the WS missed stream_end.
        const updated = st.sessions.map((s) => {
          if (!s.ticket_id) return s;
          const t = byTicket[s.ticket_id];
          if (!t) return s;
          const backendStatus: ChatSession["status"] =
            t.status === "completed" || t.status === "closed" ? "complete" :
            t.status === "failed" ? "error" :
            t.status === "deleted" ? "error" :
            (s.status === "running" ? "running" : "idle");
          // Don't downgrade a session that's actively running in this tab.
          const nextStatus = s.status === "running" && backendStatus === "idle" ? "running" : backendStatus;
          // Title sync — server-side scripts often have richer titles
          const nextTitle = t.title && t.title !== "New chat" ? t.title : s.title;
          return { ...s, status: nextStatus, title: nextTitle };
        });

        // (b) Add any backend tickets we don't have locally yet.
        const knownTicketIds = new Set(
          updated.map((s) => s.ticket_id).filter(Boolean) as string[],
        );
        const incoming: ChatSession[] = [];
        for (const t of tickets) {
          if (knownTicketIds.has(t.id)) continue;
          if (t.status === "deleted") continue;
          incoming.push({
            id: newId(),
            ticket_id: t.id,
            title: t.title || "Untitled",
            created_at: t.created_at ? new Date(t.created_at).getTime() : Date.now(),
            subagents: [],
            artifact: { markdown: "", citation_refs: [], suggested_actions: [], complete: false },
            status: t.status === "completed" || t.status === "closed" ? "complete" :
                    t.status === "failed" ? "error" : "idle",
          });
        }

        const merged = [...updated, ...incoming].sort(
          (a, b) => b.created_at - a.created_at,
        );
        return { sessions: merged };
      });
    } catch (e) {
      // Network error or backend down — leave local state alone.
      // eslint-disable-next-line no-console
      console.warn("[store] hydrate failed:", e);
    }
  },

  rehydrateSessionFromBackend: async (sessionId) => {
    const st = get();
    const s = st.sessions.find((x) => x.id === sessionId);
    if (!s?.ticket_id) return;
    try {
      const detail = await fetchJSON<{
        title?: string;
        messages?: Array<{ role: string; content: string }>;
        artifacts?: Array<{ file_path: string }>;
      }>(`/api/tickets/${s.ticket_id}`);
      // Pull the last assistant message as the artifact body (best-effort).
      const assistantMsgs = (detail.messages ?? []).filter((m) => m.role === "assistant");
      const lastAssistant = assistantMsgs[assistantMsgs.length - 1]?.content || "";
      const userMsgs = (detail.messages ?? []).filter((m) => m.role === "user");
      const firstUser = userMsgs[0]?.content || "";

      set((st2) => ({
        sessions: st2.sessions.map((x) => {
          if (x.id !== sessionId) return x;
          return {
            ...x,
            planner: x.planner ?? (firstUser ? {
              id: "rehydrated",
              name: "Past run",
              prompt: firstUser,
              text: "",
              activity: undefined,
            } : x.planner),
            artifact: lastAssistant ? {
              markdown: lastAssistant,
              citation_refs: [],
              suggested_actions: [],
              complete: true,
            } : x.artifact,
            status: x.status === "idle" ? "complete" : x.status,
          };
        }),
      }));
    } catch (e) {
      // eslint-disable-next-line no-console
      console.warn("[store] rehydrate failed:", e);
    }
  },
}), {
  name: "sourcy-chat-store-v1",
  storage: createJSONStorage(() => (typeof window === "undefined" ? undefined : window.localStorage) as any),
  partialize: (state) => ({
    sessions: state.sessions.map((s) => ({
      id: s.id,
      ticket_id: s.ticket_id,
      title: s.title,
      created_at: s.created_at,
      status: s.status,
      // Preserve the result the user already saw so reload still shows it,
      // but skip transient sub-agent / streaming-deltas state to keep
      // localStorage small.
      planner: s.planner ? {
        id: s.planner.id,
        name: s.planner.name,
        prompt: s.planner.prompt,
        text: s.planner.text,
      } : undefined,
      artifact: s.artifact,
      subagents: [],
    })),
    activeSessionId: state.activeSessionId,
  }) as any,
  version: 1,
}));


async function fetchJSON<T>(url: string): Promise<T> {
  const r = await fetch(url, { credentials: "include" });
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}

export const selectActiveSession = (state: State): ChatSession | null =>
  state.sessions.find((s) => s.id === state.activeSessionId) ?? null;
