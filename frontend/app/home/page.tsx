"use client";

import { useCallback, useEffect, useState } from "react";
import clsx from "clsx";
import { api } from "@/lib/api";

type Snapshot = Awaited<ReturnType<typeof api.homeSnapshot>>["snapshot"];
type Dashboard = Awaited<ReturnType<typeof api.homeSnapshot>>["dashboard"];

const SEVERITY_CHIP: Record<string, string> = {
  urgent: "chip-rose",
  important: "chip-amber",
  info: "chip",
};

const SEVERITY_DOT: Record<string, string> = {
  urgent: "bg-rose-500",
  important: "bg-amber-500",
  info: "bg-cyan-500",
};

export default function HomePage() {
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard>(null);
  const [stale, setStale] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [loadedAt, setLoadedAt] = useState<number | null>(null);
  // View mode toggle — start in the rich dashboard view if a dashboard exists.
  const [view, setView] = useState<"dashboard" | "summary">("dashboard");

  const load = useCallback(async () => {
    try {
      const r = await api.homeSnapshot(false);
      setSnap(r.snapshot);
      setDashboard(r.dashboard);
      setStale(r.stale);
      setRefreshing(r.refreshing);
      setLoadedAt(Date.now());
    } catch (e) {
      console.warn("home snapshot failed", e);
    }
  }, []);

  // Always load cached data instantly on mount — no blocking.
  useEffect(() => { load(); }, [load]);

  // Poll every 10s while a refresh is running so the dashboard updates as
  // soon as the background job finishes.
  useEffect(() => {
    if (!refreshing) return;
    const t = setInterval(() => load(), 10000);
    return () => clearInterval(t);
  }, [refreshing, load]);

  const onRefresh = async () => {
    // Fire-and-forget the trigger; immediately reflect "refreshing" state but
    // keep showing whatever data is currently cached.
    setRefreshing(true);
    try { await api.homeForceRefresh(); } catch { /* network only */ }
    // Pick up the new snapshot once available — polling above handles it.
  };

  const generatedAt = snap?.generated_at ? new Date(snap.generated_at * 1000) : null;
  const insights = snap?.insights ?? [];
  const movers = snap?.top_movers ?? [];
  const alerts = snap?.alerts ?? [];
  const kpis = snap?.kpis ?? [];
  const recommendations = (snap as any)?.recommendations ?? [];
  const empty = insights.length === 0 && movers.length === 0 && alerts.length === 0 && recommendations.length === 0;
  const erroredOut = snap?.status === "error";

  return (
    <div className="flex-1 overflow-y-auto thin-scroll">
      <header className="border-b bg-white/80 backdrop-blur sticky top-0 z-10 px-8 py-5" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-ink" style={{ letterSpacing: "-0.02em" }}>Today's marketing briefing</h1>
              {refreshing && <span className="chip chip-accent text-[10px]">Refreshing…</span>}
              {!refreshing && stale && <span className="chip chip-amber text-[10px]">Stale</span>}
              {!refreshing && !stale && snap && <span className="chip chip-emerald text-[10px]">Fresh</span>}
            </div>
            <p className="text-[13px] text-muted mt-1">
              Auto-pilot pulls from all your data sources and surfaces what changed. No clicks needed.
              {generatedAt && <span> Last run: {generatedAt.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}.</span>}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* View mode toggle */}
            {dashboard && (
              <div className="inline-flex rounded-lg border" style={{ borderColor: "var(--border)" }}>
                <button
                  onClick={() => setView("dashboard")}
                  className={"px-3 py-1.5 text-[12px] font-medium rounded-l-lg transition-colors " + (view === "dashboard" ? "bg-ink text-white" : "text-muted hover:text-ink")}
                  title="Full interactive dashboard (charts, tables, diagnoses)"
                >
                  📊 Full dashboard
                </button>
                <button
                  onClick={() => setView("summary")}
                  className={"px-3 py-1.5 text-[12px] font-medium rounded-r-lg transition-colors " + (view === "summary" ? "bg-ink text-white" : "text-muted hover:text-ink")}
                  title="Bullet summary view"
                >
                  📝 Summary
                </button>
              </div>
            )}
            <button className="btn-secondary" onClick={onRefresh} disabled={refreshing} title={refreshing ? "A refresh is already running — you'll see new data when it finishes (1-2 min)" : "Re-run the full marketing analysis"}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={clsx("w-4 h-4", refreshing && "animate-spin")}>
                <polyline points="23,4 23,10 17,10"/><polyline points="1,20 1,14 7,14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
              {refreshing ? "Refreshing (~1-2 min)" : "Refresh"}
            </button>
            {dashboard && (
              <a href={dashboard.url} target="_blank" rel="noreferrer" className="btn-ghost text-[12px]" title="Open the full dashboard in a new tab">
                Open ↗
              </a>
            )}
          </div>
        </div>
      </header>

      {/* Rich dashboard iframe view — mimics the synthesis_agent's UI */}
      {dashboard && view === "dashboard" && (
        <div className="flex-1" style={{ minHeight: "calc(100vh - 120px)" }}>
          <iframe
            src={dashboard.url}
            className="w-full h-full block border-0"
            style={{ minHeight: "calc(100vh - 120px)" }}
            title="Sourcy comprehensive dashboard"
          />
          <div className="absolute bottom-3 right-3 chip text-[10px]" style={{ background: "rgba(255,255,255,0.9)" }}>
            Dashboard from {new Date(dashboard.generated_at * 1000).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })} · {dashboard.size_kb} KB
          </div>
        </div>
      )}

      {/* Summary view (also shown when no dashboard exists yet) */}
      {(view === "summary" || !dashboard) && (
      <div className="p-8 max-w-5xl space-y-6">
        {!dashboard && (
          <div className="card p-4" style={{ background: "#F0F9FF", borderColor: "rgba(6,182,212,0.3)" }}>
            <div className="text-sm font-semibold" style={{ color: "#0E7490" }}>📊 Want the full interactive dashboard?</div>
            <div className="text-[12.5px] mt-1" style={{ color: "#155E75" }}>
              Run a comprehensive analysis in Chat (try "Full marketing audit — pull all sources, find top problems, prioritize next 5 actions"). It produces a rich tabbed dashboard with charts, tables, and diagnosis cards — and Home will surface it here automatically.
            </div>
          </div>
        )}
        {erroredOut && (
          <div className="card p-4" style={{ background: "#FFFBEB", borderColor: "rgba(245,158,11,0.3)" }}>
            <div className="text-sm font-semibold" style={{ color: "#92400E" }}>Last refresh hit an error</div>
            <div className="text-xs mt-1" style={{ color: "#78350F" }}>{(snap as any)?.error || "Unknown error — try again."}</div>
          </div>
        )}

        {empty && !refreshing && (
          <div className="empty-state">
            <h3>No snapshot yet</h3>
            <p>I'll pull from your connected data sources and brief you on what changed this week.</p>
            <button className="btn-primary mt-4 mx-auto" onClick={onRefresh}>Run first briefing</button>
          </div>
        )}

        {empty && refreshing && (
          <div className="card p-10 text-center">
            <div className="status-dot running mx-auto mb-3" style={{ width: 10, height: 10 }} />
            <div className="text-sm font-semibold text-ink">Running your first briefing…</div>
            <p className="text-[12.5px] text-muted mt-1 max-w-md mx-auto">
              Hitting GA4, Meta Ads, Search Console and friends. Takes 1-2 minutes the first time.
            </p>
          </div>
        )}

        {/* KPIs row */}
        {kpis.length > 0 && (
          <section>
            <div className="section-heading">
              <h2>KPIs · last 7 days</h2>
              <span className="hint">{kpis.length} metrics</span>
            </div>
            <div className="grid grid-cols-4 gap-3">
              {kpis.map((k, i) => (
                <div key={i} className="card p-4">
                  <div className="text-[11px] text-muted">{k.label}</div>
                  <div className="text-xl font-bold text-ink mt-1" style={{ letterSpacing: "-0.02em" }}>{k.value}</div>
                  <div className="flex items-center justify-between mt-1">
                    {typeof k.delta_pct === "number" ? (
                      <span className={clsx(
                        "text-[11px] font-semibold",
                        k.delta_pct > 0 ? "text-emerald-600" : k.delta_pct < 0 ? "text-rose-600" : "text-muted"
                      )}>
                        {k.delta_pct > 0 ? "↑" : k.delta_pct < 0 ? "↓" : "·"} {Math.abs(k.delta_pct).toFixed(1)}% WoW
                      </span>
                    ) : <span />}
                    <span className="text-[10px] text-muted-soft">{k.source}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Alerts */}
        {alerts.length > 0 && (
          <section>
            <div className="section-heading">
              <h2>⚡ Needs attention</h2>
              <span className="hint">{alerts.length} alert{alerts.length === 1 ? "" : "s"}</span>
            </div>
            <div className="space-y-2">
              {alerts.map((a, i) => (
                <BulletItem key={i} text={a.text} severity={a.severity} source={a.source} />
              ))}
            </div>
          </section>
        )}

        {/* Insights */}
        {insights.length > 0 && (
          <section>
            <div className="section-heading">
              <h2>What changed this week</h2>
              <span className="hint">Cited insights from your data</span>
            </div>
            <div className="space-y-2">
              {insights.map((it, i) => (
                <BulletItem key={i} text={it.text} severity={it.severity} source={it.source} />
              ))}
            </div>
          </section>
        )}

        {/* Top movers */}
        {movers.length > 0 && (
          <section>
            <div className="section-heading">
              <h2>Top movers</h2>
              <span className="hint">Wins and slips worth noting</span>
            </div>
            <div className="space-y-2">
              {movers.map((m, i) => (
                <BulletItem key={i} text={m.text} severity="info" source={m.source} />
              ))}
            </div>
          </section>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <section>
            <div className="section-heading">
              <h2>🎯 Recommended next moves</h2>
              <span className="hint">Cross-channel actions ranked by priority</span>
            </div>
            <div className="space-y-2">
              {recommendations.map((r: any, i: number) => (
                <BulletItem
                  key={i}
                  text={r.text}
                  severity={r.priority === "high" ? "urgent" : r.priority === "medium" ? "important" : "info"}
                  source={r.source}
                />
              ))}
            </div>
          </section>
        )}

        {snap?.elapsed_seconds != null && (
          <div className="text-[11px] text-muted-soft text-center pt-2">
            Generated in {snap.elapsed_seconds.toFixed(1)}s · cached for 6 hours · refresh anytime
          </div>
        )}
      </div>
      )}
    </div>
  );
}

function BulletItem({ text, severity, source }: { text: string; severity: string; source: string }) {
  return (
    <div className="card p-3.5 flex items-start gap-3">
      <span className={clsx("rounded-full mt-1.5 w-2 h-2 shrink-0", SEVERITY_DOT[severity] || "bg-slate-300")} />
      <div className="flex-1 min-w-0">
        <div className="text-[13.5px] text-ink leading-snug">{text}</div>
        <div className="text-[10.5px] text-muted mt-1 flex items-center gap-2">
          <span className={clsx("chip text-[10px]", SEVERITY_CHIP[severity] || "chip")}>{severity}</span>
          <span>Source: {source}</span>
        </div>
      </div>
    </div>
  );
}
