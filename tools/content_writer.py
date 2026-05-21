"""Content file management — save and list content outputs (blogs, audits, briefs, landing pages)."""

import json
import re as _re
from datetime import datetime
from pathlib import Path

from agents import function_tool

import config

# Ensure output directories exist
CONTENT_OUTPUT_DIR = config.CONTENT_OUTPUT_DIR
CONTENT_TYPES = {
    "blog": "blogs",
    "audit": "audits",
    "brief": "briefs",
    "landing_page": "landing-pages",
    "ad": "ads",
    "case_study": "case-studies",
}
for _subdir in CONTENT_TYPES.values():
    (CONTENT_OUTPUT_DIR / _subdir).mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    import re
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


@function_tool
def save_content_file(
    content: str,
    content_type: str,
    title: str,
    keywords: str = "",
    summary: str = "",
) -> str:
    """Save content to the appropriate output directory with YAML frontmatter.

    Args:
        content: The full content to save (markdown format)
        content_type: Type of content — 'blog', 'audit', 'brief', or 'landing_page'
        title: Content title (used for filename and frontmatter)
        keywords: Comma-separated target keywords (optional)
        summary: Brief summary of the content (optional)
    """
    if content_type not in CONTENT_TYPES:
        return json.dumps({
            "error": f"Invalid content_type '{content_type}'. Must be one of: {list(CONTENT_TYPES.keys())}",
        })

    subdir = CONTENT_TYPES[content_type]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = _slugify(title) or "untitled"
    filename = f"{slug}_{timestamp}.md"
    filepath = CONTENT_OUTPUT_DIR / subdir / filename

    # Build YAML frontmatter
    frontmatter_lines = [
        "---",
        f"title: \"{title}\"",
        f"type: {content_type}",
        f"date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    if keywords:
        frontmatter_lines.append(f"keywords: \"{keywords}\"")
    if summary:
        frontmatter_lines.append(f"summary: \"{summary}\"")
    frontmatter_lines.append("---\n")

    full_content = "\n".join(frontmatter_lines) + content

    filepath.write_text(full_content, encoding="utf-8")

    return json.dumps({
        "success": True,
        "filepath": str(filepath),
        "filename": filename,
        "content_type": content_type,
        "directory": str(CONTENT_OUTPUT_DIR / subdir),
        "title": title,
        "word_count": len(content.split()),
    })


@function_tool
def list_content_files(content_type: str = "blog") -> str:
    """List existing content files in a given output directory.

    Args:
        content_type: Type of content to list — 'blog', 'audit', 'brief', or 'landing_page'
    """
    if content_type not in CONTENT_TYPES:
        return json.dumps({
            "error": f"Invalid content_type '{content_type}'. Must be one of: {list(CONTENT_TYPES.keys())}",
        })

    subdir = CONTENT_TYPES[content_type]
    directory = CONTENT_OUTPUT_DIR / subdir

    files = []
    for f in sorted(directory.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        # Read first few lines for frontmatter
        text = f.read_text(encoding="utf-8")
        title = ""
        date = ""
        for line in text.split("\n"):
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("date:"):
                date = line.split(":", 1)[1].strip()
        files.append({
            "filename": f.name,
            "title": title,
            "date": date,
            "size_bytes": f.stat().st_size,
        })

    return json.dumps({
        "content_type": content_type,
        "directory": str(directory),
        "total_files": len(files),
        "files": files[:50],
    })


# ─── HTML Artifact CSS Template ──────────────────────────────────────────────

def _load_design_tokens() -> dict:
    """Read tokens from /design-systems/sourcy.json so generated artifacts inherit
    the Memory tab's live colors/fonts. Falls back to defaults if file missing."""
    try:
        from tools.persona_loader import load_design_system
        d = load_design_system("sourcy")
        return {
            "primary": d.get("colors", {}).get("primary", "#0F172A"),
            "accent": d.get("colors", {}).get("accent", "#22D3EE"),
            "bg": d.get("colors", {}).get("neutrals", {}).get("bg", "#FFFFFF"),
            "bg_alt": d.get("colors", {}).get("neutrals", {}).get("bg_alt", "#F8FAFC"),
            "border": d.get("colors", {}).get("neutrals", {}).get("border", "#E2E8F0"),
            "text": d.get("colors", {}).get("neutrals", {}).get("text", "#0F172A"),
            "text_muted": d.get("colors", {}).get("neutrals", {}).get("text_muted", "#64748B"),
            "font_heading": d.get("fonts", {}).get("heading", "Inter, sans-serif"),
            "font_body": d.get("fonts", {}).get("body", "Inter, sans-serif"),
        }
    except Exception:
        return {
            "primary": "#0F172A", "accent": "#22D3EE",
            "bg": "#FFFFFF", "bg_alt": "#F8FAFC", "border": "#E2E8F0",
            "text": "#0F172A", "text_muted": "#64748B",
            "font_heading": "Inter, sans-serif", "font_body": "Inter, sans-serif",
        }


def _build_html_template() -> str:
    """Build the HTML template with the current design system tokens substituted in.
    Returned string still has {title} and {body} placeholders for the caller to fill."""
    t = _load_design_tokens()
    # Use a separate substitution pass for design tokens so the body can later
    # safely contain literal {title}/{body}/{ ... } strings.
    css_template = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: __FONT_BODY__;
      background: __BG_ALT__;
      color: __TEXT__;
      line-height: 1.65;
      padding: 2rem 1rem 4rem;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }
    .sourcy-header {
      max-width: 860px;
      margin: 0 auto 1.5rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .sourcy-logo {
      width: 30px; height: 30px; border-radius: 8px;
      background: linear-gradient(135deg, __PRIMARY__ 0%, #1E293B 100%);
      color: #fff;
      display: inline-flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 13px;
      letter-spacing: -0.02em;
    }
    .sourcy-header .meta {
      font-size: 11px;
      color: __TEXT_MUTED__;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      font-weight: 600;
    }
    .container {
      max-width: 860px;
      margin: 0 auto;
      background: __BG__;
      border-radius: 16px;
      box-shadow: 0 1px 0 rgba(15,23,42,0.04), 0 12px 36px -8px rgba(15,23,42,0.08);
      padding: 3rem 3.5rem;
      border: 1px solid __BORDER__;
    }
    h1, h2, h3, h4 {
      font-family: __FONT_HEADING__;
      letter-spacing: -0.02em;
      color: __PRIMARY__;
    }
    h1 {
      font-size: 2.1rem;
      font-weight: 700;
      line-height: 1.2;
      margin-bottom: 1rem;
    }
    h2 {
      font-size: 1.35rem;
      font-weight: 700;
      margin: 2.25rem 0 0.6rem;
      padding-bottom: 0.4rem;
      border-bottom: 1px solid __BORDER__;
    }
    h3 {
      font-size: 1.05rem;
      font-weight: 700;
      margin: 1.5rem 0 0.4rem;
      color: #1E293B;
    }
    p { margin-bottom: 0.95rem; color: #1E293B; font-size: 15px; }
    ul, ol { margin: 0.5rem 0 1rem 1.4rem; color: #1E293B; }
    li { margin-bottom: 0.3rem; font-size: 15px; }
    a {
      color: __PRIMARY__;
      text-decoration: underline;
      text-decoration-color: __ACCENT__;
      text-underline-offset: 2px;
      text-decoration-thickness: 2px;
    }
    a:hover { color: __ACCENT__; }
    strong { color: __PRIMARY__; font-weight: 600; }
    blockquote {
      border-left: 3px solid __ACCENT__;
      margin: 1.25rem 0;
      padding: 0.5rem 1.15rem;
      background: __BG_ALT__;
      border-radius: 0 8px 8px 0;
      color: #1E293B;
      font-style: italic;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 1.1rem 0;
      font-size: 13.5px;
      border: 1px solid __BORDER__;
      border-radius: 8px;
      overflow: hidden;
    }
    th {
      background: __BG_ALT__;
      color: __PRIMARY__;
      font-weight: 600;
      text-align: left;
      padding: 10px 14px;
      font-size: 12px;
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }
    td {
      padding: 10px 14px;
      border-top: 1px solid __BORDER__;
      color: #1E293B;
    }
    code {
      background: __BG_ALT__;
      color: __PRIMARY__;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.88em;
      font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
      border: 1px solid __BORDER__;
    }
    pre {
      background: __PRIMARY__;
      color: #E2E8F0;
      padding: 1.1rem 1.25rem;
      border-radius: 10px;
      overflow-x: auto;
      margin: 1rem 0;
      font-size: 13px;
      font-family: 'JetBrains Mono', ui-monospace, monospace;
    }
    pre code { background: none; color: inherit; padding: 0; border: 0; }
    img {
      max-width: 100%;
      height: auto;
      border-radius: 10px;
      margin: 1.25rem 0;
      border: 1px solid __BORDER__;
      box-shadow: 0 4px 14px -4px rgba(15,23,42,0.08);
    }
    /* ── Landing-page-specific block patterns ──────────────────── */
    .hero {
      background: linear-gradient(135deg, __PRIMARY__ 0%, #1E3A5F 100%);
      color: #fff;
      border-radius: 14px;
      padding: 3rem;
      margin-bottom: 2.25rem;
      position: relative;
      overflow: hidden;
    }
    .hero::after {
      content: "";
      position: absolute;
      top: -40%; right: -10%;
      width: 60%; height: 180%;
      background: radial-gradient(ellipse at center, __ACCENT__ 0%, transparent 60%);
      opacity: 0.18;
      pointer-events: none;
    }
    .hero h1 { color: #fff; position: relative; }
    .hero p {
      color: rgba(255,255,255,0.85);
      font-size: 1.05rem;
      margin-bottom: 0;
      position: relative;
    }
    .features-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.1rem;
      margin: 1.5rem 0;
    }
    .feature-card {
      background: __BG_ALT__;
      border: 1px solid __BORDER__;
      border-radius: 12px;
      padding: 1.25rem;
      transition: border-color 0.15s ease;
    }
    .feature-card:hover { border-color: __ACCENT__; }
    .feature-card h3 { font-size: 0.95rem; margin: 0 0 0.35rem; }
    .feature-card p { font-size: 0.88rem; color: __TEXT_MUTED__; margin: 0; }
    .cta-box {
      background: __PRIMARY__;
      color: #fff;
      border-radius: 14px;
      padding: 2.5rem 2.75rem;
      margin-top: 2.75rem;
      text-align: center;
      position: relative;
      overflow: hidden;
    }
    .cta-box::after {
      content: "";
      position: absolute;
      inset: -50%;
      background: radial-gradient(ellipse at center, __ACCENT__ 0%, transparent 65%);
      opacity: 0.22;
      pointer-events: none;
    }
    .cta-box h2 {
      color: #fff;
      border: none;
      margin: 0 0 0.6rem;
      font-size: 1.6rem;
      position: relative;
    }
    .cta-box p { color: rgba(255,255,255,0.9); margin-bottom: 0; position: relative; }
    /* Variant grid for ads — 3 cards side-by-side */
    .variants-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 1.25rem;
      margin: 1.5rem 0;
    }
    .variant {
      border: 1px solid __BORDER__;
      border-radius: 12px;
      padding: 1.25rem;
      background: __BG__;
    }
    .variant h3 { margin-top: 0; }
    @media (max-width: 640px) {
      .container { padding: 1.5rem 1.25rem; }
      h1 { font-size: 1.55rem; }
      .hero, .cta-box { padding: 1.75rem; }
    }
    """
    css = (css_template
        .replace("__PRIMARY__", t["primary"])
        .replace("__ACCENT__", t["accent"])
        .replace("__BG_ALT__", t["bg_alt"])
        .replace("__BG__", t["bg"])
        .replace("__BORDER__", t["border"])
        .replace("__TEXT_MUTED__", t["text_muted"])
        .replace("__TEXT__", t["text"])
        .replace("__FONT_HEADING__", t["font_heading"])
        .replace("__FONT_BODY__", t["font_body"]))
    # The CSS contains literal `{}` (CSS rules). `.format()` will choke on those
    # unless we escape them. Escape every brace, then un-escape only the {title}
    # and {body} placeholders so the writer's format() call substitutes correctly.
    raw = (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"UTF-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "  <title>{title}</title>\n"
        "  <link rel=\"preconnect\" href=\"https://rsms.me/\">\n"
        "  <link rel=\"stylesheet\" href=\"https://rsms.me/inter/inter.css\">\n"
        "  <style>" + css + "</style>\n"
        "</head>\n"
        "<body>\n"
        "  <div class=\"sourcy-header\">\n"
        "    <span class=\"sourcy-logo\">S</span>\n"
        "    <span class=\"meta\">Sourcy · {title}</span>\n"
        "  </div>\n"
        "  <div class=\"container\">\n"
        "    {body}\n"
        "  </div>\n"
        "</body>\n"
        "</html>\n"
    )
    return raw.replace("{", "{{").replace("}", "}}").replace("{{title}}", "{title}").replace("{{body}}", "{body}")


# Built once at import time. (Persona/design changes via Memory tab will require
# a backend restart to pick up new tokens here.)
_HTML_TEMPLATE = _build_html_template()


@function_tool
def save_html_artifact(
    html_content: str,
    artifact_type: str,
    title: str,
) -> str:
    """Save a styled HTML artifact (blog post or landing page) to the reports directory.

    Wraps plain HTML body content in a full styled document if not already a full doc.
    Returns filename, URL (/reports/filename), filepath, and title.

    Args:
        html_content: HTML body content (e.g., <h1>...</h1><p>...</p>) or full HTML doc
        artifact_type: One of 'blog', 'landing-page', 'brief', 'ad', 'case-study'
        title: Page title shown in browser tab and Sourcy badge header
    """
    valid_types = ("blog", "landing-page", "brief", "ad", "case-study")
    if artifact_type not in valid_types:
        return json.dumps({
            "error": f"Invalid artifact_type '{artifact_type}'. Must be one of: {list(valid_types)}",
        })

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{artifact_type}_{timestamp}.html"
    filepath = config.OUTPUT_DIR / filename

    # Determine if already a full HTML doc
    stripped = html_content.strip()
    is_full_doc = stripped.lower().startswith("<!doctype") or stripped.lower().startswith("<html")

    if is_full_doc:
        final_html = html_content
    else:
        # Escape braces in content to avoid .format() errors
        safe_body = html_content.replace("{", "{{").replace("}", "}}")
        # Temporarily un-escape the template placeholders we want to fill
        template = _HTML_TEMPLATE.replace("{title}", "{_title}").replace("{body}", "{_body}")
        final_html = template.format(_title=title, _body=safe_body)

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath.write_text(final_html, encoding="utf-8")

    url = f"/reports/{filename}"
    return json.dumps({
        "success": True,
        "filename": filename,
        "url": url,
        "filepath": str(filepath),
        "title": title,
        "artifact_type": artifact_type,
    })
