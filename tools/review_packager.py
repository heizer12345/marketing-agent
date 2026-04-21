"""Review packager — assembles public/reviews/<ticket_id>/ review packages.

Saves all proposed changes (original HTML, proposed HTML, diffs, patches,
TSX files, JSON-LD schemas) into a structured directory for human approval
before anything touches the live site.

Directory structure:
  public/reviews/<ticket_id>/
    index.html          — dashboard linking everything
    original/           — snapshot HTML per page
    proposed/           — preview HTML per page
    diffs/              — side-by-side diff.html per page
    patches/            — *.patch files (git apply compatible)
    files/              — full rewritten *.tsx files
    schemas/            — JSON-LD *.json + JSX snippet *.jsx files
    changes.md          — human summary with file:line refs

All tools return JSON strings matching the project's @function_tool pattern.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from agents import function_tool

import config

REVIEWS_OUTPUT_DIR = config.REVIEWS_OUTPUT_DIR

# ─── Index Dashboard Template ──────────────────────────────────────────────────

_INDEX_CSS = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #f1f5f9; min-height: 100vh; }
  .header { background: #1e293b; border-bottom: 1px solid #334155; padding: 24px 32px; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { font-size: 20px; font-weight: 700; color: #f8fafc; }
  .header .meta { font-size: 13px; color: #94a3b8; }
  .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
  .status-pending { background: #fef3c7; color: #92400e; }
  .status-approved { background: #d1fae5; color: #065f46; }
  .main { padding: 32px; max-width: 1400px; margin: 0 auto; }
  .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
  .card .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; margin-bottom: 8px; }
  .card .value { font-size: 28px; font-weight: 700; color: #f8fafc; }
  .card .sub { font-size: 12px; color: #94a3b8; margin-top: 4px; }
  .section-title { font-size: 14px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 16px; }
  table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; }
  th { background: #0f172a; padding: 12px 16px; text-align: left; font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
  td { padding: 12px 16px; border-top: 1px solid #1e293b; font-size: 13px; }
  tr:hover td { background: #263348; }
  td a { color: #60a5fa; text-decoration: none; }
  td a:hover { text-decoration: underline; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .badge-blog { background: #1d4ed8; color: #bfdbfe; }
  .badge-static { background: #065f46; color: #a7f3d0; }
  .badge-case { background: #7c3aed; color: #ddd6fe; }
  .badge-trends { background: #92400e; color: #fde68a; }
  .actions { display: flex; gap: 24px; margin-top: 32px; padding: 24px; background: #1e293b; border-radius: 12px; border: 1px solid #334155; }
  .action-btn { padding: 10px 20px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
  .btn-approve { background: #16a34a; color: white; }
  .btn-changes { background: #b45309; color: white; }
  footer { text-align: center; padding: 24px; font-size: 12px; color: #475569; margin-top: 32px; }
</style>
"""


def _badge(category: str) -> str:
    cls = {"blogs": "blog", "case-studies": "case", "static": "static", "trends": "trends"}.get(category, "static")
    return f'<span class="badge badge-{cls}">{category}</span>'


def _make_index_html(ticket_id: str, pages: list[dict], summary: dict) -> str:
    """Generate the review package index.html dashboard."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    page_count = len(pages)
    query = summary.get("original_query", "SEO/AEO/GEO overhaul")

    # Derive counts from actual files on disk — don't trust agent-provided numbers
    ticket_dir = REVIEWS_OUTPUT_DIR / ticket_id
    schema_count = len(list((ticket_dir / "schemas").glob("*.json"))) if (ticket_dir / "schemas").exists() else 0
    patch_count = len(list((ticket_dir / "patches").glob("*.patch"))) if (ticket_dir / "patches").exists() else 0

    ticket_dir = REVIEWS_OUTPUT_DIR / ticket_id

    rows = []
    for p in pages:
        url = p.get("url", "")
        slug = p.get("slug", url.rstrip("/").split("/")[-1])
        cat = p.get("category", "static")
        diff_link = p.get("diff_html_relative", "")
        patch_link = p.get("patch_relative", "")
        schema_link = p.get("schema_relative", "")
        score_before = p.get("score_before", "—")
        score_after = p.get("score_after", "—")
        changes_count = p.get("changes_count", 0)

        row_cells = [
            f'<td><a href="{url}" target="_blank">{slug}</a></td>',
            f'<td>{_badge(cat)}</td>',
            f'<td>{changes_count} changes</td>',
            f'<td>{score_before}</td>',
            f'<td>{score_after}</td>',
        ]
        links = []
        # Only add links for files that actually exist on disk
        if diff_link and (ticket_dir / diff_link).exists():
            links.append(f'<a href="{diff_link}">diff</a>')
        if patch_link and (ticket_dir / patch_link).exists():
            links.append(f'<a href="{patch_link}">patch</a>')
        if schema_link and (ticket_dir / schema_link).exists():
            links.append(f'<a href="{schema_link}">schema</a>')
        row_cells.append(f'<td>{" · ".join(links)}</td>')
        rows.append(f'<tr>{"".join(row_cells)}</tr>')

    rows_html = "\n".join(rows) if rows else '<tr><td colspan="6">No pages in this review.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Review: {ticket_id} — Sourcy Marketing Agent</title>
  {_INDEX_CSS}
</head>
<body>
  <div class="header">
    <div>
      <h1>Review Package — {ticket_id}</h1>
      <div class="meta">Generated: {now} · Query: "{query}"</div>
    </div>
    <span class="status-badge status-pending">Pending Review</span>
  </div>

  <div class="main">
    <div class="summary-cards">
      <div class="card">
        <div class="label">Pages Audited</div>
        <div class="value">{page_count}</div>
        <div class="sub">across {len(set(p.get('category','') for p in pages))} categories</div>
      </div>
      <div class="card">
        <div class="label">Schema Additions</div>
        <div class="value">{schema_count}</div>
        <div class="sub">JSON-LD + JSX</div>
      </div>
      <div class="card">
        <div class="label">Patch Files</div>
        <div class="value">{patch_count}</div>
        <div class="sub">git apply ready</div>
      </div>
      <div class="card">
        <div class="label">Est. Effort</div>
        <div class="value">{summary.get('est_hours', '—')}</div>
        <div class="sub">hours to implement</div>
      </div>
    </div>

    <div style="margin-bottom: 32px;">
      <div class="section-title">Pages in Review</div>
      <table>
        <thead>
          <tr>
            <th>Page</th>
            <th>Type</th>
            <th>Changes</th>
            <th>Score Before</th>
            <th>Score After</th>
            <th>Links</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>

    <div class="actions">
      <div>
        <div class="section-title" style="margin-bottom: 8px;">Review Actions</div>
        <p style="font-size: 13px; color: #94a3b8; max-width: 600px;">
          Review each diff carefully. Patches are <code>git apply</code> compatible.
          Builder.io changes must be applied manually in the CMS.
          <strong>Nothing has been applied to the live site.</strong>
        </p>
      </div>
    </div>
  </div>

  <footer>
    Generated by Sourcy Marketing Agent · Ticket {ticket_id} · {now}<br>
    All changes are proposals only — human approval required before applying.
  </footer>
</body>
</html>"""


def _make_changes_md(ticket_id: str, pages: list[dict], summary: dict) -> str:
    """Generate changes.md human summary."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    query = summary.get("original_query", "")
    lines = [
        f"# Review Package: {ticket_id}",
        f"Generated: {now}",
        f"Query: {query}",
        "",
        "## Summary",
        f"- **Pages reviewed**: {len(pages)}",
        f"- **Schema additions**: {summary.get('schema_count', 0)}",
        f"- **Patch files**: {summary.get('patch_count', 0)}",
        "",
        "## Pages",
        "",
    ]
    for p in pages:
        url = p.get("url", "")
        cat = p.get("category", "")
        slug = p.get("slug", url.rstrip("/").split("/")[-1])
        reason = p.get("audit_summary", "")
        tsx_file = p.get("tsx_file", "")
        lines.append(f"### {slug} ({cat})")
        lines.append(f"URL: {url}")
        if tsx_file:
            lines.append(f"Source: `{tsx_file}`")
        if reason:
            lines.append(f"Audit: {reason[:300]}")
        diff = p.get("diff_html_relative", "")
        patch = p.get("patch_relative", "")
        if diff:
            lines.append(f"Diff: [{diff}]({diff})")
        if patch:
            lines.append(f"Patch: [{patch}]({patch})")
        lines.append("")

    lines.extend([
        "## How to Apply",
        "",
        "### TSX patches (static pages)",
        "```bash",
        f"cd /path/to/customer-app && git apply reviews/{ticket_id}/patches/<slug>.patch",
        "```",
        "",
        "### Builder.io changes (blogs/case-studies)",
        "Open Builder.io → find entry by ID listed in changes → apply content changes → publish.",
        "",
        "### Schema additions",
        "See `schemas/<slug>.jsx` for JSX invocations. Add to the page file at the location noted.",
        "",
        "---",
        "*Generated by Sourcy Marketing Agent. Nothing on the live site has been changed.*",
    ])
    return "\n".join(lines)


# ─── Public Tool ──────────────────────────────────────────────────────────────

@function_tool
def create_review_package(
    ticket_id: str,
    pages_json: str,
    summary_json: str = "{}",
) -> str:
    """Assemble a complete review package in public/reviews/<ticket_id>/.

    Creates the index.html dashboard, changes.md summary, and all subdirectories.
    Should be called as the FINAL step after all audits and rewrites are complete.

    Args:
        ticket_id: Unique ticket ID (from DB)
        pages_json: JSON array of page result objects. Each should have:
                    {url, category, slug?, audit_summary?, score_before?, score_after?,
                     changes_count?, diff_html_relative?, patch_relative?, schema_relative?,
                     tsx_file?, builder_id?}
        summary_json: JSON object with overall summary fields:
                      {original_query?, schema_count?, patch_count?, est_hours?}
    """
    try:
        pages = json.loads(pages_json)
    except (json.JSONDecodeError, TypeError) as e:
        return json.dumps({"error": f"Invalid pages_json: {str(e)}"})

    try:
        summary = json.loads(summary_json)
    except (json.JSONDecodeError, TypeError):
        summary = {}

    # Create directory structure
    ticket_dir = REVIEWS_OUTPUT_DIR / ticket_id
    for subdir in ("original", "proposed", "diffs", "patches", "files", "schemas"):
        (ticket_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Hard-fail guard: if pages claim schema_relative but no schema files exist on disk,
    # the agent skipped save_schema_file. Reject with a clear error so the agent retries.
    claimed_schemas = [p.get("schema_relative") for p in pages if p.get("schema_relative")]
    existing_schemas = list((ticket_dir / "schemas").glob("*.json")) if (ticket_dir / "schemas").exists() else []
    if claimed_schemas and not existing_schemas:
        return json.dumps({
            "error": (
                f"Agent claimed {len(claimed_schemas)} schemas in pages_json but no .json files exist in "
                f"{ticket_dir}/schemas/. You MUST call save_schema_file(ticket_id, page_slug, json_ld_json) "
                f"for each schema BEFORE calling create_review_package. Use the returned 'schema_relative' "
                f"path from save_schema_file in your pages_json — never invent paths."
            ),
            "claimed_schemas": claimed_schemas[:5],
            "existing_files": [],
        })

    # index.html
    index_html = _make_index_html(ticket_id, pages, summary)
    (ticket_dir / "index.html").write_text(index_html, encoding="utf-8")

    # changes.md
    changes_md = _make_changes_md(ticket_id, pages, summary)
    (ticket_dir / "changes.md").write_text(changes_md, encoding="utf-8")

    # Count existing artifacts
    patch_count = len(list((ticket_dir / "patches").glob("*.patch")))
    schema_count = len(existing_schemas)
    diff_count = len(list((ticket_dir / "diffs").glob("*.html")))

    review_url = f"/reviews/{ticket_id}/index.html"

    return json.dumps({
        "ticket_id": ticket_id,
        "review_dir": str(ticket_dir),
        "index_html": str(ticket_dir / "index.html"),
        "review_url": review_url,
        "changes_md": str(ticket_dir / "changes.md"),
        "artifact_counts": {
            "patches": patch_count,
            "schemas": schema_count,
            "diffs": diff_count,
        },
        "status": "pending_review",
        "next_steps": [
            f"Review package ready: {review_url}",
            f"Open {ticket_dir}/index.html in browser to review all changes",
            "Apply patches: git apply patches/<slug>.patch in the customer-app repo",
            "Builder.io changes: apply manually per changes.md instructions",
            "After human approval, mark ticket as approved in the system",
        ],
    })


@function_tool
def save_schema_file(
    ticket_id: str,
    page_slug: str,
    json_ld_json: str,
    jsx_snippet: str = "",
    import_line: str = "",
) -> str:
    """Save a JSON-LD schema + JSX snippet to the review package schemas/ directory.

    Args:
        ticket_id: Ticket ID (for output directory)
        page_slug: Page slug for filename (e.g., 'about', 'blog-sourcing-guide')
        json_ld_json: JSON string of the JSON-LD object
        jsx_snippet: JSX code for the schema component (optional)
        import_line: Import statement for the schema component (optional)
    """
    safe_slug = re.sub(r"[^\w\-]", "-", page_slug).strip("-")[:80]
    schemas_dir = REVIEWS_OUTPUT_DIR / ticket_id / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON-LD
    try:
        json_ld = json.loads(json_ld_json)
    except (json.JSONDecodeError, TypeError):
        json_ld = {"raw": json_ld_json}

    json_file = schemas_dir / f"{safe_slug}.json"
    json_file.write_text(json.dumps(json_ld, indent=2), encoding="utf-8")

    # Save JSX snippet
    jsx_file = None
    if jsx_snippet:
        jsx_content = f"// Schema JSX for {safe_slug}\n"
        if import_line:
            jsx_content += f"{import_line}\n\n"
        jsx_content += f"// Add to your page component:\n{jsx_snippet}\n"
        jsx_file = schemas_dir / f"{safe_slug}.jsx"
        jsx_file.write_text(jsx_content, encoding="utf-8")

    return json.dumps({
        "ticket_id": ticket_id,
        "page_slug": safe_slug,
        "json_ld_path": str(json_file),
        "jsx_path": str(jsx_file) if jsx_file else None,
        "schema_relative": f"schemas/{safe_slug}.json",
    })


@function_tool
def save_page_snapshot(
    ticket_id: str,
    page_slug: str,
    html_content: str,
    snapshot_type: str = "original",
) -> str:
    """Save an HTML snapshot of a page to the review package.

    Args:
        ticket_id: Ticket ID
        page_slug: Page slug for filename
        html_content: Full HTML content of the page
        snapshot_type: 'original' or 'proposed' (default: 'original')
    """
    safe_slug = re.sub(r"[^\w\-]", "-", page_slug).strip("-")[:80]
    snap_type = "original" if snapshot_type != "proposed" else "proposed"
    snap_dir = REVIEWS_OUTPUT_DIR / ticket_id / snap_type
    snap_dir.mkdir(parents=True, exist_ok=True)

    snap_file = snap_dir / f"{safe_slug}.html"
    snap_file.write_text(html_content, encoding="utf-8")

    return json.dumps({
        "ticket_id": ticket_id,
        "page_slug": safe_slug,
        "snapshot_type": snap_type,
        "path": str(snap_file),
        "relative": f"{snap_type}/{safe_slug}.html",
    })


@function_tool
def save_rewritten_tsx(
    ticket_id: str,
    tsx_filename: str,
    tsx_content: str,
) -> str:
    """Save a full rewritten TSX file to the review package files/ directory.

    Args:
        ticket_id: Ticket ID
        tsx_filename: Original filename (e.g., 'page.tsx' or 'VariantBuildProductsClient.tsx')
        tsx_content: Full rewritten TSX file content
    """
    safe_name = re.sub(r"[^\w\-\.]", "-", tsx_filename)[:100]
    files_dir = REVIEWS_OUTPUT_DIR / ticket_id / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    tsx_file = files_dir / safe_name
    tsx_file.write_text(tsx_content, encoding="utf-8")

    return json.dumps({
        "ticket_id": ticket_id,
        "filename": safe_name,
        "path": str(tsx_file),
        "relative": f"files/{safe_name}",
        "size_bytes": len(tsx_content.encode()),
    })
