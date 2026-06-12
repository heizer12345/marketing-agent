import type { BriefingDetail, BriefingItem } from "./api";



export const PUBLIC_SITE_ORIGIN = "https://www.sourcy.ai";

const ONBOARD_PAGE = `${PUBLIC_SITE_ORIGIN}/onboard`;



const PATH_RE = /(?:https?:\/\/(?:www\.)?sourcy\.ai)?(\/[a-zA-Z0-9_\-./%]+)|(?:^|[\s(])(\/[a-zA-Z][a-zA-Z0-9_\-./]*)/gi;



/** Display form: www.sourcy.ai/onboard */

export function displayPublicPageUrl(url: string): string {

  const p = url.trim();

  if (!p) return p;

  return p.replace(/^https?:\/\/(www\.)?/i, "www.");

}



export function toPublicPageUrl(page: string): string {

  const p = page.trim();

  if (!p) return p;

  if (p.startsWith("www.")) return `https://${p}`;

  if (p.startsWith("http://") || p.startsWith("https://")) {

    try {

      const u = new URL(p);

      if (u.hostname.replace(/^www\./, "").endsWith("sourcy.ai")) {

        return `${PUBLIC_SITE_ORIGIN}${u.pathname || "/"}`;

      }

    } catch {

      /* keep as-is */

    }

    return p;

  }

  const path = p.startsWith("/") ? p : `/${p}`;

  return `${PUBLIC_SITE_ORIGIN}${path}`;

}



function normalizePages(pages: string[]): string[] {

  const out: string[] = [];

  const seen = new Set<string>();

  for (const raw of pages) {

    const full = toPublicPageUrl(raw);

    if (full && !seen.has(full)) {

      seen.add(full);

      out.push(full);

    }

  }

  return out;

}



function pageMatches(page: string, fragment: string): boolean {

  return page.toLowerCase().includes(fragment.toLowerCase());

}



function extractPages(text: string): string[] {

  const pages: string[] = [];

  const seen = new Set<string>();

  let m: RegExpExecArray | null;

  const re = new RegExp(PATH_RE.source, PATH_RE.flags);

  while ((m = re.exec(text)) !== null) {

    const path = (m[1] || m[2] || "").trim();

    if (!path || path === "/") continue;

    const full = toPublicPageUrl(path);

    if (seen.has(full)) continue;

    seen.add(full);

    pages.push(full);

  }

  if (/onboard/i.test(text) && !seen.has(ONBOARD_PAGE)) {

    pages.unshift(ONBOARD_PAGE);

  }

  return normalizePages(pages).slice(0, 8);

}



/** Client-side fallback when API snapshot lacks detail (older cache / stale server). */

export function resolveBriefingDetail(item: BriefingItem): BriefingDetail {

  const d = item.detail;

  const text = item.text?.trim() || "";

  const source = item.source || "data";

  const rawPages = d?.pages?.length ? d.pages : extractPages(text);

  const pages = normalizePages(rawPages).filter(Boolean);



  const low = text.toLowerCase();

  const onboardLabel = displayPublicPageUrl(ONBOARD_PAGE);



  let cause = d?.cause?.trim() || "";

  if (!cause) {

    if (low.includes("0 downstream conversion") || (low.includes("0 conversion") && low.includes("onboard"))) {

      cause =

        `Traffic reaches ${onboardLabel} but GA4 and PostHog record zero downstream conversions — usually broken event tags, consent blocking, or a funnel step mismatch.`;

    } else if (low.includes("china") && (low.includes("exit") || low.includes("immediate"))) {

      cause =

        "High China session share with almost no engagement — often bot traffic, mis-targeted ads, or non-ICP visitors.";

    } else if (low.includes("spent $0") || low.includes("spend $0")) {

      cause =

        "Google Ads reported $0 spend (7d). Campaigns are likely paused or not running — confirm status in Ads Manager before treating as a delivery issue.";

    } else {

      cause = `This item was flagged from ${source} because last-7-day metrics crossed a risk threshold or conflicted with another source.`;

    }

  }



  let evidence = d?.evidence?.trim() || text;

  if (!d?.evidence?.trim() && text) {

    evidence = `Headline: ${text}\nSource: ${source} · Review period: last 7 days`;

  }



  let suggestion = d?.suggestion?.trim() || "";

  if (!suggestion) {

    if (low.includes("onboard") && low.includes("0")) {

      suggestion =

        `Align GA4 conversion events with PostHog funnel steps on ${onboardLabel}; confirm onboarding_start fires on the first real user action.`;

    } else if (pages.some((p) => pageMatches(p, "/sourcing/"))) {

      const label = displayPublicPageUrl(pages[0]);

      suggestion = `Improve title and meta description on ${label} to lift CTR from current Search Console levels.`;

    } else {

      suggestion = `Validate this metric in the native ${source} UI before changing spend or content.`;

    }

  }



  let next_step = d?.next_step?.trim() || "";

  if (!next_step) {

    if (low.includes("onboard")) {

      next_step =

        `Today: GA4 DebugView + PostHog funnel — complete ${onboardLabel} and confirm onboarding_start (or equivalent) fires.`;

    } else if (pages[0]) {

      next_step = `Today: Open ${displayPublicPageUrl(pages[0])} in GA4 (engagement + conversions) and in ${source}.`;

    } else {

      next_step = "Open Chat and ask: “Give me a step-by-step fix for this alert with owners and timelines.”";

    }

  }



  const references = (d?.references ?? []).filter(Boolean);

  return { cause, evidence, references, pages, suggestion, next_step };

}


