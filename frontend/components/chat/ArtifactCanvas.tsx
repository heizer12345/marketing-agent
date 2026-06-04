"use client";

import { useMemo } from "react";
import { useChatStore } from "@/lib/store";
import type { Artifact, SubAgent } from "@/lib/types";
import clsx from "clsx";
import { ChatMarkdown } from "@/components/chat/ChatMarkdown";

export function ArtifactCanvas({
  artifact,
  subagents,
  agentName,
  activity,
  embedded = false,
}: {
  artifact: Artifact;
  subagents: SubAgent[];
  agentName?: string;
  activity?: string;
  embedded?: boolean;
}) {
  const setActive = useChatStore((s) => s.setActiveCitation);
  const activeCitation = useChatStore((s) => s.activeCitation);

  const byLetter = useMemo(() => {
    const m: Record<string, SubAgent> = {};
    subagents.forEach((a) => { m[a.letter] = a; });
    return m;
  }, [subagents]);

  const transformed = useMemo(() => {
    return artifact.markdown.replace(/\[([A-Z]|F\d+)\]/g, "‹CITE:$1›");
  }, [artifact.markdown]);

  const isRunning = !artifact.complete && !!activity;

  const mdComponents = useMemo(
    () => ({
      p: ({ children }: { children?: React.ReactNode }) => (
        <p>{wrapCitations(children, byLetter, activeCitation, setActive)}</p>
      ),
      li: ({ children }: { children?: React.ReactNode }) => (
        <li>{wrapCitations(children, byLetter, activeCitation, setActive)}</li>
      ),
      h1: ({ children }: { children?: React.ReactNode }) => (
        <h1>{wrapCitations(children, byLetter, activeCitation, setActive)}</h1>
      ),
      h2: ({ children }: { children?: React.ReactNode }) => (
        <h2>{wrapCitations(children, byLetter, activeCitation, setActive)}</h2>
      ),
      h3: ({ children }: { children?: React.ReactNode }) => (
        <h3>{wrapCitations(children, byLetter, activeCitation, setActive)}</h3>
      ),
      img: ({ src, alt }: { src?: string; alt?: string }) => <img src={src} alt={alt || ""} />,
    }),
    [byLetter, activeCitation, setActive],
  );

  const body = (
    <>
      {(agentName || isRunning || artifact.complete) && (
        <div className={clsx("flex items-center gap-2 mb-3", !embedded && "pb-3 border-b")} style={{ borderColor: "var(--border)" }}>
          {!embedded && (
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)" }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" className="w-3.5 h-3.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14,2 14,8 20,8" />
              </svg>
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold text-ink">{agentName || "Assistant"}</div>
            {isRunning && (
              <div className="text-[11px] text-muted flex items-center gap-1.5 mt-0.5">
                <span className="status-dot running" />
                <span className="truncate">{activity}</span>
              </div>
            )}
            {!embedded && subagents.length > 0 && !isRunning && (
              <div className="text-[11px] text-muted">Click citation chips to see source agents</div>
            )}
          </div>
          {artifact.complete && <span className="chip chip-emerald text-[10px]">Done</span>}
          {artifact.elapsed_seconds != null && artifact.complete && (
            <span className="text-[11px] text-muted font-mono">{artifact.elapsed_seconds.toFixed(0)}s</span>
          )}
        </div>
      )}

      <ChatMarkdown markdown={transformed} className="prose-sourcy" components={mdComponents} />
    </>
  );

  if (embedded) {
    return (
      <div
        className="rounded-2xl rounded-bl-md px-4 py-3 border"
        style={{ background: "white", borderColor: "var(--border)" }}
      >
        {body}
      </div>
    );
  }

  return <article className="card p-7">{body}</article>;
}

function wrapCitations(
  children: React.ReactNode,
  byLetter: Record<string, SubAgent>,
  activeCitation: string | null,
  setActive: (ref: string | null) => void,
): React.ReactNode {
  const walk = (node: React.ReactNode): React.ReactNode => {
    if (typeof node === "string") {
      const parts = node.split(/(‹CITE:[^›]+›)/g);
      return parts.map((part, i) => {
        const m = part.match(/^‹CITE:([^›]+)›$/);
        if (!m) return part;
        const ref = m[1];
        const sub = byLetter[ref];
        const title = sub ? `Source: ${sub.name} [${ref}]` : `Reference ${ref}`;
        return (
          <span
            key={i}
            className={clsx("citation", activeCitation === ref && "active")}
            title={title}
            onClick={() => setActive(activeCitation === ref ? null : ref)}
          >
            {ref}
          </span>
        );
      });
    }
    if (Array.isArray(node)) return node.map((c, i) => <span key={i}>{walk(c)}</span>);
    return node;
  };
  return walk(children);
}
