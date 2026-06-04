"use client";

import clsx from "clsx";
import type { BriefingItem } from "./BriefingDetailModal";

const SEVERITY_DOT: Record<string, string> = {
  urgent: "bg-rose-500",
  important: "bg-amber-500",
  info: "bg-cyan-500",
  high: "bg-rose-500",
  medium: "bg-amber-500",
  low: "bg-cyan-500",
};

const SEVERITY_CHIP: Record<string, string> = {
  urgent: "chip-rose",
  important: "chip-amber",
  info: "chip",
  high: "chip-rose",
  medium: "chip-amber",
  low: "chip",
};

type Props = {
  item: BriefingItem;
  onClick: () => void;
};

export function AttentionCard({ item, onClick }: Props) {
  const severity = item.severity || item.priority || "info";
  const pageCount =
    item.detail?.pages?.filter(Boolean).length ??
    (item.text?.match(/\/[a-zA-Z][\w\-./]*/g)?.length ?? 0);

  return (
    <button
      type="button"
      onClick={onClick}
      className="card p-3.5 flex items-start gap-3 w-full text-left transition-shadow hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/40 group"
    >
      <span
        className={clsx(
          "rounded-full mt-1.5 w-2 h-2 shrink-0",
          SEVERITY_DOT[severity] || "bg-slate-300"
        )}
      />
      <div className="flex-1 min-w-0">
        <div className="text-[13.5px] text-ink leading-snug pr-6">{item.text}</div>
        <div className="text-[10.5px] text-muted mt-1.5 flex items-center flex-wrap gap-2">
          <span className={clsx("chip text-[10px]", SEVERITY_CHIP[severity] || "chip")}>{severity}</span>
          <span>Source: {item.source}</span>
          {pageCount > 0 && (
            <span className="text-muted-soft">{pageCount} page{pageCount === 1 ? "" : "s"} cited</span>
          )}
        </div>
        <div className="text-[11px] font-medium mt-2 text-cyan-700 group-hover:underline">
          View cause, evidence & next step →
        </div>
      </div>
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        className="w-4 h-4 text-muted shrink-0 mt-1 opacity-60 group-hover:opacity-100"
        aria-hidden
      >
        <polyline points="9,18 15,12 9,6" />
      </svg>
    </button>
  );
}
