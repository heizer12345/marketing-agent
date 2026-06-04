import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ChatSession, ChatTurn, Finding, SubAgent, SuggestedAction, WSEvent } from "./types";

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
  /** Persist backend ticket id on the session (avoids duplicate sidebar rows on hydrate). */
  linkTicketId: (sessionId: string, ticketId: string) => void;
  /** Delete a chat session entirely — both local and backend. */
  deleteSession: (sessionId: string) => void;
  /** Bulk-purge backend tickets that have no messages (empty 'New chat'). */
  cleanupEmptyTickets: () => Promise<number>;
  /** Remove broken / duplicate / empty sessions from the sidebar. */
  pruneBrokenSessions: () => Promise<number>;
  /** Merge any backend tickets that aren't already in the local store.
   * Used on /chat mount so server-side runs (scripts, other devices) show up. */
  hydrateFromBackend: () => Promise<void>;
  /** Replace a session's artifact/messages from a backend fetch — used when the
   * user opens a session we hydrated from backend (no live planner state). */
  rehydrateSessionFromBackend: (sessionId: string) => Promise<void>;
};

const emptyArtifact = (): ChatSession["artifact"] => ({
  markdown: "",
  citation_refs: [],
  suggested_actions: [],
  complete: false,
});

const blankSession = (title: string): ChatSession => ({
  id: newId(),
  title,
  created_at: Date.now(),
  turns: [],
  subagents: [],
  artifact: emptyArtifact(),
  status: "idle",
});

/** Move the current planner + artifact into turns before starting a new message. */
function archiveCurrentTurn(s: ChatSession): ChatTurn[] {
  const turns = [...(s.turns ?? [])];
  const prompt = s.planner?.prompt?.trim();
  if (!prompt) return turns;
  const answer = (s.artifact?.markdown || s.planner?.text || "").trim();
  if (!answer) return turns;
  const last = turns[turns.length - 1];
  if (last?.userPrompt === prompt && last?.assistantMarkdown === answer) return turns;
  turns.push({
    id: newId(),
    userPrompt: prompt,
    assistantMarkdown: answer,
    created_at: Date.now(),
  });
  return turns;
}

/** Build turns from backend ticket messages (user/assistant pairs). */
function turnsFromMessages(messages: Array<{ role: string; content: string }>): {
  turns: ChatTurn[];
  pendingUser: string | null;
  lastAssistant: string | null;
} {
  const turns: ChatTurn[] = [];
  let pendingUser: string | null = null;
  let lastAssistant: string | null = null;

  for (const m of messages) {
    if (m.role === "user") {
      if (pendingUser) {
        turns.push({
          id: newId(),
          userPrompt: pendingUser,
          assistantMarkdown: lastAssistant || "",
          created_at: Date.now(),
        });
        lastAssistant = null;
      }
      pendingUser = m.content;
    } else if (m.role === "assistant") {
      lastAssistant = m.content;
    }
  }

  if (pendingUser && lastAssistant) {
    turns.push({
      id: newId(),
      userPrompt: pendingUser,
      assistantMarkdown: lastAssistant,
      created_at: Date.now(),
    });
    pendingUser = null;
    lastAssistant = null;
  }

  return { turns, pendingUser, lastAssistant };
}

function dedupeSessionsByTicket(sessions: ChatSession[]): ChatSession[] {
  const byTicket = new Map<string, ChatSession>();
  const out: ChatSession[] = [];
  for (const s of sessions) {
    if (!s.ticket_id) {
      out.push(s);
      continue;
    }
    const prev = byTicket.get(s.ticket_id);
    if (!prev) {
      byTicket.set(s.ticket_id, s);
      out.push(s);
      continue;
    }
    // Keep the session with more content / turns
    const score = (x: ChatSession) =>
      (x.turns?.length ?? 0) + (x.artifact?.markdown ? 1 : 0) + (x.planner ? 1 : 0);
    if (score(s) > score(prev)) {
      const idx = out.indexOf(prev);
      if (idx >= 0) out[idx] = s;
      byTicket.set(s.ticket_id, s);
    }
  }
  return out;
}

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

  linkTicketId: (sessionId, ticketId) => set((st) => ({
    sessions: st.sessions.map((s) =>
      s.id === sessionId ? { ...s, ticket_id: ticketId } : s,
    ),
  })),

  markSubmitting: (sessionId, prompt) => set((st) => ({
    sessions: st.sessions.map((s) => {
      if (s.id !== sessionId) return s;
      const turns = archiveCurrentTurn(s);
      return {
        ...s,
        turns,
        status: "running",
        planner: {
          id: "pending",
          name: "Planner",
          prompt,
          text: "",
          activity: "Connecting to the planner…",
        },
        artifact: emptyArtifact(),
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
        const deleted = new Set<string>(data.deleted_ticket_ids ?? []);
        set((st) => ({
          sessions: dedupeSessionsByTicket(
            st.sessions.filter((s) => !s.ticket_id || !deleted.has(s.ticket_id)),
          ),
        }));
        return data.deleted_count ?? 0;
      }
    } catch { /* ignore */ }
    return 0;
  },

  pruneBrokenSessions: async () => {
    let backendDeleted = new Set<string>();
    try {
      const r = await fetch("/api/v2/cleanup/broken-tickets", { method: "POST", credentials: "include" });
      if (r.ok) {
        const data = await r.json();
        backendDeleted = new Set<string>(data.deleted_ticket_ids ?? []);
      }
    } catch { /* ignore */ }

    let removed = 0;
    set((st) => {
      const before = st.sessions.length;
      const kept = st.sessions.filter((s) => {
        if (s.ticket_id && backendDeleted.has(s.ticket_id)) return false;
        if (s.status === "error") return false;
        const empty =
          !s.ticket_id &&
          (s.turns?.length ?? 0) === 0 &&
          !s.planner &&
          !s.artifact?.markdown &&
          s.title === "New chat";
        if (empty) return false;
        const stuck =
          s.status === "running" &&
          !s.planner?.text &&
          !s.artifact?.markdown &&
          (s.turns?.length ?? 0) === 0;
        if (stuck) return false;
        return true;
      });
      const sessions = dedupeSessionsByTicket(kept);
      removed = before - sessions.length;
      const activeStill = sessions.some((x) => x.id === st.activeSessionId);
      return {
        sessions,
        activeSessionId: activeStill ? st.activeSessionId : (sessions[0]?.id ?? null),
      };
    });
    return removed;
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
          // Keep local "running" only when the server still looks in-flight.
          const nextStatus =
            s.status === "running" && backendStatus === "idle" ? "running" :
            s.status === "running" && backendStatus === "complete" ? "complete" :
            backendStatus;
          // Title sync — server-side scripts often have richer titles
          const nextTitle = t.title && t.title !== "New chat" ? t.title : s.title;
          return { ...s, status: nextStatus, title: nextTitle };
        });

        // (b) Link orphan local sessions to backend tickets (same title, no ticket_id).
        const claimedTickets = new Set(
          updated.map((s) => s.ticket_id).filter(Boolean) as string[],
        );
        const linked = updated.map((s) => {
          if (s.ticket_id) return s;
          const match = tickets.find(
            (t) =>
              t.status !== "deleted" &&
              t.title &&
              t.title === s.title &&
              !claimedTickets.has(t.id),
          );
          if (match) {
            claimedTickets.add(match.id);
            return { ...s, ticket_id: match.id };
          }
          return s;
        });

        const knownTicketIds = new Set(
          linked.map((s) => s.ticket_id).filter(Boolean) as string[],
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
            turns: [],
            subagents: [],
            artifact: emptyArtifact(),
            status: t.status === "completed" || t.status === "closed" ? "complete" :
                    t.status === "failed" ? "error" : "idle",
          });
        }

        const merged = dedupeSessionsByTicket(
          [...linked, ...incoming].sort((a, b) => b.created_at - a.created_at),
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
        status?: string;
        messages?: Array<{ role: string; content: string }>;
        artifacts?: Array<{ file_path: string }>;
      }>(`/api/tickets/${s.ticket_id}`);

      const msgs = detail.messages ?? [];
      const { turns, pendingUser, lastAssistant } = turnsFromMessages(msgs);
      const done =
        detail.status === "completed" ||
        detail.status === "closed" ||
        (!!lastAssistant && !pendingUser);

      set((st2) => ({
        sessions: st2.sessions.map((x) => {
          if (x.id !== sessionId) return x;
          const isRunning = x.status === "running" && !done;

          // Upgrade legacy sessions: one visible exchange → first turn in history.
          if (
            !isRunning &&
            (x.turns?.length ?? 0) === 0 &&
            x.artifact?.markdown &&
            x.planner?.prompt &&
            msgs.length <= 2
          ) {
            return {
              ...x,
              turns: archiveCurrentTurn(x),
              planner: undefined,
              artifact: emptyArtifact(),
              status: "complete",
            };
          }

          if (isRunning && x.planner) {
            return {
              ...x,
              turns: turns.length > (x.turns?.length ?? 0) ? turns : x.turns,
            };
          }

          if (pendingUser && !lastAssistant) {
            return {
              ...x,
              turns,
              planner: x.planner ?? {
                id: "rehydrated",
                name: "Planner",
                prompt: pendingUser,
                text: "",
              },
              artifact: x.artifact?.markdown ? x.artifact : emptyArtifact(),
              status: isRunning ? x.status : "complete",
            };
          }

          if (pendingUser && lastAssistant) {
            return {
              ...x,
              turns: [
                ...turns,
                {
                  id: newId(),
                  userPrompt: pendingUser,
                  assistantMarkdown: lastAssistant,
                  created_at: Date.now(),
                },
              ],
              planner: undefined,
              artifact: emptyArtifact(),
              status: "complete",
            };
          }

          return {
            ...x,
            turns,
            planner: undefined,
            artifact: emptyArtifact(),
            status: done ? "complete" : x.status,
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
      turns: s.turns ?? [],
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
  version: 2,
  migrate: (persisted: any, version) => {
    if (version < 2 && persisted?.sessions) {
      persisted.sessions = persisted.sessions.map((s: ChatSession) => ({
        ...s,
        turns: s.turns ?? [],
      }));
    }
    return persisted as any;
  },
}));


async function fetchJSON<T>(url: string): Promise<T> {
  const r = await fetch(url, { credentials: "include" });
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}

export const selectActiveSession = (state: State): ChatSession | null =>
  state.sessions.find((s) => s.id === state.activeSessionId) ?? null;
