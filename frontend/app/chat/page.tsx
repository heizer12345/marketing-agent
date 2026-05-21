"use client";

import { useEffect, useState } from "react";
import { useChatStore, selectActiveSession } from "@/lib/store";
import { api } from "@/lib/api";
import { useAgentStream } from "@/lib/useAgentStream";
import { SessionList } from "@/components/chat/SessionList";
import { PromptBar } from "@/components/chat/PromptBar";
import { PlannerCard } from "@/components/chat/PlannerCard";
import { ArtifactCanvas } from "@/components/chat/ArtifactCanvas";
import { StepsRail } from "@/components/chat/StepsRail";
import { ActionBar } from "@/components/chat/ActionBar";
import { SessionArtifacts } from "@/components/chat/SessionArtifacts";

export default function ChatPage() {
  const sessions = useChatStore((s) => s.sessions);
  const active = useChatStore(selectActiveSession);
  const newSession = useChatStore((s) => s.newSession);
  const setActive = useChatStore((s) => s.setActive);
  const updateTitle = useChatStore((s) => s.updateActiveTitle);
  const markSubmitting = useChatStore((s) => s.markSubmitting);
  const deleteSession = useChatStore((s) => s.deleteSession);
  const hydrateFromBackend = useChatStore((s) => s.hydrateFromBackend);
  const rehydrateSessionFromBackend = useChatStore((s) => s.rehydrateSessionFromBackend);

  const [ticketId, setTicketId] = useState<string | null>(null);
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);
  // Right rail is hidden by default — opens automatically when 1+ sub-agent fires.
  const [stepsOpen, setStepsOpen] = useState(false);
  const [stepsUserToggled, setStepsUserToggled] = useState(false);

  // Only adopt the active session's existing ticket. We DO NOT create a ticket
  // upfront — that floods the DB with empty 'New chat' rows. The ticket is
  // created lazily on first prompt submit (see submit() below).
  useEffect(() => {
    if (!active) { setTicketId(null); return; }
    setTicketId(active.ticket_id ?? null);
  }, [active?.id, active?.ticket_id]);

  const { connected, sendPrompt } = useAgentStream(active?.id || "", ticketId);
  const consumeSeed = useChatStore((s) => s.consumeSeedPrompt);

  useEffect(() => {
    if (!pendingPrompt || !connected) return;
    if (sendPrompt(pendingPrompt)) setPendingPrompt(null);
  }, [pendingPrompt, connected, sendPrompt]);

  useEffect(() => {
    if (!connected || !active) return;
    const seed = consumeSeed(active.id);
    if (seed) setPendingPrompt(seed);
  }, [connected, active?.id, consumeSeed]);

  const submit = async (prompt: string) => {
    if (!prompt.trim() || !active) return;
    if (active.title === "New chat" || !active.title) {
      updateTitle(prompt.slice(0, 60));
    }
    // Optimistic UI: show planner card + running status the instant Send is hit.
    markSubmitting(active.id, prompt);
    // Lazy ticket creation — only now do we hit /api/tickets, so empty
    // 'New chat' rows never get persisted.
    if (!active.ticket_id) {
      try {
        const r = await api.createTicket(prompt.slice(0, 60), "Eugene");
        active.ticket_id = r.id;
        setTicketId(r.id);
      } catch (e) {
        console.warn("ticket create failed", e);
        return;
      }
    }
    setPendingPrompt(prompt);
  };

  // Hydrate any backend-created tickets (scripts, other devices) into the
  // session list, then poll every 30s so new server-side runs surface live.
  useEffect(() => {
    hydrateFromBackend();
    const i = setInterval(hydrateFromBackend, 30_000);
    return () => clearInterval(i);
  }, [hydrateFromBackend]);

  useEffect(() => {
    if (sessions.length === 0) newSession("New chat");
  }, []); // eslint-disable-line

  // Rehydrate logic:
  // (a) No live data at all → fetch the backend record so we have something to show
  // (b) Live planner but empty artifact + backend likely complete → pull the
  //     final assistant message so the session doesn't appear stuck
  useEffect(() => {
    if (!active || !active.ticket_id) return;
    const noLiveData = !active.planner && active.subagents.length === 0 && !active.artifact.markdown;
    const stuckRunning = !!active.planner && !active.artifact.markdown && active.status === "running";
    if (noLiveData || stuckRunning) {
      rehydrateSessionFromBackend(active.id);
    }
  }, [active?.id, active?.status, active?.artifact.markdown]); // eslint-disable-line

  // Auto-open the right rail the first time sub-agents fire in this session,
  // unless the user has explicitly toggled it.
  useEffect(() => {
    if (!stepsUserToggled && active && active.subagents.length > 0 && !stepsOpen) {
      setStepsOpen(true);
    }
  }, [active?.subagents.length, stepsUserToggled, stepsOpen, active]);

  if (!active) return null;

  const hasContent = !!active.planner || active.subagents.length > 0 || !!active.artifact.markdown;
  const hasSubagents = active.subagents.length > 0;

  return (
    <div className="flex h-full overflow-hidden">
      <SessionList active={active} onNew={() => newSession("New chat")} onSelect={setActive} />

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto thin-scroll px-8 py-6 space-y-5">
            <header className="flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <h1 className="text-base font-semibold text-ink truncate">{active.title}</h1>
                <p className="text-[11.5px] text-muted mt-0.5 flex items-center gap-1.5">
                  <span className={`status-dot ${connected ? "running" : "pending"}`} />
                  {connected ? (
                    <>Connected · live streaming{active.status !== "idle" && ` · ${active.status}`}</>
                  ) : ticketId ? "Reconnecting to agent service…" : "Ready to chat"}
                </p>
              </div>
              <div className="flex items-center gap-1">
                {active.ticket_id && (
                  <button
                    className="btn-ghost text-[12px]"
                    title="Pull the latest from the server (use this if the chat looks stuck)"
                    onClick={() => rehydrateSessionFromBackend(active.id)}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                      <polyline points="23,4 23,10 17,10"/><polyline points="1,20 1,14 7,14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                    </svg>
                    Reload
                  </button>
                )}
                {hasSubagents && (
                  <button className="btn-ghost text-[12px]" onClick={() => { setStepsOpen((v) => !v); setStepsUserToggled(true); }}>
                    {stepsOpen ? "Hide" : "Show"} how I figured it out
                    <span className="chip text-[10px] ml-1">{active.subagents.length}</span>
                  </button>
                )}
              </div>
            </header>

            {!hasContent && <EmptyChatState />}

            {active.planner && <PlannerCard planner={active.planner} />}

            {active.artifact.markdown && (
              <ArtifactCanvas artifact={active.artifact} subagents={active.subagents} />
            )}

            <SessionArtifacts ticketId={ticketId} sessionStatus={active.status} />

            {active.status === "error" && (
              <div className="card p-4" style={{ background: "#FEF2F2", borderColor: "rgba(239,68,68,0.3)" }}>
                <div className="text-sm font-semibold" style={{ color: "#B91C1C" }}>Something went wrong</div>
                <div className="text-xs mt-1" style={{ color: "#7F1D1D" }}>{active.error || "Stream ended unexpectedly."}</div>
              </div>
            )}
          </div>

          <ActionBar session={active} />
          {/* Don't gate the Send button on WS connectivity — for new sessions
              we lazily create the ticket + open the WS during submit(). */}
          <PromptBar onSubmit={submit} disabled={false} showExamples={!hasContent} />
        </div>

        {stepsOpen && hasSubagents && <StepsRail session={active} />}
      </div>
    </div>
  );
}

function EmptyChatState() {
  return (
    <div className="empty-state mt-8">
      <div className="mx-auto w-12 h-12 rounded-xl flex items-center justify-center mb-3"
           style={{ background: "linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)" }}>
        <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <h3>Ask anything — I'll dispatch the right agents</h3>
      <p>
        When you send a prompt, a planner reads it, fans out to specialist agents,
        and assembles their findings into one artifact with clickable citations.
        Pick an example below or type your own.
      </p>
    </div>
  );
}
