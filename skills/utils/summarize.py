"""Summarization utility — compresses large agent outputs between A2A rounds.

Uses gpt-4o-mini to reduce each round's output to ≤3K tokens before the
orchestrator proceeds to the next round. This prevents context explosion when
running multi-round A2A loops across 20+ pages.

Usage:
    from skills.utils.summarize import compress_round_output

    summary = compress_round_output(
        raw_output="<long agent output...>",
        context="Summarizing SEO audit results for round 1",
        max_chars=3000,
    )
"""

import asyncio
from openai import AsyncOpenAI

import config

_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
_SUMMARIZER_MODEL = "gpt-4o-mini"


async def compress_round_output(
    raw_output: str,
    context: str = "",
    max_chars: int = 3000,
) -> str:
    """Compress a large agent output to ≤max_chars using gpt-4o-mini.

    Args:
        raw_output: The full text output from an agent round
        context: Brief description of what was done (e.g., "Round 1 SEO audit of 5 blogs")
        max_chars: Target character limit for the summary (default 3000)

    Returns:
        Compressed summary string. If raw_output is already ≤max_chars, returns it unchanged.
    """
    if len(raw_output) <= max_chars:
        return raw_output

    context_line = f"Context: {context}\n\n" if context else ""
    prompt = f"""{context_line}Compress the following agent output to under {max_chars} characters.
Preserve:
- All numerical scores (e.g., SEO: 72/100, EEAT: 58/100)
- All URLs and page references
- Top 3-5 findings per page/section
- All specific action items and recommendations
- All keyword data (grouped if needed)
- File paths and artifact references

Discard:
- Repetitive boilerplate text
- Verbose explanations when a bullet point suffices
- Duplicate information
- Tool response wrappers and metadata noise

Output format: structured bullets, not prose.

---
{raw_output}
---

Compressed output (under {max_chars} chars):"""

    try:
        response = await _client.chat.completions.create(
            model=_SUMMARIZER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.1,
        )
        summary = response.choices[0].message.content or raw_output[:max_chars]
        return summary
    except Exception as e:
        # Fallback: simple truncation with ellipsis
        return raw_output[:max_chars] + f"\n[TRUNCATED — summarization failed: {str(e)[:100]}]"


def compress_round_output_sync(
    raw_output: str,
    context: str = "",
    max_chars: int = 3000,
) -> str:
    """Synchronous wrapper for compress_round_output."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context — use asyncio.create_task via nest_asyncio or direct truncate
            # Safe fallback for sync callers inside async context
            return raw_output[:max_chars] + ("\n[truncated]" if len(raw_output) > max_chars else "")
        return loop.run_until_complete(
            compress_round_output(raw_output, context, max_chars)
        )
    except Exception:
        return raw_output[:max_chars]


async def compress_batch(
    outputs: list[tuple[str, str]],
    max_chars_each: int = 3000,
) -> list[str]:
    """Compress multiple outputs concurrently.

    Args:
        outputs: List of (raw_output, context) tuples
        max_chars_each: Target limit per output

    Returns:
        List of compressed strings in same order
    """
    tasks = [
        compress_round_output(raw, ctx, max_chars_each)
        for raw, ctx in outputs
    ]
    return await asyncio.gather(*tasks, return_exceptions=False)
