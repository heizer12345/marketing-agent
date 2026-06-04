"""GPT Image 2 generation tool — design-system-scoped, brand-asset-aware.

Single source of truth for all image generation in the marketing agent.
Every generation skill (ad_writer, case_study_writer, blog_writer, landing_page_writer)
calls generate_image() — they never hit the OpenAI API directly. That guarantees:

1. Prompts are built from the design system's image_style block — not free-form LLM output.
2. The logo + uploaded brand assets are passed as reference images automatically.
3. Banned visuals are listed in the prompt every time.
4. Provider is swappable (Nano Banana 2 can drop in later; the interface stays the same).

Quality note: GPT Image 2 (`gpt-image-2`) supports up to 16 reference images. We pass
the logo first, then up to 5 brand assets matching the requested job_type tag.
"""

from __future__ import annotations

import base64
import logging
import time
from io import BytesIO
from pathlib import Path
from typing import Literal

from agents import function_tool

import config
from tools.persona_loader import image_prompt as build_image_prompt, load_design_system

log = logging.getLogger("sourcy")

# Output directory for generated images.
IMAGES_DIR = config.BASE_DIR / "public" / "content" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Brand asset directory — uploads land here via /api/v2/setup/upload-asset.
BRAND_DIR = config.BASE_DIR / "public" / "brand"

JobType = Literal["ad_style", "blog_image_style", "case_study_style", "lp_hero_style", "infographic_style"]


def _collect_reference_images(job_type: str, design_name: str = "sourcy") -> list[Path]:
    """Logo first, then brand assets tagged for this job type (up to 5 total refs)."""
    refs: list[Path] = []
    design = load_design_system(design_name)
    logo_url = (design.get("logo") or {}).get("primary_url")
    if logo_url:
        # logo_url is `/brand/foo.svg` → map to disk
        candidate = config.BASE_DIR / "public" / logo_url.lstrip("/")
        if candidate.exists():
            refs.append(candidate)

    assets = design.get("brand_assets", []) or []
    job_tag = job_type.replace("_style", "")  # "ad_style" → "ad"
    for asset in assets:
        if len(refs) >= 6:
            break
        path = asset.get("path", "")
        if not path:
            continue
        tags = asset.get("tags") or []
        # If asset has tags, require a match. Otherwise it's a generic brand asset, include.
        if tags and job_tag not in tags and "any" not in tags:
            continue
        candidate = config.BASE_DIR / "public" / path.lstrip("/")
        if candidate.exists():
            refs.append(candidate)

    return refs


def _save_image_bytes(data: bytes, hint: str = "img") -> str:
    """Write image bytes to disk and return the public URL path."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    # File extension defaults to png; gpt-image-2 returns PNG by default.
    fname = f"{hint}_{ts}_{int(time.time()*1000) % 10000}.png"
    dest = IMAGES_DIR / fname
    dest.write_bytes(data)
    return f"/content/images/{fname}"


def _generate_with_openai(prompt: str, refs: list[Path], size: str) -> bytes:
    """Call gpt-image-2. Falls back to gpt-image-1 if the new model isn't available
    on the account yet (rolled out April 2026, gradual access)."""
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    # Map our aspect-ratio-friendly sizes to GPT Image 2 supported sizes.
    size = size if size in {"1024x1024", "1024x1536", "1536x1024", "auto"} else "1024x1024"

    last_err: Exception | None = None
    for model in ("gpt-image-2", "gpt-image-1"):
        try:
            if refs:
                # Use images.edit to provide references — this is how gpt-image-2 does
                # ref-aware generation (style transfer + subject preservation).
                ref_files = [open(p, "rb") for p in refs[:16]]
                try:
                    resp = client.images.edit(
                        model=model,
                        image=ref_files if len(ref_files) > 1 else ref_files[0],
                        prompt=prompt,
                        size=size,
                        n=1,
                    )
                finally:
                    for f in ref_files:
                        try: f.close()
                        except Exception: pass
            else:
                resp = client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size,
                    n=1,
                )
            b64 = resp.data[0].b64_json
            if not b64:
                # Some endpoints return url instead of b64 — fetch it
                url = resp.data[0].url
                import urllib.request
                with urllib.request.urlopen(url) as r:
                    return r.read()
            return base64.b64decode(b64)
        except Exception as e:
            last_err = e
            log.warning(f"image_gen: model {model} failed: {e}")
            continue
    raise RuntimeError(f"All image models failed: {last_err}")


@function_tool
def generate_image(
    job_type: str,
    subject: str,
    aspect_ratio: str = "square",
    extra_prompt: str = "",
    persona_name: str = "sourcy",
    design_name: str = "sourcy",
) -> dict:
    """Generate a single brand-aware image via GPT Image 2.

    Args:
        job_type: One of `ad_style`, `blog_image_style`, `case_study_style`,
                  `lp_hero_style`, `infographic_style`. Picks the right style
                  descriptor from the design system.
        subject: What the image should depict (e.g. "kraft-paper packaged whey-protein tub").
        aspect_ratio: `square`, `portrait` (vertical), or `landscape` (wide).
        extra_prompt: Optional extra detail to append to the prompt.

    Returns: {url, public_url, copy_url, prompt_used, refs_used, elapsed_seconds}
    Use public_url (https://www.sourcy.ai/content/images/...) in artifacts and chat — not bare /content/ paths.
    """
    started = time.time()

    size = {
        "square": "1024x1024",
        "portrait": "1024x1536",
        "landscape": "1536x1024",
    }.get(aspect_ratio, "1024x1024")

    prompt = build_image_prompt(
        job_type=job_type,
        subject=subject,
        design_name=design_name,
        persona_name=persona_name,
        extra=extra_prompt,
    )

    refs = _collect_reference_images(job_type, design_name=design_name)
    log.info(f"image_gen: job={job_type} subject={subject!r} refs={len(refs)} size={size}")

    try:
        img_bytes = _generate_with_openai(prompt, refs, size)
    except Exception as e:
        log.warning(f"image_gen failed: {e}")
        return {
            "url": None,
            "prompt_used": prompt,
            "refs_used": [str(r.name) for r in refs],
            "error": str(e),
            "elapsed_seconds": round(time.time() - started, 2),
        }

    url = _save_image_bytes(img_bytes, hint=job_type)
    public_url = f"{config.PUBLIC_SITE_URL}{url}"
    return {
        "url": url,
        "public_url": public_url,
        "copy_url": public_url.replace("https://", "www."),
        "prompt_used": prompt,
        "refs_used": [str(r.name) for r in refs],
        "elapsed_seconds": round(time.time() - started, 2),
    }


# Tier-1 #4: programmatic helper for skills that want to generate multiple
# images in parallel (e.g., ad_writer with 3 variants).
async def generate_images_parallel(
    jobs: list[dict],
) -> list[dict]:
    """Run multiple `generate_image` calls in parallel via asyncio.to_thread.

    Each job is a dict of kwargs for generate_image.
    """
    import asyncio
    results = await asyncio.gather(
        *(asyncio.to_thread(_run_one, j) for j in jobs),
        return_exceptions=True,
    )
    out = []
    for r in results:
        if isinstance(r, Exception):
            out.append({"url": None, "error": str(r)})
        else:
            out.append(r)
    return out


def _run_one(job: dict) -> dict:
    """Synchronous wrapper for parallel asyncio.to_thread."""
    # generate_image is a function_tool wrapper; call the underlying callable.
    fn = generate_image.fn if hasattr(generate_image, "fn") else generate_image
    return fn(**job)
