from __future__ import annotations

"""Alt text writer — generates SEO-optimized alt text for images using OpenAI vision.

Takes a list of image URLs and generates descriptive, keyword-rich alt text
for each one. Part of the on-page hygiene improvements in the Website Overhaul flow.

All tools return JSON strings matching the project's @function_tool pattern.
"""

import asyncio
import base64
import json

import httpx
from openai import AsyncOpenAI

from agents import function_tool

import config

_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
_VISION_MODEL = "gpt-4o-mini"
_HTTP_TIMEOUT = 15


async def _generate_alt_text(
    image_url: str,
    page_context: str = "",
    target_keywords: list[str] | None = None,
) -> dict:
    """Generate alt text for a single image URL using vision."""
    keywords_hint = ""
    if target_keywords:
        top_kws = target_keywords[:5]
        keywords_hint = f"\nRelevant keywords for this page: {', '.join(top_kws)}"

    context_hint = f"\nPage context: {page_context}" if page_context else ""

    prompt = f"""Generate SEO-optimized alt text for this image.{context_hint}{keywords_hint}

Requirements:
- Describe what is actually in the image (accurate, not generic)
- Include relevant keywords naturally IF they match what's shown (don't force them)
- Keep it under 125 characters
- Write as a plain description, no "image of" or "photo of" prefix
- Be specific (e.g., "factory floor with workers inspecting fabric samples" not "manufacturing")

Return ONLY the alt text, nothing else."""

    try:
        # Try URL-based vision first (most images will be accessible)
        response = await _client.chat.completions.create(
            model=_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url, "detail": "low"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=60,
            temperature=0.3,
        )
        alt_text = response.choices[0].message.content or ""
        alt_text = alt_text.strip().strip('"').strip("'")
        return {"url": image_url, "alt_text": alt_text, "status": "success"}
    except Exception as e:
        return {"url": image_url, "alt_text": "", "status": "error", "error": str(e)[:200]}


async def _batch_generate(
    image_urls: list[str],
    page_context: str,
    target_keywords: list[str],
    max_concurrent: int = 5,
) -> list[dict]:
    """Process image URLs concurrently with a semaphore."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _bounded(url: str) -> dict:
        async with semaphore:
            return await _generate_alt_text(url, page_context, target_keywords)

    tasks = [_bounded(url) for url in image_urls]
    return await asyncio.gather(*tasks, return_exceptions=False)


@function_tool
def generate_alt_texts(
    image_urls_json: str,
    page_context: str = "",
    target_keywords_json: str = "",
) -> str:
    """Generate SEO-optimized alt text for a list of image URLs using OpenAI vision.

    Args:
        image_urls_json: JSON array of image URL strings.
                         Example: '["https://sourcy.ai/img/factory.jpg", ...]'
        page_context: Brief description of the page these images appear on
                      (e.g., "Blog post about sourcing eco-friendly bags from China")
        target_keywords_json: JSON array of target keywords for the page (optional).
                               Example: '["China sourcing", "bag manufacturer", "MOQ"]'
    """
    try:
        image_urls = json.loads(image_urls_json)
    except (json.JSONDecodeError, TypeError) as e:
        return json.dumps({"error": f"Invalid image_urls_json: {str(e)}"})

    if not isinstance(image_urls, list) or not image_urls:
        return json.dumps({"error": "image_urls_json must be a non-empty JSON array"})

    target_keywords: list[str] = []
    if target_keywords_json:
        try:
            target_keywords = json.loads(target_keywords_json)
        except (json.JSONDecodeError, TypeError):
            pass

    # Cap at 30 images per call to avoid rate limits
    image_urls = image_urls[:30]
    images_without_alt = [u for u in image_urls if u.strip()]

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Inside async context — create a new loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    asyncio.run,
                    _batch_generate(images_without_alt, page_context, target_keywords),
                )
                results = future.result(timeout=120)
        else:
            results = loop.run_until_complete(
                _batch_generate(images_without_alt, page_context, target_keywords)
            )
    except Exception as e:
        return json.dumps({"error": f"Batch generation failed: {str(e)}"})

    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]

    return json.dumps({
        "total_images": len(image_urls),
        "successful": len(successful),
        "failed": len(failed),
        "results": results,
        "summary": [
            {"url": r["url"], "alt_text": r["alt_text"]}
            for r in successful
        ],
        "instructions": (
            "For TSX pages: add alt={...} to each <img> or <Image> component.\n"
            "For Next.js Image: <Image src='...' alt='<alt_text>' .../>.\n"
            "For Builder.io images: set alt text in the Builder.io image element properties."
        ),
    })


@function_tool
def generate_alt_text_single(
    image_url: str,
    page_context: str = "",
    target_keywords_json: str = "",
) -> str:
    """Generate alt text for a single image URL.

    Args:
        image_url: Full image URL
        page_context: Brief page context description
        target_keywords_json: JSON array of target keywords (optional)
    """
    target_keywords: list[str] = []
    if target_keywords_json:
        try:
            target_keywords = json.loads(target_keywords_json)
        except (json.JSONDecodeError, TypeError):
            pass

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    asyncio.run,
                    _generate_alt_text(image_url, page_context, target_keywords),
                )
                result = future.result(timeout=30)
        else:
            result = loop.run_until_complete(
                _generate_alt_text(image_url, page_context, target_keywords)
            )
    except Exception as e:
        return json.dumps({"error": str(e), "url": image_url})

    return json.dumps(result)
