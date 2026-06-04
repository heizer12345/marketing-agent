"""REST endpoints for the new Next.js frontend (Home / Chat / Library / Memory tabs).

Kept in a separate router so the existing /api/* surface (used by the legacy
Kanban UI) is untouched. Mounted at /api/v2 in server.py.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse

import config
from tools.persona_loader import (
    load_persona,
    load_design_system,
    list_principles,
    list_winners,
    clear_caches,
)

router = APIRouter(prefix="/api/v2")


# ─── Memory tab — read state ──────────────────────────────────────────

@router.get("/memory/state")
async def memory_state(persona: str = "sourcy", design: str = "sourcy"):
    """Snapshot for the Memory tab: persona, design system, principles, winners,
    plus API-connection status."""
    persona_data = load_persona(persona)
    design_data = load_design_system(design)
    principles = list_principles()
    winners = list_winners()

    setup_complete = bool(persona_data) and bool(design_data)

    ga4_ping = config.ping_ga4()
    gsc_ping = config.ping_search_console()

    api_status = {
        "openai": bool(config.OPENAI_API_KEY),
        "ga4": ga4_ping["ok"],
        "search_console": gsc_ping["ok"],
        "google_ads": bool(getattr(config, "GOOGLE_ADS_REFRESH_TOKEN", "")),
        "meta_ads": bool(getattr(config, "META_ACCESS_TOKEN", "")),
        "semrush": bool(getattr(config, "SEMRUSH_API_KEY", "")),
        "instagram": bool(getattr(config, "INSTAGRAM_BUSINESS_ACCOUNT_ID", "")),
        "posthog": bool(getattr(config, "POSTHOG_API_KEY", "")),
    }

    api_status_detail = {
        "ga4": ga4_ping,
        "search_console": gsc_ping,
    }

    return JSONResponse({
        "setup_complete": setup_complete,
        "persona": persona_data,
        "design_system": design_data,
        "principles": principles,
        "winners": winners,
        "api_status": api_status,
        "api_status_detail": api_status_detail,
    })


# ─── Memory tab — save (persona + design) ─────────────────────────────

PERSONAS_DIR = config.BASE_DIR / "personas"
DESIGNS_DIR = config.BASE_DIR / "design-systems"
BRAND_DIR = config.BASE_DIR / "public" / "brand"
for _d in (PERSONAS_DIR, DESIGNS_DIR, BRAND_DIR):
    _d.mkdir(parents=True, exist_ok=True)


@router.post("/setup/persona")
async def save_persona(request: Request):
    body = await request.json()
    name = body.get("name", "sourcy")
    persona = body.get("persona", body)  # accept either {persona: {...}} or the whole body
    if not isinstance(persona, dict):
        raise HTTPException(400, "persona must be an object")
    path = PERSONAS_DIR / f"{name}.json"
    path.write_text(json.dumps(persona, indent=2))
    clear_caches()
    return {"ok": True, "path": str(path.relative_to(config.BASE_DIR))}


@router.post("/setup/design-system")
async def save_design_system(request: Request):
    body = await request.json()
    name = body.get("name", "sourcy")
    design = body.get("design_system", body)
    if not isinstance(design, dict):
        raise HTTPException(400, "design_system must be an object")
    path = DESIGNS_DIR / f"{name}.json"
    path.write_text(json.dumps(design, indent=2))
    clear_caches()
    return {"ok": True, "path": str(path.relative_to(config.BASE_DIR))}


@router.post("/setup/upload-asset")
async def upload_brand_asset(
    file: UploadFile = File(...),
    asset_type: str = Form("logo"),
    tag: str = Form(""),
):
    """Upload logo or brand asset. Saves to /public/brand/."""
    if not file.filename:
        raise HTTPException(400, "missing filename")
    safe = file.filename.replace("/", "_").replace("..", "_")
    dest = BRAND_DIR / safe
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    rel_url = f"/brand/{safe}"
    return {"ok": True, "url": rel_url, "asset_type": asset_type, "tag": tag}


# ─── Home tab — auto-pilot dashboard snapshot ────────────────────────
#
# The Home tab shows a passive "dashboard view" of Sourcy marketing health.
# It auto-runs an analysis in the background on first load (and on every
# explicit refresh), caches the result to disk, and returns AI insights as
# structured bullets. No streaming, no agent dispatch UI — that all happens
# in Chat. Home is the calm "morning briefing" view.

_HOME_CACHE = config.BASE_DIR / "data" / "home_snapshot.json"
_HOME_CACHE.parent.mkdir(parents=True, exist_ok=True)

# How long a snapshot is considered fresh (seconds). Beyond this, /home/snapshot
# will return the cached version BUT schedule a background refresh.
_SNAPSHOT_TTL_SECONDS = 6 * 60 * 60  # 6 hours

_home_refresh_lock = asyncio.Lock()


def _read_home_cache() -> dict | None:
    if not _HOME_CACHE.exists():
        return None
    try:
        return json.loads(_HOME_CACHE.read_text())
    except Exception:
        return None


def _write_home_cache(data: dict) -> None:
    _HOME_CACHE.write_text(json.dumps(data, indent=2))


def _normalize_home_snapshot(parsed: dict) -> dict:
    """Apply consistent drill-down structure to attention items."""
    from app.briefing_detail import build_briefing_detail

    kpis = parsed.get("kpis") if isinstance(parsed.get("kpis"), list) else []

    alerts = [
        build_briefing_detail(
            a,
            default_next="Open Chat and ask for a step-by-step fix plan for this alert.",
            kpis=kpis,
        )
        for a in (parsed.get("alerts") or [])
        if isinstance(a, dict) and (a.get("text") or "").strip()
    ]
    recommendations = [
        build_briefing_detail(
            r,
            default_next="Assign an owner and add this to this week's marketing sprint.",
            kpis=kpis,
        )
        for r in (parsed.get("recommendations") or [])
        if isinstance(r, dict) and (r.get("text") or "").strip()
    ]
    return {**parsed, "alerts": alerts, "recommendations": recommendations}


async def _run_home_analysis_background() -> None:
    """Run a deep marketing analysis and cache structured insights.

    Uses the Marketing Data Analyst directly with a depth-targeted prompt.
    This is faster than master_agent (1-2 min vs 3-5 min) while still
    pulling from every connected data source.

    Failures are caught and recorded in the cache."""
    started = time.time()
    try:
        from agents import Runner
        from skills.marketing_data_analyst import marketing_data_analyst

        prompt = (
            "Produce a COMPREHENSIVE Sourcy marketing dashboard snapshot for the last 7 days. "
            "Pull and cross-reference data from EVERY connected source:\n"
            "- GA4 (traffic, channels, geo, engagement)\n"
            "- Search Console (rankings, CTR, branded vs non-branded)\n"
            "- Google Ads (spend, CPL, top keywords, geo leakage)\n"
            "- Meta Ads (impressions, CTR, creative fatigue, audience overlap)\n"
            "- Instagram (posts, engagement, top content)\n"
            "- PostHog (funnel drop-offs) if available\n"
            "- Sourcy DB (real leads, activations)\n\n"
            "Output ONLY a JSON object between <<<JSON>>> and <<<END_JSON>>> with this exact shape:\n\n"
            "{\n"
            '  "kpis": [{"label": "Sessions (7d)", "value": "12,180", "delta_pct": -8.2, "source": "GA4"}, ...],\n'
            '  "insights": [{"text": "Sessions dropped 12% in DE week-over-week", "severity": "important", "source": "GA4"}, ...],\n'
            '  "top_movers": [{"text": "\\"private label sourcing\\" rank 8 → 4", "kind": "keyword_up", "source": "Search Console"}, ...],\n'
            '  "alerts": [{\n'
            '    "text": "Short headline (max 120 chars)",\n'
            '    "severity": "urgent",\n'
            '    "source": "GA4",\n'
            '    "detail": {\n'
            '      "cause": "Why this is happening — causal mechanism, not just the symptom",\n'
            '      "evidence": "Specific metrics with numbers, date range, and comparison (WoW/benchmark)",\n'
            '      "pages": ["https://www.sourcy.ai/onboard", "https://www.sourcy.ai/blogs/example-slug"],\n'
            '      "suggestion": "What we recommend doing about it",\n'
            '      "next_step": "One concrete action marketing can take today"\n'
            '    }\n'
            '  }, ...],\n'
            '  "recommendations": [{\n'
            '    "text": "Short action headline",\n'
            '    "priority": "high",\n'
            '    "source": "Google Ads",\n'
            '    "detail": { "cause": "...", "evidence": "...", "pages": ["..."], "suggestion": "...", "next_step": "..." }\n'
            '  }, ...]\n'
            "}\n\n"
            "Rules:\n"
            "- Severity: 'urgent' / 'important' / 'info'.   Priority: 'high' / 'medium' / 'low'.\n"
            "- DEPTH targets: 6-8 KPIs, 10-15 insights, 5-8 top_movers, 3-6 alerts, 5-10 recommendations.\n"
            "- Insights must span ALL channels — at least 1-2 from each of: GA4, Search Console, Google Ads, Meta Ads, Sourcy DB.\n"
            "- Every entry needs a `source` field referencing the data source.\n"
            "- Quote specific numbers, never vague claims.\n"
            "- **MANDATORY for every `alerts[]` and `recommendations[]` item**: include a complete `detail` object with all 5 keys:\n"
            "  cause, evidence, pages (array of full https://www.sourcy.ai/... URLs — at least 1 when GA4/GSC/page-level), suggestion, next_step.\n"
            "- `pages` must use full sourcy.ai URLs (e.g. https://www.sourcy.ai/onboard, https://www.sourcy.ai/blogs/slug) — never bare paths like /onboard.\n"
            "- In cause, suggestion, and next_step prose, reference pages as www.sourcy.ai/path (not /path).\n"
            "- `text` is the card headline only; put depth in `detail`.\n"
            "- If a data source is unavailable, omit entries for it — DO NOT make numbers up.\n"
            "- Return ONLY the JSON object. No HTML artifact, no extra prose.\n"
            "- The <<<JSON>>>...<<<END_JSON>>> wrappers are mandatory."
        )
        result = await Runner.run(marketing_data_analyst, prompt, max_turns=15)
        text = str(result.final_output or "")

        # Extract the JSON block.
        import re as _re
        m = _re.search(r"<<<JSON>>>(.*?)<<<END_JSON>>>", text, _re.DOTALL)
        parsed: dict = {}
        if m:
            try:
                parsed = json.loads(m.group(1).strip())
            except json.JSONDecodeError:
                pass
        if not parsed:
            # As a fallback, dump the whole text as an "insights" bullet
            parsed = {"kpis": [], "insights": [{"text": text[:280], "severity": "info", "source": "raw output"}], "top_movers": [], "alerts": []}

        parsed = _normalize_home_snapshot(parsed)

        snapshot = {
            "generated_at": int(time.time()),
            "elapsed_seconds": round(time.time() - started, 2),
            "kpis": parsed.get("kpis", []),
            "insights": parsed.get("insights", []),
            "top_movers": parsed.get("top_movers", []),
            "alerts": parsed.get("alerts", []),
            "recommendations": parsed.get("recommendations", []),
            "raw_response_excerpt": text[:600],
            "status": "ok",
        }
        _write_home_cache(snapshot)
    except Exception as e:
        _write_home_cache({
            "generated_at": int(time.time()),
            "elapsed_seconds": round(time.time() - started, 2),
            "kpis": [], "insights": [], "top_movers": [], "alerts": [], "recommendations": [],
            "status": "error",
            "error": str(e)[:300],
        })


def _latest_dashboard_html_url() -> dict | None:
    """Find a dedicated Home dashboard HTML, if one exists.

    Home snapshot generation currently requests JSON only and does NOT create an
    HTML artifact. Chat/report runs do create `report_<ticket>_<ts>.html`, but
    those are ticket-specific artifacts and should not be embedded into the Home
    page. Doing so makes Home show an unrelated SEO/report artifact, which is
    misleading.

    Until Home has its own dedicated artifact writer, only surface files that are
    explicitly named for Home dashboards.
    """
    reports = config.BASE_DIR / "public" / "reports"
    if not reports.exists():
        return None
    # Only dedicated Home artifacts belong on the Home tab.
    candidates = sorted(
        list(reports.glob("home_dashboard_*.html")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return None
    f = candidates[0]
    return {
        "url": f"/reports/{f.name}",
        "generated_at": int(f.stat().st_mtime),
        "size_kb": round(f.stat().st_size / 1024, 1),
    }


@router.get("/home/snapshot")
async def home_snapshot(force: bool = False):
    """Return the cached dashboard snapshot + URL of the latest comprehensive
    HTML dashboard built by the synthesis_agent. The frontend embeds that HTML
    as the primary view (rich charts, tables, KPIs) and falls back to the
    structured bullets for at-a-glance summary."""
    cache = _read_home_cache()
    if cache and cache.get("status") == "ok":
        normalized = _normalize_home_snapshot(cache)
        cache = {
            **cache,
            "alerts": normalized.get("alerts", []),
            "recommendations": normalized.get("recommendations", []),
        }
        # Persist enriched detail so restarts and other workers see the same shape.
        try:
            _write_home_cache(cache)
        except Exception:
            pass
    now = int(time.time())
    is_stale = cache is None or (now - cache.get("generated_at", 0) > _SNAPSHOT_TTL_SECONDS)

    if force or is_stale:
        if not _home_refresh_lock.locked():
            asyncio.create_task(_refresh_with_lock())
        refreshing = True
    else:
        refreshing = False

    dashboard = _latest_dashboard_html_url()

    return {
        "snapshot": cache or {"status": "empty", "kpis": [], "insights": [], "top_movers": [], "alerts": []},
        "dashboard": dashboard,  # {url, generated_at, size_kb} or null
        "stale": is_stale,
        "refreshing": refreshing,
        "ttl_seconds": _SNAPSHOT_TTL_SECONDS,
    }


async def _refresh_with_lock() -> None:
    if _home_refresh_lock.locked():
        return
    async with _home_refresh_lock:
        await _run_home_analysis_background()


@router.get("/home/kpi-trend")
async def home_kpi_trend(label: str, source: str = ""):
    """Daily trend series + drivers for a Home KPI card (loaded on click)."""
    from app.kpi_trends import fetch_kpi_trend, resolve_kpi_key

    cache = _read_home_cache() or {}
    insights = cache.get("insights") if isinstance(cache.get("insights"), list) else []
    kpi_key = resolve_kpi_key(label, source)
    return fetch_kpi_trend(kpi_key, label, source, insights)


@router.post("/home/refresh")
async def home_refresh_now():
    """Force an immediate background refresh. Returns instantly; poll
    /home/snapshot for completion."""
    if not _home_refresh_lock.locked():
        asyncio.create_task(_refresh_with_lock())
    return {"ok": True, "queued": True, "already_running": _home_refresh_lock.locked()}


# Kept for backwards-compat with the existing frontend (Run-live-analysis CTA).
@router.get("/home/refresh")
async def home_refresh_meta():
    return {
        "seed_prompt": (
            "Run a full Sourcy marketing analysis for the last 7 days. Pull from "
            "every connected source. Surface: top 3-5 wins, top 3-5 problems, "
            "and 3 prioritized next-week actions. Cite each finding."
        ),
        "agents_to_dispatch": [
            "SEO Analyst",
            "Traffic Analyst",
            "Paid/Organic Overlap",
            "Recommendation Engine",
            "Socials Analyst",
        ],
    }


# ─── Library tab ─────────────────────────────────────────────────────

_LIBRARY_TYPES = {
    "blogs": [config.BASE_DIR / "output" / "content" / "blogs",
              config.BASE_DIR / "public" / "content" / "blogs"],
    "landing_pages": [config.BASE_DIR / "output" / "content" / "landing-pages",
                       config.BASE_DIR / "public" / "content" / "landing-pages"],
    "ads": [config.BASE_DIR / "output" / "content" / "ads",
            config.BASE_DIR / "public" / "content" / "ads"],
    "case_studies": [config.BASE_DIR / "output" / "content" / "case-studies",
                      config.BASE_DIR / "public" / "content" / "case-studies"],
    "images": [config.BASE_DIR / "public" / "content" / "images"],
}

# Additional file-name patterns to pull from /public/reports for each type.
# Many of our skills save HTML artifacts (ad_*.html, case-study_*.html, etc.)
# to /public/reports rather than to /public/content/{type}.
_LIBRARY_REPORTS_PATTERNS = {
    "blogs":         ["blog_*.html"],
    "landing_pages": ["landing-page_*.html"],
    "ads":           ["ad_*.html"],
    "case_studies":  ["case-study_*.html"],
}


# ─── Session ↔ artifact mapping helpers ──────────────────────────────

async def _load_artifact_source_map() -> dict[str, dict]:
    """Returns { artifact_path → {ticket_id, ticket_title, created_at} } so the
    Library can show which chat session produced each artifact."""
    import app.database as db
    rows = await db.get_all_artifacts_with_tickets()
    out: dict[str, dict] = {}
    for r in rows:
        # File paths can be stored as either /reports/foo.html or absolute paths
        # depending on the writer. Normalize to the public URL form.
        p = r["file_path"]
        if isinstance(p, str):
            if "public/reports/" in p:
                p = "/reports/" + p.split("public/reports/", 1)[1]
            elif "public/content/" in p:
                p = "/content/" + p.split("public/content/", 1)[1]
        out[p] = {
            "ticket_id": r["ticket_id"],
            "ticket_title": r["ticket_title"],
            "created_at": r["created_at"],
        }
    return out


@router.get("/sessions/{ticket_id}/artifacts")
async def session_artifacts(ticket_id: str):
    """All artifacts (HTML, images, content files) produced inside this chat session."""
    import app.database as db
    artifacts = await db.get_artifacts(ticket_id)
    enriched = []
    for a in artifacts:
        p = a["file_path"]
        if "public/reports/" in p:
            url = "/reports/" + p.split("public/reports/", 1)[1]
        elif "public/content/" in p:
            url = "/content/" + p.split("public/content/", 1)[1]
        else:
            url = p if p.startswith("/") else "/" + p
        ext = (url.rsplit(".", 1)[1] if "." in url else "").lower()
        kind = (
            "image" if ext in ("png", "jpg", "jpeg", "webp", "svg") else
            "html" if ext == "html" else
            "doc"
        )
        enriched.append({
            "url": url,
            "name": url.rsplit("/", 1)[-1],
            "kind": kind,
            "ext": ext,
            "created_at": a.get("created_at"),
        })
    ticket = await db.get_ticket(ticket_id)
    return {
        "ticket_id": ticket_id,
        "ticket_title": ticket.get("title") if ticket else None,
        "count": len(enriched),
        "artifacts": enriched,
    }


@router.get("/library/{type_}")
async def list_library(type_: str):
    """List artifacts for a type. Paths are mapped to FastAPI static-mount URLs:
    - /public/content/blogs/x.md → /content/blogs/x.md   (mounted at /content)
    - /public/reports/x.html     → /reports/x.html       (mounted at /reports)
    - /output/content/...        → /content/...          (also reachable for legacy paths)
    """
    dirs = _LIBRARY_TYPES.get(type_)
    if dirs is None:
        raise HTTPException(404, f"unknown library type: {type_}")
    items: list[dict] = []
    for d in dirs:
        if not d.exists():
            continue
        for f in d.iterdir():
            if not f.is_file():
                continue
            if f.name.startswith("."):
                continue
            stat = f.stat()
            # Map to served URLs by stripping the FS prefix.
            rel = str(f.relative_to(config.BASE_DIR))
            if rel.startswith("public/content/"):
                url = "/content/" + rel[len("public/content/"):]
            elif rel.startswith("output/content/"):
                # Legacy location — copy on demand isn't worth it; fall back to the
                # raw path which still works because FastAPI exposes /content from
                # public/content. We surface a relative path so the link breaks
                # cleanly rather than masking the move.
                url = "/" + rel
            elif rel.startswith("public/reports/"):
                url = "/reports/" + rel[len("public/reports/"):]
            elif rel.startswith("public/"):
                url = "/" + rel[len("public/"):]
            else:
                url = "/" + rel
            items.append({
                "name": f.name,
                "path": url,
                "size_bytes": stat.st_size,
                "modified": int(stat.st_mtime),
                "ext": f.suffix.lstrip(".").lower(),
            })
    # Also include HTML artifacts saved to /public/reports for this type.
    reports_dir = config.BASE_DIR / "public" / "reports"
    for pat in _LIBRARY_REPORTS_PATTERNS.get(type_, []):
        for f in reports_dir.glob(pat):
            if not f.is_file() or f.name.startswith("."):
                continue
            stat = f.stat()
            items.append({
                "name": f.name,
                "path": f"/reports/{f.name}",
                "size_bytes": stat.st_size,
                "modified": int(stat.st_mtime),
                "ext": f.suffix.lstrip(".").lower(),
            })

    items.sort(key=lambda x: x["modified"], reverse=True)

    # Enrich every item with `from_session` so the Library can show
    # "Generated in chat: …" with a click-through link.
    source_map = await _load_artifact_source_map()
    for it in items:
        src = source_map.get(it["path"])
        if src:
            it["from_session"] = {
                "ticket_id": src["ticket_id"],
                "ticket_title": src["ticket_title"],
            }

    return {"type": type_, "count": len(items), "items": items}


# ─── Stuck-job reaper ─────────────────────────────────────────────────

@router.post("/cleanup/stuck-jobs")
async def cleanup_stuck_jobs(stale_minutes: int = 10):
    """Flag tickets stuck in 'in_progress'/'open' status for too long.

    A ticket counts as 'stuck' if:
      - status is 'in_progress' or 'open'
      - updated_at is older than `stale_minutes`
      - has at least one user message (was actually started)
      - has zero assistant messages (no reply landed)

    We don't delete them — we flip status to 'failed' so the user can re-send
    without losing their original prompt. Returns the IDs we changed."""
    import aiosqlite
    import app.database as db
    flipped: list[dict] = []
    cutoff_iso = (datetime.utcnow() - timedelta(minutes=stale_minutes)).isoformat()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            """
            SELECT t.id, t.title, t.updated_at
              FROM tickets t
              JOIN messages m_user ON m_user.ticket_id = t.id AND m_user.role = 'user'
         LEFT JOIN messages m_asst ON m_asst.ticket_id = t.id AND m_asst.role = 'assistant'
             WHERE t.status IN ('in_progress','open')
               AND t.updated_at < ?
             GROUP BY t.id
            HAVING COUNT(m_asst.id) = 0
            """,
            (cutoff_iso,),
        )
        rows = await cur.fetchall()
        for row in rows:
            await conn.execute(
                "UPDATE tickets SET status = 'failed', updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), row["id"]),
            )
            flipped.append({"id": row["id"], "title": row["title"]})
        await conn.commit()
    return {"ok": True, "stale_minutes": stale_minutes, "flipped_count": len(flipped), "flipped": flipped}


# ─── Cleanup empty tickets ────────────────────────────────────────────

@router.post("/cleanup/empty-tickets")
async def cleanup_empty_tickets():
    """Delete every ticket that has no messages AND no artifacts. These come
    from /chat mounting and lazily creating 'New chat' rows that never receive
    a prompt. Returns the deleted IDs so the frontend can prune local state."""
    import app.database as db
    import aiosqlite
    deleted: list[str] = []
    async with aiosqlite.connect(db.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        # Find tickets with zero messages and zero artifacts.
        cur = await conn.execute(
            """
            SELECT t.id
              FROM tickets t
         LEFT JOIN messages m ON m.ticket_id = t.id
         LEFT JOIN artifacts a ON a.ticket_id = t.id
             GROUP BY t.id
            HAVING COUNT(m.id) = 0 AND COUNT(a.id) = 0
            """
        )
        rows = await cur.fetchall()
        for row in rows:
            tid = row["id"]
            # Cascade delete: artifacts (none), messages (none), then ticket itself.
            await conn.execute("DELETE FROM tickets WHERE id = ?", (tid,))
            deleted.append(tid)
        await conn.commit()
    return {"ok": True, "deleted_count": len(deleted), "deleted_ticket_ids": deleted}


@router.post("/cleanup/broken-tickets")
async def cleanup_broken_tickets():
    """Delete failed tickets and in-progress tickets with no assistant reply (stuck/empty runs)."""
    import app.database as db
    import aiosqlite

    deleted: list[str] = []
    async with aiosqlite.connect(db.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            """
            SELECT t.id
              FROM tickets t
             WHERE t.status IN ('failed', 'deleted')
                OR NOT EXISTS (
                    SELECT 1 FROM messages m WHERE m.ticket_id = t.id
                )
            """
        )
        rows = await cur.fetchall()
        for row in rows:
            tid = row["id"]
            await conn.execute("DELETE FROM messages WHERE ticket_id = ?", (tid,))
            await conn.execute("DELETE FROM artifacts WHERE ticket_id = ?", (tid,))
            await conn.execute("DELETE FROM tickets WHERE id = ?", (tid,))
            deleted.append(tid)
        await conn.commit()
    return {"ok": True, "deleted_count": len(deleted), "deleted_ticket_ids": deleted}


# ─── Dispatch endpoint — translate action → seed prompt the WebSocket can run ──

@router.post("/dispatch/{action_id}")
async def dispatch_action(action_id: str, request: Request):
    """Translate a generation action into a seed prompt that the frontend feeds
    into a new chat session over WebSocket.

    Body: {selected_findings: [...], selected_agents: [...], channel?: str,
           subject?: str, customer_name?: str, ticket_id?: str}

    Returns: {seed_prompt: str, target_skill: str}
    The frontend opens a new chat session with `seed_prompt` so the streaming
    Steps rail + artifact canvas + citation flow all work like any other run.
    """
    body = await request.json()
    selected_findings = body.get("selected_findings") or []
    selected_agents = body.get("selected_agents") or []
    channel = body.get("channel") or "meta"
    subject = body.get("subject") or ""
    customer_name = body.get("customer_name") or ""

    # Compact the findings into a JSON blob the skill can read.
    findings_str = json.dumps(selected_findings, ensure_ascii=False)
    agents_str = ", ".join(selected_agents) if selected_agents else "(none)"

    # Map action_id → target skill + seed prompt.
    if action_id.startswith("gen-ad"):
        target = "write_ad_variants"
        seed = (
            "Generate 3 ad variants using the Ad Writer (write_ad_variants). "
            f"Channel: {channel}. "
            f"{'Subject: ' + subject + '. ' if subject else ''}"
            f"Selected findings (use these as the anchor angles): {findings_str}. "
            f"Agent refs: {agents_str}. "
            "Run all 3 image generations in parallel. Return the artifact URL "
            "and the structured findings sentinel."
        )
    elif action_id.startswith("gen-case-study"):
        target = "write_case_study"
        seed = (
            "Generate a case study using the Case Study Writer (write_case_study). "
            f"{'Customer: ' + customer_name + '. ' if customer_name else ''}"
            f"Selected findings (use these proof points): {findings_str}. "
            "Generate one hero image. Return the artifact URL and the findings sentinel."
        )
    elif action_id.startswith("gen-blog"):
        target = "write_blog"
        seed = (
            "Generate a blog post using the Blog Writer (write_blog). "
            f"Selected findings (use these as the content angle / target keyword cluster): {findings_str}. "
            f"{'Subject: ' + subject + '. ' if subject else ''}"
            "Pick the marketing principle that best fits the audience awareness stage."
        )
    elif action_id.startswith("gen-landing-page") or action_id.startswith("gen-lp"):
        target = "write_landing_page"
        seed = (
            "Generate a landing page using the Landing Page Writer (write_landing_page). "
            f"Selected findings (use these as the offer + ICP signals): {findings_str}. "
            f"{'Subject / product: ' + subject + '. ' if subject else ''}"
            "Pick the marketing principle that best fits the audience (Hormozi value stack for offer pages, JTBD for outcome-led)."
        )
    else:
        # Unknown action_id — return a no-op seed so the UI doesn't break.
        return {
            "ok": False,
            "action_id": action_id,
            "error": f"unknown action_id: {action_id}",
            "supported": ["gen-ad", "gen-case-study", "gen-blog", "gen-landing-page"],
        }

    return {
        "ok": True,
        "action_id": action_id,
        "target_skill": target,
        "seed_prompt": seed,
        "channel": channel,
        "subject": subject,
        "selected_findings": selected_findings,
        "selected_agents": selected_agents,
    }
