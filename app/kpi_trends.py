"""Fetch daily KPI trends + drivers for Home KPI drill-down modals."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def resolve_kpi_key(label: str, source: str) -> str:
    """Map snapshot KPI label + source to a trend fetcher key."""
    low = (label or "").lower()
    src = (source or "").lower()
    if "engaged" in low and "session" in low and "ga4" in src:
        return "ga4_engaged_sessions"
    if ("engagement rate" in low or "engagement %" in low) and "ga4" in src:
        return "ga4_engagement_rate"
    if "session" in low and "ga4" in src:
        return "ga4_sessions"
    if ("user" in low or "visitor" in low) and "ga4" in src:
        return "ga4_users"
    if "engagement" in low and "ga4" in src:
        return "ga4_engagement_rate"
    if ("organic" in low or "click" in low) and ("search" in src or "console" in src or "gsc" in src):
        return "gsc_clicks"
    if "impression" in low and ("search" in src or "console" in src or "gsc" in src):
        return "gsc_impressions"
    if ("spend" in low or "cost" in low) and "google" in src:
        return "google_ads_spend"
    if ("spend" in low or "impression" in low or "reach" in low) and "meta" in src:
        return "meta_spend"
    if "lead" in low or "activation" in low or "sourcy" in src or "db" in src:
        return "sourcy_leads"
    if "posthog" in src and ("lead" in low or "onboard" in low):
        return "posthog_onboard"
    return f"generic_{_slug(label)}"


def _date_range_days(days: int, end_offset: int = 0) -> str:
    end = datetime.now() - timedelta(days=end_offset)
    start = end - timedelta(days=days - 1)
    return f"{start.strftime('%Y-%m-%d')}:{end.strftime('%Y-%m-%d')}"


def _format_ga4_date(raw: str) -> str:
    try:
        return datetime.strptime(raw, "%Y%m%d").strftime("%b %d")
    except Exception:
        return raw


def _series_delta(series: list[dict]) -> tuple[float | None, float | None]:
    """WoW % comparing last 7 days sum vs prior 7 days sum."""
    if len(series) < 2:
        return None, None
    vals = [float(p.get("value") or 0) for p in series]
    if len(vals) >= 14:
        cur, prev = sum(vals[-7:]), sum(vals[-14:-7])
    elif len(vals) >= 7:
        mid = len(vals) // 2
        cur, prev = sum(vals[mid:]), sum(vals[:mid])
    else:
        cur, prev = vals[-1], vals[0]
    if prev == 0:
        return round(cur, 2), None
    return round(cur, 2), round((cur - prev) / prev * 100, 1)


def _ga4_daily(metric: str, days: int = 14) -> dict[str, Any]:
    from tools.google_analytics import _run_report

    dr = _date_range_days(days)
    rows = _run_report(["date"], [metric], dr, limit=500)
    if rows and isinstance(rows[0], dict) and rows[0].get("error"):
        return {"error": rows[0]["error"], "series": [], "drivers": []}

    by_date: dict[str, float] = {}
    for r in rows or []:
        d = r.get("date", "")
        if not d:
            continue
        val = r.get(metric, 0)
        try:
            by_date[d] = float(val)
        except (TypeError, ValueError):
            by_date[d] = 0.0

    series = [
        {"date": _format_ga4_date(d), "raw_date": d, "value": round(by_date[d], 2)}
        for d in sorted(by_date.keys())
    ]
    total, delta = _series_delta(series)
    drivers = _ga4_channel_drivers(metric)
    return {"series": series, "total_current": total, "delta_pct": delta, "drivers": drivers, "unit": ""}


def _ga4_channel_drivers(metric: str = "sessions") -> list[dict]:
    from tools.google_analytics import _run_report

    cur_dr = _date_range_days(7)
    prev_dr = _date_range_days(7, end_offset=7)
    cur = _run_report(["sessionDefaultChannelGroup"], [metric], cur_dr, order_by_metric=metric, limit=12)
    prev = _run_report(["sessionDefaultChannelGroup"], [metric], prev_dr, order_by_metric=metric, limit=12)
    if cur and isinstance(cur[0], dict) and cur[0].get("error"):
        return []

    prev_map: dict[str, float] = {}
    for r in prev or []:
        ch = r.get("sessionDefaultChannelGroup", "Unknown")
        try:
            prev_map[ch] = float(r.get(metric, 0))
        except (TypeError, ValueError):
            prev_map[ch] = 0.0

    drivers: list[dict] = []
    for r in cur or []:
        ch = r.get("sessionDefaultChannelGroup", "Unknown")
        try:
            cur_v = float(r.get(metric, 0))
        except (TypeError, ValueError):
            cur_v = 0.0
        prev_v = prev_map.get(ch, 0)
        if prev_v > 0:
            chg = round((cur_v - prev_v) / prev_v * 100, 1)
        elif cur_v > 0:
            chg = 100.0
        else:
            chg = 0.0
        drivers.append({"label": ch, "current": round(cur_v, 1), "previous": round(prev_v, 1), "change_pct": chg})

    drivers.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    return drivers[:5]


def _gsc_daily(metric: str = "clicks", days: int = 14) -> dict[str, Any]:
    from tools.search_console import _query_search_analytics

    end = datetime.now() - timedelta(days=3)
    start = end - timedelta(days=days - 1)
    dr = f"{start.strftime('%Y-%m-%d')}:{end.strftime('%Y-%m-%d')}"

    rows = _query_search_analytics(["date"], dr, row_limit=500)
    if rows and isinstance(rows[0], dict) and rows[0].get("error"):
        return {"error": rows[0]["error"], "series": [], "drivers": []}

    by_date: dict[str, float] = {}
    for r in rows or []:
        d = r.get("date", "")
        if not d:
            continue
        by_date[d] = float(r.get(metric, 0))

    series = [
        {"date": datetime.strptime(d, "%Y-%m-%d").strftime("%b %d"), "raw_date": d, "value": round(by_date[d], 2)}
        for d in sorted(by_date.keys())
    ]
    total, delta = _series_delta(series)
    return {"series": series, "total_current": total, "delta_pct": delta, "drivers": [], "unit": ""}


def _google_ads_daily_spend(days: int = 14) -> dict[str, Any]:
    import config
    if not config.GOOGLE_ADS_REFRESH_TOKEN:
        return {"error": "Google Ads not configured", "series": [], "drivers": []}

    from tools.google_ads import _run_query

    end = datetime.now()
    start = end - timedelta(days=days - 1)
    q = f"""
        SELECT segments.date, metrics.cost_micros
        FROM campaign
        WHERE segments.date BETWEEN '{start.strftime('%Y-%m-%d')}' AND '{end.strftime('%Y-%m-%d')}'
        ORDER BY segments.date
    """
    rows = _run_query(q)
    if rows and isinstance(rows[0], dict) and "error" in rows[0]:
        return {"error": rows[0]["error"], "series": [], "drivers": []}

    by_date: dict[str, float] = {}
    for row in rows or []:
        d = str(row.segments.date)
        cost = row.metrics.cost_micros / 1_000_000
        by_date[d] = by_date.get(d, 0) + cost

    series = [
        {"date": datetime.strptime(d, "%Y-%m-%d").strftime("%b %d"), "raw_date": d, "value": round(by_date[d], 2)}
        for d in sorted(by_date.keys())
    ]
    total, delta = _series_delta(series)
    return {"series": series, "total_current": total, "delta_pct": delta, "drivers": [], "unit": "USD"}


def _sourcy_leads_daily(days: int = 14) -> dict[str, Any]:
    from tools.sourcy_activation import _api_get

    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00")
    data = _api_get("unified_activation_conversations", {
        "select": "id,stage,created_at,updated_at",
        "stage": "eq.complete",
        "created_at": f"gte.{since}",
        "order": "created_at.asc",
        "limit": 500,
    })
    if not data or (isinstance(data, list) and data and isinstance(data[0], dict) and "error" in data[0]):
        err = data[0].get("error", "Sourcy DB unavailable") if data else "Sourcy DB unavailable"
        return {"error": str(err), "series": [], "drivers": []}

    by_date: dict[str, int] = {}
    for r in data or []:
        created = (r.get("created_at") or "")[:10]
        if created:
            by_date[created] = by_date.get(created, 0) + 1

    # Fill missing days with 0
    end = datetime.now().date()
    series = []
    for i in range(days - 1, -1, -1):
        d = (end - timedelta(days=i)).isoformat()
        series.append({
            "date": datetime.strptime(d, "%Y-%m-%d").strftime("%b %d"),
            "raw_date": d,
            "value": by_date.get(d, 0),
        })
    total, delta = _series_delta(series)
    return {"series": series, "total_current": total, "delta_pct": delta, "drivers": [], "unit": "leads"}


def _match_insights(label: str, source: str, insights: list[dict]) -> list[str]:
    tokens = set(re.findall(r"[a-z]{4,}", f"{label} {source}".lower()))
    matched: list[str] = []
    for ins in insights or []:
        text = (ins.get("text") or "").lower()
        src = (ins.get("source") or "").lower()
        if source.lower() in src or any(t in text for t in tokens if t not in ("last", "days", "week")):
            matched.append(ins.get("text", ""))
    return matched[:3]


def build_explanation_bullets(
    *,
    label: str,
    kpi_key: str,
    delta_pct: float | None,
    drivers: list[dict],
    related_insights: list[str],
    error: str | None = None,
) -> list[str]:
    """Short bullet points for the KPI modal — one idea per line."""
    if error:
        return [
            f"Live trend data unavailable: {error}",
            "The headline number on the card still comes from your last briefing snapshot.",
        ]

    direction = "up" if (delta_pct or 0) > 0 else "down" if (delta_pct or 0) < 0 else "flat"
    bullets: list[str] = []

    if delta_pct is not None:
        bullets.append(
            f"**Week-over-week:** {label} is {direction} **{abs(delta_pct):.1f}%** "
            f"(last 7 days vs the prior 7)."
        )
    else:
        bullets.append(
            f"**Trend window:** Daily values for the last 7–14 days ({kpi_key.replace('_', ' ')})."
        )

    if drivers:
        top = drivers[0]
        sign = "up" if top["change_pct"] > 0 else "down" if top["change_pct"] < 0 else "flat"
        bullets.append(
            f"**Top channel:** {top['label']} is {sign} **{abs(top['change_pct']):.1f}%** WoW "
            f"({top['previous']} → {top['current']})."
        )
        for d in drivers[1:3]:
            bullets.append(
                f"**Also:** {d['label']} {d['change_pct']:+.1f}% WoW ({d['previous']} → {d['current']})."
            )

    used = " ".join(bullets).lower()
    for ins in related_insights:
        text = (ins or "").strip()
        if text and text.lower() not in used:
            bullets.append(f"**From briefing:** {text}")
            break

    if direction == "up" and not related_insights and drivers and drivers[0]["change_pct"] > 0:
        bullets.append(
            "**Next check:** Confirm traffic quality (geo, bounce) before scaling spend on the winning channel."
        )
    elif direction == "down" and not related_insights:
        bullets.append(
            "**Next check:** Rule out seasonality, tracking gaps, or a paused campaign before changing strategy."
        )

    return bullets


def fetch_kpi_trend(kpi_key: str, label: str, source: str, insights: list[dict] | None = None) -> dict[str, Any]:
    """Return chart series + explanation for a Home KPI card."""
    fetchers = {
        "ga4_sessions": lambda: _ga4_daily("sessions"),
        "ga4_engaged_sessions": lambda: _ga4_daily("engagedSessions"),
        "ga4_users": lambda: _ga4_daily("totalUsers"),
        "ga4_engagement_rate": lambda: _ga4_daily("engagementRate"),
        "gsc_clicks": lambda: _gsc_daily("clicks"),
        "gsc_impressions": lambda: _gsc_daily("impressions"),
        "google_ads_spend": _google_ads_daily_spend,
        "sourcy_leads": _sourcy_leads_daily,
    }

    fn = fetchers.get(kpi_key)
    if not fn:
        # Fallback: try GA4 sessions if source is GA4
        if "ga4" in source.lower():
            data = _ga4_daily("sessions")
            kpi_key = "ga4_sessions"
        else:
            _err_bullets = build_explanation_bullets(
                label=label,
                kpi_key=kpi_key,
                delta_pct=None,
                drivers=[],
                related_insights=_match_insights(label, source, insights or []),
                error="No live trend API mapped for this metric yet.",
            )
            return {
                "kpi_key": kpi_key,
                "label": label,
                "source": source,
                "series": [],
                "delta_pct": None,
                "drivers": [],
                "explanation_bullets": _err_bullets,
                "explanation": " ".join(b.replace("**", "") for b in _err_bullets),
                "error": "unsupported_metric",
            }
    else:
        data = fn()

    err = data.get("error")
    series = data.get("series") or []
    delta = data.get("delta_pct")
    drivers = data.get("drivers") or []
    related = _match_insights(label, source, insights or [])
    bullets = build_explanation_bullets(
        label=label,
        kpi_key=kpi_key,
        delta_pct=delta,
        drivers=drivers,
        related_insights=related,
        error=err,
    )

    return {
        "kpi_key": kpi_key,
        "label": label,
        "source": source,
        "series": series,
        "delta_pct": delta,
        "total_current": data.get("total_current"),
        "unit": data.get("unit", ""),
        "drivers": drivers,
        "explanation_bullets": bullets,
        "explanation": " ".join(b.replace("**", "") for b in bullets),
        "related_insights": related,
        "error": err,
    }
