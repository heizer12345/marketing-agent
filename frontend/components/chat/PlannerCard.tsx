"use client";

import type { Planner } from "@/lib/types";

export function PlannerCard({ planner }: { planner: Planner }) {
  return (
    <div className="card p-5">
      <div className="flex items-center gap-2.5 mb-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center text-white text-sm font-bold shadow-sm"
             style={{ background: "linear-gradient(135deg, #06B6D4 0%, #0891B2 100%)" }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
            <circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/>
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-ink leading-tight">{planner.name || "Planner"}</div>
          <div className="text-[11.5px] text-muted leading-tight flex items-center gap-1.5 mt-0.5">
            {planner.activity ? (
              <>
                <span className="status-dot running" />
                <span className="truncate">{planner.activity}</span>
              </>
            ) : (
              "Routing your request to the right specialists"
            )}
          </div>
        </div>
      </div>

      {planner.prompt && (
        <div className="text-[12px] mb-3 rounded-md px-3 py-2 leading-snug" style={{ background: "var(--bg-alt)", color: "var(--ink-soft)" }}>
          <span className="label-strong mr-2">You asked:</span>
          {planner.prompt}
        </div>
      )}

      {planner.text && (
        <div className="text-[13px] text-ink whitespace-pre-wrap leading-relaxed">
          {planner.text}
        </div>
      )}
    </div>
  );
}
