"use client";

import type { ReactNode } from "react";
import clsx from "clsx";
import { displayPublicPageUrl, resolveBriefingDetail } from "@/lib/briefingDetail";

export type BriefingDetail = {
  cause: string;
  evidence: string;
  pages: string[];
  suggestion: string;
  next_step: string;
};

export type BriefingItem = {
  text: string;
  severity?: string;
  source: string;
  priority?: string;
  detail?: BriefingDetail;
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
  item: BriefingItem | null;
  onClose: () => void;
};

function formatPage(page: string): { label: string; href: string | null } {
  const p = page.trim();
  if (!p) return { label: "", href: null };
  if (p.startsWith("http://") || p.startsWith("https://") || p.startsWith("www.")) {
    const href = p.startsWith("www.") ? `https://${p}` : p;
    return { label: displayPublicPageUrl(href), href };
  }
  if (p.startsWith("/")) {
    const href = `https://www.sourcy.ai${p}`;
    return { label: displayPublicPageUrl(href), href };
  }
  return { label: p, href: null };
}

export function BriefingDetailModal({ item, onClose }: Props) {
  if (!item) return null;

  const d = resolveBriefingDetail(item);
  const severity = item.severity || item.priority || "info";
  const pages = (d.pages ?? []).filter(Boolean);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
      <button
        type="button"
        className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
        aria-label="Close"
        onClick={onClose}
      />
      <div
        className="relative card w-full max-w-lg max-h-[min(88vh,720px)] overflow-hidden flex flex-col shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="briefing-detail-title"
      >
        <div className="flex items-start justify-between gap-3 px-5 pt-5 pb-3 border-b shrink-0" style={{ borderColor: "var(--border)" }}>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className={clsx("chip text-[10px]", SEVERITY_CHIP[severity] || "chip")}>{severity}</span>
              <span className="text-[10px] text-muted">Source: {item.source}</span>
            </div>
            <h2 id="briefing-detail-title" className="text-base font-semibold text-ink leading-snug">
              {item.text}
            </h2>
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
          <DetailSection title="What's the cause?" body={d.cause} />
          <DetailSection title="Evidence & specific pages" body={d.evidence}>
            {pages.length > 0 && (
              <ul className="mt-2 space-y-1">
                {pages.map((page, i) => {
                  const { label, href } = formatPage(page);
                  return (
                    <li key={i} className="text-[12.5px]">
                      {href ? (
                        <a
                          href={href}
                          target="_blank"
                          rel="noreferrer"
                          className="text-cyan-700 hover:underline font-medium break-all"
                        >
                          {label}
                        </a>
                      ) : (
                        <span className="text-ink font-medium break-all">{label}</span>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </DetailSection>
          <DetailSection title="Suggestion" body={d.suggestion} />
          <DetailSection title="Next step" body={d.next_step} highlight />
        </div>

        <div className="px-5 py-3 border-t shrink-0 flex justify-end gap-2" style={{ borderColor: "var(--border)" }}>
          <button type="button" className="btn-secondary text-[12px]" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function DetailSection({
  title,
  body,
  children,
  highlight,
}: {
  title: string;
  body: string;
  children?: ReactNode;
  highlight?: boolean;
}) {
  return (
    <section
      className={clsx(
        "rounded-lg p-3.5",
        highlight ? "border" : "bg-bg-alt"
      )}
      style={highlight ? { background: "#F0FDFA", borderColor: "rgba(6,182,212,0.35)" } : undefined}
    >
      <h3 className="text-[11px] uppercase tracking-wider font-semibold text-muted mb-1.5">{title}</h3>
      {body && (
        <p className="text-[13px] text-ink leading-relaxed whitespace-pre-wrap">{body}</p>
      )}
      {children}
    </section>
  );
}
