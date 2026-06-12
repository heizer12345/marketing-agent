"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import type { BriefingItem } from "@/lib/api";
import { groupRecommendationsByChannel, type ChannelGroup } from "@/lib/homeChannels";
import { AttentionCard } from "@/components/home/AttentionCard";

type Props = {
  items: BriefingItem[];
  onSelect: (item: BriefingItem) => void;
};

export function RecommendationChannelTabs({ items, onSelect }: Props) {
  const groups = groupRecommendationsByChannel(items);
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    if (!groups.length) {
      setActiveId(null);
      return;
    }
    if (!activeId || !groups.some((g) => g.id === activeId)) {
      setActiveId(groups[0].id);
    }
  }, [groups, activeId]);

  if (!groups.length) return null;

  const active = groups.find((g) => g.id === activeId) ?? groups[0];

  return (
    <section>
      <div className="section-heading">
        <h2>🎯 Recommended next moves</h2>
        <span className="hint">Pick a channel · click a card for detail</span>
      </div>

      <div
        className="flex flex-wrap gap-1 p-1 rounded-lg border bg-bg-alt"
        style={{ borderColor: "var(--border)" }}
        role="tablist"
        aria-label="Recommendation channels"
      >
        {groups.map((group) => (
          <button
            key={group.id}
            type="button"
            role="tab"
            aria-selected={active.id === group.id}
            onClick={() => setActiveId(group.id)}
            className={clsx(
              "px-3 py-1.5 rounded-md text-[12px] font-medium transition-colors",
              active.id === group.id
                ? "bg-ink text-white shadow-sm"
                : "text-muted hover:text-ink hover:bg-white",
            )}
          >
            {tabShortLabel(group)}
            <span className={clsx("ml-1.5 tabular-nums", active.id === group.id ? "opacity-80" : "opacity-60")}>
              ({group.items.length})
            </span>
          </button>
        ))}
      </div>

      <div className="mt-3 space-y-2" role="tabpanel">
        {active.items.map((item, i) => (
          <AttentionCard key={`${active.id}-${i}`} item={item} onClick={() => onSelect(item)} />
        ))}
      </div>
    </section>
  );
}

function tabShortLabel(group: ChannelGroup): string {
  const short: Record<string, string> = {
    ga4: "GA4",
    seo: "SEO",
    google_ads: "Google Ads",
    meta: "Meta Ads",
    instagram: "Instagram",
    posthog: "PostHog",
    sourcy_db: "Leads",
    other: "Other",
  };
  return short[group.id] ?? group.label;
}
