from __future__ import annotations

"""Source mapper — maps sourcy.ai URLs to their Next.js App Router source files.

Uses filesystem introspection of the customer-app Next.js repo to:
- Map URL paths → TSX source files (static routes)
- Map blog/case-study URLs → Builder.io CMS entry IDs (not TSX)
- Locate the target JSX block within a TSX file (Hero, FAQ section, etc.)

All tools return JSON strings matching the project's @function_tool pattern.
"""

import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from agents import function_tool

import config

# Root of the Next.js app repo
APP_ROOT = config.CUSTOMER_APP_PATH
APP_DIR = APP_ROOT / "app" / "[lang]"

# Builder.io-backed collections (no TSX source — content lives in CMS)
BUILDER_COLLECTIONS = {"blogs", "case-studies", "case_studies"}

# Known route prefix → Builder.io collection mapping
BUILDER_ROUTE_MAP = {
    "blogs": "blogs",
    "blog": "blogs",
    "case-studies": "case-studies",
    "case_studies": "case-studies",
}

# Candidate filenames for a route directory (Next.js App Router conventions)
ROUTE_FILE_CANDIDATES = [
    "page.tsx",
    "page.ts",
    "page.jsx",
    "page.js",
    "index.tsx",
    "index.ts",
]

# JSX block heuristics — pattern name → regex that marks the START of the block
JSX_BLOCK_PATTERNS = {
    "hero": re.compile(r"<(?:Hero|HeroSection|HeroBlock|section[^>]*hero)", re.IGNORECASE),
    "faq": re.compile(r"<(?:FAQ|FAQSection|FAQBlock|Accordion)[^>]*>", re.IGNORECASE),
    "schema": re.compile(r"<(?:FAQPageLD|ArticleLD|OrganizationLD|WebSiteLD|ProductLD|ServiceLD|BreadcrumbLD)[^>]*>", re.IGNORECASE),
    "h1": re.compile(r"<h1[^>]*>"),
    "meta": re.compile(r"export\s+(?:const\s+)?metadata"),
    "cta": re.compile(r"<(?:CTA|CTASection|CallToAction|Button)[^>]*>", re.IGNORECASE),
    "testimonials": re.compile(r"<(?:Testimonial|TestimonialSection|Reviews)[^>]*>", re.IGNORECASE),
}


def _url_to_path_segments(url: str) -> list[str]:
    """Extract clean path segments from a URL."""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    path = parsed.path.rstrip("/")
    segments = [s for s in path.split("/") if s]
    return segments


def _find_tsx_file(route_dir: Path) -> Path | None:
    """Find the page file in a route directory."""
    for candidate in ROUTE_FILE_CANDIDATES:
        candidate_path = route_dir / candidate
        if candidate_path.exists():
            return candidate_path
    return None


def _find_jsx_block(tsx_content: str, block_type: str) -> dict | None:
    """Locate a JSX block within TSX source. Returns line range and preview."""
    pattern = JSX_BLOCK_PATTERNS.get(block_type.lower())
    if pattern is None:
        return None

    lines = tsx_content.split("\n")
    for i, line in enumerate(lines):
        if pattern.search(line):
            # Grab surrounding context (up to 15 lines)
            end = min(i + 15, len(lines))
            snippet = "\n".join(lines[i:end])
            return {
                "start_line": i + 1,  # 1-indexed
                "end_line_approx": end,
                "preview": snippet[:500],
            }
    return None


def scan_static_routes() -> list[dict]:
    """Walk the App Router [lang] directory and return static route info.

    Public helper — call this directly from other tools (e.g. page_prioritizer).
    """
    routes = []
    if not APP_DIR.exists():
        return routes

    for entry in sorted(APP_DIR.iterdir()):
        if not entry.is_dir():
            continue
        name = entry.name
        # Skip dynamic segments like [slug], route groups like (foo)
        if name.startswith("[") or name.startswith("("):
            continue

        tsx_file = _find_tsx_file(entry)
        if tsx_file:
            routes.append({
                "url_path": f"/{name}",
                "tsx_file": str(tsx_file.relative_to(APP_ROOT)),
                "directory": str(entry.relative_to(APP_ROOT)),
            })

        # One level deeper (nested routes, not dynamic)
        for sub in sorted(entry.iterdir()):
            if not sub.is_dir() or sub.name.startswith("[") or sub.name.startswith("("):
                continue
            sub_tsx = _find_tsx_file(sub)
            if sub_tsx:
                routes.append({
                    "url_path": f"/{name}/{sub.name}",
                    "tsx_file": str(sub_tsx.relative_to(APP_ROOT)),
                    "directory": str(sub.relative_to(APP_ROOT)),
                })

    return routes


@function_tool
def map_url_to_source(url: str, block_type: str = "") -> str:
    """Map a sourcy.ai URL to its Next.js source file (or Builder.io CMS entry).

    For static pages: returns the TSX file path and optionally the target JSX block.
    For blog/case-study pages: returns a note that content is in Builder.io CMS.

    Args:
        url: Page URL (e.g., 'https://sourcy.ai/about' or '/blogs/sourcing-guide')
        block_type: Optional JSX block to locate — 'hero', 'faq', 'schema', 'h1',
                    'meta', 'cta', 'testimonials'. Leave empty to skip block search.
    """
    segments = _url_to_path_segments(url)

    if not segments:
        # Root URL → homepage
        tsx_file = _find_tsx_file(APP_DIR)
        if tsx_file is None:
            # Try page.tsx directly in [lang]
            for candidate in ROUTE_FILE_CANDIDATES:
                p = APP_DIR / candidate
                if p.exists():
                    tsx_file = p
                    break

        result: dict = {
            "url": url,
            "type": "static",
            "url_path": "/",
            "tsx_file": str(tsx_file.relative_to(APP_ROOT)) if tsx_file else None,
            "app_root": str(APP_ROOT),
        }
        if tsx_file and block_type:
            content = tsx_file.read_text(encoding="utf-8", errors="ignore")
            block = _find_jsx_block(content, block_type)
            if block:
                result["block"] = block
        return json.dumps(result)

    # Check if first segment is a Builder.io-backed collection
    first_segment = segments[0].lower()
    if first_segment in BUILDER_ROUTE_MAP:
        collection = BUILDER_ROUTE_MAP[first_segment]
        slug = segments[1] if len(segments) > 1 else None
        return json.dumps({
            "url": url,
            "type": "builder_io",
            "collection": collection,
            "slug": slug,
            "note": (
                f"Content for /{'/'.join(segments)} lives in Builder.io CMS "
                f"(collection: '{collection}'). "
                f"Fetch via GET https://cdn.builder.io/api/v3/content/{collection}"
                f"?apiKey=<BUILDER_API_KEY>&query.data.slug={slug or '<slug>'} "
                f"to retrieve the CMS entry. Proposed edits must be applied in Builder.io "
                f"(not via TSX patch files)."
            ),
            "edit_instructions": (
                f"1. Find entry in Builder.io with slug='{slug}' in collection '{collection}'.\n"
                "2. Apply the proposed text/FAQ changes directly in Builder.io visual editor.\n"
                "3. Publish the entry in Builder.io."
            ),
        })

    # Static route — walk the filesystem
    route_dir = APP_DIR
    for seg in segments:
        candidate_dir = route_dir / seg
        if candidate_dir.exists() and candidate_dir.is_dir():
            route_dir = candidate_dir
        else:
            # Try with dynamic [slug] child — still useful for template TSX
            dynamic_children = [
                d for d in route_dir.iterdir()
                if d.is_dir() and d.name.startswith("[")
            ]
            if dynamic_children:
                route_dir = dynamic_children[0]
                break
            else:
                return json.dumps({
                    "url": url,
                    "type": "not_found",
                    "note": f"Could not find route directory for segment '{seg}' under {route_dir}",
                    "app_root": str(APP_ROOT),
                })

    tsx_file = _find_tsx_file(route_dir)
    if tsx_file is None:
        return json.dumps({
            "url": url,
            "type": "static",
            "url_path": "/" + "/".join(segments),
            "tsx_file": None,
            "route_dir": str(route_dir.relative_to(APP_ROOT)),
            "note": "Route directory found but no page.tsx present.",
        })

    result = {
        "url": url,
        "type": "static",
        "url_path": "/" + "/".join(segments),
        "tsx_file": str(tsx_file.relative_to(APP_ROOT)),
        "full_path": str(tsx_file),
        "file_size_bytes": tsx_file.stat().st_size,
    }

    if block_type:
        content = tsx_file.read_text(encoding="utf-8", errors="ignore")
        block = _find_jsx_block(content, block_type)
        if block:
            result["block"] = block
        else:
            result["block_note"] = f"Block type '{block_type}' not found in {tsx_file.name}."

    return json.dumps(result)


@function_tool
def list_static_routes() -> str:
    """List all static routes in the Sourcy Next.js app with their TSX source files.

    Scans the App Router [lang] directory. Excludes Builder.io-backed routes
    (blogs, case-studies) and dynamic segments.

    Returns a JSON list of {url_path, tsx_file, directory} objects.
    """
    routes = scan_static_routes()

    # Classify Builder.io-backed routes separately
    static = [r for r in routes if not any(
        r["url_path"].lstrip("/").split("/")[0] in BUILDER_ROUTE_MAP
        for _ in [1]
    )]

    return json.dumps({
        "app_root": str(APP_ROOT),
        "total_static_routes": len(static),
        "routes": static,
        "builder_io_collections": list(BUILDER_ROUTE_MAP.values()),
        "note": "Trends pages are served dynamically via PostgREST — not individual TSX files.",
    })


@function_tool
def read_tsx_source(tsx_relative_path: str, max_lines: int = 300) -> str:
    """Read the content of a TSX source file from the Next.js app.

    Use this after map_url_to_source() to fetch the file content for audit or rewriting.

    Args:
        tsx_relative_path: Path relative to app root (e.g., 'app/[lang]/about/page.tsx')
        max_lines: Maximum number of lines to return (default 300, max 1000)
    """
    max_lines = min(max_lines, 1000)
    tsx_path = APP_ROOT / tsx_relative_path

    if not tsx_path.exists():
        return json.dumps({"error": f"File not found: {tsx_path}"})

    try:
        content = tsx_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")
        truncated = len(lines) > max_lines
        visible_lines = lines[:max_lines]

        return json.dumps({
            "path": tsx_relative_path,
            "full_path": str(tsx_path),
            "total_lines": len(lines),
            "returned_lines": len(visible_lines),
            "truncated": truncated,
            "content": "\n".join(visible_lines),
            "note": f"Showing first {max_lines} of {len(lines)} lines." if truncated else "",
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to read {tsx_relative_path}: {str(e)}"})
