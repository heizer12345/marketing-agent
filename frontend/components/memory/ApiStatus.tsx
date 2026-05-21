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
};

export function ApiStatus({ status }: { status: Record<string, boolean> }) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted">
        These connections feed the Home dashboard refresh and the analysis sub-agents. Set values in <code>.env</code>.
      </p>
      <div className="grid grid-cols-2 gap-3">
        {Object.entries(LABELS).map(([key, meta]) => (
          <div key={key} className="card p-4 flex items-start gap-3">
            <span
              className={
                "mt-1 w-2.5 h-2.5 rounded-full " +
                (status[key] ? "bg-emerald-500" : "bg-slate-300")
              }
              title={status[key] ? "Connected" : "Not connected"}
            />
            <div>
              <div className="text-sm font-medium text-ink">{meta.name}</div>
              <div className="text-xs text-muted">{meta.hint}</div>
              <div className="mt-1 text-[11px] uppercase tracking-wide font-medium">
                {status[key] ? <span className="text-emerald-600">Connected</span> : <span className="text-muted">Missing</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
