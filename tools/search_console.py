"""Google Search Console API tools for the Data Analyst agent."""

from datetime import datetime, timedelta
from agents import function_tool
from googleapiclient.discovery import build
import config
from tools.google_credentials import GSC_SCOPES, get_service_account_credentials


def _get_service():
    """Create a Search Console API service client."""
    if not config.has_search_console_configured():
        raise FileNotFoundError(
            "Search Console not configured — set SEARCH_CONSOLE_SITE_URL and credentials."
        )
    credentials = get_service_account_credentials(GSC_SCOPES)
    return build("searchconsole", "v1", credentials=credentials)


def _parse_date_range(date_range: str) -> tuple[str, str]:
    """Parse date range string into start/end dates."""
    today = datetime.now()
    if date_range == "last_7_days":
        start = (today - timedelta(days=10)).strftime("%Y-%m-%d")  # SC has ~3 day lag
        end = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    elif date_range == "last_30_days":
        start = (today - timedelta(days=33)).strftime("%Y-%m-%d")
        end = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    elif date_range == "last_month":
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        start = last_month_end.replace(day=1).strftime("%Y-%m-%d")
        end = last_month_end.strftime("%Y-%m-%d")
    elif ":" in date_range:
        start, end = date_range.split(":")
    else:
        start = (today - timedelta(days=10)).strftime("%Y-%m-%d")
        end = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    return start, end


def _query_search_analytics(dimensions: list[str], date_range: str,
                            row_limit: int = 50) -> list[dict]:
    """Execute a Search Console query."""
    service = _get_service()
    start, end = _parse_date_range(date_range)
    site_url = config.SEARCH_CONSOLE_SITE_URL

    request = {
        "startDate": start,
        "endDate": end,
        "dimensions": dimensions,
        "rowLimit": row_limit,
    }

    try:
        response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
    except Exception as ex:
        return [{"error": str(ex)}]

    rows = []
    for row in response.get("rows", []):
        entry = {}
        for i, dim in enumerate(dimensions):
            entry[dim] = row["keys"][i]
        entry["clicks"] = row.get("clicks", 0)
        entry["impressions"] = row.get("impressions", 0)
        entry["ctr"] = round(row.get("ctr", 0) * 100, 2)
        entry["position"] = round(row.get("position", 0), 1)
        rows.append(entry)

    return rows


@function_tool
def get_organic_keywords(date_range: str = "last_7_days") -> str:
    """Get organic search keyword performance from Google Search Console.
    Shows what queries your site appears for in Google Search.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'last_month',
                    or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    rows = _query_search_analytics(["query"], date_range, row_limit=5000)

    if rows and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    start, end = _parse_date_range(date_range)
    return str({
        "date_range": f"{start} to {end}",
        "keywords": rows,
        "note": "Compare with Google Ads keywords to find paid/organic overlap and gaps."
    })


@function_tool
def get_organic_pages(date_range: str = "last_7_days") -> str:
    """Get organic search performance by page URL.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'last_month',
                    or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    rows = _query_search_analytics(["page"], date_range, row_limit=100)

    if rows and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    start, end = _parse_date_range(date_range)
    return str({"date_range": f"{start} to {end}", "pages": rows})


@function_tool
def get_organic_by_country(date_range: str = "last_7_days") -> str:
    """Get organic search performance by country.
    Useful for comparing organic reach in target markets.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'last_month',
                    or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    rows = _query_search_analytics(["country"], date_range, row_limit=50)

    if rows and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    target_codes = [c.lower() for c in config.TARGET_COUNTRY_CODES]
    start, end = _parse_date_range(date_range)
    return str({
        "date_range": f"{start} to {end}",
        "target_countries": target_codes,
        "countries": rows,
        "note": "Country codes are 3-letter ISO. Compare against target_countries to find organic reach gaps."
    })


@function_tool
def get_organic_keywords_by_page(page_url: str, date_range: str = "last_30_days") -> str:
    """Get the keywords driving organic traffic to a specific page URL.
    Useful for understanding which keywords a particular landing page ranks for.

    Args:
        page_url: Full page URL to filter (e.g., 'https://www.sourcy.ai/products/ai-sourcing-agent')
        date_range: Time period - 'last_7_days', 'last_30_days', 'last_month',
                    or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    service = _get_service()
    start, end = _parse_date_range(date_range)
    site_url = config.SEARCH_CONSOLE_SITE_URL

    request = {
        "startDate": start,
        "endDate": end,
        "dimensions": ["query"],
        "dimensionFilterGroups": [{
            "filters": [{
                "dimension": "page",
                "operator": "equals",
                "expression": page_url,
            }]
        }],
        "rowLimit": 200,  # Raised from 100 to support top-100 keyword requirement
    }

    try:
        response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
    except Exception as ex:
        return f"Error: {str(ex)}"

    rows = []
    for row in response.get("rows", []):
        rows.append({
            "query": row["keys"][0],
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "position": round(row.get("position", 0), 1),
        })

    # Classify striking distance keywords (pos 11-30)
    striking = [r for r in rows if 11 <= r["position"] <= 30]

    return str({
        "page_url": page_url,
        "date_range": f"{start} to {end}",
        "keywords_found": len(rows),
        "striking_distance_count": len(striking),
        "keywords": rows,
        "striking_distance_keywords": striking[:20],
    })


# ─── Tool 5: Keyword Weekly Positions (for heatmap) ─────────────────

@function_tool
def get_keyword_weekly_positions(date_range: str = "last_30_days", top_n: int = 50) -> str:
    """Get weekly position trends for top keywords — enables position heatmap.
    Shows how each keyword's ranking changed over multiple weeks.
    Critical for detecting ranking improvements/declines.

    Args:
        date_range: 'last_30_days', 'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
        top_n: Number of top keywords to track (default 50).
    """
    import json
    from datetime import datetime as _dt

    # Fetch with date dimension for time-series
    rows = _query_search_analytics(["query", "date"], date_range, row_limit=5000)

    if rows and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    # Group by keyword + ISO week
    keywords = {}
    for row in rows:
        query = row.get("query", "")
        date_str = row.get("date", "")
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            iso_week = dt.strftime("%Y-W%V")
        except Exception:
            continue

        if query not in keywords:
            keywords[query] = {"query": query, "total_clicks": 0, "total_impressions": 0, "weekly": {}}
        k = keywords[query]
        k["total_clicks"] += row.get("clicks", 0)
        k["total_impressions"] += row.get("impressions", 0)

        if iso_week not in k["weekly"]:
            k["weekly"][iso_week] = {"positions": [], "clicks": 0, "impressions": 0}
        w = k["weekly"][iso_week]
        w["positions"].append(row.get("position", 0))
        w["clicks"] += row.get("clicks", 0)
        w["impressions"] += row.get("impressions", 0)

    # Helper: compute Mon–Sun date labels for an ISO week string like "2026-W11"
    def _week_labels(iso_week: str) -> dict:
        try:
            year_str, w_str = iso_week.split("-W")
            year, wnum = int(year_str), int(w_str)
            monday = datetime.strptime(f"{year}-W{wnum:02d}-1", "%G-W%V-%u")
            sunday = monday + timedelta(days=6)
            return {
                "week_start": monday.strftime("%b %d"),   # "Mar 10"
                "week_end":   sunday.strftime("%b %d"),   # "Mar 16"
                "week_label": f"{monday.strftime('%b %d')}–{sunday.strftime('%b %d')}",  # "Mar 10–16"
            }
        except Exception:
            return {"week_start": "", "week_end": "", "week_label": iso_week}

    # Take top N by total clicks, compute weekly averages
    sorted_keywords = sorted(keywords.values(), key=lambda x: x["total_clicks"], reverse=True)[:top_n]

    all_weeks = sorted(set(w for k in sorted_keywords for w in k["weekly"].keys()))
    # Build a lookup: "2026-W11" → {week_start, week_end, week_label} — used for chart axis labels (R1)
    week_label_map = {w: _week_labels(w) for w in all_weeks}

    results = []
    for kw in sorted_keywords:
        weekly_list = []
        positions_over_time = []
        for week in all_weeks:
            w = kw["weekly"].get(week, {})
            positions = w.get("positions", [])
            avg_pos = round(sum(positions) / len(positions), 1) if positions else None
            positions_over_time.append(avg_pos)
            labels = week_label_map.get(week, {})
            weekly_list.append({
                "week": week,
                "week_start": labels.get("week_start", ""),   # "Mar 10" — use for chart X-axis NOT "W11"
                "week_end":   labels.get("week_end", ""),     # "Mar 16"
                "week_label": labels.get("week_label", week), # "Mar 10–16" — use in prose NOT "W11"
                "avg_position": avg_pos,
                "clicks": w.get("clicks", 0),
                "impressions": w.get("impressions", 0),
                "ctr": round((w.get("clicks", 0) / w.get("impressions", 1) * 100), 2) if w.get("impressions", 0) > 0 else 0,
            })

        # Position change: first available vs last available
        valid_positions = [p for p in positions_over_time if p is not None]
        position_change = None
        if len(valid_positions) >= 2:
            position_change = round(valid_positions[-1] - valid_positions[0], 1)

        results.append({
            "query": kw["query"],
            "total_clicks": kw["total_clicks"],
            "total_impressions": kw["total_impressions"],
            "position_change": position_change,  # negative = improved, positive = declined
            "direction": "improved" if position_change and position_change < -1 else "declined" if position_change and position_change > 1 else "stable",
            "weekly": weekly_list,
            "sparkline_positions": positions_over_time,
        })

    start, end = _parse_date_range(date_range)
    return json.dumps({
        "date_range": f"{start} to {end}",
        "weeks": all_weeks,                              # ISO week strings e.g. ["2026-W10", "2026-W11"]
        "week_labels": [week_label_map[w]["week_label"] for w in all_weeks],  # ["Mar 4–10", "Mar 11–17"] — use these for chart X-axis (R1: no bare W##)
        "keywords": results,
        "improving": [k["query"] for k in results if k["direction"] == "improved"][:10],
        "declining": [k["query"] for k in results if k["direction"] == "declined"][:10],
    })
