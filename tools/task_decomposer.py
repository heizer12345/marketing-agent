"""Task Decomposer — LLM-based non-deterministic task splitter.

Uses gpt-4o-mini to decide if a user message contains multiple independent
deliverables and splits them into a structured task list with phase assignments.
"""

import json
import logging
from typing import List, Optional

from openai import AsyncOpenAI

log = logging.getLogger("sourcy")

# Lazy client — instantiated on first call so the module can be imported
# without OPENAI_API_KEY set at import time.
_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


_SYSTEM_PROMPT = """You are a task planner for a marketing AI agent system.

Analyze the user's message and decide if it contains MULTIPLE INDEPENDENT deliverables that should run separately.

SPLIT when:
- User asks for multiple distinct outputs (e.g., "write a blog AND a landing page")
- Some tasks are strategic/fast (text advice) and others are creative/slow (content files)
- Tasks can genuinely run in parallel without depending on each other's output

DO NOT split:
- Single questions or analysis requests ("how are our ads doing?")
- Follow-up questions in an ongoing conversation
- A request that is conceptually one thing even if long ("full SEO audit")

PHASE rules:
- Phase 1 = strategic/advice tasks (fast, text output, run first)
- Phase 2 = content creation tasks (slow, generates files, run in parallel after phase 1)
- If all tasks are same type, assign them all to phase 1 (they'll run in parallel)

agent_hint values: "data_analysis" | "content_audit" | "content_write" | "strategy" | "implementation" | "report" | "auto"

Return JSON only. No markdown."""

# Few-shot examples: (user_message, expected_output)
_FEW_SHOT = [
    (
        "What should we do to improve organic? Create a sample landing page and write a blog post",
        '{"is_multi_task":true,"reason":"3 independent deliverables: strategic advice, landing page file, blog post file","tasks":[{"id":1,"brief":"What should Sourcy.ai (B2B sourcing platform) focus on to improve organic search traffic? Give specific prioritized actions.","phase":1,"agent_hint":"strategy"},{"id":2,"brief":"Create a sample landing page for Sourcy.ai focused on AI-powered B2B sourcing and supplier discovery","phase":2,"agent_hint":"content_write"},{"id":3,"brief":"Write a blog post for Sourcy.ai about how B2B companies can improve organic search traffic through better content strategy","phase":2,"agent_hint":"content_write"}]}',
    ),
    (
        "How are our Meta Ads performing this week?",
        '{"is_multi_task":false,"reason":"Single analysis request","tasks":[{"id":1,"brief":"How are our Meta Ads performing this week?","phase":1,"agent_hint":"data_analysis"}]}',
    ),
    (
        "Write a landing page and a blog post about AI sourcing",
        '{"is_multi_task":true,"reason":"Two independent content creation tasks","tasks":[{"id":1,"brief":"Write a landing page for Sourcy.ai about AI-powered B2B sourcing and supplier discovery","phase":1,"agent_hint":"content_write"},{"id":2,"brief":"Write a blog post for Sourcy.ai about AI sourcing and how it transforms B2B procurement","phase":1,"agent_hint":"content_write"}]}',
    ),
    (
        "Full SEO audit and then write 2 blog posts to fix the gaps",
        '{"is_multi_task":true,"reason":"Audit informs blog topics — sequential dependency","tasks":[{"id":1,"brief":"Run a full SEO content audit of sourcy.ai and identify the top content gaps and opportunities","phase":1,"agent_hint":"content_audit"},{"id":2,"brief":"Write 2 blog posts addressing the top content gaps found for sourcy.ai (B2B sourcing platform)","phase":2,"agent_hint":"content_write"}]}',
    ),
    (
        "Rewrite our about page to target China sourcing service better",
        '{"is_multi_task":false,"reason":"Single implementation task — audit + rewrite + schema + review package","tasks":[{"id":1,"brief":"Rewrite the sourcy.ai/about page to better target the keyword \'China sourcing service\'. Audit current page, rewrite content, add schema, and package for review.","phase":1,"agent_hint":"implementation"}]}',
    ),
    (
        "Add FAQ schema to our main service pages",
        '{"is_multi_task":false,"reason":"Single implementation task — schema generation and packaging","tasks":[{"id":1,"brief":"Add FAQ schema markup to sourcy.ai main service pages (sourcing, easysourcing, products). Generate JSON-LD and package for review.","phase":1,"agent_hint":"implementation"}]}',
    ),
    (
        "Improve SEO/GEO/AEO of our top 20 blogs with proposed changes",
        '{"is_multi_task":false,"reason":"Single complex implementation task — audit + rewrite + review package","tasks":[{"id":1,"brief":"Improve the SEO, GEO, and AEO of sourcy.ai\'s top 20 blog posts. Audit each, enrich with keywords, rewrite, add schemas, and package all proposed changes for human review.","phase":1,"agent_hint":"implementation"}]}',
    ),
]


async def decompose_tasks(user_message: str, recent_context: str = "") -> List[dict]:
    """
    Analyze the user's message and split it into independent tasks if needed.

    Args:
        user_message: The raw user input.
        recent_context: Optional string of recent conversation context (last 2 exchanges).

    Returns:
        A list of task dicts: [{"id": 1, "brief": "...", "phase": 1, "agent_hint": "auto"}]
        Falls back to a single-task list if JSON parsing fails.
    """
    # Build few-shot messages
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for user_ex, assistant_ex in _FEW_SHOT:
        messages.append({"role": "user", "content": user_ex})
        messages.append({"role": "assistant", "content": assistant_ex})

    # Actual user message — include recent context if provided
    content = user_message
    if recent_context:
        content = f"[Recent context: {recent_context}]\n\nUser message: {user_message}"
    messages.append({"role": "user", "content": content})

    try:
        response = await _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        tasks = parsed.get("tasks", [])
        if not tasks:
            raise ValueError("Empty tasks list in decomposer response")
        log.info(
            f"[decomposer] is_multi_task={parsed.get('is_multi_task')} "
            f"reason={parsed.get('reason', '')!r} tasks={len(tasks)}"
        )
        return tasks
    except Exception as e:
        log.warning(f"[decomposer] Falling back to single task. Error: {e}")
        return [{"id": 1, "brief": user_message, "phase": 1, "agent_hint": "auto"}]
