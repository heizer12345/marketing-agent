"use client";

import { useEffect, useRef, useState } from "react";
import { useChatStore, selectActiveSession } from "@/lib/store";
import { api } from "@/lib/api";
import { useAgentStream } from "@/lib/useAgentStream";
import { CHAT_QUICK_STARTS, titleFromPrompt, type QuickStartCategory } from "@/lib/chatQuickStarts";
import { SessionList } from "@/components/chat/SessionList";
import { PromptBar, type PromptBarHandle } from "@/components/chat/PromptBar";
import { ChatQuickStarts } from "@/components/chat/ChatQuickStarts";
import { ChatThread } from "@/components/chat/ChatThread";
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
  const linkTicketId = useChatStore((s) => s.linkTicketId);
  const hydrateFromBackend = useChatStore((s) => s.hydrateFromBackend);
  const rehydrateSessionFromBackend = useChatStore((s) => s.rehydrateSessionFromBackend);
  const pruneBrokenSessions = useChatStore((s) => s.pruneBrokenSessions);

  const [ticketId, setTicketId] = useState<string | null>(null);
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);
  const [stepsOpen, setStepsOpen] = useState(false);
  const [stepsUserToggled, setStepsUserToggled] = useState(false);
  const [ticketError, setTicketError] = useState<string | null>(null);
  const promptRef = useRef<PromptBarHandle>(null);

  useEffect(() => {
    if (!active) {
      setTicketId(null);
      return;
    }
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
    const title = titleFromPrompt(prompt);
    if (active.title === "New chat" || !active.title) {
      updateTitle(title);
    }
    markSubmitting(active.id, prompt);
    setTicketError(null);
    if (!active.ticket_id) {
      try {
        const r = await api.createTicket(title, "user");
        linkTicketId(active.id, r.id);
        setTicketId(r.id);
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Could not create chat session";
        setTicketError(msg);
        console.warn("ticket create failed", e);
        return;
      }
    }
    setPendingPrompt(prompt);
  };

  const handleQuickStart = (id: QuickStartCategory) => {
    const opt = CHAT_QUICK_STARTS.find((o) => o.id === id);
    if (!opt) return;
    promptRef.current?.setValue(opt.starterPrompt);
    promptRef.current?.focus();
  };

  useEffect(() => {
    (async () => {
      await hydrateFromBackend();
      await pruneBrokenSessions();
    })();
    const i = setInterval(hydrateFromBackend, 30_000);
    return () => clearInterval(i);
  }, [hydrateFromBackend, pruneBrokenSessions]);

  useEffect(() => {
    if (sessions.length === 0) newSession("New chat");
  }, []); // eslint-disable-line

  useEffect(() => {
    if (!active?.ticket_id) return;
    const noLiveData =
      !active.planner &&
      active.subagents.length === 0 &&
      !active.artifact.markdown &&
      (active.turns?.length ?? 0) === 0;
    const stuckRunning = !!active.planner && !active.artifact.markdown && active.status === "running";
    const needsHistory = (active.turns?.length ?? 0) === 0 && active.status === "complete";
    if (noLiveData || stuckRunning || needsHistory) {
      rehydrateSessionFromBackend(active.id);
    }
  }, [active?.id, active?.status, active?.artifact.markdown, active?.turns?.length]); // eslint-disable-line

  useEffect(() => {
    if (!stepsUserToggled && active && active.subagents.length > 0 && !stepsOpen) {
      setStepsOpen(true);
    }
  }, [active?.subagents.length, stepsUserToggled, stepsOpen, active]);

  if (!active) return null;

  const hasContent =
    (active.turns?.length ?? 0) > 0 ||
    !!active.planner ||
    active.subagents.length > 0 ||
    !!active.artifact.markdown;
  const hasSubagents = active.subagents.length > 0;
  const showQuickStarts = !hasContent;

  return (
    <div className="flex h-full overflow-hidden">
      <SessionList active={active} onNew={() => newSession("New chat")} onSelect={setActive} />

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto thin-scroll px-6 py-5 space-y-4">
            <header className="flex items-center justify-between gap-3 pb-1">
              <div className="min-w-0 flex-1">
                <h1 className="text-base font-semibold text-ink truncate">{active.title}</h1>
                <p className="text-[11px] text-muted mt-0.5">
                  {showQuickStarts
                    ? "Pick a topic or type below"
                    : active.status === "running"
                      ? "Thinking…"
                      : active.status === "error"
                        ? "Something went wrong"
                        : connected
                          ? "Continue the conversation below"
                          : ticketId
                            ? "Reconnecting…"
                            : "Ready"}
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
                      <polyline points="23,4 23,10 17,10" />
                      <polyline points="1,20 1,14 7,14" />
                      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                    </svg>
                    Reload
                  </button>
                )}
                {hasSubagents && (
                  <button
                    className="btn-ghost text-[12px]"
                    onClick={() => {
                      setStepsOpen((v) => !v);
                      setStepsUserToggled(true);
                    }}
                  >
                    {stepsOpen ? "Hide" : "Show"} how I figured it out
                    <span className="chip text-[10px] ml-1">{active.subagents.length}</span>
                  </button>
                )}
              </div>
            </header>

            {showQuickStarts && <ChatQuickStarts onSelectCategory={handleQuickStart} />}

            {ticketError && (
              <div className="card p-4" style={{ background: "#FEF2F2", borderColor: "rgba(239,68,68,0.3)" }}>
                <div className="text-sm font-semibold" style={{ color: "#B91C1C" }}>Chat cannot connect to the API</div>
                <div className="text-xs mt-1" style={{ color: "#7F1D1D" }}>{ticketError}</div>
              </div>
            )}

            {hasContent && <ChatThread session={active} />}

            <SessionArtifacts ticketId={ticketId} sessionStatus={active.status} />

            {active.status === "error" && (
              <div className="card p-4" style={{ background: "#FEF2F2", borderColor: "rgba(239,68,68,0.3)" }}>
                <div className="text-sm font-semibold" style={{ color: "#B91C1C" }}>
                  Something went wrong
                </div>
                <div className="text-xs mt-1" style={{ color: "#7F1D1D" }}>
                  {active.error || "Stream ended unexpectedly."}
                </div>
              </div>
            )}
          </div>

          <ActionBar session={active} />
          <PromptBar ref={promptRef} onSubmit={submit} disabled={false} />
        </div>

        {stepsOpen && hasSubagents && <StepsRail session={active} />}
      </div>
    </div>
  );
}
