"""Google Analytics GA4 API tools for the Data Analyst agent."""

from datetime import datetime, timedelta
from typing import Optional
from agents import function_tool
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    OrderBy,
)

import config


def _get_client() -> BetaAnalyticsDataClient:
    """Create a GA4 API client using default credentials."""
    return BetaAnalyticsDataClient()


def _parse_date_range(date_range: str) -> tuple[str, str]:
    """Parse a date range string into start/end dates for GA4.

    Supports: 'last_7_days', 'last_30_days', 'this_month', 'last_month',
              or 'YYYY-MM-DD:YYYY-MM-DD' format.
    """
    today = datetime.now()
    if date_range == "last_7_days":
        start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
    elif date_range == "last_30_days":
        start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
    elif date_range == "this_month":
        start = today.replace(day=1).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
    elif date_range == "last_month":
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        start = last_month_end.replace(day=1).strftime("%Y-%m-%d")
        end = last_month_end.strftime("%Y-%m-%d")
    elif ":" in date_range:
        start, end = date_range.split(":")
    else:
        start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
    return start, end


def _run_report(dimensions: list[str], metrics: list[str], date_range: str,
                order_by_metric: Optional[str] = None, limit: int = 50) -> list[dict]:
    """Run a GA4 report and return rows as dicts."""
    client = _get_client()
    property_id = config.GA4_PROPERTY_ID
    start, end = _parse_date_range(date_range)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        limit=limit,
    )

    if order_by_metric:
        request.order_bys = [
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order_by_metric), desc=True)
        ]

    try:
        response = client.run_report(request)
    except Exception as ex:
        return [{"error": str(ex)}]

    rows = []
    for row in response.rows:
        entry = {}
        for i, dim in enumerate(dimensions):
            entry[dim] = row.dimension_values[i].value
        for i, met in enumerate(metrics):
            val = row.metric_values[i].value
            try:
                entry[met] = float(val) if "." in val else int(val)
            except ValueError:
                entry[met] = val
        rows.append(entry)

    return rows


@function_tool
def get_website_overview(date_range: str = "last_7_days") -> str:
    """Get top-line website metrics: sessions, users, pageviews, bounce rate, avg duration.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    # GA4 API limits requests to 10 metrics — split into two batches
    metrics_batch1 = [
        "sessions", "totalUsers", "newUsers", "screenPageViews",
        "bounceRate", "averageSessionDuration", "engagementRate",
        "engagedSessions", "sessionsPerUser", "screenPageViewsPerSession",
    ]
    metrics_batch2 = [
        "conversions", "totalRevenue",
    ]

    client = _get_client()
    property_id = config.GA4_PROPERTY_ID
    start, end = _parse_date_range(date_range)

    result = {"date_range": f"{start} to {end}"}

    for batch in [metrics_batch1, metrics_batch2]:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            metrics=[Metric(name=m) for m in batch],
            date_ranges=[DateRange(start_date=start, end_date=end)],
        )
        try:
            response = client.run_report(request)
        except Exception as ex:
            return f"Error: {str(ex)}"

        if not response.rows:
            continue

        row = response.rows[0]
        for i, m in enumerate(batch):
            val = row.metric_values[i].value
            try:
                result[m] = round(float(val), 2) if "." in val else int(val)
            except ValueError:
                result[m] = val

    return str(result)


@function_tool
def get_traffic_sources(date_range: str = "last_7_days") -> str:
    """Get traffic sources breakdown by source/medium.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    rows = _run_report(
        dimensions=["sessionSource", "sessionMedium"],
        metrics=["sessions", "totalUsers", "bounceRate", "averageSessionDuration",
                 "conversions", "totalRevenue"],
        date_range=date_range,
        order_by_metric="sessions",
        limit=30,
    )

    if rows and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    start, end = _parse_date_range(date_range)
    return str({"date_range": f"{start} to {end}", "sources": rows})


@function_tool
def get_country_breakdown(date_range: str = "last_7_days") -> str:
    """Get website traffic and performance by country.
    Critical for comparing against target markets.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    rows = _run_report(
        dimensions=["country", "countryId"],
        metrics=["sessions", "totalUsers", "newUsers", "bounceRate",
                 "averageSessionDuration", "conversions", "totalRevenue"],
        date_range=date_range,
        order_by_metric="sessions",
        limit=50,
    )

    if rows and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    target_codes = config.TARGET_COUNTRY_CODES
    start, end = _parse_date_range(date_range)
    return str({
        "date_range": f"{start} to {end}",
        "target_countries": target_codes,
        "countries": rows,
        "note": "Compare countryId against target_countries to identify non-target traffic."
    })


@function_tool
def get_landing_pages(date_range: str = "last_7_days") -> str:
    """Get landing page performance metrics.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    rows = _run_report(
        dimensions=["landingPagePlusQueryString"],
        metrics=["sessions", "totalUsers", "bounceRate",
                 "averageSessionDuration", "conversions"],
        date_range=date_range,
        order_by_metric="sessions",
        limit=30,
    )

    if rows and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    start, end = _parse_date_range(date_range)
    return str({"date_range": f"{start} to {end}", "landing_pages": rows})


@function_tool
def get_audience_segments(date_range: str = "last_7_days") -> str:
    """Get user demographics and device breakdown.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    # Device breakdown
    device_rows = _run_report(
        dimensions=["deviceCategory"],
        metrics=["sessions", "totalUsers", "bounceRate", "conversions"],
        date_range=date_range,
        order_by_metric="sessions",
    )

    # Browser breakdown
    browser_rows = _run_report(
        dimensions=["browser"],
        metrics=["sessions", "totalUsers"],
        date_range=date_range,
        order_by_metric="sessions",
        limit=10,
    )

    start, end = _parse_date_range(date_range)
    return str({
        "date_range": f"{start} to {end}",
        "devices": device_rows,
        "browsers": browser_rows,
    })


@function_tool
def get_conversion_paths(date_range: str = "last_7_days") -> str:
    """Get conversion data by channel grouping to understand the conversion funnel.

    Args:
        date_range: Time period - 'last_7_days', 'last_30_days', 'this_month',
                    'last_month', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    rows = _run_report(
        dimensions=["sessionDefaultChannelGroup"],
        metrics=["sessions", "totalUsers", "conversions", "totalRevenue",
                 "engagementRate", "averageSessionDuration"],
        date_range=date_range,
        order_by_metric="conversions",
        limit=20,
    )

    if rows and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    start, end = _parse_date_range(date_range)
    return str({"date_range": f"{start} to {end}", "channels": rows})


# ─── Tool 7: Weekly Comparison (5-week trend) ────────────────────────

@function_tool
def get_weekly_comparison(weeks: int = 5) -> str:
    """Get 5-week performance trend with WoW changes for all key metrics.
    Essential for spotting trends, seasonality, and anomalies.

    Args:
        weeks: Number of weeks to compare (default 5).
    """
    import json
    from datetime import datetime as _dt, timedelta as _td

    days = weeks * 7
    date_range = f"{(_dt.now() - _td(days=days)).strftime('%Y-%m-%d')}:{_dt.now().strftime('%Y-%m-%d')}"

    # GA4 API limits requests to 10 metrics — split into two batches and merge
    metrics_batch1 = [
        "sessions", "totalUsers", "newUsers",
        "bounceRate", "averageSessionDuration", "engagementRate",
        "engagedSessions", "sessionsPerUser", "screenPageViewsPerSession",
    ]
    metrics_batch2 = [
        "conversions", "totalRevenue",
    ]

    rows1 = _run_report(dimensions=["date"], metrics=metrics_batch1, date_range=date_range, limit=500)
    if rows1 and "error" in rows1[0]:
        return f"Error: {rows1[0]['error']}"

    rows2 = _run_report(dimensions=["date"], metrics=metrics_batch2, date_range=date_range, limit=500)

    # Merge batch2 into batch1 by date
    batch2_by_date = {}
    if rows2 and not (rows2 and "error" in rows2[0]):
        for r in rows2:
            batch2_by_date[r.get("date", "")] = r

    rows = []
    for r in rows1:
        merged = dict(r)
        extra = batch2_by_date.get(r.get("date", ""), {})
        for m in metrics_batch2:
            merged[m] = extra.get(m, 0)
        rows.append(merged)

    if not rows:
        return json.dumps({"weeks_requested": weeks, "periods": [], "period_count": 0})

    # Group by ISO week
    weekly = {}
    for row in rows:
        try:
            dt = _dt.strptime(row.get("date", ""), "%Y%m%d")
            iso_week = dt.strftime("%Y-W%V")
        except Exception:
            continue

        if iso_week not in weekly:
            # Compute Mon–Sun for this ISO week so axes show dates not "W11"
            week_num = int(dt.strftime("%V"))
            year = int(dt.strftime("%G"))  # ISO year (can differ from calendar year at year edges)
            week_monday = _dt.strptime(f"{year}-W{week_num:02d}-1", "%G-W%V-%u")
            week_sunday = week_monday + _td(days=6)
            weekly[iso_week] = {
                "week": iso_week,
                "week_start": week_monday.strftime("%b %d"),   # e.g. "Mar 10"
                "week_end": week_sunday.strftime("%b %d"),     # e.g. "Mar 16"
                "week_label": f"{week_monday.strftime('%b %d')}–{week_sunday.strftime('%b %d')}",  # "Mar 10–16"
                "sessions": 0, "totalUsers": 0, "newUsers": 0,
                "bounceRate_sum": 0, "avgDuration_sum": 0, "engagementRate_sum": 0,
                "engagedSessions": 0, "conversions": 0, "totalRevenue": 0, "_days": 0,
            }
        w = weekly[iso_week]
        w["sessions"] += int(row.get("sessions", 0))
        w["totalUsers"] += int(row.get("totalUsers", 0))
        w["newUsers"] += int(row.get("newUsers", 0))
        w["engagedSessions"] += int(row.get("engagedSessions", 0))
        w["conversions"] += int(row.get("conversions", 0))
        w["totalRevenue"] += float(row.get("totalRevenue", 0))
        w["bounceRate_sum"] += float(row.get("bounceRate", 0))
        w["avgDuration_sum"] += float(row.get("averageSessionDuration", 0))
        w["engagementRate_sum"] += float(row.get("engagementRate", 0))
        w["_days"] += 1

    # Compute averages and WoW changes
    periods = []
    prev = None
    for week_key in sorted(weekly.keys()):
        w = weekly[week_key]
        days_count = max(w["_days"], 1)

        result = {
            "week": w["week"],
            "week_start": w.get("week_start", ""),   # "Mar 10" — use for chart labels, not "W11"
            "week_end": w.get("week_end", ""),       # "Mar 16"
            "week_label": w.get("week_label", w["week"]),  # "Mar 10–16" — use in prose and tooltips
            "sessions": w["sessions"],
            "users": w["totalUsers"],
            "new_users": w["newUsers"],
            "engaged_sessions": w["engagedSessions"],
            "bounce_rate": round(w["bounceRate_sum"] / days_count, 2),
            "avg_session_duration": round(w["avgDuration_sum"] / days_count, 1),
            "engagement_rate": round(w["engagementRate_sum"] / days_count, 4),
            "conversions": w["conversions"],
            "revenue": round(w["totalRevenue"], 2),
        }

        # WoW changes
        if prev:
            for key in ["sessions", "users", "conversions"]:
                prev_val = prev.get(key, 0)
                if prev_val > 0:
                    result[f"{key}_wow_pct"] = round((result[key] - prev_val) / prev_val * 100, 1)
                else:
                    result[f"{key}_wow_pct"] = None

        prev = result
        del w["_days"]
        del w["bounceRate_sum"]
        del w["avgDuration_sum"]
        del w["engagementRate_sum"]
        periods.append(result)

    return json.dumps({
        "weeks_requested": weeks,
        "periods": periods,
        "period_count": len(periods),
    })


# ─── Tool 8: Traffic by Source Weekly ────────────────────────────────

@function_tool
def get_traffic_by_source_weekly(weeks: int = 5) -> str:
    """Get traffic source/medium breakdown with weekly trend data.
    Shows how each channel's contribution changes over time.
    Also cross-references Google Ads campaigns via googleAdsCampaignName dimension.

    Args:
        weeks: Number of weeks to analyze (default 5).
    """
    import json
    from datetime import datetime as _dt, timedelta as _td

    days = weeks * 7
    date_range = f"{(_dt.now() - _td(days=days)).strftime('%Y-%m-%d')}:{_dt.now().strftime('%Y-%m-%d')}"

    rows = _run_report(
        dimensions=["sessionSource", "sessionMedium", "date"],
        metrics=["sessions", "totalUsers", "bounceRate", "conversions"],
        date_range=date_range,
        limit=2000,
    )

    if rows and "error" in rows[0]:
        return f"Error: {rows[0]['error']}"

    # Group by source/medium + week
    sources = {}
    for row in rows:
        src = row.get("sessionSource", "")
        med = row.get("sessionMedium", "")
        key = f"{src} / {med}"
        try:
            dt = _dt.strptime(row.get("date", ""), "%Y%m%d")
            iso_week = dt.strftime("%Y-W%V")
        except Exception:
            continue

        if key not in sources:
            sources[key] = {"source_medium": key, "total_sessions": 0, "weekly": {}}
        s = sources[key]
        s["total_sessions"] += int(row.get("sessions", 0))

        if iso_week not in s["weekly"]:
            s["weekly"][iso_week] = {"sessions": 0, "users": 0, "conversions": 0}
        w = s["weekly"][iso_week]
        w["sessions"] += int(row.get("sessions", 0))
        w["users"] += int(row.get("totalUsers", 0))
        w["conversions"] += int(row.get("conversions", 0))

    # Format output
    results = []
    for key in sorted(sources.keys(), key=lambda k: sources[k]["total_sessions"], reverse=True)[:20]:
        s = sources[key]
        weekly_sorted = sorted(s["weekly"].items())
        sparkline = [w[1]["sessions"] for w in weekly_sorted]
        results.append({
            "source_medium": s["source_medium"],
            "total_sessions": s["total_sessions"],
            "weekly": [{"week": w, **d} for w, d in weekly_sorted],
            "sparkline_sessions": sparkline,
        })

    return json.dumps({
        "weeks_analyzed": weeks,
        "sources": results,
        "total_sources": len(results),
    })
