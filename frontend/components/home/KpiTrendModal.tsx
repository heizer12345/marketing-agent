"use client";

import { useEffect, useId, useMemo, useState } from "react";
import clsx from "clsx";
import { api, type KpiTrendResponse, type KpiTrendPoint } from "@/lib/api";

type ChartPoint = KpiTrendPoint & { x: number; y: number };

function explanationBullets(trend: KpiTrendResponse): string[] {
  if (trend.explanation_bullets?.length) return trend.explanation_bullets;
  const raw = (trend.explanation || "").trim();
  if (!raw) return [];
  const split = raw.split(/(?<=\.)\s+(?=\S)/).map((s) => s.trim()).filter((s) => s.length > 12);
  return split.length > 1 ? split : [raw];
}

function formatMetricValue(value: number, unit?: string): string {
  const n = Number.isInteger(value)
    ? value.toLocaleString()
    : value.toLocaleString(undefined, { maximumFractionDigits: 1 });
  if (!unit) return n;
  if (unit === "USD") return `$${n}`;
  return `${n} ${unit}`;
}

function dayOverDay(points: ChartPoint[], index: number): { delta: number; pct: number | null } | null {
  if (index <= 0) return null;
  const prev = points[index - 1].value;
  const cur = points[index].value;
  const delta = cur - prev;
  const pct = prev !== 0 ? (delta / prev) * 100 : null;
  return { delta, pct };
}

export type KpiCard = {
  label: string;
  value: string | number;
  delta_pct?: number;
  source: string;
};

type Props = {
  kpi: KpiCard | null;
  onClose: () => void;
};

export function KpiTrendModal({ kpi, onClose }: Props) {
  const [trend, setTrend] = useState<KpiTrendResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!kpi) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [kpi, onClose]);

  useEffect(() => {
    if (!kpi) {
      setTrend(null);
      setErr(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setErr(null);
    api
      .kpiTrend(kpi.label, kpi.source)
      .then((r) => {
        if (!cancelled) setTrend(r);
      })
      .catch((e) => {
        if (!cancelled) setErr(String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [kpi]);

  if (!kpi) return null;

  const displayDelta = trend?.delta_pct ?? kpi.delta_pct;
  const unit = trend?.unit;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      <button
        type="button"
        className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
        aria-label="Close"
        onClick={onClose}
      />
      <div
        className="relative card w-full max-w-lg max-h-[min(90vh,720px)] overflow-hidden flex flex-col shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="kpi-trend-title"
      >
        <div
          className="flex items-start justify-between gap-3 px-5 pt-5 pb-3 border-b shrink-0"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="min-w-0 flex-1">
            <div className="text-[10px] text-muted uppercase tracking-wider">KPI trend · last 7–14 days</div>
            <h2 id="kpi-trend-title" className="text-base font-semibold text-ink mt-0.5">
              {kpi.label}
            </h2>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="text-xl font-bold text-ink">{kpi.value}</span>
              {typeof displayDelta === "number" && (
                <span
                  className={clsx(
                    "text-[12px] font-semibold",
                    displayDelta > 0 ? "text-emerald-600" : displayDelta < 0 ? "text-rose-600" : "text-muted",
                  )}
                >
                  {displayDelta > 0 ? "↑" : displayDelta < 0 ? "↓" : "·"} {Math.abs(displayDelta).toFixed(1)}% WoW
                </span>
              )}
              <span className="text-[10px] text-muted-soft">{kpi.source}</span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-muted hover:text-ink hover:bg-bg-alt text-lg"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="overflow-y-auto thin-scroll px-5 py-4 space-y-4 flex-1">
          {loading && (
            <div className="py-10 text-center text-[13px] text-muted">Loading daily trend…</div>
          )}
          {err && !loading && (
            <div className="text-[13px] text-rose-700 rounded-lg p-3" style={{ background: "#FEF2F2" }}>
              {err}
            </div>
          )}
          {!loading && (trend?.series?.length ?? 0) > 0 && (
            <KpiTrendChart
              label={kpi.label}
              series={trend!.series}
              unit={unit}
            />
          )}
          {!loading && (trend?.series?.length ?? 0) === 0 && !err && (
            <p className="text-[13px] text-muted">No daily series available for this metric yet.</p>
          )}

          {trend?.drivers && trend.drivers.length > 0 && (
            <section>
              <h3 className="text-[11px] uppercase tracking-wider font-semibold text-muted mb-2">
                Top drivers (channels)
              </h3>
              <ul className="space-y-1.5">
                {trend.drivers.map((d, i) => (
                  <li
                    key={i}
                    className="flex items-center justify-between text-[12.5px] rounded-md px-2.5 py-1.5 bg-white border"
                    style={{ borderColor: "var(--border)" }}
                  >
                    <span className="font-medium text-ink truncate pr-2">{d.label}</span>
                    <span
                      className={clsx(
                        "shrink-0 font-semibold tabular-nums",
                        d.change_pct > 0 ? "text-emerald-600" : d.change_pct < 0 ? "text-rose-600" : "text-muted",
                      )}
                    >
                      {d.change_pct > 0 ? "+" : ""}
                      {d.change_pct.toFixed(1)}%
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {trend && explanationBullets(trend).length > 0 && (
            <section
              className="rounded-lg p-3.5 border"
              style={{ background: "#F0FDFA", borderColor: "rgba(6,182,212,0.35)" }}
            >
              <h3 className="text-[11px] uppercase tracking-wider font-semibold text-muted mb-2">
                Why it moved
              </h3>
              <ul className="space-y-2 list-none m-0 p-0">
                {explanationBullets(trend).map((bullet, i) => (
                  <li key={i} className="flex gap-2 text-[13px] text-ink leading-snug">
                    <span
                      className="shrink-0 w-1.5 h-1.5 rounded-full mt-[0.45rem]"
                      style={{ background: "#0891B2" }}
                      aria-hidden
                    />
                    <ExplanationBullet text={bullet} />
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <div
          className="px-5 py-3 border-t shrink-0 flex justify-end"
          style={{ borderColor: "var(--border)" }}
        >
          <button type="button" className="btn-secondary text-[12px]" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

/** Renders optional **bold** labels inside explanation bullets. */
function ExplanationBullet({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return (
    <span>
      {parts.map((part, i) =>
        part.startsWith("**") && part.endsWith("**") ? (
          <strong key={i} className="font-semibold text-ink">
            {part.slice(2, -2)}
          </strong>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </span>
  );
}

function KpiTrendChart({
  label,
  series,
  unit,
}: {
  label: string;
  series: KpiTrendPoint[];
  unit?: string;
}) {
  const gradientId = useId().replace(/:/g, "");
  const [hovered, setHovered] = useState<number | null>(null);

  const chartH = 160;
  const chartW = 480;
  const pad = { l: 12, r: 12, t: 36, b: 28 };
  const innerW = chartW - pad.l - pad.r;
  const innerH = chartH - pad.t - pad.b;

  const { points, linePath, areaPath } = useMemo(() => {
    const max = Math.max(...series.map((p) => p.value), 1);
    const pts: ChartPoint[] =
      series.length > 1
        ? series.map((p, i) => {
            const x = pad.l + (i / (series.length - 1)) * innerW;
            const y = pad.t + innerH - (p.value / max) * innerH;
            return { x, y, ...p };
          })
        : series.length === 1
          ? [{ x: pad.l + innerW / 2, y: pad.t + innerH / 2, ...series[0] }]
          : [];

    const line =
      pts.length > 1
        ? pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ")
        : "";
    const area =
      pts.length > 1
        ? `${line} L ${pts[pts.length - 1].x.toFixed(1)} ${pad.t + innerH} L ${pts[0].x.toFixed(1)} ${pad.t + innerH} Z`
        : "";

    return { points: pts, linePath: line, areaPath: area };
  }, [series, innerW, innerH, pad.l, pad.t]);

  const active = hovered !== null ? points[hovered] : null;
  const dod = hovered !== null ? dayOverDay(points, hovered) : null;
  const tooltipLeftPct =
    points.length > 1 && hovered !== null
      ? (hovered / (points.length - 1)) * 100
      : 50;

  return (
    <div
      className="rounded-lg border p-3 bg-bg-alt"
      style={{ borderColor: "var(--border)" }}
      onMouseLeave={() => setHovered(null)}
    >
      <p className="text-[10px] text-muted mb-2">Hover a point for daily value and day-over-day change</p>
      <div className="relative">
        {active && (
          <div
            className="absolute z-10 pointer-events-none -translate-x-1/2 min-w-[120px] max-w-[200px] rounded-lg border px-2.5 py-2 shadow-md text-center"
            style={{
              left: `${tooltipLeftPct}%`,
              top: 0,
              background: "rgba(255,255,255,0.98)",
              borderColor: "rgba(6,182,212,0.45)",
            }}
          >
            <div className="text-[10px] font-medium text-muted">{active.date}</div>
            <div className="text-[15px] font-bold text-ink tabular-nums leading-tight mt-0.5">
              {formatMetricValue(active.value, unit)}
            </div>
            {dod ? (
              <div
                className={clsx(
                  "text-[11px] font-semibold tabular-nums mt-0.5",
                  dod.delta > 0 ? "text-emerald-600" : dod.delta < 0 ? "text-rose-600" : "text-muted",
                )}
              >
                {dod.delta > 0 ? "+" : ""}
                {formatMetricValue(dod.delta, unit)}
                {dod.pct !== null && (
                  <span className="text-muted font-medium">
                    {" "}
                    ({dod.pct > 0 ? "+" : ""}
                    {dod.pct.toFixed(1)}% vs prior day)
                  </span>
                )}
              </div>
            ) : (
              <div className="text-[10px] text-muted mt-0.5">First day in range</div>
            )}
          </div>
        )}
        <svg
          viewBox={`0 0 ${chartW} ${chartH}`}
          className="w-full h-auto"
          role="img"
          aria-label={`${label} daily trend`}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(6,182,212,0.35)" />
              <stop offset="100%" stopColor="rgba(6,182,212,0.02)" />
            </linearGradient>
          </defs>
          {areaPath && <path d={areaPath} fill={`url(#${gradientId})`} />}
          {hovered !== null && points[hovered] && (
            <line
              x1={points[hovered].x}
              y1={pad.t}
              x2={points[hovered].x}
              y2={pad.t + innerH}
              stroke="rgba(6,182,212,0.35)"
              strokeWidth="1"
              strokeDasharray="4 3"
            />
          )}
          {linePath && (
            <path d={linePath} fill="none" stroke="#0891B2" strokeWidth="2.5" strokeLinecap="round" />
          )}
          {points.map((p, i) => {
            const isActive = hovered === i;
            return (
              <g
                key={i}
                onMouseEnter={() => setHovered(i)}
                onFocus={() => setHovered(i)}
                style={{ cursor: "pointer" }}
                tabIndex={0}
                role="button"
                aria-label={`${p.date}: ${formatMetricValue(p.value, unit)}`}
              >
                <circle cx={p.x} cy={p.y} r="14" fill="transparent" />
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={isActive ? 6 : 3.5}
                  fill={isActive ? "#0E7490" : "#0891B2"}
                  stroke={isActive ? "#fff" : "none"}
                  strokeWidth={isActive ? 2 : 0}
                  className="transition-all duration-150"
                />
                {(isActive || i === 0 || i === points.length - 1) && (
                  <text x={p.x} y={chartH - 6} textAnchor="middle" fontSize="9" fill={isActive ? "#0E7490" : "#64748B"} fontWeight={isActive ? 600 : 400}>
                    {p.date}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
