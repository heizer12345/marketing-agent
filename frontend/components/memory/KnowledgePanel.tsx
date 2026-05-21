"use client";

import { useState } from "react";

export function KnowledgePanel({
  principles,
  winners,
}: {
  principles: Array<{ slug: string; name: string; summary?: string; [k: string]: any }>;
  winners: { ads: any[]; blogs: any[]; landing_pages: any[]; case_studies: any[] };
}) {
  const [tab, setTab] = useState<"principles" | "winners">("principles");
  const [wTab, setWTab] = useState<keyof typeof winners>("ads");

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 border-b border-border">
        {(["principles", "winners"] as const).map((k) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={
              "px-3 py-2 text-sm font-medium border-b-2 -mb-px " +
              (tab === k ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink")
            }
          >
            {k === "principles" ? "Marketing principles" : "Winners library"}
          </button>
        ))}
      </div>

      {tab === "principles" ? (
        <div className="space-y-2">
          {principles.map((p) => (
            <div key={p.slug} className="card p-4">
              <div className="flex items-baseline justify-between">
                <div className="font-medium text-ink">{p.name}</div>
                <code className="text-xs text-muted">{p.slug}</code>
              </div>
              {p.summary && <p className="text-sm text-muted mt-1">{p.summary}</p>}
              {(p.use_for || p.best_for) && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {(p.use_for || []).map((u: string) => <span key={u} className="chip">{u}</span>)}
                  {p.best_for && <span className="chip-accent" title={p.best_for}>best for</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-2 border-b border-border">
            {(Object.keys(winners) as Array<keyof typeof winners>).map((k) => (
              <button
                key={k}
                onClick={() => setWTab(k)}
                className={
                  "px-3 py-2 text-sm font-medium border-b-2 -mb-px " +
                  (wTab === k ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink")
                }
              >
                {k.replace("_", " ")} ({winners[k]?.length || 0})
              </button>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-3">
            {(winners[wTab] || []).map((w: any) => (
              <div key={w.id} className="card p-4">
                <div className="font-medium text-ink">{w.title}</div>
                <div className="text-xs text-muted mt-0.5">{w.industry}{w.channel ? ` · ${w.channel}` : ""}</div>
                {w.why_it_won && <p className="text-sm text-ink mt-2">{w.why_it_won}</p>}
                {w.applies_to_sourcy && <p className="text-xs text-muted mt-2 italic">Apply to Sourcy: {w.applies_to_sourcy}</p>}
                <div className="mt-2 flex flex-wrap gap-1">
                  {(w.principle_tags || []).map((t: string) => <span key={t} className="chip">{t}</span>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
