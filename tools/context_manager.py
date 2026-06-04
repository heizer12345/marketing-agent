"""Context Manager — history compression and task context building.

Provides utilities to keep agent context lean so that deep chains
don't hit token limits or slow down significantly.
"""

import re
from typing import List

_BLOG_EXEC_RE = re.compile(
    r"\b(generate|write|draft|create|produce|build)\b.{0,40}\bblog\b|\bblog\b.{0,40}\b(generate|write|draft|create|produce|build)\b",
    re.IGNORECASE,
)
_CALENDAR_BLOG_RE = re.compile(
    r"\b(day\s*\d+|write|draft|generate).{0,30}\bblog\b|\bapproved\b.{0,40}\bblog\b",
    re.IGNORECASE,
)

# Do not force content_write routing when intake is required on turn 1
def should_skip_routing_enrichment(user_message: str, conversation_messages: list) -> bool:
    from tools.intake_gate import should_run_intake_first

    return should_run_intake_first(user_message, conversation_messages)


_ROUTING_PREFIXES = {
    "content_write": (
        "[ROUTING: content_write — MANDATORY]\n"
        "Call **content_engine** only. Run: keyword_strategy (if needed) → write_blog → score_content.\n"
        "Use blog title/topic/angle from this thread (calendar row, intake answers, or user message).\n"
        "Skip blog intake if context already exists. Do NOT call data_analyst, content_calendar_planner, or project_manager.\n"
        "Return the blog artifact path (/reports/blog_*.html) in your reply.\n\n"
    ),
    "content_audit": (
        "[ROUTING: content_audit — MANDATORY]\n"
        "Call **content_engine** only for SEO/GEO/AEO/technical audits. Do NOT call data_analyst.\n\n"
    ),
}


def is_blog_execution_request(user_message: str, recent_context: str = "") -> bool:
    """True when the user wants a blog draft, not analytics."""
    combined = f"{recent_context} {user_message}"
    if _BLOG_EXEC_RE.search(user_message):
        return True
    low = user_message.lower()
    if "blog" in low and any(v in low for v in ("generate", "write", "draft", "create", "produce")):
        return True
    if _CALENDAR_BLOG_RE.search(combined) and "blog" in low:
        return True
    return False


def enrich_task_brief(
    task_brief: str,
    agent_hint: str,
    user_message: str,
    conversation_messages: list | None = None,
) -> tuple[str, str]:
    """Inject routing directives; return (brief, effective_hint)."""
    if conversation_messages and should_skip_routing_enrichment(user_message, conversation_messages):
        return task_brief, agent_hint or "auto"

    hint = (agent_hint or "auto").strip()
    if hint == "auto" and is_blog_execution_request(user_message):
        hint = "content_write"
    prefix = _ROUTING_PREFIXES.get(hint, "")
    if prefix and prefix not in task_brief:
        return prefix + task_brief, hint
    return task_brief, hint


def compress_history(messages: List[dict], keep_last: int = 6, max_msg_chars: int = 2000) -> List[dict]:
    """
    Keep only the last N messages and truncate any single message > max_msg_chars.

    Truncation format:
        <first 600 chars>

        [... X chars omitted for context efficiency ...]

        <last 200 chars>

    The LAST message (current user input) is never truncated.

    Args:
        messages: Full conversation history as list of {"role": ..., "content": ...} dicts.
        keep_last: Number of most-recent messages to retain (default 6).
        max_msg_chars: Maximum characters per message before truncation (default 2000).

    Returns:
        Compressed list of message dicts.
    """
    # Keep only the most recent N messages
    recent = messages[-keep_last:] if len(messages) > keep_last else list(messages)

    if not recent:
        return recent

    compressed = []
    last_idx = len(recent) - 1

    for i, msg in enumerate(recent):
        content = msg.get("content") or ""
        # Never truncate the last message (current user input)
        if i == last_idx or len(content) <= max_msg_chars:
            compressed.append(msg)
        else:
            keep_head = 600
            keep_tail = 200
            omitted = len(content) - keep_head - keep_tail
            truncated = (
                content[:keep_head]
                + f"\n\n[... {omitted} chars omitted for context efficiency ...]\n\n"
                + content[-keep_tail:]
            )
            compressed.append({**msg, "content": truncated})

    return compressed


def build_task_context(compressed_history: List[dict], task_brief: str) -> List[dict]:
    """
    Build a clean message list for a single task.

    Takes the compressed history (minus the last user message, since the task
    brief replaces it) and appends the task brief as the new user turn.

    Args:
        compressed_history: Output of compress_history().
        task_brief: The specific task instruction to run.

    Returns:
        Message list ready to pass to Runner.run_streamed().
    """
    # Drop the last user message — the task brief replaces it
    history_without_last_user = list(compressed_history)
    if history_without_last_user and history_without_last_user[-1].get("role") == "user":
        history_without_last_user = history_without_last_user[:-1]

    return history_without_last_user + [{"role": "user", "content": task_brief}]
