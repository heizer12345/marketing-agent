"""PostHog Analytics API tools — website behavior analytics via HogQL.

Provides pageview stats, conversion funnels, user paths, event tracking,
onboarding funnel analysis, and weekly trends for WoW comparison.
Uses HogQL query API (PostHog's SQL interface).

Requires: httpx (already in requirements)
Auth: POSTHOG_API_KEY (Personal API key, starts with phx_) + POSTHOG_PROJECT_ID
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Tuple
from agents import function_tool

import config

_http_client = None


def _get_client():
    global _http_client
    if _http_client is None:
        import httpx
        _http_client = httpx.Client(timeout=30)
    return _http_client


def _missing_key():
    return json.dumps({
        "error": "PostHog API not configured. Add POSTHOG_API_KEY (personal key, phx_...) and POSTHOG_PROJECT_ID to .env",
        "skipped": True,
    })


def _posthog_host():
    return getattr(config, "POSTHOG_HOST", "https://us.posthog.com")


def _headers():
    api_key = getattr(config, "POSTHOG_API_KEY", "")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _project_id():
    return getattr(config, "POSTHOG_PROJECT_ID", "")


def _hogql_query(query: str) -> Optional[dict]:
    """Execute a HogQL query against PostHog."""
    client = _get_client()
    base = _posthog_host()
    pid = _project_id()
    url = f"{base}/api/projects/{pid}/query/"
    try:
        resp = client.post(url, json={"query": {"kind": "HogQLQuery", "query": query}}, headers=_headers())
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def _days_ago(n: int) -> str:
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


def _parse_days(date_range: str) -> int:
    """Convert standard date_range to number of days."""
    mapping = {"last_7_days": 7, "last_14_days": 14, "last_30_days": 30, "last_90_days": 90}
    return mapping.get(date_range, 30)


# ─── Tool 1: Top Pages & Traffic Overview ──────────────────────────────

@function_tool
def get_posthog_session_stats(date_range: str = "last_7_days") -> str:
    """Get website traffic overview from PostHog — top pages, total pageviews,
    unique users, and daily breakdown.

    Args:
        date_range: 'last_7_days', 'last_14_days', 'last_30_days', 'last_90_days'.
    """
    api_key = getattr(config, "POSTHOG_API_KEY", "")
    if not api_key or not _project_id():
        return _missing_key()

    days = _parse_days(date_range)

    # Top pages
    pages_data = _hogql_query(f"""
        SELECT
            properties.$current_url as url,
            count() as pageviews,
            uniq(distinct_id) as unique_users
        FROM events
        WHERE event = '$pageview'
            AND properties.$current_url LIKE '%sourcy.ai%'
            AND timestamp > now() - interval {days} day
        GROUP BY url
        ORDER BY pageviews DESC
        LIMIT 30
    """)

    # Daily totals
    daily_data = _hogql_query(f"""
        SELECT
            toDate(timestamp) as day,
            count() as pageviews,
            uniq(distinct_id) as unique_users
        FROM events
        WHERE event = '$pageview'
            AND properties.$current_url LIKE '%sourcy.ai%'
            AND timestamp > now() - interval {days} day
        GROUP BY day
        ORDER BY day ASC
    """)

    top_pages = []
    if pages_data and "results" in pages_data:
        for row in pages_data["results"]:
            top_pages.append({"url": row[0], "pageviews": row[1], "unique_users": row[2]})

    daily = []
    total_pv = 0
    total_users = 0
    if daily_data and "results" in daily_data:
        for row in daily_data["results"]:
            daily.append({"date": str(row[0]), "pageviews": row[1], "unique_users": row[2]})
            total_pv += row[1]
            total_users += row[2]

    return json.dumps({
        "date_range": date_range,
        "total_pageviews": total_pv,
        "total_unique_users": total_users,
        "avg_daily_pageviews": round(total_pv / max(len(daily), 1), 1),
        "top_pages": top_pages,
        "daily_breakdown": daily,
    }, indent=2)


# ─── Tool 2: Onboarding Funnel ────────────────────────────────────────

@function_tool
def get_posthog_funnel(date_range: str = "last_30_days") -> str:
    """Get the Sourcy onboarding conversion funnel from PostHog.
    Tracks: Homepage → Onboard page → Onboarding started → Onboarding stage 1 completion.
    Also shows which UTM sources/campaigns drive onboard visits.

    Args:
        date_range: 'last_7_days', 'last_14_days', 'last_30_days', 'last_90_days'.
    """
    api_key = getattr(config, "POSTHOG_API_KEY", "")
    if not api_key or not _project_id():
        return _missing_key()

    days = _parse_days(date_range)

    # Funnel stages via separate queries
    stages = {}

    # Stage 1: All site visitors
    r1 = _hogql_query(f"""
        SELECT uniq(distinct_id) as users FROM events
        WHERE event = '$pageview' AND properties.$current_url LIKE '%sourcy.ai%'
        AND timestamp > now() - interval {days} day
    """)
    stages["site_visitors"] = r1["results"][0][0] if r1 and "results" in r1 and r1["results"] else 0

    # Stage 2: Visited /onboard
    r2 = _hogql_query(f"""
        SELECT uniq(distinct_id) as users FROM events
        WHERE event = '$pageview' AND properties.$current_url LIKE '%sourcy.ai/onboard%'
        AND timestamp > now() - interval {days} day
    """)
    stages["onboard_page"] = r2["results"][0][0] if r2 and "results" in r2 and r2["results"] else 0

    # Stage 3: Onboarding event fired
    r3 = _hogql_query(f"""
        SELECT uniq(distinct_id) as users FROM events
        WHERE event = 'onboarding'
        AND timestamp > now() - interval {days} day
    """)
    stages["onboarding_started"] = r3["results"][0][0] if r3 and "results" in r3 and r3["results"] else 0

    # Stage 4: Onboarding stage 1 complete
    r4 = _hogql_query(f"""
        SELECT uniq(distinct_id) as users FROM events
        WHERE event = 'onboarding-stage-1'
        AND timestamp > now() - interval {days} day
    """)
    stages["onboarding_stage1"] = r4["results"][0][0] if r4 and "results" in r4 and r4["results"] else 0

    # Build funnel with drop-off
    funnel = []
    prev_count = None
    for name, count in stages.items():
        drop_off = prev_count - count if prev_count is not None else 0
        drop_pct = round(drop_off / prev_count * 100, 1) if prev_count and prev_count > 0 else 0
        conv_rate = round(count / stages["site_visitors"] * 100, 1) if stages["site_visitors"] > 0 else 0
        funnel.append({
            "stage": name,
            "users": count,
            "drop_off_from_previous": drop_off,
            "drop_off_pct": drop_pct,
            "overall_conversion": conv_rate,
        })
        prev_count = count

    # UTM sources driving /onboard
    utm_data = _hogql_query(f"""
        SELECT
            properties.$referring_domain as referrer,
            properties.utm_source as utm_source,
            properties.utm_campaign as utm_campaign,
            uniq(distinct_id) as users,
            count() as pageviews
        FROM events
        WHERE event = '$pageview' AND properties.$current_url LIKE '%sourcy.ai/onboard%'
        AND timestamp > now() - interval {days} day
        GROUP BY referrer, utm_source, utm_campaign
        ORDER BY users DESC
        LIMIT 20
    """)

    utm_sources = []
    if utm_data and "results" in utm_data:
        for row in utm_data["results"]:
            utm_sources.append({
                "referrer": row[0] or "direct",
                "utm_source": row[1] or "",
                "utm_campaign": row[2] or "",
                "users": row[3],
                "pageviews": row[4],
            })

    return json.dumps({
        "date_range": date_range,
        "funnel": funnel,
        "utm_sources_to_onboard": utm_sources,
        "biggest_drop_off": max(funnel[1:], key=lambda x: x["drop_off_pct"]) if len(funnel) > 1 else None,
    }, indent=2)


# ─── Tool 3: User Paths ───────────────────────────────────────────────

@function_tool
def get_posthog_user_paths(date_range: str = "last_7_days") -> str:
    """Get common user navigation paths — where do users go after landing?
    Shows page-to-page flow patterns.

    Args:
        date_range: 'last_7_days', 'last_14_days', 'last_30_days'.
    """
    api_key = getattr(config, "POSTHOG_API_KEY", "")
    if not api_key or not _project_id():
        return _missing_key()

    days = _parse_days(date_range)

    # Entry pages (first pageview per session)
    entry_data = _hogql_query(f"""
        SELECT
            properties.$current_url as url,
            count() as entries
        FROM events
        WHERE event = '$pageview'
            AND properties.$current_url LIKE '%sourcy.ai%'
            AND timestamp > now() - interval {days} day
            AND properties.$is_initial_event = true
        GROUP BY url
        ORDER BY entries DESC
        LIMIT 15
    """)

    # Pages visited by onboard users (what pages do converting users visit?)
    onboard_user_pages = _hogql_query(f"""
        SELECT
            properties.$current_url as url,
            count() as views
        FROM events
        WHERE event = '$pageview'
            AND properties.$current_url LIKE '%sourcy.ai%'
            AND timestamp > now() - interval {days} day
            AND distinct_id IN (
                SELECT distinct_id FROM events
                WHERE event = '$pageview'
                    AND properties.$current_url LIKE '%/onboard%'
                    AND timestamp > now() - interval {days} day
            )
        GROUP BY url
        ORDER BY views DESC
        LIMIT 20
    """)

    entry_pages = []
    if entry_data and "results" in entry_data:
        for row in entry_data["results"]:
            entry_pages.append({"url": row[0], "entries": row[1]})

    converting_user_pages = []
    if onboard_user_pages and "results" in onboard_user_pages:
        for row in onboard_user_pages["results"]:
            converting_user_pages.append({"url": row[0], "views": row[1]})

    return json.dumps({
        "date_range": date_range,
        "entry_pages": entry_pages,
        "pages_visited_by_onboard_users": converting_user_pages,
    }, indent=2)


# ─── Tool 4: Custom Events ────────────────────────────────────────────

@function_tool
def get_posthog_events(event_name: str = "", date_range: str = "last_7_days") -> str:
    """Get custom event data from PostHog.
    Without event_name: lists all events with counts.
    With event_name: shows daily breakdown for that event.

    Args:
        event_name: Event name (e.g., 'onboarding', 'search', 'ai-assistant').
                    Leave empty to list all events.
        date_range: 'last_7_days', 'last_14_days', 'last_30_days'.
    """
    api_key = getattr(config, "POSTHOG_API_KEY", "")
    if not api_key or not _project_id():
        return _missing_key()

    days = _parse_days(date_range)

    if not event_name:
        # List all events with counts
        data = _hogql_query(f"""
            SELECT event, count() as total, uniq(distinct_id) as unique_users
            FROM events
            WHERE timestamp > now() - interval {days} day
            GROUP BY event
            ORDER BY total DESC
            LIMIT 30
        """)
        events = []
        if data and "results" in data:
            for row in data["results"]:
                events.append({"event": row[0], "total": row[1], "unique_users": row[2]})
        return json.dumps({"date_range": date_range, "events": events}, indent=2)

    # Specific event daily breakdown
    data = _hogql_query(f"""
        SELECT
            toDate(timestamp) as day,
            count() as total,
            uniq(distinct_id) as unique_users
        FROM events
        WHERE event = '{event_name}'
            AND timestamp > now() - interval {days} day
        GROUP BY day
        ORDER BY day ASC
    """)

    daily = []
    grand_total = 0
    if data and "results" in data:
        for row in data["results"]:
            daily.append({"date": str(row[0]), "total": row[1], "unique_users": row[2]})
            grand_total += row[1]

    return json.dumps({
        "event": event_name,
        "date_range": date_range,
        "total": grand_total,
        "avg_daily": round(grand_total / max(len(daily), 1), 1),
        "daily_breakdown": daily,
    }, indent=2)


# ─── Tool 5: Weekly Trends (WoW) ──────────────────────────────────────

@function_tool
def get_posthog_weekly_trends(event_name: str = "$pageview", date_range: str = "last_30_days") -> str:
    """Get weekly trends for WoW comparison. Shows weekly totals with change percentages.

    Args:
        event_name: Event to track (default '$pageview'). Common: '$pageview', 'onboarding', 'search'.
        date_range: 'last_30_days' or 'last_90_days'.
    """
    api_key = getattr(config, "POSTHOG_API_KEY", "")
    if not api_key or not _project_id():
        return _missing_key()

    days = _parse_days(date_range)

    # Filter for sourcy.ai if tracking pageviews
    url_filter = "AND properties.$current_url LIKE '%sourcy.ai%'" if event_name == "$pageview" else ""

    data = _hogql_query(f"""
        SELECT
            toStartOfWeek(timestamp) as week_start,
            count() as total,
            uniq(distinct_id) as unique_users
        FROM events
        WHERE event = '{event_name}'
            AND timestamp > now() - interval {days} day
            {url_filter}
        GROUP BY week_start
        ORDER BY week_start ASC
    """)

    weekly = []
    if data and "results" in data:
        prev_total = None
        for row in data["results"]:
            total = row[1]
            wow_change = round((total - prev_total) / prev_total * 100, 1) if prev_total and prev_total > 0 else None
            weekly.append({
                "week_starting": str(row[0]),
                "total": total,
                "unique_users": row[2],
                "wow_change_pct": wow_change,
            })
            prev_total = total

    this_week = weekly[-1] if weekly else None
    last_week = weekly[-2] if len(weekly) >= 2 else None

    return json.dumps({
        "event": event_name,
        "date_range": date_range,
        "weekly_breakdown": weekly,
        "this_week": this_week,
        "last_week": last_week,
        "wow_summary": {
            "change_pct": this_week["wow_change_pct"] if this_week else None,
            "direction": "up" if this_week and this_week.get("wow_change_pct") and this_week["wow_change_pct"] > 0 else "down",
        } if this_week else None,
    }, indent=2)


# ─── Tool 6: Google Ads → PostHog Attribution ─────────────────────────

@function_tool
def get_posthog_ads_attribution(date_range: str = "last_30_days") -> str:
    """Get how Google/Meta Ads traffic behaves on-site via PostHog.
    Shows which ad campaigns drive onboard visits and engagement.
    Connects ad spend to on-site conversion behavior.

    Args:
        date_range: 'last_7_days', 'last_14_days', 'last_30_days'.
    """
    api_key = getattr(config, "POSTHOG_API_KEY", "")
    if not api_key or not _project_id():
        return _missing_key()

    days = _parse_days(date_range)

    # Google Ads traffic (has gclid or gad_campaignid)
    google_ads = _hogql_query(f"""
        SELECT
            properties.utm_campaign as campaign,
            properties.gad_campaignid as campaign_id,
            count() as pageviews,
            uniq(distinct_id) as users
        FROM events
        WHERE event = '$pageview'
            AND properties.$current_url LIKE '%sourcy.ai%'
            AND (properties.gclid != '' OR properties.utm_source = 'google')
            AND timestamp > now() - interval {days} day
        GROUP BY campaign, campaign_id
        ORDER BY users DESC
        LIMIT 20
    """)

    # Which ad users reached /onboard?
    ads_to_onboard = _hogql_query(f"""
        SELECT
            properties.utm_campaign as campaign,
            properties.utm_source as source,
            uniq(distinct_id) as users,
            count() as pageviews
        FROM events
        WHERE event = '$pageview'
            AND properties.$current_url LIKE '%sourcy.ai/onboard%'
            AND (properties.gclid != '' OR properties.utm_source IN ('google', 'meta', 'facebook', 'instagram'))
            AND timestamp > now() - interval {days} day
        GROUP BY campaign, source
        ORDER BY users DESC
        LIMIT 20
    """)

    google_traffic = []
    if google_ads and "results" in google_ads:
        for row in google_ads["results"]:
            google_traffic.append({
                "campaign": row[0] or "unknown",
                "campaign_id": row[1] or "",
                "pageviews": row[2],
                "users": row[3],
            })

    ads_onboard = []
    if ads_to_onboard and "results" in ads_to_onboard:
        for row in ads_to_onboard["results"]:
            ads_onboard.append({
                "campaign": row[0] or "unknown",
                "source": row[1] or "unknown",
                "users": row[2],
                "pageviews": row[3],
            })

    return json.dumps({
        "date_range": date_range,
        "google_ads_traffic": google_traffic,
        "ads_driving_to_onboard": ads_onboard,
        "insight": "Cross-reference campaign IDs with Google Ads data to connect ad spend → on-site behavior",
    }, indent=2)
