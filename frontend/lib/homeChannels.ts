import type { BriefingItem } from "./api";

export type ChannelGroup = { id: string; label: string; items: BriefingItem[] };

const CHANNELS: Array<{ id: string; label: string; match: (source: string) => boolean }> = [
  { id: "ga4", label: "GA4 & website", match: (s) => /ga4|analytics/i.test(s) },
  { id: "seo", label: "SEO / Search Console", match: (s) => /search console|gsc|seo/i.test(s) },
  { id: "google_ads", label: "Google Ads", match: (s) => /google ads/i.test(s) },
  { id: "meta", label: "Meta Ads", match: (s) => /meta/i.test(s) && !/instagram/i.test(s) },
  { id: "instagram", label: "Instagram / social", match: (s) => /instagram|social/i.test(s) },
  { id: "posthog", label: "PostHog", match: (s) => /posthog/i.test(s) },
  { id: "sourcy_db", label: "Sourcy DB / leads", match: (s) => /sourcy|db|lead/i.test(s) },
];

export function groupRecommendationsByChannel(items: BriefingItem[]): ChannelGroup[] {
  const buckets = new Map<string, ChannelGroup>();
  const other: BriefingItem[] = [];

  for (const item of items) {
    const src = item.source || "";
    const channel = CHANNELS.find((c) => c.match(src));
    if (!channel) {
      other.push(item);
      continue;
    }
    if (!buckets.has(channel.id)) {
      buckets.set(channel.id, { id: channel.id, label: channel.label, items: [] });
    }
    buckets.get(channel.id)!.items.push(item);
  }

  const ordered = CHANNELS.map((c) => buckets.get(c.id)).filter((g): g is ChannelGroup => Boolean(g?.items.length));
  if (other.length) {
    ordered.push({ id: "other", label: "Other", items: other });
  }
  return ordered;
}
