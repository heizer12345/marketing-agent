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

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: #f9fafb;
      color: #111827;
      line-height: 1.7;
      padding: 2rem 1rem 4rem;
    }}
    .sourcy-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #ff6b35;
      color: #fff;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 4px 12px;
      border-radius: 20px;
      margin-bottom: 1.5rem;
    }}
    .sourcy-badge::before {{ content: "●"; font-size: 8px; }}
    .container {{
      max-width: 860px;
      margin: 0 auto;
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,.08), 0 8px 24px rgba(0,0,0,.04);
      padding: 3rem 3.5rem;
    }}
    h1 {{
      font-size: 2rem;
      font-weight: 800;
      line-height: 1.25;
      color: #0f172a;
      margin-bottom: 1rem;
    }}
    h2 {{
      font-size: 1.4rem;
      font-weight: 700;
      color: #1e293b;
      margin: 2.5rem 0 0.75rem;
      padding-bottom: 0.35rem;
      border-bottom: 2px solid #f1f5f9;
    }}
    h3 {{
      font-size: 1.1rem;
      font-weight: 700;
      color: #334155;
      margin: 1.75rem 0 0.5rem;
    }}
    p {{ margin-bottom: 1rem; color: #374151; }}
    ul, ol {{
      margin: 0.75rem 0 1rem 1.5rem;
      color: #374151;
    }}
    li {{ margin-bottom: 0.35rem; }}
    blockquote {{
      border-left: 4px solid #ff6b35;
      margin: 1.5rem 0;
      padding: 0.75rem 1.25rem;
      background: #fff7f4;
      border-radius: 0 8px 8px 0;
      font-style: italic;
      color: #4b5563;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.25rem 0;
      font-size: 0.92rem;
    }}
    th {{
      background: #f8fafc;
      color: #334155;
      font-weight: 700;
      text-align: left;
      padding: 10px 14px;
      border-bottom: 2px solid #e2e8f0;
    }}
    td {{
      padding: 9px 14px;
      border-bottom: 1px solid #f1f5f9;
      color: #374151;
    }}
    tr:last-child td {{ border-bottom: none; }}
    .meta {{
      font-size: 0.85rem;
      color: #9ca3af;
      margin-bottom: 2rem;
    }}
    .cta-box {{
      background: linear-gradient(135deg, #ff6b35 0%, #f43f5e 100%);
      color: #fff;
      border-radius: 12px;
      padding: 2rem 2.5rem;
      margin-top: 3rem;
      text-align: center;
    }}
    .cta-box h2 {{
      color: #fff;
      border: none;
      margin: 0 0 0.5rem;
      font-size: 1.5rem;
    }}
    .cta-box p {{ color: rgba(255,255,255,0.9); margin-bottom: 0; }}
    code {{
      background: #f1f5f9;
      color: #e11d48;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.88em;
    }}
    pre {{
      background: #0f172a;
      color: #e2e8f0;
      padding: 1.25rem;
      border-radius: 8px;
      overflow-x: auto;
      margin: 1rem 0;
      font-size: 0.88rem;
    }}
    pre code {{ background: none; color: inherit; padding: 0; }}
    strong {{ color: #111827; }}
    .hero {{
      background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
      color: #fff;
      border-radius: 12px;
      padding: 3rem;
      margin-bottom: 2.5rem;
    }}
    .hero h1 {{ color: #fff; }}
    .hero p {{ color: rgba(255,255,255,0.8); font-size: 1.1rem; margin-bottom: 0; }}
    .features-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.25rem;
      margin: 1.5rem 0;
    }}
    .feature-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 1.25rem;
    }}
    .feature-card h3 {{
      font-size: 1rem;
      margin: 0 0 0.4rem;
      color: #0f172a;
    }}
    .feature-card p {{ font-size: 0.9rem; color: #64748b; margin: 0; }}
    @media (max-width: 640px) {{
      .container {{ padding: 1.5rem 1.25rem; }}
      h1 {{ font-size: 1.5rem; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="sourcy-badge">sourcy.ai</div>
    {body}
  </div>
</body>
</html>
"""


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
        artifact_type: One of 'blog', 'landing-page', 'brief'
        title: Page title shown in browser tab and Sourcy badge header
    """
    valid_types = ("blog", "landing-page", "brief")
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
