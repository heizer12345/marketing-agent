"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Artifact = {
  url: string;
  name: string;
  kind: "image" | "html" | "doc";
  ext: string;
  created_at?: string;
};

/** Shows every artifact (HTML pages, images, content files) produced inside
 * this chat session. Lets the user reopen old work without hunting through
 * the Library. Auto-refreshes when the session status changes. */
export function SessionArtifacts({
  ticketId,
  sessionStatus,
}: {
  ticketId: string | null;
  sessionStatus: string;
}) {
  const [items, setItems] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ticketId) { setItems([]); return; }
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const r = await api.sessionArtifacts(ticketId);
        if (!cancelled) setItems(r.artifacts);
      } catch {
        // 404 / empty session is fine
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [ticketId, sessionStatus]);

  if (!ticketId || items.length === 0) return null;

  const images = items.filter((i) => i.kind === "image");
  const pages = items.filter((i) => i.kind === "html");
  const docs = items.filter((i) => i.kind === "doc");

  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-sm font-bold"
             style={{ background: "linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)" }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/>
          </svg>
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold text-ink">Artifacts from this chat</div>
          <div className="text-[11.5px] text-muted">
            {items.length} item{items.length === 1 ? "" : "s"} · {pages.length} page{pages.length === 1 ? "" : "s"}
            {images.length > 0 && ` · ${images.length} image${images.length === 1 ? "" : "s"}`}
            {docs.length > 0 && ` · ${docs.length} doc${docs.length === 1 ? "" : "s"}`}
          </div>
        </div>
        {loading && <span className="status-dot running" />}
      </div>

      {images.length > 0 && (
        <div className="mb-3">
          <div className="label mb-2">Images</div>
          <div className="grid grid-cols-5 gap-2">
            {images.map((a) => (
              <a key={a.url} href={a.url} target="_blank" rel="noreferrer"
                 className="aspect-square rounded-md overflow-hidden border hover:border-cyan transition-colors"
                 style={{ borderColor: "var(--border)" }}>
                <img src={a.url} alt={a.name} className="w-full h-full object-cover" />
              </a>
            ))}
          </div>
        </div>
      )}

      {pages.length > 0 && (
        <div className="space-y-1.5">
          <div className="label mb-1">Pages</div>
          {pages.map((a) => (
            <a key={a.url} href={a.url} target="_blank" rel="noreferrer"
               className="flex items-center gap-2.5 rounded-md px-3 py-2 hover:bg-bg-alt transition-colors"
               style={{ background: "var(--bg-alt)" }}>
              <span className="chip text-[10px]">{a.ext.toUpperCase()}</span>
              <span className="text-[12.5px] text-ink truncate flex-1">{a.name.replace(/_\d{8}_\d{6}.*/, "")}</span>
              <span className="text-[11px] text-muted">↗</span>
            </a>
          ))}
        </div>
      )}

      {docs.length > 0 && (
        <div className="mt-3 space-y-1">
          <div className="label mb-1">Docs</div>
          {docs.map((a) => (
            <a key={a.url} href={a.url} target="_blank" rel="noreferrer"
               className="text-[12.5px] text-ink hover:text-cyan block truncate">
              📄 {a.name}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
