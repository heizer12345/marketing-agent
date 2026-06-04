"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { contentPreviewHref } from "@/lib/contentPaths";
import { displayTitleFromPath, parseMarkdownDocument } from "@/lib/markdownContent";

type Props = {
  path: string;
  compact?: boolean;
};

export function ContentFilePreview({ path, compact = false }: Props) {
  const [body, setBody] = useState<string | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(path, { credentials: "include" });
        if (!r.ok) throw new Error(String(r.status));
        const text = await r.text();
        if (!cancelled) setBody(text);
      } catch {
        if (!cancelled) setErr(true);
      }
    })();
    return () => { cancelled = true; };
  }, [path]);

  const doc = body ? parseMarkdownDocument(body) : null;
  const name = displayTitleFromPath(path, doc?.meta);
  const previewBody = doc?.body ?? "";
  const preview = previewBody
    ? previewBody.length > (compact ? 1200 : 4000)
      ? `${previewBody.slice(0, compact ? 1200 : 4000)}\n\n…`
      : previewBody
    : null;

  return (
    <div
      className="rounded-xl border overflow-hidden my-4"
      style={{ borderColor: "var(--border)", background: "linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 48%)" }}
    >
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-wide text-cyan-800">Saved file</div>
          <div className="text-sm font-semibold text-ink capitalize truncate">{name}</div>
        </div>
        <Link
          href={contentPreviewHref(path)}
          className="btn-primary text-[12px] py-1.5 px-3 shrink-0"
          target="_blank"
          rel="noreferrer"
        >
          Open preview
        </Link>
      </div>

      <div className="px-4 py-3">
        {err && (
          <p className="text-[12px] text-muted">
            Could not load preview.{" "}
            <a href={path} className="text-cyan-700 underline" target="_blank" rel="noreferrer">
              Open raw file
            </a>
          </p>
        )}
        {!err && !preview && (
          <p className="text-[12px] text-muted animate-pulse">Loading preview…</p>
        )}
        {preview && (
          <div className={compact ? "prose-sourcy text-[12px] max-h-64 overflow-y-auto thin-scroll" : "prose-sourcy text-[13px]"}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{preview}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
