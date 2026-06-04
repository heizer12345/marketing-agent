"""External trend signals for content calendar planning (no API keys required)."""

import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from agents import function_tool

# B2B sourcing / marketing relevance filters
_HIGH = [
    "sourcing", "supply chain", "manufacturing", "alibaba", "supplier", "oem",
    "private label", "b2b", "wholesale", "import", "procurement", "factory",
    "moq", "logistics", "ecommerce", "amazon fba", "brand",
]
_MEDIUM = [
    "marketing", "seo", "startup", "growth", "trade", "export", "import",
    "ai", "automation", "business",
]

_REDDIT_SUBS = ["marketing", "ecommerce", "Entrepreneur", "FulfillmentByAmazon", "smallbusiness"]


def _relevance_score(text: str) -> tuple[int, str]:
    t = text.lower()
    hits_high = [k for k in _HIGH if k in t]
    hits_med = [k for k in _MEDIUM if k in t]
    if hits_high:
        return 3, f"high ({', '.join(hits_high[:3])})"
    if hits_med:
        return 2, f"medium ({', '.join(hits_med[:3])})"
    return 1, "low (weak fit for Sourcy ICP)"


def _fetch_google_trends(geo: str = "US", limit: int = 15) -> list[dict]:
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    req = urllib.request.Request(url, headers={"User-Agent": "SourcyMarketingAgent/1.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        data = response.read().decode("utf-8")
    root = ET.fromstring(data)
    ns = {"ht": "https://trends.google.com/trending/rss"}
    out = []
    for item in root.findall(".//item")[:limit]:
        title_el = item.find("title")
        traffic_el = item.find("ht:approx_traffic", ns)
        topic = title_el.text if title_el is not None else "Unknown"
        traffic = traffic_el.text if traffic_el is not None else "N/A"
        news_urls = []
        for ni in item.findall("ht:news_item", ns)[:2]:
            nu = ni.find("ht:news_item_url", ns)
            if nu is not None and nu.text:
                news_urls.append(nu.text)
        score, rel = _relevance_score(topic)
        out.append({
            "source": "google_trends",
            "topic": topic,
            "approx_search_volume": traffic,
            "relevance": rel,
            "relevance_score": score,
            "reference_urls": news_urls,
            "geo": geo,
        })
    return sorted(out, key=lambda x: x["relevance_score"], reverse=True)


def _fetch_reddit_hot(limit: int = 12) -> list[dict]:
    posts = []
    for sub in _REDDIT_SUBS:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
        req = urllib.request.Request(url, headers={"User-Agent": "SourcyMarketingAgent/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                title = post.get("title", "")
                score = int(post.get("score", 0))
                comments = int(post.get("num_comments", 0))
                if score < 30:
                    continue
                rel_score, rel = _relevance_score(title)
                posts.append({
                    "source": "reddit",
                    "subreddit": sub,
                    "title": title,
                    "upvotes": score,
                    "comments": comments,
                    "engagement_total": score + comments,
                    "relevance": rel,
                    "relevance_score": rel_score,
                    "reference_url": f"https://reddit.com{post.get('permalink', '')}",
                })
        except Exception:
            continue
    posts.sort(key=lambda x: (x["relevance_score"], x["engagement_total"]), reverse=True)
    return posts[:limit]


@function_tool
def scan_marketing_trends(geo: str = "US") -> str:
    """Scan external trend sources for content-calendar ideation.

    Pulls Google Trends (RSS) and high-engagement Reddit posts from B2B-relevant
    subreddits. Returns structured JSON with topics, engagement metrics, relevance
    to Sourcy, and reference URLs the marketing team can verify.

    Args:
        geo: Google Trends geo code (US, ID, BR, etc.). Default US.
    """
    scanned_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    trends = _fetch_google_trends(geo=geo.upper(), limit=15)
    reddit = _fetch_reddit_hot(limit=12)
    relevant_trends = [t for t in trends if t["relevance_score"] >= 2]
    relevant_reddit = [r for r in reddit if r["relevance_score"] >= 2]

    return json.dumps({
        "scanned_at": scanned_at,
        "geo": geo.upper(),
        "summary": {
            "google_trends_total": len(trends),
            "google_trends_relevant": len(relevant_trends),
            "reddit_posts_relevant": len(relevant_reddit),
        },
        "google_trends": trends,
        "reddit": reddit,
        "usage_note": (
            "Use Trends/Reddit URLs in the calendar References column as discourse proxies when "
            "no LinkedIn/Meta viral link is available — label them clearly (e.g. 'Reddit thread' or "
            "'Google Trends news'). For LinkedIn/Meta rows, prefer external creator/ad URLs the team "
            "provides. Put volume/upvotes in Evidence; put mimic-target URLs in References. "
            "Never use sourcy.ai or our own social posts as References."
        ),
    }, indent=2)
