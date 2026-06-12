"""Build structured drill-down detail for Home briefing cards."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import config

_PUBLIC_SITE = config.PUBLIC_SITE_URL
_ONBOARD_PAGE = f"{_PUBLIC_SITE}/onboard"

_PATH_IN_TEXT = re.compile(
    r"(?:https?://(?:www\.)?sourcy\.ai)?(/[a-zA-Z0-9_\-./%]+)|"
    r"(?:^|[\s(])(/[a-zA-Z][a-zA-Z0-9_\-./]*)",
    re.IGNORECASE,
)
_CAMPAIGN_ID = re.compile(r"campaign\s+(\d{8,})|campaign\s+['\"]?([^'\"]+)['\"]?", re.I)


def _public_page_url(page: str) -> str:
    """Normalize a path or partial URL to https://www.sourcy.ai/..."""
    p = (page or "").strip()
    if not p:
        return p
    if p.startswith("www."):
        p = f"https://{p}"
    if p.startswith("http://") or p.startswith("https://"):
        try:
            u = urlparse(p)
            if u.netloc and u.netloc.replace("www.", "").endswith("sourcy.ai"):
                path = u.path or "/"
                return f"{_PUBLIC_SITE}{path}"
        except ValueError:
            pass
        return p
    path = p if p.startswith("/") else f"/{p}"
    return f"{_PUBLIC_SITE}{path}"


def _normalize_pages(pages: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in pages:
        full = _public_page_url(str(raw).strip())
        if full and full not in seen:
            seen.add(full)
            out.append(full)
    return out


def _page_matches(page: str, fragment: str) -> bool:
    return fragment.lower() in page.lower()


def _extract_pages(text: str) -> list[str]:
    pages: list[str] = []
    seen: set[str] = set()
    for m in _PATH_IN_TEXT.finditer(text or ""):
        path = (m.group(1) or m.group(2) or "").strip()
        if not path or path == "/" or len(path) < 2:
            continue
        full = _public_page_url(path)
        if full not in seen:
            seen.add(full)
            pages.append(full)
    low = (text or "").lower()
    if (
        "/onboard" in low
        or "onboard-page" in low
        or "reaching /onboard" in low
        or "sourcy.ai/onboard" in low
        or "www.sourcy.ai/onboard" in low
    ):
        if _ONBOARD_PAGE not in seen:
            pages.insert(0, _ONBOARD_PAGE)
    return _normalize_pages(pages)[:8]


def _kpi_lookup(kpis: list[dict] | None, *needles: str) -> str | None:
    if not kpis:
        return None
    for k in kpis:
        label = (k.get("label") or "").lower()
        if any(n in label for n in needles):
            val = k.get("value")
            delta = k.get("delta_pct")
            part = f"{k.get('label')}: {val}"
            if isinstance(delta, (int, float)):
                part += f" ({delta:+.1f}% WoW)"
            return part
    return None


def _build_cause(item: dict, text: str, source: str) -> str:
    low = text.lower()
    if "0 downstream conversion" in low or ("0 conversion" in low and "onboard" in low):
        return (
            "Traffic reaches the onboarding funnel but no conversion events are recorded in "
            "GA4 or PostHog. That usually means event tags are missing, misnamed, blocked by "
            f"consent mode, or the funnel step definition does not match the live {_ONBOARD_PAGE.replace('https://', '')} flow."
        )
    if "china" in low and ("exit" in low or "bounce" in low or "immediate" in low):
        return (
            "A large share of sessions comes from China with almost no engagement. "
            "This is often bot traffic, mis-targeted ads, or scrapers — not qualified B2B sourcing buyers."
        )
    if "spent $0" in low or "spend $0" in low or ("google ads" in low and "$0" in low):
        return (
            "Google Ads reported $0 spend in the last 7 days. "
            "This usually means campaigns are paused or not running — confirm status in Ads Manager "
            "before treating it as a delivery failure."
        )
    if "frequency" in low and "320" in low:
        return (
            "The same user(s) saw the Meta ad repeatedly (very high frequency) with no downstream "
            "landing-page views — classic audience-too-small or boosted-post misconfiguration."
        )
    if "non-target" in low and "meta" in low:
        return (
            "Meta spend is leaking into countries outside Sourcy's target markets, wasting budget "
            "on audiences that will not convert to sourcing leads."
        )
    if "ctr" in low and ("impression" in low or "/sourcing/" in low or "sourcy.ai/sourcing" in low):
        return (
            "Pages rank on Google (decent average position) but almost nobody clicks — "
            "usually weak title/meta, SERP snippet mismatch, or low brand awareness for that query."
        )
    if "tracking" in low or "misconfiguration" in low:
        return (
            f"Metrics from {source} conflict with business reality or with another data source, "
            "which points to tracking setup — not necessarily a true performance change."
        )
    return (
        f"This alert was raised because {source} metrics crossed a threshold or conflicted with "
        "another channel in the last-7-day review."
    )


def _build_evidence(item: dict, text: str, source: str, kpis: list[dict] | None) -> str:
    lines = [text]
    if source.upper() == "GA4" or "ga4" in text.lower():
        for needle in ("session", "engagement", "user"):
            k = _kpi_lookup(kpis, needle)
            if k:
                lines.append(f"GA4 KPI — {k}")
    if source.upper() == "POSTHOG" or "posthog" in text.lower():
        k = _kpi_lookup(kpis, "lead", "onboard")
        if k:
            lines.append(f"PostHog KPI — {k}")
    if source.upper() == "SEARCH CONSOLE" or "search console" in source.lower():
        k = _kpi_lookup(kpis, "organic", "click", "branded")
        if k:
            lines.append(f"Search Console KPI — {k}")
    if "GOOGLE ADS" in source.upper():
        k = _kpi_lookup(kpis, "google ads", "spend")
        if k:
            lines.append(f"Google Ads KPI — {k}")
    m = _CAMPAIGN_ID.search(text)
    if m:
        cid = m.group(1) or m.group(2)
        if cid:
            lines.append(f"Campaign referenced in analysis: {cid}")
    return "\n".join(lines)


def _build_suggestion(item: dict, text: str, source: str, pages: list[str]) -> str:
    low = text.lower()
    if "0 downstream conversion" in low or ("0 conversion" in low and "onboard" in low):
        onboard = _ONBOARD_PAGE.replace("https://", "")
        return (
            f"Reconcile GA4 conversion events with PostHog funnel steps on {onboard}. "
            "Confirm onboarding_start (or equivalent) fires on the first meaningful user action, "
            "not only page_view."
        )
    if "china" in low:
        return (
            "Segment China in GA4 by source/medium and campaign. If paid-driven, add geo exclusions; "
            "if organic/bot, consider firewall rules or Analytics filters for reporting."
        )
    if "spent $0" in low:
        return (
            "In Google Ads → Campaigns, confirm which campaigns are Paused vs Enabled. "
            "If spend is intentionally off, no action needed; if a campaign should be live, "
            "check status, budget, ad approval, and geo targeting for that named campaign."
        )
    if "negative keyword" in low:
        return text
    if pages and any(_page_matches(p, "/sourcing/") for p in pages):
        page_labels = ", ".join(p.replace("https://www.", "www.") for p in pages[:2])
        return (
            f"Improve SERP snippets for {page_labels}: rewrite title tag and meta description "
            "to match search intent and add a clear value prop in the first 60 characters."
        )
    return (
        f"Prioritize a fix in {source} this week — validate the metric in the native tool "
        "(GA4, PostHog, Ads Manager, or Search Console) before changing budgets or content."
    )


def _build_next_step(item: dict, text: str, source: str, pages: list[str], default_next: str) -> str:
    low = text.lower()
    page = pages[0] if pages else None
    if "0 downstream conversion" in low or ("onboard" in low and "0" in low):
        onboard = _ONBOARD_PAGE.replace("https://", "")
        return (
            f"Today: In GA4 → Admin → DebugView, complete {onboard} on staging and confirm "
            "onboarding_start fires. In PostHog → Funnels, verify step 1 matches that event."
        )
    if page and _page_matches(page, "/sourcing/"):
        label = page.replace("https://www.", "www.")
        return (
            f"Today: Open Search Console → Pages → {label}, compare queries vs title/meta. "
            f"Draft new title + description, then deploy on {label}."
        )
    if "spent $0" in low and "google" in low:
        return (
            "Today: In Google Ads, list campaign names + Status. "
            "Only troubleshoot delivery if an Enabled campaign with budget spent $0; "
            "otherwise document that ads are intentionally paused."
        )
    if "meta" in low and "frequency" in low:
        return (
            "Today: Pause the boosted post ad set. Relaunch with broader targeting "
            "(≥50k reach) and frequency cap ≤3 per 7 days."
        )
    if page:
        label = page.replace("https://www.", "www.")
        return f"Today: Review {label} in GA4 (pages + conversions) and in the {source} native UI."
    return default_next


def build_briefing_detail(
    item: dict,
    *,
    default_next: str,
    kpis: list[dict] | None = None,
) -> dict[str, Any]:
    """Return item with a populated detail block (cause, evidence, pages, suggestion, next_step)."""
    text = (item.get("text") or "").strip()
    source = (item.get("source") or "data").strip()
    raw_detail = item.get("detail") if isinstance(item.get("detail"), dict) else {}

    pages = raw_detail.get("pages") or []
    if isinstance(pages, str):
        pages = [p.strip() for p in pages.split(",") if p.strip()]
    pages = [str(p).strip() for p in pages if str(p).strip()]
    if not pages:
        pages = _extract_pages(text)
    else:
        pages = _normalize_pages(pages)

    refs = raw_detail.get("references") or []
    if isinstance(refs, str):
        refs = [r.strip() for r in refs.split(",") if r.strip()]
    refs = [str(r).strip() for r in refs if str(r).strip()]

    cause = (raw_detail.get("cause") or "").strip() or _build_cause(item, text, source)
    evidence = (raw_detail.get("evidence") or "").strip() or _build_evidence(item, text, source, kpis)
    suggestion = (raw_detail.get("suggestion") or "").strip() or _build_suggestion(item, text, source, pages)
    next_step = (raw_detail.get("next_step") or "").strip() or _build_next_step(
        item, text, source, pages, default_next
    )

    return {
        **item,
        "detail": {
            "cause": cause,
            "evidence": evidence,
            "references": refs,
            "pages": pages,
            "suggestion": suggestion,
            "next_step": next_step,
        },
    }
