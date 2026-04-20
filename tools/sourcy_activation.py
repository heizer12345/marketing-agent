"""Sourcy Activation & Conversion data — PostgREST API.

Pulls REAL conversion data from Sourcy's database: onboarding conversations,
stage progression, contact captures, and product requests. This is the
ground truth for whether ads/traffic actually convert into leads.

Auth: JWT token for PostgREST API.
"""

import json
from datetime import datetime, timedelta
from typing import Optional
from agents import function_tool

import config

_SOURCY_API_BASE = "https://api.sourcy.ai/db"
_SOURCY_AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjdXN0b21lcl9pZCI6IjAiLCJyb2xlIjoicG9zdGdyZXMiLCJpYXQiOjE3NTAxNDY2OTIsImV4cCI6MjA2NTcyMjY5Mn0.82WMU8QtBGohz0FGWfDYnFEkP_EKUgXjJHAX23kh3wk"

_http_client = None


def _get_client():
    global _http_client
    if _http_client is None:
        import httpx
        _http_client = httpx.Client(timeout=30)
    return _http_client


def _headers():
    return {
        "Authorization": f"Bearer {_SOURCY_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }


def _api_get(endpoint: str, params: Optional[dict] = None) -> Optional[list]:
    """GET request to Sourcy PostgREST API."""
    client = _get_client()
    try:
        resp = client.get(f"{_SOURCY_API_BASE}/{endpoint}", params=params or {}, headers=_headers())
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return [{"error": str(e)}]


# ─── Tool 1: Conversion Funnel (Ground Truth) ─────────────────────────

@function_tool
def get_activation_funnel(date_range: str = "last_30_days") -> str:
    """Get Sourcy's REAL conversion funnel from the database — ground truth for lead generation.
    Shows: conversations started → stage progression → completed leads.
    This is the ACTUAL conversion data, not tracking events.

    Stages: 1 (started) → 2 (product details) → 3 (requirements) → 4 (pricing) → complete (contact given = LEAD)

    Args:
        date_range: 'last_7_days', 'last_14_days', 'last_30_days', 'last_90_days'.
    """
    days = {"last_7_days": 7, "last_14_days": 14, "last_30_days": 30, "last_90_days": 90}.get(date_range, 30)
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00")

    data = _api_get("unified_activation_conversations", {
        "select": "id,stage,created_at,updated_at,message_count,products_count",
        "created_at": f"gte.{since}",
        "order": "created_at.desc",
        "limit": 500,
    })

    if not data or (data and isinstance(data[0], dict) and "error" in data[0]):
        return json.dumps({"error": f"API error: {data}", "skipped": True})

    # Stage distribution
    stages = {}
    for r in data:
        s = str(r.get("stage", "?"))
        stages[s] = stages.get(s, 0) + 1

    total = len(data)

    # Build funnel
    stage_order = ["1", "2", "3", "4", "complete"]
    stage_labels = {
        "1": "Started Onboarding",
        "2": "Product Details Given",
        "3": "Requirements Specified",
        "4": "Pricing Discussed",
        "complete": "Contact Given (LEAD)",
    }

    funnel = []
    cumulative = total
    for stage in stage_order:
        count = stages.get(stage, 0)
        # Users at this stage OR higher = everyone who reached at least this stage
        at_or_above = sum(stages.get(s, 0) for s in stage_order[stage_order.index(stage):])
        drop_off = cumulative - at_or_above if cumulative > at_or_above else 0
        drop_pct = round(drop_off / cumulative * 100, 1) if cumulative > 0 else 0
        conv_rate = round(at_or_above / total * 100, 1) if total > 0 else 0

        funnel.append({
            "stage": stage,
            "label": stage_labels.get(stage, f"Stage {stage}"),
            "users_at_stage": count,
            "users_reached": at_or_above,
            "drop_off_from_previous": drop_off,
            "drop_off_pct": drop_pct,
            "overall_rate": conv_rate,
        })
        cumulative = at_or_above

    # Weekly breakdown
    weekly = {}
    for r in data:
        created = r.get("created_at", "")[:10]
        if created:
            try:
                dt = datetime.strptime(created, "%Y-%m-%d")
                week = dt.strftime("%Y-W%V")
                if week not in weekly:
                    weekly[week] = {"total": 0, "completed": 0}
                weekly[week]["total"] += 1
                if r.get("stage") == "complete":
                    weekly[week]["completed"] += 1
            except Exception:
                pass

    weekly_list = []
    prev_total = None
    for week in sorted(weekly.keys()):
        w = weekly[week]
        wow = round((w["total"] - prev_total) / prev_total * 100, 1) if prev_total and prev_total > 0 else None
        conv_rate = round(w["completed"] / w["total"] * 100, 1) if w["total"] > 0 else 0
        weekly_list.append({
            "week": week,
            "conversations_started": w["total"],
            "leads_completed": w["completed"],
            "conversion_rate": conv_rate,
            "wow_change_pct": wow,
        })
        prev_total = w["total"]

    return json.dumps({
        "date_range": date_range,
        "total_conversations": total,
        "stage_distribution": stages,
        "funnel": funnel,
        "weekly_breakdown": weekly_list,
        "leads_generated": stages.get("complete", 0),
        "overall_conversion_rate": round(stages.get("complete", 0) / total * 100, 1) if total > 0 else 0,
        "avg_messages_per_conversation": round(sum(r.get("message_count", 0) for r in data) / max(total, 1), 1),
    }, indent=2)


# ─── Tool 2: Recent Leads (Completed Conversions) ─────────────────────

@function_tool
def get_recent_leads(date_range: str = "last_30_days", limit: int = 20) -> str:
    """Get recent completed leads — people who gave their contact info through onboarding.
    Shows contact name, email, when they converted, how many messages/products they discussed.

    Args:
        date_range: 'last_7_days', 'last_14_days', 'last_30_days'.
        limit: Max leads to return (default 20).
    """
    days = {"last_7_days": 7, "last_14_days": 14, "last_30_days": 30}.get(date_range, 30)
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00")

    data = _api_get("unified_activation_conversations", {
        "select": "id,stage,contact_name,contact_email,created_at,updated_at,message_count,products_count",
        "stage": "eq.complete",
        "created_at": f"gte.{since}",
        "order": "updated_at.desc",
        "limit": limit,
    })

    if not data or (data and isinstance(data[0], dict) and "error" in data[0]):
        return json.dumps({"error": f"API error: {data}", "skipped": True})

    leads = []
    for r in data:
        created = r.get("created_at", "")
        updated = r.get("updated_at", "")
        # Calculate time to convert
        try:
            c = datetime.fromisoformat(created.replace("Z", "+00:00"))
            u = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            time_to_convert_min = round((u - c).total_seconds() / 60, 1)
        except Exception:
            time_to_convert_min = None

        leads.append({
            "name": r.get("contact_name", ""),
            "email": r.get("contact_email", ""),
            "created": created[:19],
            "completed": updated[:19],
            "time_to_convert_min": time_to_convert_min,
            "messages": r.get("message_count", 0),
            "products": r.get("products_count", 0),
        })

    return json.dumps({
        "date_range": date_range,
        "total_leads": len(leads),
        "leads": leads,
        "avg_time_to_convert_min": round(
            sum(l["time_to_convert_min"] for l in leads if l["time_to_convert_min"]) /
            max(len([l for l in leads if l["time_to_convert_min"]]), 1), 1
        ),
    }, indent=2)


# ─── Tool 3: Drop-off Analysis ────────────────────────────────────────

@function_tool
def get_activation_dropoffs(date_range: str = "last_30_days") -> str:
    """Analyze WHERE users drop off in the onboarding flow.
    Shows conversations that started but didn't complete — which stage they stopped at,
    how many messages they sent before abandoning, and time patterns.

    Args:
        date_range: 'last_7_days', 'last_14_days', 'last_30_days'.
    """
    days = {"last_7_days": 7, "last_14_days": 14, "last_30_days": 30}.get(date_range, 30)
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00")

    data = _api_get("unified_activation_conversations", {
        "select": "id,stage,created_at,updated_at,message_count,products_count",
        "stage": "neq.complete",
        "created_at": f"gte.{since}",
        "order": "created_at.desc",
        "limit": 300,
    })

    if not data or (data and isinstance(data[0], dict) and "error" in data[0]):
        return json.dumps({"error": f"API error: {data}", "skipped": True})

    # Analyze drop-offs by stage
    stage_dropoffs = {}
    total = len(data)

    for r in data:
        stage = str(r.get("stage", "?"))
        if stage not in stage_dropoffs:
            stage_dropoffs[stage] = {"count": 0, "total_messages": 0, "products": 0}
        s = stage_dropoffs[stage]
        s["count"] += 1
        s["total_messages"] += r.get("message_count", 0)
        s["products"] += r.get("products_count", 0)

    # Enrich with averages
    analysis = []
    stage_labels = {
        "1": "Dropped at Start (didn't describe product)",
        "2": "Dropped after Product Details (didn't give requirements)",
        "3": "Dropped after Requirements (didn't discuss pricing)",
        "4": "Dropped after Pricing (didn't give contact)",
    }
    for stage, s in sorted(stage_dropoffs.items()):
        cnt = s["count"]
        analysis.append({
            "stage": stage,
            "label": stage_labels.get(stage, f"Stage {stage}"),
            "dropped_count": cnt,
            "pct_of_all_dropoffs": round(cnt / max(total, 1) * 100, 1),
            "avg_messages_before_drop": round(s["total_messages"] / max(cnt, 1), 1),
            "avg_products_discussed": round(s["products"] / max(cnt, 1), 1),
        })

    # Biggest drop-off
    biggest = max(analysis, key=lambda x: x["dropped_count"]) if analysis else None

    return json.dumps({
        "date_range": date_range,
        "total_incomplete": total,
        "dropoff_by_stage": analysis,
        "biggest_dropoff": biggest,
        "insight": f"Most users drop at Stage {biggest['stage']}: {biggest['label']}" if biggest else "No data",
    }, indent=2)
