"use client";

import { useChatStore } from "@/lib/store";
import clsx from "clsx";
import type { ChatSession } from "@/lib/types";

export function SessionList({
  active,
  onNew,
  onSelect,
}: {
  active: ChatSession;
  onNew: () => void;
  onSelect: (id: string) => void;
}) {
  const sessions = useChatStore((s) => s.sessions);
  const deleteSession = useChatStore((s) => s.deleteSession);
  const cleanupEmpty = useChatStore((s) => s.cleanupEmptyTickets);
  const pruneBroken = useChatStore((s) => s.pruneBrokenSessions);

  const onDelete = (id: string, title: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm(`Delete "${title}"? This cannot be undone.`)) {
      deleteSession(id);
    }
  };

  const onCleanup = async () => {
    const n = await cleanupEmpty();
    alert(n > 0 ? `Cleaned up ${n} empty chat${n === 1 ? "" : "s"}.` : "No empty chats to clean up.");
  };

  const onPruneBroken = async () => {
    if (!confirm("Remove broken, empty, and duplicate chats from the sidebar?")) return;
    const n = await pruneBroken();
    alert(n > 0 ? `Removed ${n} chat${n === 1 ? "" : "s"}.` : "No broken chats to remove.");
  };

  return (
    <aside className="w-64 shrink-0 border-r flex flex-col" style={{ background: "var(--bg-rail)", borderColor: "var(--border)" }}>
      <div className="p-3 border-b space-y-2" style={{ borderColor: "var(--border)" }}>
        <button onClick={onNew} className="btn-primary w-full justify-center">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New chat
        </button>
        <button onClick={onPruneBroken} className="btn-ghost w-full justify-center text-[12px]">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
            <polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/>
          </svg>
          Remove broken chats
        </button>
      </div>
      <div className="flex-1 overflow-y-auto thin-scroll p-2 space-y-1.5">
        {sessions.map((s) => {
          const isActive = s.id === active.id;
          return (
            <div key={s.id}
              onClick={() => onSelect(s.id)}
              className={clsx(
                "group block w-full text-left rounded-lg px-3 py-2.5 transition-all duration-150 cursor-pointer relative",
                isActive ? "bg-white shadow-sm border" : "hover:bg-white/60 border border-transparent",
              )}
              style={isActive ? { borderColor: "var(--border)" } : undefined}
            >
              <div className="flex items-center gap-2 pr-7">
                <SessionStatusDot status={s.status} />
                <div className="text-[13px] font-medium text-ink truncate flex-1">
                  {s.title || "New chat"}
                </div>
              </div>
              <div className="text-[10.5px] text-muted mt-0.5 ml-3.5 flex items-center gap-1.5">
                <span>{new Date(s.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                <span>·</span>
                <SessionStatusLabel status={s.status} />
              </div>
              <button
                onClick={(e) => onDelete(s.id, s.title || "New chat", e)}
                title="Delete chat"
                className="absolute top-2.5 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-rose-50 text-muted hover:text-rose-600"
                aria-label="Delete chat"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

function SessionStatusDot({ status }: { status: ChatSession["status"] }) {
  return <span className={clsx("status-dot", status === "complete" ? "finished" : status)} />;
}
function SessionStatusLabel({ status }: { status: ChatSession["status"] }) {
  const map: Record<ChatSession["status"], string> = {
    idle: "Ready",
    running: "Working…",
    complete: "Complete",
    error: "Error",
  };
  return <span className="text-muted">{map[status]}</span>;
}
