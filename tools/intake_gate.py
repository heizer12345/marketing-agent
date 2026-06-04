"""Detect when chat should ask clarifying questions before running tools."""

from __future__ import annotations

import re

_SKIP_RE = re.compile(
    r"\b(skip\s+intake|skip\s+questions?|no\s+questions?|just\s+run|proceed\s+immediately|use\s+defaults?|use\s+assumptions?)\b",
    re.I,
)

_INTAKE_TAG_RE = re.compile(r"\[intake-first:\s*(seo|ads|content)\]", re.I)

_SIMPLE_METRIC_RE = re.compile(
    r"^\s*(how many|how much|what(?:'s| is) our|show me|top \d+|list our)\b.*\b(sessions?|visits?|keywords?|clicks?|spend|users?)\b",
    re.I,
)

_SOCIAL_CHANNEL_RE = re.compile(
    r"\b("
    r"linkedin|instagram|insta|ig\b|tiktok|facebook|fb\b|twitter|x\.com|threads|"
    r"youtube|pinterest|social\s+media|social\s+post|reel|carousel|caption|feed\s+post"
    r")\b",
    re.I,
)

_BLOG_RE = re.compile(
    r"\b("
    r"blog(?:\s+post)?|write\s+(?:a\s+)?blog|draft\s+(?:a\s+)?blog|generate\s+(?:the\s+)?blog|"
    r"seo\s+article|long[- ]form|article\s+for\s+(?:our\s+)?(?:site|blog)|landing\s+page\s+copy"
    r")\b",
    re.I,
)

_CALENDAR_RE = re.compile(
    r"\b("
    r"content calendar|editorial calendar|weekly (?:content )?plan|content plan|"
    r"plan (?:our )?posts|\d+[- ]?day (?:content )?calendar"
    r")\b",
    re.I,
)

_DISCOVERY_RE = re.compile(
    r"\b("
    r"content calendar|editorial calendar|plan (?:our )?posts|weekly (?:content )?plan|"
    r"linkedin post|social post|social media|instagram post|tiktok|facebook post|"
    r"write (?:a )?blog|blog post|generate (?:the )?blog|draft (?:the )?blog|"
    r"landing page|content ideas?|help me with|audit (?:our |the )?|"
    r"seo audit|content audit|full (?:marketing )?audit|"
    r"meta ads|google ads|paid ads|ad review|"
    r"competitor analysis|keyword research|content plan|"
    r"caption ideas?|reel ideas?|post ideas?"
    r")\b",
    re.I,
)

_GOAL_RE = re.compile(
    r"\b("
    r"engagement|likes?|comments?|shares?|saves?|leads?|awareness|traffic|seo|authority|"
    r"conversions?|thought leadership|brand|roas|cpl|followers?|dm[s]?|sign[- ]?ups?|"
    r"product education|lead capture"
    r")\b",
    re.I,
)

_TOPIC_RE = re.compile(
    r"(?:\b(about|on|for|around|regarding|covering|focused on|angle|theme|topic)\s+[\w-]{3,})|"
    r"(?:topic|angle|theme|title|keyword)\s*[:=]\s*\S+|"
    r'["\'][^"\']{8,}["\']',
    re.I,
)

_AUDIENCE_RE = re.compile(
    r"\b(b2b|b2c|founder|procurement|sourcing team|importers?|brands?|sellers?|"
    r"us\b|usa|indonesia|vietnam|philippines|latam|southeast asia|target (?:market|audience))\b",
    re.I,
)


def _user_turn_count(messages: list) -> int:
    return sum(1 for m in messages if (m.get("role") or "").lower() == "user")


def content_task_kind(message: str) -> str | None:
    """Returns social | blog | calendar | None."""
    if not (message or "").strip():
        return None
    if _CALENDAR_RE.search(message):
        return "calendar"
    if _BLOG_RE.search(message) and not _SOCIAL_CHANNEL_RE.search(message):
        return "blog"
    if _SOCIAL_CHANNEL_RE.search(message) or re.search(
        r"\b(social post|social media|caption|reel|post ideas?)\b", message, re.I
    ):
        return "social"
    if _DISCOVERY_RE.search(message):
        if _BLOG_RE.search(message):
            return "blog"
        if re.search(r"\b(social|linkedin|instagram|tiktok|caption|reel)\b", message, re.I):
            return "social"
        return "calendar"
    return None


def _intake_category(message: str) -> str | None:
    m = _INTAKE_TAG_RE.search(message)
    if m:
        return m.group(1).lower()
    low = message.lower()
    if re.search(r"\b(seo|keyword|organic|ranking|search console|technical seo)\b", low):
        return "seo"
    if re.search(r"\b(meta ads|google ads|paid ads|roas|cpl|campaign)\b", low):
        return "ads"
    if content_task_kind(message) or re.search(
        r"\b(linkedin|blog|calendar|content|instagram|tiktok|social)\b", low
    ):
        return "content"
    if _DISCOVERY_RE.search(message):
        return "content"
    return None


def _is_social_detailed_enough(message: str) -> bool:
    has_channel = bool(_SOCIAL_CHANNEL_RE.search(message))
    has_goal = bool(_GOAL_RE.search(message))
    has_topic = bool(_TOPIC_RE.search(message)) or (
        len(message) > 160
        and has_channel
        and len(re.findall(r"\b\w{4,}\b", message)) >= 12
    )
    if has_channel and has_goal and has_topic:
        return True
    if re.search(r"https?://|www\.sourcy\.ai/", message) and has_channel and (has_goal or has_topic):
        return True
    return False


def _is_blog_detailed_enough(message: str) -> bool:
    low = message.lower()
    has_topic = bool(_TOPIC_RE.search(message)) or bool(
        re.search(
            r"\b(blog|article)\b.{0,80}\b(about|on|for|covering|titled?|called)\b",
            low,
        )
    )
    has_scope = (
        bool(_GOAL_RE.search(message))
        or bool(_AUDIENCE_RE.search(message))
        or bool(re.search(r"\b((?:primary\s+)?keyword|search intent|word count|length)\b", low))
        or bool(re.search(r"https?://|www\.sourcy\.ai/", message))
    )
    if has_topic and has_scope:
        return True
    if len(message) > 240 and _BLOG_RE.search(message) and has_topic:
        return True
    return False


def _is_calendar_detailed_enough(message: str) -> bool:
    low = message.lower()
    has_channels = bool(
        _SOCIAL_CHANNEL_RE.search(message)
        or re.search(r"\b(blog|meta ad|google ad|ads)\b", low)
    )
    has_goal = bool(_GOAL_RE.search(message))
    has_extra = bool(
        re.search(r"https?://|www\.sourcy\.ai/", message)
        or re.search(r"\b(last \d+ days|7d|30 days|this week|7[- ]?day|monthly)\b", low)
        or _AUDIENCE_RE.search(message)
    )
    return has_channels and has_goal and has_extra


def _is_detailed_enough(message: str) -> bool:
    kind = content_task_kind(message)
    if kind == "social":
        return _is_social_detailed_enough(message)
    if kind == "blog":
        return _is_blog_detailed_enough(message)
    if kind == "calendar":
        return _is_calendar_detailed_enough(message)

    low = message.lower()
    score = 0
    if re.search(r"https?://|www\.sourcy\.ai/", message):
        score += 2
    if re.search(r"\b(last \d+ days|7d|30 days|this week|q[1-4])\b", low):
        score += 1
    if _AUDIENCE_RE.search(message):
        score += 1
    if _GOAL_RE.search(message):
        score += 1
    if (_SOCIAL_CHANNEL_RE.search(message) or _BLOG_RE.search(message)) and len(low) > 120:
        score += 2
    if len(low) > 280:
        score += 1
    return score >= 3


def should_run_intake_first(user_message: str, conversation_messages: list) -> bool:
    """Ask 3 questions with no tools; skip when user already gave enough context."""
    if not (user_message or "").strip():
        return False
    if _SKIP_RE.search(user_message):
        return False
    if _SIMPLE_METRIC_RE.search(user_message):
        return False
    if _user_turn_count(conversation_messages) > 1:
        return False
    if _is_detailed_enough(user_message):
        return False
    if _INTAKE_TAG_RE.search(user_message):
        return True
    if content_task_kind(user_message):
        return True
    if _DISCOVERY_RE.search(user_message):
        return True
    if re.search(r"\bhelp me\b", user_message, re.I) and len(user_message) < 200:
        return True
    return False


_INTAKE_QUESTIONS = {
    "seo": (
        "1) **Scope** — Whole site, specific URLs, or a section (e.g. blogs, product pages)?\n"
        "2) **Markets** — Which countries/regions matter most (US, ID, VN, PH, Latam, etc.)?\n"
        "3) **Primary goal** — Traffic growth, rankings, technical fixes, or conversion/landing-page improvements?"
    ),
    "ads": (
        "1) **Platforms** — Meta, Google, or both?\n"
        "2) **Date range** — Last 7 days, 14 days, or 30 days?\n"
        "3) **Primary KPI** — CPL, ROAS, leads, spend efficiency, or creative fatigue?"
    ),
    "social": (
        "1) **Primary result** — What should these posts achieve? (engagement, likes, leads, awareness, etc.)\n"
        "2) **Topic / angle** — Must-cover theme, or should I propose what's trending?\n"
        "3) **Channels** — LinkedIn, Instagram, TikTok, or multiple? (If LinkedIn: short ~120–180 words or long ~300–500?)"
    ),
    "blog": (
        "1) **Goal** — SEO traffic, leads, authority/thought leadership, or product education?\n"
        "2) **Audience + angle** — Who is it for and what's the key message or POV?\n"
        "3) **Constraints** — Target keyword (if any), length, must-include points, CTA, or examples to mimic/avoid?"
    ),
    "calendar": (
        "1) **Results** — What should this content achieve? (engagement, likes, leads, awareness, SEO traffic, etc.)\n"
        "2) **Topics** — Must-cover themes, or should I propose what's trending?\n"
        "3) **Formats** — LinkedIn, IG/TikTok, ads, blogs — which channels for this plan?"
    ),
}


def _content_questions_for_message(message: str) -> str:
    kind = content_task_kind(message)
    if kind == "social":
        return _INTAKE_QUESTIONS["social"]
    if kind == "blog":
        return _INTAKE_QUESTIONS["blog"]
    if kind == "calendar":
        q = _INTAKE_QUESTIONS["calendar"]
        low = message.lower()
        extra = ""
        if "linkedin" in low:
            extra = "\n4) **LinkedIn length** — Short (~120–180 words) or long (~300–500 words)?"
        if "blog" in low or _BLOG_RE.search(message):
            extra += "\n4) **Blog aim** — SEO traffic, leads, authority, or product education?"
        return q + extra
    return _INTAKE_QUESTIONS["calendar"]


def intake_router_prefix(user_message: str) -> str:
    """Injected into task brief so the CEO agent must not call tools on turn 1."""
    cat = _intake_category(user_message) or "content"
    if cat == "content":
        questions = _content_questions_for_message(user_message)
        task_hint = content_task_kind(user_message) or "content"
    else:
        questions = _INTAKE_QUESTIONS.get(cat, _INTAKE_QUESTIONS["calendar"])
        task_hint = cat

    return (
        "[INTAKE-FIRST — MANDATORY ON THIS TURN]\n"
        f"Task type: {task_hint}. The user has NOT provided enough context yet.\n"
        "Do **NOT** call any tools (no data_analyst, content_engine, content_calendar_planner, "
        "social post ideator, or project_manager).\n"
        "Reply in chat with **exactly 3 numbered questions** (use the set below; you may rephrase slightly):\n\n"
        f"{questions}\n\n"
        'End with: "Reply with your answers, or say **skip intake** to proceed immediately."\n'
        "Do not generate calendars, blogs, social posts, or artifacts until they answer or skip.\n"
        "If their message already contained full scope (goal + topic + channel for social; "
        "goal + audience + topic for blog), you would not see this block — do not re-ask what they already said.\n\n"
        "---\n"
        "User message:\n"
    )
