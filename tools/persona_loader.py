"""Persona + design system loader.

Single source of truth for company voice, ICP, design tokens, and image-style
descriptors. Every generation skill (blog, LP, ad, case study) and every
image_gen call reads from here — never hardcoded.

Switching companies = drop a new JSON pair in /personas and /design-systems.

The composed `system_prompt_block()` is deterministic and small (~1K tokens)
so the OpenAI Agents SDK can cache it across runs.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import config

PERSONAS_DIR = config.BASE_DIR / "personas"
DESIGN_SYSTEMS_DIR = config.BASE_DIR / "design-systems"
PRINCIPLES_DIR = config.BASE_DIR / "knowledge" / "principles"
WINNERS_DIR = config.BASE_DIR / "knowledge" / "winners"


@lru_cache(maxsize=8)
def load_persona(name: str = "sourcy") -> dict:
    path = PERSONAS_DIR / f"{name}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


@lru_cache(maxsize=8)
def load_design_system(name: str = "sourcy") -> dict:
    path = DESIGN_SYSTEMS_DIR / f"{name}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


@lru_cache(maxsize=8)
def load_principle(slug: str) -> dict | None:
    path = PRINCIPLES_DIR / f"{slug}.md"
    if not path.exists():
        return None
    return {"slug": slug, "body": path.read_text()}


@lru_cache(maxsize=1)
def list_principles() -> list[dict]:
    index = PRINCIPLES_DIR / "_index.json"
    if not index.exists():
        return []
    data = json.loads(index.read_text())
    return data.get("principles", [])


@lru_cache(maxsize=1)
def list_winners() -> dict:
    index = WINNERS_DIR / "_index.json"
    empty = {"ads": [], "blogs": [], "landing_pages": [], "case_studies": []}
    if not index.exists():
        return empty
    data = json.loads(index.read_text())
    return {k: data.get(k, []) for k in empty}


def _fmt_list(items: list, max_items: int | None = None) -> str:
    if not items:
        return "(none)"
    items = items[:max_items] if max_items else items
    return ", ".join(str(i) for i in items)


def system_prompt_block(
    persona_name: str = "sourcy",
    design_name: str = "sourcy",
) -> str:
    """Compose the persona + design system prompt block.

    Injected at the top of every generation agent's system instructions.
    Kept tight (~1K tokens) and deterministic so the SDK caches it.
    """
    p = load_persona(persona_name)
    d = load_design_system(design_name)

    if not p or not d:
        return ""

    do = "\n".join(f"  - {x}" for x in p.get("tone_rules", {}).get("do", []))
    dont = "\n".join(f"  - {x}" for x in p.get("tone_rules", {}).get("dont", []))
    banned = _fmt_list(p.get("banned_phrases", []))
    preferred = _fmt_list(p.get("lexicon", {}).get("preferred", []))
    proof = "\n".join(f"  - {pp['stat']} — {pp['context']}" for pp in p.get("proof_points", []))
    voice_examples = "\n".join(
        f"  - [{v['context']}] {v['text']}" for v in p.get("voice_examples", [])[:5]
    )
    icp_lines = "\n".join(
        f"  - {seg['segment']}: {seg['jtbd']}" for seg in p.get("icp", [])
    )

    image_style = d.get("image_style", {})
    voice_traits = _fmt_list(image_style.get("voice_traits", []))
    banned_visuals = _fmt_list(image_style.get("banned_visuals", []))
    colors = d.get("colors", {})

    return f"""
## Brand Persona — {p.get("name", "unknown").title()}

**One-liner**: {p.get("one_liner", "")}

**Positioning**: {p.get("positioning_vs_competitors", "")}

**ICP (who we sell to)**:
{icp_lines}

**Tone — DO**:
{do}

**Tone — DON'T**:
{dont}

**Preferred lexicon**: {preferred}

**Banned phrases (NEVER use)**: {banned}

**Proof points (use these specifically when relevant)**:
{proof}

**Voice examples** (match this register):
{voice_examples}

## Visual / Design System

**Brand colors**: primary {colors.get("primary")} ({colors.get("primary_label")}), accent {colors.get("accent")} ({colors.get("accent_label")})
**Stack**: {d.get("stack", {}).get("framework")} + {d.get("stack", {}).get("css")} + {d.get("stack", {}).get("components")}
**Visual voice traits**: {voice_traits}
**Banned visuals (NEVER generate)**: {banned_visuals}

When you suggest images or generate copy that references visuals, stay inside this design system. Image prompts must be built via tools/image_gen, not freeform.
""".strip()


def image_prompt(
    job_type: str,
    subject: str,
    design_name: str = "sourcy",
    persona_name: str = "sourcy",
    extra: str = "",
) -> str:
    """Build a deterministic, design-system-scoped image prompt.

    job_type: one of "ad_style", "blog_image_style", "case_study_style",
              "lp_hero_style", "infographic_style".
    subject: the specific subject for this image.
    extra: any extra prompt detail (e.g. specific product name).

    Image prompts are NEVER free-form LLM output. They are built from
    design system fields so every generated image looks like the brand.
    """
    d = load_design_system(design_name)
    p = load_persona(persona_name)
    img = d.get("image_style", {})
    colors = d.get("colors", {})

    style_block = img.get(job_type) or img.get("ad_style", "")
    voice_traits = _fmt_list(img.get("voice_traits", []))
    banned = _fmt_list(img.get("banned_visuals", []))
    brand_color_hint = f"{colors.get('primary')} as primary; {colors.get('accent')} as a single accent"

    parts = [
        style_block,
        f"Subject: {subject}.",
    ]
    if extra:
        parts.append(extra)
    parts.extend([
        f"Mood: {voice_traits}.",
        f"Brand colors: {brand_color_hint}.",
        f"Avoid: {banned}.",
        f"Brand: {p.get('name', 'sourcy')}.",
    ])
    return " ".join(part.strip() for part in parts if part)


def clear_caches() -> None:
    """Call after Memory tab edits persona or design files so reload picks up changes."""
    load_persona.cache_clear()
    load_design_system.cache_clear()
    load_principle.cache_clear()
    list_principles.cache_clear()
    list_winners.cache_clear()
