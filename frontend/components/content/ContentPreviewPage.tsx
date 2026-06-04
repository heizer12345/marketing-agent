"use client";

import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { parseMarkdownDocument } from "@/lib/markdownContent";
import type { ContentFrontmatter } from "@/lib/markdownContent";

const mdComponents = {
  table: ({ children }: { children?: ReactNode }) => (
    <div className="overflow-x-auto my-4 rounded-lg border" style={{ borderColor: "var(--border)" }}>
      <table className="w-full text-[13px]">{children}</table>
    </div>
  ),
  thead: ({ children }: { children?: ReactNode }) => (
    <thead style={{ background: "var(--bg-alt)" }}>{children}</thead>
  ),
  th: ({ children }: { children?: ReactNode }) => (
    <th className="text-left px-3 py-2 font-semibold text-ink border-b" style={{ borderColor: "var(--border)" }}>
      {children}
    </th>
  ),
  td: ({ children }: { children?: ReactNode }) => (
    <td className="px-3 py-2 align-top border-b text-ink-soft" style={{ borderColor: "var(--border)" }}>
      {children}
    </td>
  ),
  h1: ({ children }: { children?: ReactNode }) => (
    <h1 className="text-2xl font-bold text-ink mb-4">{children}</h1>
  ),
  h2: ({ children }: { children?: ReactNode }) => (
    <h2 className="text-lg font-semibold text-ink mt-8 mb-3">{children}</h2>
  ),
  h3: ({ children }: { children?: ReactNode }) => (
    <h3 className="text-base font-semibold text-ink mt-6 mb-2">{children}</h3>
  ),
  a: ({ href, children }: { href?: string; children?: ReactNode }) => (
    <a href={href} className="text-cyan-700 underline" target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
};

function MetaStrip({ meta }: { meta: ContentFrontmatter }) {
  const chips: string[] = [];
  if (meta.type) chips.push(meta.type.replace(/_/g, " "));
  if (meta.date) {
    const d = meta.date.split(" ")[0];
    chips.push(d);
  }
  if (meta.keywords) {
    meta.keywords.split(",").slice(0, 4).forEach((k) => chips.push(k.trim()));
  }
  if (!meta.summary && chips.length === 0) return null;

  return (
    <div
      className="mb-6 pb-5 border-b rounded-lg px-4 py-3"
      style={{ borderColor: "var(--border)", background: "var(--bg-alt)" }}
    >
      {meta.summary && (
        <p className="text-[14px] text-ink-soft leading-relaxed mb-3">{meta.summary}</p>
      )}
      {chips.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {chips.map((c) => (
            <span key={c} className="chip text-[10px] capitalize">
              {c}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export function ContentPreviewPage({ markdown }: { markdown: string }) {
  const { meta, body } = parseMarkdownDocument(markdown);

  return (
    <article className="card p-8 prose-sourcy" style={{ maxWidth: "none" }}>
      <MetaStrip meta={meta} />
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
        {body}
      </ReactMarkdown>
    </article>
  );
}
