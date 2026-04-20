"""Instagram Graph API tools — READ-ONLY post and account analytics.

Provides account overview, post-level engagement metrics, and insights.
Uses the Instagram Graph API through existing Meta App credentials.
All tools gracefully degrade if credentials are not configured.

Requires: httpx (already in requirements)
Auth: Meta App credentials + Instagram Business Account ID.
"""

import json
import time as _time
from datetime import datetime, timedelta
from typing import Optional, Tuple
from agents import function_tool

import config

_GRAPH_BASE = "https://graph.facebook.com/v21.0"
_http_client = None


def _get_client():
    """Lazily initialize httpx client."""
    global _http_client
    if _http_client is None:
        import httpx
        _http_client = httpx.Client(timeout=30)
    return _http_client


def _missing_key():
    return json.dumps({
        "error": "Instagram API not configured. Add INSTAGRAM_BUSINESS_ACCOUNT_ID and META_ACCESS_TOKEN to .env",
        "skipped": True,
    })


def _parse_date_range(date_range: str) -> Tuple[datetime, datetime]:
    """Convert standard date_range string to (start, end) datetimes."""
    today = datetime.now()
    if date_range == "last_7_days":
        start = today - timedelta(days=7)
    elif date_range == "last_14_days":
        start = today - timedelta(days=14)
    elif date_range == "last_30_days":
        start = today - timedelta(days=30)
    elif date_range == "last_90_days":
        start = today - timedelta(days=90)
    elif ":" in date_range:
        parts = date_range.split(":")
        start = datetime.strptime(parts[0], "%Y-%m-%d")
        today = datetime.strptime(parts[1], "%Y-%m-%d")
    else:
        start = today - timedelta(days=30)
    return start, today


def _graph_get(endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
    """Make a GET request to the Instagram Graph API."""
    client = _get_client()
    url = f"{_GRAPH_BASE}/{endpoint}"
    all_params = {"access_token": config.META_ACCESS_TOKEN}
    if params:
        all_params.update(params)
    try:
        resp = client.get(url, params=all_params)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ─── Tool 1: Account Overview ─────────────────────────────────────────

@function_tool
def get_ig_account_overview() -> str:
    """Get Instagram Business account overview stats.
    Returns follower count, media count, profile info."""
    ig_id = getattr(config, "INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    if not ig_id or not config.META_ACCESS_TOKEN:
        return _missing_key()

    data = _graph_get(ig_id, {
        "fields": "id,name,username,biography,media_count,followers_count,follows_count,profile_picture_url,website"
    })
    if not data or "error" in data:
        return json.dumps({"error": f"Failed to fetch IG account: {data}", "skipped": True})

    return json.dumps({
        "account": {
            "id": data.get("id"),
            "username": data.get("username", ""),
            "name": data.get("name", ""),
            "bio": data.get("biography", ""),
            "followers": data.get("followers_count", 0),
            "following": data.get("follows_count", 0),
            "total_posts": data.get("media_count", 0),
            "profile_picture": data.get("profile_picture_url", ""),
            "website": data.get("website", ""),
        }
    }, indent=2)


# ─── Tool 2: Recent Posts ─────────────────────────────────────────────

@function_tool
def get_ig_recent_posts(limit: int = 25, date_range: str = "last_30_days") -> str:
    """Get recent Instagram posts with basic engagement metrics.

    Args:
        limit: Max posts to return (default 25, max 100).
        date_range: 'last_7_days', 'last_14_days', 'last_30_days', 'last_90_days',
                    or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    ig_id = getattr(config, "INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    if not ig_id or not config.META_ACCESS_TOKEN:
        return _missing_key()

    start_dt, end_dt = _parse_date_range(date_range)

    fields = "id,caption,media_type,media_url,thumbnail_url,timestamp,permalink,like_count,comments_count"
    data = _graph_get(f"{ig_id}/media", {
        "fields": fields,
        "limit": min(limit, 100),
    })

    if not data or "error" in data:
        return json.dumps({"error": f"Failed to fetch IG posts: {data}", "skipped": True})

    posts = []
    for item in data.get("data", []):
        ts = item.get("timestamp", "")
        if ts:
            try:
                post_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                if post_dt < start_dt or post_dt > end_dt:
                    continue
            except Exception:
                pass

        caption = item.get("caption", "")
        posts.append({
            "id": item.get("id"),
            "media_type": item.get("media_type", "UNKNOWN"),
            "caption": caption[:200] + ("..." if len(caption) > 200 else ""),
            "timestamp": ts,
            "permalink": item.get("permalink", ""),
            "like_count": item.get("like_count", 0),
            "comments_count": item.get("comments_count", 0),
            "media_url": item.get("media_url", ""),
            "thumbnail_url": item.get("thumbnail_url", ""),
        })

    return json.dumps({
        "posts": posts,
        "count": len(posts),
        "date_range": date_range,
    }, indent=2)


# ─── Tool 3: Post Insights ────────────────────────────────────────────

@function_tool
def get_ig_post_insights(media_id: str) -> str:
    """Get detailed insights for a specific Instagram post.
    Returns impressions, reach, saves, shares, video views, plays.

    Args:
        media_id: The Instagram media ID to get insights for.
    """
    if not config.META_ACCESS_TOKEN:
        return _missing_key()

    # Different metrics for different media types — request all, handle errors
    metrics_video = "impressions,reach,saved,shares,video_views,plays,total_interactions"
    metrics_image = "impressions,reach,saved,shares,total_interactions"

    # Try video metrics first (works for REEL and VIDEO)
    data = _graph_get(f"{media_id}/insights", {"metric": metrics_video})

    if data and "error" in data:
        # Fallback to image metrics
        data = _graph_get(f"{media_id}/insights", {"metric": metrics_image})

    if not data or "error" in data:
        return json.dumps({"error": f"Failed to fetch insights for {media_id}: {data}", "media_id": media_id})

    insights = {}
    for item in data.get("data", []):
        name = item.get("name", "")
        values = item.get("values", [{}])
        insights[name] = values[0].get("value", 0) if values else 0

    return json.dumps({
        "media_id": media_id,
        "insights": insights,
    }, indent=2)


# ─── Tool 4: Posts with Full Insights (Composite) ─────────────────────

@function_tool
def get_ig_posts_with_insights(limit: int = 25, date_range: str = "last_7_days") -> str:
    """Get Instagram posts with FULL insights — engagement, reach, saves, shares.
    Combines post data with per-post insights. Includes content type analysis
    (REEL vs IMAGE vs CAROUSEL performance comparison) and WoW metrics.

    Args:
        limit: Max posts to analyze (default 25). Each post requires an API call,
               so keep reasonable.
        date_range: 'last_7_days', 'last_14_days', 'last_30_days', or 'YYYY-MM-DD:YYYY-MM-DD'.
    """
    ig_id = getattr(config, "INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    if not ig_id or not config.META_ACCESS_TOKEN:
        return _missing_key()

    start_dt, end_dt = _parse_date_range(date_range)

    # Get posts
    fields = "id,caption,media_type,media_url,thumbnail_url,timestamp,permalink,like_count,comments_count"
    data = _graph_get(f"{ig_id}/media", {
        "fields": fields,
        "limit": min(limit * 2, 100),  # fetch extra to filter by date
    })

    if not data or "error" in data:
        return json.dumps({"error": f"Failed to fetch posts: {data}", "skipped": True})

    # Filter by date range
    filtered_posts = []
    for item in data.get("data", []):
        ts = item.get("timestamp", "")
        if ts:
            try:
                post_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                if post_dt < start_dt or post_dt > end_dt:
                    continue
            except Exception:
                pass
        filtered_posts.append(item)
        if len(filtered_posts) >= limit:
            break

    # Enrich with insights
    enriched = []
    for post in filtered_posts:
        media_id = post.get("id")
        if not media_id:
            continue

        # Rate limiting
        _time.sleep(0.3)

        # Fetch insights
        metrics_video = "impressions,reach,saved,shares,video_views,plays,total_interactions"
        metrics_image = "impressions,reach,saved,shares,total_interactions"

        insight_data = _graph_get(f"{media_id}/insights", {"metric": metrics_video})
        if insight_data and "error" in insight_data:
            insight_data = _graph_get(f"{media_id}/insights", {"metric": metrics_image})

        insights = {}
        if insight_data and "data" in insight_data:
            for item in insight_data["data"]:
                name = item.get("name", "")
                values = item.get("values", [{}])
                insights[name] = values[0].get("value", 0) if values else 0

        caption = post.get("caption", "")
        reach = insights.get("reach", 0)
        likes = post.get("like_count", 0)
        comments = post.get("comments_count", 0)
        saves = insights.get("saved", 0)
        shares = insights.get("shares", 0)
        total_engagement = likes + comments + saves + shares
        engagement_rate = round((total_engagement / reach * 100), 2) if reach > 0 else 0

        enriched.append({
            "id": media_id,
            "media_type": post.get("media_type", "UNKNOWN"),
            "caption": caption[:200] + ("..." if len(caption) > 200 else ""),
            "timestamp": post.get("timestamp", ""),
            "permalink": post.get("permalink", ""),
            "media_url": post.get("media_url", ""),
            "thumbnail_url": post.get("thumbnail_url", ""),
            "metrics": {
                "likes": likes,
                "comments": comments,
                "saves": saves,
                "shares": shares,
                "reach": reach,
                "impressions": insights.get("impressions", 0),
                "video_views": insights.get("video_views", 0),
                "plays": insights.get("plays", 0),
                "total_interactions": insights.get("total_interactions", 0),
                "engagement_rate": engagement_rate,
            }
        })

    # Content type analysis
    type_stats = {}
    for post in enriched:
        mtype = post["media_type"]
        if mtype not in type_stats:
            type_stats[mtype] = {
                "count": 0, "total_likes": 0, "total_comments": 0,
                "total_saves": 0, "total_shares": 0, "total_reach": 0,
                "total_engagement_rate": 0,
            }
        s = type_stats[mtype]
        s["count"] += 1
        s["total_likes"] += post["metrics"]["likes"]
        s["total_comments"] += post["metrics"]["comments"]
        s["total_saves"] += post["metrics"]["saves"]
        s["total_shares"] += post["metrics"]["shares"]
        s["total_reach"] += post["metrics"]["reach"]
        s["total_engagement_rate"] += post["metrics"]["engagement_rate"]

    for mtype, s in type_stats.items():
        cnt = s["count"]
        if cnt > 0:
            s["avg_likes"] = round(s["total_likes"] / cnt, 1)
            s["avg_comments"] = round(s["total_comments"] / cnt, 1)
            s["avg_saves"] = round(s["total_saves"] / cnt, 1)
            s["avg_shares"] = round(s["total_shares"] / cnt, 1)
            s["avg_reach"] = round(s["total_reach"] / cnt, 1)
            s["avg_engagement_rate"] = round(s["total_engagement_rate"] / cnt, 2)

    # Sort by engagement rate for ranking
    enriched.sort(key=lambda p: p["metrics"]["engagement_rate"], reverse=True)

    return json.dumps({
        "posts": enriched,
        "count": len(enriched),
        "date_range": date_range,
        "content_type_analysis": type_stats,
        "top_performers": [p["id"] for p in enriched[:5]] if len(enriched) >= 5 else [p["id"] for p in enriched],
        "bottom_performers": [p["id"] for p in enriched[-5:]] if len(enriched) >= 5 else [],
    }, indent=2)


# ─── Tool 5: Weekly Summary (5-week trend) ──────────────────────────

@function_tool
def get_ig_weekly_summary(weeks: int = 5) -> str:
    """Get 5-week Instagram performance summary with WoW trends.
    Aggregates post metrics by week to show engagement trends over time.

    Args:
        weeks: Number of weeks to analyze (default 5).
    """
    ig_id = getattr(config, "INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    if not ig_id or not config.META_ACCESS_TOKEN:
        return _missing_key()

    days = weeks * 7
    start_dt = datetime.now() - timedelta(days=days)
    end_dt = datetime.now()

    # Fetch posts
    fields = "id,caption,media_type,timestamp,like_count,comments_count"
    data = _graph_get(f"{ig_id}/media", {
        "fields": fields,
        "limit": 100,
    })

    if not data or "error" in data:
        return json.dumps({"error": f"Failed to fetch IG posts: {data}", "skipped": True})

    # Filter and group by week
    weekly = {}
    for item in data.get("data", []):
        ts = item.get("timestamp", "")
        if not ts:
            continue
        try:
            post_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
            if post_dt < start_dt or post_dt > end_dt:
                continue
            iso_week = post_dt.strftime("%Y-W%V")
        except Exception:
            continue

        if iso_week not in weekly:
            weekly[iso_week] = {
                "posts": 0, "total_likes": 0, "total_comments": 0,
                "types": {},
            }
        w = weekly[iso_week]
        w["posts"] += 1
        w["total_likes"] += item.get("like_count", 0)
        w["total_comments"] += item.get("comments_count", 0)
        mtype = item.get("media_type", "UNKNOWN")
        w["types"][mtype] = w["types"].get(mtype, 0) + 1

    # Build weekly list with WoW changes
    periods = []
    prev_likes = None
    for week_key in sorted(weekly.keys()):
        w = weekly[week_key]
        avg_likes = round(w["total_likes"] / max(w["posts"], 1), 1)
        avg_comments = round(w["total_comments"] / max(w["posts"], 1), 1)

        wow_likes_pct = None
        if prev_likes is not None and prev_likes > 0:
            wow_likes_pct = round((avg_likes - prev_likes) / prev_likes * 100, 1)

        periods.append({
            "week": week_key,
            "posts_count": w["posts"],
            "total_likes": w["total_likes"],
            "total_comments": w["total_comments"],
            "avg_likes_per_post": avg_likes,
            "avg_comments_per_post": avg_comments,
            "content_types": w["types"],
            "wow_likes_change_pct": wow_likes_pct,
        })
        prev_likes = avg_likes

    return json.dumps({
        "weeks_analyzed": weeks,
        "periods": periods,
        "total_posts": sum(p["posts_count"] for p in periods),
        "sparkline_likes": [p["avg_likes_per_post"] for p in periods],
        "sparkline_comments": [p["avg_comments_per_post"] for p in periods],
    }, indent=2)
