"""AI web research for viral social posts (no LinkedIn/IG/TikTok APIs).

Uses Perplexity Sonar (web search + citations) when PERPLEXITY_API_KEY is set.
Falls back to OpenAI chat when only OPENAI_API_KEY is available — team should verify URLs.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import httpx
from agents import function_tool

import config

_TIMEOUT = 60
_CHANNELS = {"linkedin", "instagram", "tiktok", "ig"}


def _channel_label(channel: str) -> str:
    c = channel.strip().lower()
    if c in ("ig", "instagram"):
        return "Instagram"
    if c == "tiktok":
        return "TikTok"
    return "LinkedIn"


def _build_prompt(channel: str, topic: str, geo: str, limit: int) -> str:
    label = _channel_label(channel)
    return f"""You are researching viral {label} content for a B2B marketing team planning a content calendar.

Topic / niche: {topic}
Market: {geo}
Find up to {limit} high-performing **external** posts on {label} (any creator — NOT sourcy.ai).

For each example you must provide:
1. creator_name — person or brand
2. hook_or_title — opening line or post title
3. engagement_metric — views/likes/comments/reposts (state if estimated)
4. reference_url — direct public URL on {label.lower()}.com (required)
5. format — e.g. carousel, short video, text post, poll
6. why_mimic — one sentence on what format/angle to copy

Rules:
- Only include reference_url values you found via web search. Never invent URLs.
- Prefer posts from the last 90 days with clearly stated engagement.
- Exclude sourcy.ai, sourcy blog URLs, and the brand's own social accounts entirely.
- Do NOT return sourcy.ai website pages as examples — only third-party creators on {label}.
- Exclude generic advice articles with no direct post link.

Respond with ONLY valid JSON (no markdown fences):
{{
  "channel": "{label}",
  "topic": "{topic}",
  "geo": "{geo}",
  "examples": [ ... ],
  "research_notes": "brief limitations"
}}
"""


def _parse_json_blob(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _research_perplexity(prompt: str) -> tuple[dict | None, list[str], str]:
    resp = httpx.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {config.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You search the live web and return factual JSON. "
                        "Every reference_url must appear in your search citations."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    citations = data.get("citations") or []
    parsed = _parse_json_blob(content)
    return parsed, citations, content


def _research_openai(prompt: str) -> tuple[dict | None, list[str], str]:
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return only valid JSON. Include reference_url only for posts you are "
                        "confident are real and publicly documented; otherwise omit the example. "
                        "Do not fabricate LinkedIn/Instagram/TikTok URLs."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    parsed = _parse_json_blob(content)
    return parsed, [], content


def _filter_examples(examples: list, channel: str) -> list[dict]:
    label = _channel_label(channel).lower()
    domain_hints = {
        "linkedin": ("linkedin.com",),
        "instagram": ("instagram.com", "instagr.am"),
        "tiktok": ("tiktok.com",),
    }
    key = "instagram" if label == "instagram" else label
    allowed = domain_hints.get(key, ("linkedin.com",))

    out: list[dict] = []
    for ex in examples:
        if not isinstance(ex, dict):
            continue
        url = str(ex.get("reference_url") or ex.get("url") or "").strip()
        if not url or not any(d in url.lower() for d in allowed):
            continue
        if "sourcy.ai" in url.lower():
            continue
        low = url.lower()
        # Skip embed/video patterns that often 404 or show "Video unavailable"
        if any(x in low for x in ("/embed/", "/video/", "player.vimeo", "watch?v=")):
            continue
        out.append({
            "creator_name": ex.get("creator_name") or ex.get("creator") or "Unknown",
            "hook_or_title": ex.get("hook_or_title") or ex.get("title") or "",
            "engagement_metric": ex.get("engagement_metric") or ex.get("metric") or "",
            "reference_url": url,
            "format": ex.get("format") or "",
            "why_mimic": ex.get("why_mimic") or ex.get("why") or "",
        })
    return out


@function_tool
def research_social_trends(
    channel: str,
    topic: str,
    geo: str = "US",
    limit: int = 5,
) -> str:
    """Find viral external posts on LinkedIn, Instagram, or TikTok via AI web research.

    No platform APIs required. Uses Perplexity Sonar (live web + citations) when
    PERPLEXITY_API_KEY is set; otherwise OpenAI (verify URLs before using in calendar).

    Use results in the calendar **References** column: creator — hook — metric — URL.

    Args:
        channel: linkedin | instagram | ig | tiktok
        topic: niche or theme (e.g. "B2B sourcing", "supplier verification")
        geo: market code for context (US, ID, BR, etc.)
        limit: max examples to return (default 5)
    """
    ch = channel.strip().lower()
    if ch not in _CHANNELS:
        return json.dumps({
            "error": f"Unsupported channel '{channel}'. Use linkedin, instagram, or tiktok.",
        })

    limit = max(1, min(int(limit), 8))
    prompt = _build_prompt(ch, topic, geo.upper(), limit)
    scanned_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    engine = None
    parsed = None
    citations: list = []
    raw = ""

    try:
        if config.PERPLEXITY_API_KEY:
            engine = "perplexity_sonar"
            parsed, citations, raw = _research_perplexity(prompt)
        elif config.OPENAI_API_KEY:
            engine = "openai_gpt4o"
            parsed, citations, raw = _research_openai(prompt)
        else:
            return json.dumps({
                "error": "No research API configured. Add PERPLEXITY_API_KEY (recommended) or OPENAI_API_KEY to .env",
                "skipped": True,
            })
    except Exception as e:
        return json.dumps({"error": str(e), "channel": ch, "topic": topic})

    examples = []
    research_notes = ""
    if parsed:
        examples = _filter_examples(parsed.get("examples") or [], ch)
        research_notes = str(parsed.get("research_notes") or "")

    return json.dumps({
        "scanned_at": scanned_at,
        "engine": engine,
        "channel": _channel_label(ch),
        "topic": topic,
        "geo": geo.upper(),
        "examples": examples,
        "citations": citations[:15],
        "research_notes": research_notes,
        "usage_note": (
            "LinkedIn table → LinkedIn post reference: plain URL + views/comments/likes. "
            "IG/TikTok table → TikTok/IG post reference: markdown link [Creator — metric](reference_url). "
            "Only use reference_url from this tool. Never sourcy.ai."
        ),
        "raw_snippet": raw[:800] if not examples else "",
    }, indent=2)
