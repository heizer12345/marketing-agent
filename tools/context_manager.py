"""Context Manager — history compression and task context building.

Provides utilities to keep agent context lean so that deep chains
don't hit token limits or slow down significantly.
"""

from typing import List


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
