"use client";

const LABELS: Record<string, { name: string; hint: string }> = {
  openai: { name: "OpenAI", hint: "Required for all generation skills + GPT Image 2." },
  ga4: { name: "Google Analytics (GA4)", hint: "Traffic, sessions, conversions." },
  search_console: { name: "Search Console", hint: "Organic keyword rankings, CTR." },
  google_ads: { name: "Google Ads", hint: "Paid search spend + performance." },
  meta_ads: { name: "Meta Ads", hint: "Facebook + Instagram ad performance." },
  semrush: { name: "SEMrush", hint: "Competitor data, keyword research." },
  instagram: { name: "Instagram", hint: "Organic IG post performance." },
  posthog: { name: "PostHog", hint: "Funnel analysis, product analytics." },
  sourcy_db: { name: "Sourcy DB", hint: "Real leads and activation funnel (ground truth)." },
};

export function ApiStatus({
  status,
  detail,
  checkedAt,
  onRefresh,
  refreshing,
}: {
  status: Record<string, boolean>;
  detail?: Record<string, { ok?: boolean; detail?: string; sessions_7d?: string; events_7d?: string }>;
  checkedAt?: number;
  onRefresh?: () => void;
  refreshing?: boolean;
}) {
  const okCount = Object.values(status).filter(Boolean).length;
  const total = Object.keys(LABELS).length;

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted">
            Live API checks — not just whether keys exist in <code>.env</code>. Green means the
            backend reached the service and got a response. Home briefing data is cached up to 6
            hours; use <strong>Refresh</strong> on Home for newer analysis.
          </p>
          <p className="text-[12px] text-muted mt-2">
            {okCount}/{total} connected
            {checkedAt ? (
              <> · checked {new Date(checkedAt * 1000).toLocaleString()}</>
            ) : null}
          </p>
        </div>
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
            className="btn-secondary text-[12px] shrink-0"
          >
            {refreshing ? "Checking…" : "Re-check APIs"}
          </button>
        )}
      </div>
      <div className="grid grid-cols-2 gap-3">
        {Object.entries(LABELS).map(([key, meta]) => {
          const live = detail?.[key];
          const connected = status[key];
          return (
            <div key={key} className="card p-4 flex items-start gap-3">
              <span
                className={
                  "mt-1 w-2.5 h-2.5 rounded-full shrink-0 " +
                  (connected ? "bg-emerald-500" : "bg-slate-300")
                }
                title={connected ? "Live check passed" : "Failed or not configured"}
              />
              <div className="min-w-0">
                <div className="text-sm font-medium text-ink">{meta.name}</div>
                <div className="text-xs text-muted">{meta.hint}</div>
                <div className="mt-1 text-[11px] uppercase tracking-wide font-medium">
                  {connected ? (
                    <span className="text-emerald-600">Connected</span>
                  ) : (
                    <span className="text-rose-600">Unavailable</span>
                  )}
                </div>
                {live?.detail && (
                  <div
                    className={
                      "mt-1 text-[11px] leading-snug " +
                      (connected ? "text-muted" : "text-rose-700/80")
                    }
                  >
                    {live.detail}
                    {live.sessions_7d != null && ` · ${live.sessions_7d} sessions (7d)`}
                    {live.events_7d != null && ` · ${live.events_7d} events (7d)`}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
