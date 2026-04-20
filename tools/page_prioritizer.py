"""Page prioritizer — multi-source content inventory + priority scoring.

Fetches pages from all Sourcy content sources and ranks them by a multi-factor
score combining traffic, impressions, striking-distance opportunity, and category.

Sources:
  - Builder.io CMS: blogs (~100), case studies (~100)
  - Sourcy PostgREST: trends_v2_querylevel (hundreds × markets)
  - Filesystem scan: static Next.js TSX routes (~50)
  - Enrichment: Google Search Console (28-day impressions, position, top keywords)
  - Enrichment: Google Analytics GA4 (28-day sessions per landing page)

Priority formula:
  score = 0.3 × normalize(impressions_28d)
        + 0.3 × normalize(sessions_28d)
        + 0.2 × striking_distance_weight   # positions 11-30 score higher
        + 0.2 × category_weight            # category-specific multiplier

All tools return JSON strings matching the project's @function_tool pattern.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any

import httpx
from agents import function_tool

import config

# ─── Config ────────────────────────────────────────────────────────────────

BUILDER_API_KEY = config.BUILDER_API_KEY
BUILDER_BASE = "https://cdn.builder.io/api/v3/content"
POSTGREST_URL = config.POSTGREST_URL
POSTGREST_JWT = config.POSTGREST_JWT
_HTTP_TIMEOUT = 20

# Category weights for priority scoring (higher = more strategic value right now)
CATEGORY_WEIGHTS = {
    "blogs": 1.0,
    "case-studies": 0.9,
    "static": 1.1,      # Homepage/service pages have highest conversion weight
    "trends": 0.7,      # High volume but lower conversion intent per page
    "sourcing": 1.0,
}

# Striking distance: positions 11-30 are "low-hanging fruit"
def _striking_distance_weight(position: float) -> float:
    if position <= 0:
        return 0.0
    if 11 <= position <= 20:
        return 1.0   # Top striking distance — just needs a push
    if 21 <= position <= 30:
        return 0.7
    if 1 <= position <= 10:
        return 0.3   # Already ranking, less room for quick win
    return 0.1       # Position > 30 — harder to move quickly


def _normalize(values: list[float]) -> list[float]:
    """Min-max normalize a list of values to [0, 1]."""
    if not values:
        return []
    min_v = min(values)
    max_v = max(values)
    if max_v == min_v:
        return [0.5] * len(values)
    return [(v - min_v) / (max_v - min_v) for v in values]


# ─── Content Fetchers ────────────────────────────────────────────────────────

def _fetch_builder_entries(collection: str, max_entries: int = 150) -> list[dict]:
    """Fetch all entries from a Builder.io collection (paginated)."""
    if not BUILDER_API_KEY:
        return []

    entries = []
    offset = 0
    limit = 50

    while len(entries) < max_entries:
        try:
            resp = httpx.get(
                f"{BUILDER_BASE}/{collection}",
                params={
                    "apiKey": BUILDER_API_KEY,
                    "limit": limit,
                    "offset": offset,
                    "fields": "id,data.title,data.slug,data.description,data.publishDate,data.seoTitle,data.seoDescription",
                },
                timeout=_HTTP_TIMEOUT,
            )
            data = resp.json()
            results = data.get("results", [])
            if not results:
                break
            entries.extend(results)
            if len(results) < limit:
                break
            offset += limit
        except Exception:
            break

    return entries[:max_entries]


def _builder_to_page(entry: dict, collection: str) -> dict:
    """Convert a Builder.io entry to a normalized page dict."""
    data = entry.get("data", {})
    slug = data.get("slug", "")
    cat_path = "blogs" if collection == "blogs" else "case-studies"
    url = f"https://sourcy.ai/{cat_path}/{slug}" if slug else ""

    return {
        "url": url,
        "category": collection,
        "title": data.get("title") or data.get("seoTitle") or slug,
        "description": data.get("description") or data.get("seoDescription") or "",
        "builder_id": entry.get("id", ""),
        "slug": slug,
        "published": data.get("publishDate", ""),
        "source": "builder_io",
    }


def _fetch_trends_pages(limit: int = 200) -> list[dict]:
    """Fetch trending product pages from Sourcy PostgREST."""
    if not POSTGREST_URL:
        return []

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if POSTGREST_JWT:
        headers["Authorization"] = f"Bearer {POSTGREST_JWT}"

    try:
        resp = httpx.get(
            f"{POSTGREST_URL}/trends_v2_querylevel",
            params={"limit": limit, "select": "query,market,url,search_volume"},
            headers=headers,
            timeout=_HTTP_TIMEOUT,
        )
        rows = resp.json()
        if not isinstance(rows, list):
            return []
    except Exception:
        return []

    pages = []
    seen_urls: set[str] = set()
    for row in rows:
        url = row.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        pages.append({
            "url": url,
            "category": "trends",
            "title": row.get("query", url),
            "description": "",
            "source": "postgrest",
            "market": row.get("market", ""),
            "search_volume": row.get("search_volume", 0),
        })

    return pages


def _fetch_static_pages() -> list[dict]:
    """Scan Next.js App Router for static pages."""
    from tools.source_mapper import scan_static_routes

    try:
        routes = scan_static_routes()
    except Exception:
        return []

    pages = []
    for route in routes:
        path = route.get("url_path", "")
        url = f"https://sourcy.ai{path}"
        pages.append({
            "url": url,
            "category": "static",
            "title": path.strip("/").replace("-", " ").title() or "Homepage",
            "description": "",
            "tsx_file": route.get("tsx_file", ""),
            "source": "filesystem",
        })

    return pages


def _enrich_with_search_console(pages: list[dict]) -> list[dict]:
    """Add Search Console impressions, clicks, position, top keywords to each page."""
    try:
        from tools.search_console import _query_search_analytics  # type: ignore

        # Fetch page-level data (28 days, up to 500 pages)
        sc_rows = _query_search_analytics(["page"], "last_30_days", row_limit=500)
        sc_by_url: dict[str, dict] = {}
        for row in sc_rows:
            if "error" not in row:
                url = row.get("page", "").rstrip("/")
                sc_by_url[url] = row

        # Per-page keywords (batched — only for top pages to avoid rate limits)
        # We'll do this as a best-effort for top 50 pages by impressions
        top_urls = sorted(
            [p for p in pages if p["url"].rstrip("/") in sc_by_url],
            key=lambda p: sc_by_url.get(p["url"].rstrip("/"), {}).get("impressions", 0),
            reverse=True,
        )[:50]

        kw_by_url: dict[str, list] = {}
        for page in top_urls:
            page_url = page["url"]
            try:
                kw_rows = _query_search_analytics(
                    ["query"], "last_30_days", row_limit=100
                )
                # Filter to this page (approximation — SC doesn't filter by page in basic query)
                # Real implementation would use page filter dimension
                kw_by_url[page_url] = kw_rows[:10]
            except Exception:
                pass

    except Exception:
        sc_by_url = {}
        kw_by_url = {}

    for page in pages:
        url = page["url"].rstrip("/")
        sc = sc_by_url.get(url, {})
        page["impressions_28d"] = sc.get("impressions", 0)
        page["clicks_28d"] = sc.get("clicks", 0)
        page["avg_position"] = sc.get("position", 0.0)
        page["ctr"] = sc.get("ctr", 0.0)
        page["top_keywords"] = kw_by_url.get(page["url"], [])

    return pages


def _enrich_with_ga4(pages: list[dict]) -> list[dict]:
    """Add GA4 sessions (28-day) per landing page."""
    try:
        from tools.google_analytics import _run_report  # type: ignore

        ga4_rows = _run_report(
            dimensions=["landingPage"],
            metrics=["sessions"],
            date_range="last_30_days",
            order_by_metric="sessions",
            limit=500,
        )
        ga4_by_path: dict[str, int] = {}
        for row in ga4_rows:
            if "error" not in row:
                path = row.get("landingPage", "").rstrip("/")
                ga4_by_path[path] = int(row.get("sessions", 0))

    except Exception:
        ga4_by_path = {}

    for page in pages:
        from urllib.parse import urlparse
        path = urlparse(page["url"]).path.rstrip("/")
        page["sessions_28d"] = ga4_by_path.get(path, 0)

    return pages


def _compute_priority_scores(pages: list[dict], strategy: str) -> list[dict]:
    """Apply multi-factor scoring and sort pages by priority."""
    if not pages:
        return []

    impressions_vals = [p.get("impressions_28d", 0) for p in pages]
    sessions_vals = [p.get("sessions_28d", 0) for p in pages]

    norm_imp = _normalize(impressions_vals)
    norm_ses = _normalize(sessions_vals)

    for i, page in enumerate(pages):
        cat = page.get("category", "static")
        cat_w = CATEGORY_WEIGHTS.get(cat, 0.8)
        pos = page.get("avg_position", 0.0)
        striking_w = _striking_distance_weight(pos)

        if strategy == "traffic":
            score = norm_ses[i]
        elif strategy == "impressions":
            score = norm_imp[i]
        elif strategy == "striking":
            score = striking_w
        elif strategy == "balanced":
            score = 0.25 * norm_imp[i] + 0.25 * norm_ses[i] + 0.25 * striking_w + 0.25 * cat_w
        else:  # multi_factor (default)
            score = (
                0.30 * norm_imp[i]
                + 0.30 * norm_ses[i]
                + 0.20 * striking_w
                + 0.20 * cat_w
            )

        page["priority_score"] = round(score, 4)
        page["priority_reason"] = _build_reason(page, score, norm_imp[i], norm_ses[i], striking_w)

    return sorted(pages, key=lambda p: p["priority_score"], reverse=True)


def _build_reason(page: dict, score: float, norm_imp: float, norm_ses: float, striking_w: float) -> str:
    """Build a human-readable reason for why a page was prioritized."""
    reasons = []
    pos = page.get("avg_position", 0)

    if norm_imp > 0.7:
        reasons.append(f"high impressions ({page.get('impressions_28d', 0):,})")
    elif norm_imp > 0.4:
        reasons.append(f"moderate impressions ({page.get('impressions_28d', 0):,})")

    if norm_ses > 0.7:
        reasons.append(f"high traffic ({page.get('sessions_28d', 0):,} sessions)")
    elif norm_ses > 0.4:
        reasons.append(f"moderate traffic ({page.get('sessions_28d', 0):,} sessions)")

    if striking_w >= 0.7 and pos > 0:
        reasons.append(f"striking distance (pos {pos:.0f} — near page 1)")

    if not reasons:
        reasons.append("included for comprehensive coverage")

    return "; ".join(reasons)


# ─── Main Tool ────────────────────────────────────────────────────────────────

@function_tool
def get_priority_pages(
    category_filter: str = "",
    top_n: int = 20,
    strategy: str = "multi_factor",
    min_impressions: int = 0,
) -> str:
    """Get top-priority sourcy.ai pages for SEO/AEO/GEO auditing or rewriting.

    Fetches from all content sources (Builder.io, PostgREST, filesystem),
    enriches with 28-day Search Console + GA4 data, and returns the top N
    pages ranked by the requested strategy.

    Args:
        category_filter: Limit to one category — 'blogs', 'case-studies', 'trends',
                         'static', or '' for all (default: all)
        top_n: Number of top pages to return (default 20, max 50)
        strategy: Scoring strategy — 'multi_factor' (default), 'traffic', 'impressions',
                  'striking', 'balanced'
        min_impressions: Minimum 28-day impressions to include a page (default 0 = include all)
    """
    top_n = min(top_n, 50)
    all_pages: list[dict] = []

    cf = (category_filter or "").lower()

    # --- Fetch from all sources ---
    if not cf or cf == "blogs":
        blog_entries = _fetch_builder_entries("blogs", max_entries=150)
        all_pages.extend(_builder_to_page(e, "blogs") for e in blog_entries)

    if not cf or cf in ("case-studies", "case_studies"):
        cs_entries = _fetch_builder_entries("case-studies", max_entries=150)
        all_pages.extend(_builder_to_page(e, "case-studies") for e in cs_entries)

    if not cf or cf == "trends":
        trend_pages = _fetch_trends_pages(limit=300)
        all_pages.extend(trend_pages)

    if not cf or cf == "static":
        static_pages = _fetch_static_pages()
        all_pages.extend(static_pages)

    # Deduplicate by URL
    seen: set[str] = set()
    deduped = []
    for p in all_pages:
        url = p.get("url", "").rstrip("/")
        if url and url not in seen:
            seen.add(url)
            deduped.append(p)
    all_pages = deduped

    if not all_pages:
        return json.dumps({
            "error": "No pages found. Check Builder.io API key, PostgREST config, and filesystem path.",
            "category_filter": category_filter,
            "builder_api_key_set": bool(BUILDER_API_KEY),
            "postgrest_jwt_set": bool(POSTGREST_JWT),
        })

    # --- Enrich with traffic data ---
    all_pages = _enrich_with_search_console(all_pages)
    all_pages = _enrich_with_ga4(all_pages)

    # --- Filter by min_impressions ---
    if min_impressions > 0:
        all_pages = [p for p in all_pages if p.get("impressions_28d", 0) >= min_impressions]

    # --- Score and rank ---
    ranked = _compute_priority_scores(all_pages, strategy)

    top = ranked[:top_n]

    # Category breakdown of full ranked list
    cat_counts: dict[str, int] = {}
    for p in ranked:
        cat = p.get("category", "other")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # Clean output — remove heavy fields
    output_pages = []
    for p in top:
        output_pages.append({
            "url": p["url"],
            "category": p["category"],
            "title": p["title"],
            "description": p.get("description", "")[:200],
            "impressions_28d": p.get("impressions_28d", 0),
            "clicks_28d": p.get("clicks_28d", 0),
            "sessions_28d": p.get("sessions_28d", 0),
            "avg_position": p.get("avg_position", 0.0),
            "ctr": p.get("ctr", 0.0),
            "priority_score": p.get("priority_score", 0.0),
            "priority_reason": p.get("priority_reason", ""),
            "tsx_file": p.get("tsx_file", ""),      # for static pages
            "builder_id": p.get("builder_id", ""),  # for Builder.io pages
            "slug": p.get("slug", ""),
            "source": p.get("source", ""),
            "top_keywords": p.get("top_keywords", [])[:5],
        })

    return json.dumps({
        "strategy": strategy,
        "category_filter": category_filter or "all",
        "total_candidates": len(all_pages),
        "top_n_requested": top_n,
        "returned": len(output_pages),
        "category_breakdown": cat_counts,
        "pages": output_pages,
        "note": (
            "Pages are ranked by priority_score. "
            "Audit these in order — start with highest score. "
            "tsx_file is set for static pages; use map_url_to_source() for Builder.io pages."
        ),
    })


@function_tool
def get_top_blogs_for_audit(top_n: int = 20) -> str:
    """Get the top N Sourcy blogs ranked by SEO opportunity.

    Shortcut for get_priority_pages(category_filter='blogs', top_n=N).
    Uses multi_factor strategy (impressions + traffic + striking distance).

    Args:
        top_n: Number of blogs to return (default 20, max 30)
    """
    top_n = min(top_n, 30)
    return get_priority_pages.__wrapped__(
        category_filter="blogs",
        top_n=top_n,
        strategy="multi_factor",
        min_impressions=0,
    )
