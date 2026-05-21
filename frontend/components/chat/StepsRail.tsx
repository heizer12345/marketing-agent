"use client";

import { useChatStore } from "@/lib/store";
import type { ChatSession, SubAgent } from "@/lib/types";
import clsx from "clsx";

const FRIENDLY = (name: string): { short: string; role: string; emoji: string } => {
  const n = name.toLowerCase();
  if (n.includes("seo content")) return { short: "SEO Content Analyst", role: "Auditing pages, meta tags, internal linking", emoji: "🔎" };
  if (n.includes("seo")) return { short: "SEO Analyst", role: "Rankings, CTR, keyword gaps", emoji: "🔎" };
  if (n.includes("geo content")) return { short: "GEO Content Analyst", role: "Citability for AI answers", emoji: "🤖" };
  if (n.includes("geo")) return { short: "GEO Analyst", role: "Citability for AI answers (Perplexity, ChatGPT)", emoji: "🤖" };
  if (n.includes("aeo")) return { short: "AEO Analyst", role: "Featured snippets, People Also Ask", emoji: "💬" };
  if (n.includes("eeat")) return { short: "E-E-A-T Auditor", role: "Experience · Expertise · Authority · Trust", emoji: "🏷️" };
  if (n.includes("entity")) return { short: "Entity Optimizer", role: "Knowledge Panel, Wikidata, brand SERP", emoji: "🆔" };
  if (n.includes("keyword")) return { short: "Keyword Strategist", role: "Search intent, content gaps, clusters", emoji: "🎯" };
  if (n.includes("technical seo")) return { short: "Technical SEO", role: "Sitemap, schema, Core Web Vitals", emoji: "⚙️" };
  if (n.includes("traffic")) return { short: "Traffic Analyst", role: "Sessions, sources, geo, WoW trends", emoji: "📊" };
  if (n.includes("competitor")) return { short: "Competitor Analyst", role: "Keyword gaps, share of voice", emoji: "🥷" };
  if (n.includes("paid") || n.includes("overlap")) return { short: "Paid/Organic Overlap", role: "Keyword cannibalization, savings", emoji: "🔁" };
  if (n.includes("recommend")) return { short: "Recommendation Engine", role: "Prioritized actions across channels", emoji: "💡" };
  if (n.includes("social")) return { short: "Socials Analyst", role: "Instagram posts, engagement", emoji: "📱" };
  if (n.includes("data analyst") || n.includes("marketing data")) return { short: "Marketing Data Analyst", role: "GA4, Meta Ads, Google Ads, Search Console", emoji: "📈" };
  if (n.includes("content engine")) return { short: "Content Engine", role: "Orchestrating content skills", emoji: "📝" };
  if (n.includes("intent")) return { short: "Intent Router", role: "Routing your request to the right agent", emoji: "🚦" };
  if (n.includes("synthesis")) return { short: "Synthesis Agent", role: "Assembling the final artifact + citations", emoji: "🧩" };
  if (n.includes("ad writer")) return { short: "Ad Writer", role: "Generating 3 ad variants + images", emoji: "🎨" };
  if (n.includes("case study")) return { short: "Case Study Writer", role: "Before · After · Bridge structure", emoji: "📖" };
  if (n.includes("blog")) return { short: "Blog Writer", role: "Writing the blog with chosen principle", emoji: "✍️" };
  if (n.includes("landing")) return { short: "Landing Page Writer", role: "Hero · proof · LP blocks", emoji: "🛬" };
  if (n.includes("brief")) return { short: "Content Brief", role: "Detailed brief for the writer", emoji: "📋" };
  if (n.includes("quality") || n.includes("scorer")) return { short: "Quality Scorer", role: "Voice + AI detection grade", emoji: "🎚️" };
  if (n.includes("knowledge")) return { short: "Knowledge Expert", role: "Strategic advice from knowledge base", emoji: "📚" };
  return { short: name, role: "Analyzing your request", emoji: "•" };
};

export function StepsRail({ session }: { session: ChatSession }) {
  const toggleExpand = useChatStore((s) => s.toggleSubExpand);
  const toggleSelect = useChatStore((s) => s.toggleSubSelect);
  const selected = useChatStore((s) => s.selectedSubagentIds[session.id] || {});
  const expanded = useChatStore((s) => s.expandedSubagentIds);
  const activeCitation = useChatStore((s) => s.activeCitation);

  const finishedCount = session.subagents.filter((a) => a.status === "finished").length;
  const runningCount = session.subagents.filter((a) => a.status === "running").length;

  return (
    <aside className="w-[380px] shrink-0 border-l flex flex-col" style={{ background: "var(--bg-rail)", borderColor: "var(--border)" }}>
      <header className="px-5 py-4 border-b bg-white" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-ink">How I figured this out</h2>
          {(finishedCount > 0 || runningCount > 0) && (
            <div className="flex items-center gap-2 text-[11px]">
              {runningCount > 0 && (
                <span className="flex items-center gap-1"><span className="status-dot running" /> {runningCount}</span>
              )}
              {finishedCount > 0 && (
                <span className="flex items-center gap-1 text-muted"><span className="status-dot finished" /> {finishedCount}</span>
              )}
            </div>
          )}
        </div>
        <p className="text-[11.5px] text-muted mt-1 leading-snug">
          Each agent below ran independently. Click a citation chip in the answer (like <span className="citation" style={{cursor:"default"}}>A</span>) to jump to its source.
        </p>
      </header>

      <div className="flex-1 overflow-y-auto thin-scroll p-3 space-y-2.5">
        {session.subagents.length === 0 && (
          <div className="text-xs text-muted px-2 py-6 text-center leading-relaxed">
            No agents dispatched yet.
            <div className="mt-1 text-muted-soft">Send a prompt and the planner will fan out to specialists.</div>
          </div>
        )}

        {session.subagents.map((a) => {
          const isExpanded = expanded[`${session.id}|${a.id}`];
          const isHighlighted = activeCitation === a.letter;
          const isSelected = !!selected[a.id];
          const meta = FRIENDLY(a.name);

          return (
            <div
              key={a.id}
              className={clsx(
                "rounded-xl bg-white transition-all duration-150 border",
                isHighlighted ? "card-active" : "border-[color:var(--border)] hover:border-[color:var(--border-strong)]",
              )}
            >
              <div className="flex items-start gap-3 px-3.5 py-3">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleSelect(session.id, a.id)}
                  className="mt-0.5 h-4 w-4 rounded border-[color:var(--border-strong)] accent-ink"
                  title="Select this agent for the next generation action"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="role-tag">
                      <span aria-hidden>{meta.emoji}</span>
                      {meta.short}
                      <span className="ref">[{a.letter}]</span>
                    </span>
                    <StatusBadge status={a.status} />
                  </div>
                  <div className="text-[11.5px] text-muted mt-1 leading-snug">{meta.role}</div>
                  {a.findings.length > 0 && (
                    <div className="text-[11px] text-emerald-600 mt-1.5 font-medium">
                      {a.findings.length} {a.findings.length === 1 ? "finding" : "findings"}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => toggleExpand(session.id, a.id)}
                  className="text-[11px] text-muted hover:text-ink font-medium"
                >
                  {isExpanded ? "Hide" : "View"}
                </button>
              </div>
              {isExpanded && (
                <div className="px-3.5 pb-3.5 space-y-2.5 border-t" style={{ borderColor: "var(--border)" }}>
                  <FindingsList agent={a} />
                  <div>
                    <div className="label mb-1.5 pt-2">Raw output</div>
                    <pre className="text-[11px] whitespace-pre-wrap font-mono rounded-lg p-3 max-h-72 overflow-y-auto thin-scroll" style={{ background: "var(--bg-alt)" }}>
                      {a.text || "(no output yet — agent is still working)"}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
}

function FindingsList({ agent }: { agent: SubAgent }) {
  if (!agent.findings.length) return null;
  return (
    <div>
      <div className="label pt-2 mb-1.5">Findings</div>
      <div className="space-y-1.5">
        {agent.findings.map((f, i) => (
          <div key={f.finding_id || i} className="text-[12px] text-ink rounded-md px-2.5 py-2" style={{ background: "var(--bg-alt)" }}>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-[10px] text-muted shrink-0">{f.finding_id || `F${i+1}`}</span>
              {f.confidence && (
                <span className={clsx("chip text-[10px] py-0",
                  f.confidence === "High" ? "chip-emerald" :
                  f.confidence === "Medium" ? "chip-amber" : "chip"
                )}>{f.confidence}</span>
              )}
            </div>
            <div className="mt-1 leading-snug">{f.claim || JSON.stringify(f)}</div>
            {f.evidence && <div className="mt-1 text-[11px] text-muted leading-snug italic">{f.evidence}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: SubAgent["status"] }) {
  if (status === "running") return <span className="chip chip-accent text-[10px] py-0">Working…</span>;
  if (status === "finished") return <span className="chip chip-emerald text-[10px] py-0">Done</span>;
  return <span className="chip text-[10px] py-0">Queued</span>;
}
