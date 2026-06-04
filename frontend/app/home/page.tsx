"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import { api, type BriefingItem } from "@/lib/api";
import { assetUrl } from "@/lib/backendUrl";
import { AttentionCard } from "@/components/home/AttentionCard";
import { BriefingDetailModal } from "@/components/home/BriefingDetailModal";
import { KpiTrendModal, type KpiCard } from "@/components/home/KpiTrendModal";

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

type HighlightCategory = "attention" | "changed" | "movers";
type HighlightItem = {
  id: string;
  category: HighlightCategory;
  text: string;
  severity: string;
  source: string;
  detail?: BriefingItem;
};

export default function HomePage() {
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard>(null);
  const [stale, setStale] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [loadedAt, setLoadedAt] = useState<number | null>(null);
  const [view, setView] = useState<"dashboard" | "summary">("dashboard");
  const [detailItem, setDetailItem] = useState<BriefingItem | null>(null);
  const [kpiTrend, setKpiTrend] = useState<KpiCard | null>(null);
  const [highlightFilter, setHighlightFilter] = useState<"all" | HighlightCategory>("all");
  const [showAllHighlights, setShowAllHighlights] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [pollCount, setPollCount] = useState(0);

  const load = useCallback(async () => {
    try {
      const r = await api.homeSnapshot(false);
      setSnap(r.snapshot);
      setDashboard(r.dashboard);
      setStale(r.stale);
      setRefreshing(r.refreshing);
      setLoadedAt(Date.now());
      setApiError(null);
      if (!r.refreshing) setPollCount(0);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Could not load briefing";
      setApiError(msg);
      console.warn("home snapshot failed", e);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!refreshing || apiError) return;
    if (pollCount >= 18) return;
    const t = setInterval(() => {
      setPollCount((n) => n + 1);
      load();
    }, 10000);
    return () => clearInterval(t);
  }, [refreshing, load, apiError, pollCount]);

  useEffect(() => {
    if (!detailItem) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setDetailItem(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [detailItem]);

  const onRefresh = async () => {
    setRefreshing(true);
    try { await api.homeForceRefresh(); } catch { /* network only */ }
  };

  const generatedAt = snap?.generated_at ? new Date(snap.generated_at * 1000) : null;
  const insights = snap?.insights ?? [];
  const movers = snap?.top_movers ?? [];
  const alerts = (snap?.alerts ?? []) as BriefingItem[];
  const kpis = snap?.kpis ?? [];
  const recommendations = (snap?.recommendations ?? []) as BriefingItem[];
  const empty = insights.length === 0 && movers.length === 0 && alerts.length === 0 && recommendations.length === 0;
  const erroredOut = snap?.status === "error";
  const highlights = useMemo<HighlightItem[]>(() => {
    const attention = alerts.map((a, i) => ({
      id: `a-${i}`,
      category: "attention" as const,
      text: a.text,
      severity: a.severity || a.priority || "important",
      source: a.source,
      detail: a,
    }));
    const changed = insights.map((it, i) => ({
      id: `c-${i}`,
      category: "changed" as const,
      text: it.text,
      severity: it.severity || "info",
      source: it.source,
    }));
    const topMovers = movers.map((m, i) => ({
      id: `m-${i}`,
      category: "movers" as const,
      text: m.text,
      severity: "info",
      source: m.source,
    }));
    const rank: Record<string, number> = { urgent: 0, important: 1, info: 2 };
    return [...attention, ...changed, ...topMovers].sort(
      (a, b) => (rank[a.severity] ?? 3) - (rank[b.severity] ?? 3),
    );
  }, [alerts, insights, movers]);
  const filteredHighlights = useMemo(
    () =>
      highlightFilter === "all"
        ? highlights
        : highlights.filter((h) => h.category === highlightFilter),
    [highlightFilter, highlights],
  );
  const visibleHighlights = showAllHighlights ? filteredHighlights : filteredHighlights.slice(0, 8);

  return (
    <div className="flex-1 overflow-y-auto thin-scroll">
      <BriefingDetailModal item={detailItem} onClose={() => setDetailItem(null)} />
      <KpiTrendModal kpi={kpiTrend} onClose={() => setKpiTrend(null)} />

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
              Auto-pilot pulls from all your data sources and surfaces what changed. Click a KPI for its trend chart; click any alert for cause, evidence, and next steps.
              {generatedAt && <span> Last run: {generatedAt.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}.</span>}
            </p>
          </div>
          <div className="flex items-center gap-2">
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
              <a href={assetUrl(dashboard.url)} target="_blank" rel="noreferrer" className="btn-ghost text-[12px]" title="Open the full dashboard in a new tab">
                Open ↗
              </a>
            )}
          </div>
        </div>
      </header>

      {apiError && (
        <div className="mx-8 mt-6 card p-4" style={{ background: "#FEF2F2", borderColor: "rgba(239,68,68,0.3)" }}>
          <div className="text-sm font-semibold" style={{ color: "#B91C1C" }}>Could not load briefing data</div>
          <div className="text-[12px] mt-1" style={{ color: "#7F1D1D" }}>{apiError}</div>
          <p className="text-[12px] mt-2" style={{ color: "#7F1D1D" }}>
            Deploy the Python backend and set Vercel env vars{" "}
            <code className="text-[11px]">NEXT_PUBLIC_BACKEND_URL</code> and{" "}
            <code className="text-[11px]">NEXT_PUBLIC_BACKEND_WS_URL</code>. On the backend use{" "}
            <code className="text-[11px]">V2_PUBLIC_ACCESS=1</code> for prototype access.
          </p>
        </div>
      )}

      {refreshing && pollCount >= 18 && !apiError && (
        <div className="mx-8 mt-4 card p-3 text-[12px]" style={{ background: "#FFFBEB", borderColor: "rgba(245,158,11,0.3)", color: "#78350F" }}>
          Briefing refresh is taking longer than usual (~3 min). The backend may still be analyzing, or the API connection may be slow — try Refresh again or check the banner above.
        </div>
      )}

      {dashboard && view === "dashboard" && (
        <div className="flex-1 relative" style={{ minHeight: "calc(100vh - 120px)" }}>
          <iframe
            src={assetUrl(dashboard.url)}
            className="w-full h-full block border-0"
            style={{ minHeight: "calc(100vh - 120px)" }}
            title="Sourcy comprehensive dashboard"
          />
          <div className="absolute bottom-3 right-3 chip text-[10px]" style={{ background: "rgba(255,255,255,0.9)" }}>
            Dashboard from {new Date(dashboard.generated_at * 1000).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })} · {dashboard.size_kb} KB
          </div>
        </div>
      )}

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

        {kpis.length > 0 && (
          <section>
            <div className="section-heading">
              <h2>KPIs · last 7 days</h2>
              <span className="hint">Click a metric for daily trend & why it moved</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {kpis.map((k, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setKpiTrend(k)}
                  className="card p-4 text-left transition-shadow hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50 cursor-pointer"
                  title="View 7-day trend chart"
                >
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
                </button>
              ))}
            </div>
          </section>
        )}

        {highlights.length > 0 && (
          <section className="card p-4 md:p-5">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <h2 className="text-base font-semibold text-ink">Weekly highlights</h2>
                <p className="text-[12px] text-muted mt-0.5">
                  Consolidated view of needs attention, changes, and top movers.
                </p>
              </div>
              <div className="inline-flex rounded-lg border" style={{ borderColor: "var(--border)" }}>
                {[
                  { id: "all", label: `All (${highlights.length})` },
                  { id: "attention", label: `Needs attention (${alerts.length})` },
                  { id: "changed", label: `Changed (${insights.length})` },
                  { id: "movers", label: `Top movers (${movers.length})` },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setHighlightFilter(tab.id as any);
                      setShowAllHighlights(false);
                    }}
                    className={clsx(
                      "px-2.5 py-1.5 text-[11px] md:text-[12px] font-medium transition-colors border-r last:border-r-0",
                      highlightFilter === tab.id ? "bg-ink text-white" : "text-muted hover:text-ink",
                    )}
                    style={{ borderColor: "var(--border)" }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 space-y-2">
              {visibleHighlights.map((item) => (
                <CompactHighlightRow
                  key={item.id}
                  item={item}
                  onOpenDetail={item.detail ? () => setDetailItem(item.detail!) : undefined}
                />
              ))}
            </div>

            {filteredHighlights.length > 8 && (
              <div className="mt-3 flex justify-center">
                <button
                  className="btn-ghost text-[12px]"
                  onClick={() => setShowAllHighlights((v) => !v)}
                >
                  {showAllHighlights
                    ? "Show less"
                    : `Show ${filteredHighlights.length - 8} more`}
                </button>
              </div>
            )}
          </section>
        )}

        {recommendations.length > 0 && (
          <section>
            <div className="section-heading">
              <h2>🎯 Recommended next moves</h2>
              <span className="hint">Click any item for cause, evidence & steps</span>
            </div>
            <div className="space-y-2">
              {recommendations.map((r, i) => (
                <AttentionCard key={i} item={r} onClick={() => setDetailItem(r)} />
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

function CompactHighlightRow({
  item,
  onOpenDetail,
}: {
  item: HighlightItem;
  onOpenDetail?: () => void;
}) {
  const categoryLabel: Record<HighlightCategory, string> = {
    attention: "Needs attention",
    changed: "What changed",
    movers: "Top mover",
  };
  const row = (
    <div className="card p-3 flex items-start gap-2.5">
      <span className={clsx("rounded-full mt-1.5 w-2 h-2 shrink-0", SEVERITY_DOT[item.severity] || "bg-slate-300")} />
      <div className="min-w-0 flex-1">
        <div className="text-[13px] text-ink leading-snug">{item.text}</div>
        <div className="text-[10.5px] text-muted mt-1 flex items-center flex-wrap gap-2">
          <span className={clsx("chip text-[10px]", SEVERITY_CHIP[item.severity] || "chip")}>{item.severity}</span>
          <span className="chip text-[10px]">{categoryLabel[item.category]}</span>
          <span>Source: {item.source}</span>
        </div>
      </div>
    </div>
  );
  if (!onOpenDetail) return row;
  return (
    <button
      type="button"
      onClick={onOpenDetail}
      className="w-full text-left rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/40"
      title="Open cause, evidence & next steps"
    >
      {row}
    </button>
  );
}
