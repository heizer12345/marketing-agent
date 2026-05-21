"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type LibItem = {
  name: string;
  path: string;
  size_bytes: number;
  modified: number;
  ext: string;
  from_session?: { ticket_id: string; ticket_title: string };
};
type TabKey = "blogs" | "landing_pages" | "ads" | "case_studies" | "images";

const TABS: Array<{ key: TabKey; label: string; emoji: string; desc: string }> = [
  { key: "blogs",        label: "Blogs",         emoji: "✍️", desc: "SEO-optimized blog posts" },
  { key: "landing_pages",label: "Landing pages", emoji: "🛬", desc: "Conversion LPs by block pattern" },
  { key: "ads",          label: "Ads",           emoji: "🎨", desc: "Multi-variant ads with images" },
  { key: "case_studies", label: "Case studies",  emoji: "📖", desc: "Customer outcome stories" },
  { key: "images",       label: "Images",        emoji: "🖼️", desc: "Generated brand assets" },
];

export default function LibraryPage() {
  const [tab, setTab] = useState<TabKey>("blogs");
  const [items, setItems] = useState<LibItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState("");

  useEffect(() => {
    setLoading(true);
    api.library(tab).then((r) => setItems(r.items)).finally(() => setLoading(false));
  }, [tab]);

  const filtered = items.filter((i) => i.name.toLowerCase().includes(q.toLowerCase()));
  const meta = TABS.find((t) => t.key === tab)!;

  return (
    <div className="flex-1 overflow-y-auto thin-scroll">
      <header className="border-b bg-white px-8 py-5" style={{ borderColor: "var(--border)" }}>
        <h1 className="text-xl font-semibold text-ink" style={{ letterSpacing: "-0.02em" }}>Library</h1>
        <p className="text-[13px] text-muted mt-1">Every artifact the agents have generated. Click to open · regenerate · approve.</p>
      </header>

      <div className="px-8 pt-5">
        <nav className="flex items-center gap-1 border-b" style={{ borderColor: "var(--border)" }}>
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={
                "px-4 py-2.5 text-[13px] font-medium border-b-2 -mb-px transition-colors flex items-center gap-2 " +
                (tab === t.key ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink")
              }
            >
              <span aria-hidden>{t.emoji}</span>
              {t.label}
              <span className="chip text-[10px] py-0">{tab === t.key ? items.length : ""}</span>
            </button>
          ))}
          <div className="ml-auto pb-2 flex items-center gap-2">
            <input className="input w-72 text-[12.5px]" placeholder="Filter by name…" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
        </nav>
        <p className="text-[12px] text-muted mt-2">{meta.desc} · {items.length} item{items.length === 1 ? "" : "s"}</p>
      </div>

      <div className="p-8">
        {loading ? (
          <div className="empty-state"><p>Loading…</p></div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <h3>No {meta.label.toLowerCase()} yet</h3>
            <p>Run analysis in Chat, then click a "Generate {meta.label.toLowerCase().slice(0, -1)}" suggestion at the bottom of the artifact.</p>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-3">
            {filtered.map((it) => (
              <a key={it.path} href={it.path} target="_blank" rel="noreferrer" className="card-hover p-4 block">
                {tab === "images" && it.ext === "png" ? (
                  <div className="aspect-square rounded-md mb-3 overflow-hidden" style={{ background: "var(--bg-alt)" }}>
                    <img src={it.path} alt={it.name} className="w-full h-full object-cover" />
                  </div>
                ) : (
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-9 h-9 rounded-md flex items-center justify-center text-base"
                         style={{ background: "var(--bg-alt)" }}>
                      {meta.emoji}
                    </div>
                    <span className="chip text-[10px]">{it.ext.toUpperCase()}</span>
                  </div>
                )}
                <div className="text-[13px] font-medium text-ink truncate leading-tight" title={it.name}>
                  {it.name.replace(/_\d{8}_\d{6}.*$/, "")}
                </div>
                <div className="text-[11px] text-muted mt-1">
                  {new Date(it.modified * 1000).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                  {" · "}
                  {(it.size_bytes / 1024).toFixed(1)} KB
                </div>
                {it.from_session && (
                  <div className="mt-2 pt-2 border-t" style={{ borderColor: "var(--border)" }}>
                    <span className="text-[10px] uppercase tracking-wider text-muted">From chat</span>
                    <div className="text-[11.5px] text-ink truncate mt-0.5" title={it.from_session.ticket_title}>
                      💬 {it.from_session.ticket_title || "Untitled chat"}
                    </div>
                  </div>
                )}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
