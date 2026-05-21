"use client";

import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChatStore } from "@/lib/store";
import type { Artifact, SubAgent } from "@/lib/types";
import clsx from "clsx";

/** Renders artifact markdown with inline citation chips that highlight the
 * matching sub-agent in the Steps rail on click. */
export function ArtifactCanvas({
  artifact,
  subagents,
}: {
  artifact: Artifact;
  subagents: SubAgent[];
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

  return (
    <article className="card p-7">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
             style={{ background: "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)" }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/>
          </svg>
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold text-ink">Answer</div>
          <div className="text-[11px] text-muted">Citations link back to the source agent — click any chip</div>
        </div>
        {artifact.complete && <span className="chip chip-emerald">Complete</span>}
        {artifact.elapsed_seconds != null && (
          <span className="text-[11px] text-muted font-mono">{artifact.elapsed_seconds.toFixed(1)}s</span>
        )}
      </div>

      <div className="prose-sourcy">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ children }) => <p>{wrapCitations(children, byLetter, activeCitation, setActive)}</p>,
            li: ({ children }) => <li>{wrapCitations(children, byLetter, activeCitation, setActive)}</li>,
            h1: ({ children }) => <h1>{wrapCitations(children, byLetter, activeCitation, setActive)}</h1>,
            h2: ({ children }) => <h2>{wrapCitations(children, byLetter, activeCitation, setActive)}</h2>,
            h3: ({ children }) => <h3>{wrapCitations(children, byLetter, activeCitation, setActive)}</h3>,
            img: ({ src, alt }) => <img src={src as string} alt={alt || ""} />,
            a: ({ children, href }) => <a href={href} target="_blank" rel="noreferrer">{children}</a>,
          }}
        >
          {transformed}
        </ReactMarkdown>
      </div>
    </article>
  );
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
        const title = sub ? `Source: ${sub.name} [${ref}] — click to see agent's full output` : `Reference ${ref}`;
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
