"""Smart analysis tools that combine multiple data sources and produce insights."""

import json
from datetime import datetime, timedelta
from agents import function_tool

from tools.google_analytics import (
    _run_report as ga4_report,
    _parse_date_range as ga4_parse_dates,
    _get_client as ga4_client,
)
from tools.search_console import (
    _query_search_analytics as sc_query,
    _parse_date_range as sc_parse_dates,
)
import config

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric, OrderBy, FilterExpression,
    Filter,
)


def _ga4_raw_report(dimensions, metrics, start, end, limit=100):
    """Direct GA4 report with explicit dates."""
    client = BetaAnalyticsDataClient()
    request = RunReportRequest(
        property=f"properties/{config.GA4_PROPERTY_ID}",
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        limit=limit,
    )
    if metrics:
        request.order_bys = [
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name=metrics[0]), desc=True)
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
def analyze_blindspots(date_range: str = "last_30_days") -> str:
    """Deep blindspot analysis: checks country targeting, traffic anomalies,
    wasted organic reach, and unexpected patterns. Compares against target
    countries (ID, PH, TH, BR, US, MX).

    Args:
        date_range: 'last_7_days', 'last_30_days', or 'YYYY-MM-DD:YYYY-MM-DD'
    """
    start, end = ga4_parse_dates(date_range)
    target_codes = {c["code"]: c["name"] for c in config.TARGET_MARKETS["target_countries"]}
    acceptable = {c["code"]: c["name"] for c in config.TARGET_MARKETS.get("acceptable_countries", [])}
    all_valid = set(target_codes.keys()) | set(acceptable.keys())

    findings = []

    # 1. GA4 Country traffic analysis
    country_data = _ga4_raw_report(
        ["country", "countryId"],
        ["sessions", "totalUsers", "newUsers", "bounceRate",
         "averageSessionDuration", "conversions"],
        start, end, limit=50
    )

    total_sessions = sum(r.get("sessions", 0) for r in country_data)
    target_sessions = 0
    non_target_traffic = []
    target_performance = []

    for row in country_data:
        country_id = row.get("countryId", "")
        country_name = row.get("country", "Unknown")
        sessions = row.get("sessions", 0)
        pct = round(sessions / total_sessions * 100, 1) if total_sessions > 0 else 0

        if country_id in target_codes:
            target_sessions += sessions
            target_performance.append({
                "country": country_name,
                "code": country_id,
                "sessions": sessions,
                "pct_of_total": pct,
                "bounce_rate": round(row.get("bounceRate", 0) * 100, 1) if isinstance(row.get("bounceRate", 0), float) and row.get("bounceRate", 0) < 1 else round(row.get("bounceRate", 0), 1),
                "avg_duration": round(row.get("averageSessionDuration", 0), 0),
                "conversions": row.get("conversions", 0),
            })
        elif country_id not in all_valid and sessions > 0:
            non_target_traffic.append({
                "country": country_name,
                "code": country_id,
                "sessions": sessions,
                "pct_of_total": pct,
            })

    non_target_total_pct = round(sum(r["pct_of_total"] for r in non_target_traffic), 1)

    if non_target_traffic:
        findings.append({
            "type": "WASTED_TRAFFIC",
            "severity": "high" if non_target_total_pct > 10 else "medium",
            "title": f"{non_target_total_pct}% of traffic from non-target countries",
            "detail": "Top non-target sources: " + ", ".join(f"{r['country']} ({r['pct_of_total']}%)" for r in non_target_traffic[:5]),
            "action": "Review ad targeting settings. Add negative geo targeting for these countries.",
        })

    # Check which target countries are MISSING or low
    for code, name in target_codes.items():
        matching = [r for r in target_performance if r["code"] == code]
        if not matching:
            findings.append({
                "type": "MISSING_TARGET",
                "severity": "high",
                "title": f"No traffic from target country: {name} ({code})",
                "detail": "Zero sessions recorded from this target market.",
                "action": f"Check if campaigns are running for {name}. Verify geo targeting.",
            })
        elif matching[0]["pct_of_total"] < 3:
            findings.append({
                "type": "LOW_TARGET_TRAFFIC",
                "severity": "medium",
                "title": f"Low traffic from {name}: only {matching[0]['pct_of_total']}% of total",
                "detail": f"{matching[0]['sessions']} sessions, bounce rate {matching[0]['bounce_rate']}%",
                "action": f"Consider increasing ad spend or content targeting for {name}.",
            })

    # 2. Traffic source anomalies
    source_data = _ga4_raw_report(
        ["sessionSource", "sessionMedium"],
        ["sessions", "bounceRate", "conversions"],
        start, end, limit=20
    )

    for src in source_data:
        bounce = src.get("bounceRate", 0)
        if isinstance(bounce, float) and bounce < 1:
            bounce = bounce * 100
        sessions = src.get("sessions", 0)
        if sessions > 50 and bounce > 80:
            findings.append({
                "type": "HIGH_BOUNCE_SOURCE",
                "severity": "medium",
                "title": f"High bounce rate from {src['sessionSource']}/{src['sessionMedium']}: {round(bounce, 1)}%",
                "detail": f"{sessions} sessions with {round(bounce, 1)}% bounce rate",
                "action": "Check landing page relevance for this traffic source.",
            })

    # 3. Landing page issues
    page_data = _ga4_raw_report(
        ["landingPagePlusQueryString"],
        ["sessions", "bounceRate", "averageSessionDuration", "conversions"],
        start, end, limit=20
    )

    for page in page_data:
        bounce = page.get("bounceRate", 0)
        if isinstance(bounce, float) and bounce < 1:
            bounce = bounce * 100
        sessions = page.get("sessions", 0)
        if sessions > 30 and bounce > 75:
            findings.append({
                "type": "BAD_LANDING_PAGE",
                "severity": "medium",
                "title": f"Landing page with {round(bounce, 1)}% bounce rate",
                "detail": f"Page: {page['landingPagePlusQueryString']} ({sessions} sessions)",
                "action": "Review page content, load speed, and mobile experience.",
            })

    # 4. Search Console - organic blindspots
    try:
        sc_country_data = sc_query(["country"], date_range, row_limit=30)
        if sc_country_data and "error" not in sc_country_data[0]:
            total_organic_clicks = sum(r.get("clicks", 0) for r in sc_country_data)
            for row in sc_country_data:
                country_code = row.get("country", "").upper()
                clicks = row.get("clicks", 0)
                impressions = row.get("impressions", 0)
                ctr = row.get("ctr", 0)

                if country_code in [c.lower() for c in target_codes.keys()] or country_code in target_codes:
                    if impressions > 100 and ctr < 2.0:
                        findings.append({
                            "type": "LOW_ORGANIC_CTR",
                            "severity": "medium",
                            "title": f"Low organic CTR in {country_code}: {ctr}%",
                            "detail": f"{impressions} impressions but only {clicks} clicks ({ctr}% CTR)",
                            "action": "Improve meta titles and descriptions for this market.",
                        })
    except Exception:
        pass

    # 5. Daily traffic spikes/drops detection
    daily_data = _ga4_raw_report(
        ["date"],
        ["sessions", "totalUsers"],
        start, end, limit=60
    )

    if len(daily_data) >= 7:
        sessions_list = [d.get("sessions", 0) for d in daily_data]
        avg_sessions = sum(sessions_list) / len(sessions_list) if sessions_list else 0

        for day in daily_data:
            day_sessions = day.get("sessions", 0)
            if avg_sessions > 0:
                deviation = ((day_sessions - avg_sessions) / avg_sessions) * 100
                if deviation > 80:
                    findings.append({
                        "type": "TRAFFIC_SPIKE",
                        "severity": "info",
                        "title": f"Traffic spike on {day['date']}: +{round(deviation)}% above average",
                        "detail": f"{day_sessions} sessions vs {round(avg_sessions)} daily average",
                        "action": "Investigate what caused the spike (campaign launch, viral content, press).",
                    })
                elif deviation < -50:
                    findings.append({
                        "type": "TRAFFIC_DROP",
                        "severity": "high",
                        "title": f"Traffic drop on {day['date']}: {round(deviation)}% below average",
                        "detail": f"{day_sessions} sessions vs {round(avg_sessions)} daily average",
                        "action": "Check for technical issues, paused campaigns, or site downtime.",
                    })

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "info": 2}
    findings.sort(key=lambda f: severity_order.get(f["severity"], 3))

    return json.dumps({
        "date_range": f"{start} to {end}",
        "total_sessions": total_sessions,
        "target_country_sessions": target_sessions,
        "target_country_pct": round(target_sessions / total_sessions * 100, 1) if total_sessions > 0 else 0,
        "target_performance": target_performance,
        "non_target_traffic": non_target_traffic[:10],
        "findings_count": len(findings),
        "findings": findings,
    }, indent=2)


@function_tool
def generate_weekly_deep_report(date_range: str = "last_7_days") -> str:
    """Generate a comprehensive weekly analysis combining GA4, Search Console data.
    Returns pre-analyzed data ready for report generation.

    Args:
        date_range: 'last_7_days', 'last_30_days', or 'YYYY-MM-DD:YYYY-MM-DD'
    """
    start, end = ga4_parse_dates(date_range)
    target_codes = {c["code"]: c["name"] for c in config.TARGET_MARKETS["target_countries"]}

    report = {"date_range": f"{start} to {end}", "sections": {}}

    # 1. Overall website metrics
    overview = _ga4_raw_report(
        [], ["sessions", "totalUsers", "newUsers", "screenPageViews",
             "bounceRate", "averageSessionDuration", "engagementRate", "conversions"],
        start, end
    )
    report["sections"]["overview"] = overview[0] if overview else {}

    # Previous period comparison
    days = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days
    prev_end = (datetime.strptime(start, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_start = (datetime.strptime(start, "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")

    prev_overview = _ga4_raw_report(
        [], ["sessions", "totalUsers", "newUsers", "screenPageViews",
             "bounceRate", "averageSessionDuration", "conversions"],
        prev_start, prev_end
    )
    report["sections"]["previous_period"] = prev_overview[0] if prev_overview else {}
    report["sections"]["prev_dates"] = f"{prev_start} to {prev_end}"

    # 2. Traffic sources
    report["sections"]["traffic_sources"] = _ga4_raw_report(
        ["sessionDefaultChannelGroup"],
        ["sessions", "totalUsers", "bounceRate", "conversions"],
        start, end, limit=10
    )

    # 3. Country breakdown
    report["sections"]["countries"] = _ga4_raw_report(
        ["country", "countryId"],
        ["sessions", "totalUsers", "bounceRate", "conversions"],
        start, end, limit=20
    )

    # 4. Top landing pages
    report["sections"]["landing_pages"] = _ga4_raw_report(
        ["landingPagePlusQueryString"],
        ["sessions", "bounceRate", "averageSessionDuration", "conversions"],
        start, end, limit=15
    )

    # 5. Device breakdown
    report["sections"]["devices"] = _ga4_raw_report(
        ["deviceCategory"],
        ["sessions", "totalUsers", "bounceRate", "conversions"],
        start, end
    )

    # 6. Daily trend
    report["sections"]["daily_trend"] = _ga4_raw_report(
        ["date"],
        ["sessions", "totalUsers", "conversions"],
        start, end, limit=60
    )

    # 7. Referral domains
    report["sections"]["referral_domains"] = _ga4_raw_report(
        ["sessionSource"],
        ["sessions", "totalUsers", "bounceRate"],
        start, end, limit=15
    )

    # 8. Search Console - top queries
    try:
        report["sections"]["organic_queries"] = sc_query(["query"], date_range, row_limit=20)
    except Exception:
        report["sections"]["organic_queries"] = []

    # 9. Search Console - by country
    try:
        report["sections"]["organic_countries"] = sc_query(["country"], date_range, row_limit=15)
    except Exception:
        report["sections"]["organic_countries"] = []

    # 10. Search Console - top pages
    try:
        report["sections"]["organic_pages"] = sc_query(["page"], date_range, row_limit=15)
    except Exception:
        report["sections"]["organic_pages"] = []

    # Calculate WoW changes
    changes = {}
    curr = report["sections"].get("overview", {})
    prev = report["sections"].get("previous_period", {})
    for key in ["sessions", "totalUsers", "conversions"]:
        c = curr.get(key, 0)
        p = prev.get(key, 0)
        if p > 0:
            changes[key] = round(((c - p) / p) * 100, 1)
        else:
            changes[key] = 0
    report["sections"]["wow_changes"] = changes

    report["target_countries"] = list(target_codes.keys())

    return json.dumps(report, indent=2)


@function_tool
def analyze_organic_deep(date_range: str = "last_30_days") -> str:
    """Deep organic search analysis: keyword opportunities, ranking changes,
    top performing pages, CTR optimization opportunities.

    Args:
        date_range: 'last_7_days', 'last_30_days', or 'YYYY-MM-DD:YYYY-MM-DD'
    """
    findings = []

    # Top keywords with metrics
    keywords = sc_query(["query"], date_range, row_limit=50)
    if keywords and "error" in keywords[0]:
        return json.dumps({"error": keywords[0]["error"]})

    # Keywords by country
    country_keywords = sc_query(["country", "query"], date_range, row_limit=50)

    # Pages performance
    pages = sc_query(["page"], date_range, row_limit=30)

    # High impression, low CTR keywords (optimization opportunities)
    low_ctr_keywords = []
    for kw in keywords:
        if kw.get("impressions", 0) > 50 and kw.get("ctr", 0) < 3.0:
            low_ctr_keywords.append({
                "query": kw["query"],
                "impressions": kw["impressions"],
                "clicks": kw["clicks"],
                "ctr": kw["ctr"],
                "position": kw["position"],
                "opportunity": "Improve meta title/description" if kw["position"] <= 10
                    else "Improve content to rank higher",
            })

    # Position 4-10 keywords (striking distance to top 3)
    striking_distance = [
        kw for kw in keywords
        if 4 <= kw.get("position", 0) <= 10 and kw.get("impressions", 0) > 20
    ]

    # Top pages by clicks
    top_pages = sorted(pages, key=lambda p: p.get("clicks", 0), reverse=True)[:10]

    # Pages with high impressions but low clicks
    underperforming_pages = [
        p for p in pages
        if p.get("impressions", 0) > 100 and p.get("ctr", 0) < 2.0
    ]

    # Country-level organic performance for target markets
    target_organic = {}
    target_codes_lower = [c["code"].lower() for c in config.TARGET_MARKETS["target_countries"]]
    for row in (country_keywords or []):
        country = row.get("country", "").lower()
        if country in target_codes_lower:
            if country not in target_organic:
                target_organic[country] = []
            target_organic[country].append(row)

    return json.dumps({
        "date_range": date_range,
        "total_keywords_tracked": len(keywords),
        "top_keywords": keywords[:15],
        "low_ctr_opportunities": low_ctr_keywords[:10],
        "striking_distance_keywords": striking_distance[:10],
        "top_pages": top_pages,
        "underperforming_pages": underperforming_pages[:5],
        "target_market_organic": {k: v[:5] for k, v in target_organic.items()},
        "summary": {
            "total_clicks": sum(kw.get("clicks", 0) for kw in keywords),
            "total_impressions": sum(kw.get("impressions", 0) for kw in keywords),
            "avg_position": round(sum(kw.get("position", 0) for kw in keywords) / len(keywords), 1) if keywords else 0,
            "optimization_opportunities": len(low_ctr_keywords),
            "striking_distance_count": len(striking_distance),
        },
    }, indent=2)


@function_tool
def analyze_traffic_patterns(date_range: str = "last_30_days") -> str:
    """Analyze traffic patterns: daily/weekly trends, spikes, drops,
    top referral domains, device splits, and user behavior patterns.

    Args:
        date_range: 'last_7_days', 'last_30_days', or 'YYYY-MM-DD:YYYY-MM-DD'
    """
    start, end = ga4_parse_dates(date_range)

    # Daily sessions trend
    daily = _ga4_raw_report(
        ["date"], ["sessions", "totalUsers", "conversions"],
        start, end, limit=60
    )

    # Calculate stats
    sessions_list = [d.get("sessions", 0) for d in daily]
    avg = sum(sessions_list) / len(sessions_list) if sessions_list else 0
    max_day = max(daily, key=lambda d: d.get("sessions", 0)) if daily else {}
    min_day = min(daily, key=lambda d: d.get("sessions", 0)) if daily else {}

    # Day of week analysis
    dow_stats = {}
    for d in daily:
        try:
            dt = datetime.strptime(d["date"], "%Y%m%d")
            dow = dt.strftime("%A")
            if dow not in dow_stats:
                dow_stats[dow] = []
            dow_stats[dow].append(d.get("sessions", 0))
        except Exception:
            pass

    dow_avg = {dow: round(sum(v) / len(v)) for dow, v in dow_stats.items()} if dow_stats else {}

    # Hour of day (if available - GA4 supports this)
    hourly = _ga4_raw_report(
        ["hour"], ["sessions"],
        start, end, limit=24
    )

    # Source/medium breakdown
    sources = _ga4_raw_report(
        ["sessionSource", "sessionMedium"],
        ["sessions", "totalUsers", "bounceRate", "conversions"],
        start, end, limit=15
    )

    # New vs returning
    user_type = _ga4_raw_report(
        ["newVsReturning"],
        ["sessions", "totalUsers", "conversions", "bounceRate"],
        start, end
    )

    # Device category
    devices = _ga4_raw_report(
        ["deviceCategory"],
        ["sessions", "totalUsers", "bounceRate", "conversions"],
        start, end
    )

    # Detect anomalies
    anomalies = []
    for d in daily:
        s = d.get("sessions", 0)
        if avg > 0:
            dev = ((s - avg) / avg) * 100
            if abs(dev) > 50:
                anomalies.append({
                    "date": d["date"],
                    "sessions": s,
                    "deviation_pct": round(dev, 1),
                    "type": "spike" if dev > 0 else "drop",
                })

    return json.dumps({
        "date_range": f"{start} to {end}",
        "daily_trend": daily,
        "stats": {
            "avg_daily_sessions": round(avg),
            "peak_day": max_day,
            "lowest_day": min_day,
            "total_sessions": sum(sessions_list),
        },
        "day_of_week_avg": dow_avg,
        "hourly_distribution": hourly,
        "traffic_sources": sources,
        "user_type": user_type,
        "devices": devices,
        "anomalies": anomalies,
    }, indent=2)
