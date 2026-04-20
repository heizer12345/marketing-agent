"""FastAPI server for the Marketing Analyst agent — with ticket system and streaming."""

import json
import re
import asyncio
import traceback
import logging
import time as _time
from typing import Optional

# ─── Logging Setup ────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("sourcy")

import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.auth import login_router, AuthMiddleware, require_session

from agents import Runner
from agents.run_error_handlers import RunErrorHandlerResult
from agents.stream_events import AgentUpdatedStreamEvent, RawResponsesStreamEvent, RunItemStreamEvent
from openai.types.responses import ResponseTextDeltaEvent


# ─── Error Handler for Graceful Degradation ──────────────────────────

async def _handle_max_turns(handler_input):
    """Graceful degradation when agent exceeds max turns."""
    return RunErrorHandlerResult(
        final_output=(
            "Analysis partially complete — the agent reached its maximum turn limit. "
            "Some skills may not have finished. Try a more specific query "
            "(e.g., 'Analyze Meta Ads' instead of 'analyze everything') for faster results."
        ),
        include_in_history=True,
    )

_ERROR_HANDLERS = {"max_turns": _handle_max_turns}

import openai
from openai import AsyncOpenAI
from agents import RunConfig
from agents.models.openai_provider import OpenAIProvider


# ─── Error Classification ────────────────────────────────────────────

_RETRYABLE_EXCEPTIONS = (
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.RateLimitError,
    openai.InternalServerError,
)

def _classify_error(exc: Exception, agent_name: str) -> dict:
    """Map an exception to a structured error payload for the frontend."""
    friendly_agent = FRIENDLY_MAP.get(agent_name, agent_name)
    detail = str(exc)[:200]

    if isinstance(exc, openai.APITimeoutError):
        return {
            "error_type": "timeout",
            "agent": friendly_agent,
            "message": f"{friendly_agent} timed out. Complex analyses can exceed the time limit — try again or use a more specific query.",
            "retryable": True,
            "detail": detail,
        }
    if isinstance(exc, openai.RateLimitError):
        return {
            "error_type": "rate_limit",
            "agent": friendly_agent,
            "message": "Rate limit reached. Please wait a moment and retry.",
            "retryable": True,
            "detail": detail,
        }
    if isinstance(exc, openai.APIConnectionError):
        return {
            "error_type": "connection",
            "agent": friendly_agent,
            "message": "Lost connection to AI service. Check your network or retry.",
            "retryable": True,
            "detail": detail,
        }
    if isinstance(exc, openai.InternalServerError):
        return {
            "error_type": "server_error",
            "agent": friendly_agent,
            "message": "OpenAI is having issues — try again shortly.",
            "retryable": True,
            "detail": detail,
        }
    if isinstance(exc, openai.AuthenticationError):
        return {
            "error_type": "auth",
            "agent": friendly_agent,
            "message": "API key issue. Check your OpenAI configuration.",
            "retryable": False,
            "detail": detail,
        }
    return {
        "error_type": "unknown",
        "agent": friendly_agent,
        "message": f"Unexpected error while running {friendly_agent}.",
        "retryable": False,
        "detail": detail,
    }


def _retry_delay(exc: Exception) -> float:
    """Return how many seconds to wait before retrying."""
    if isinstance(exc, openai.RateLimitError):
        return 10.0
    if isinstance(exc, openai.InternalServerError):
        return 5.0
    return 3.0

from skills.intent_router import master_agent
from app.ui import get_ui_html
from app import database as db
import config
from pathlib import Path
from tools.artifact_generator import SCRIPTS_DIR
from tools.task_decomposer import decompose_tasks
from tools.context_manager import compress_history, build_task_context

# Long timeout for deep agent chains (Content Engine can be 3-4 levels deep with multiple tool calls)
_openai_client = AsyncOpenAI(timeout=1200.0, max_retries=3)  # 20 min timeout, 3 retries for deep agent chains
_model_provider = OpenAIProvider(openai_client=_openai_client)
_run_config = RunConfig(model_provider=_model_provider)

app = FastAPI(title="Sourcy Marketing Analyst")
app.mount("/reports", StaticFiles(directory=str(config.OUTPUT_DIR)), name="reports")
app.mount("/content", StaticFiles(directory=str(config.CONTENT_OUTPUT_DIR)), name="content")
app.mount("/reviews", StaticFiles(directory=str(config.REVIEWS_OUTPUT_DIR)), name="reviews")

# Auth — middlewares applied in reverse-added order, so SessionMiddleware runs first
app.add_middleware(AuthMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-secret-change-in-prod"),
    session_cookie="sourcy_session",
    https_only=False,   # Railway terminates TLS at the edge; internal traffic is HTTP
    same_site="lax",
)
app.include_router(login_router)

_has_ga4 = bool(config.GA4_PROPERTY_ID)
_has_sc = bool(config.SEARCH_CONSOLE_SITE_URL)
_has_ads = bool(config.GOOGLE_ADS_REFRESH_TOKEN)
_has_meta = bool(config.META_ACCESS_TOKEN)
_has_semrush = bool(config.SEMRUSH_API_KEY)
_has_ig = bool(getattr(config, "INSTAGRAM_BUSINESS_ACCOUNT_ID", ""))
_has_posthog = bool(getattr(config, "POSTHOG_API_KEY", ""))


@app.on_event("startup")
async def startup():
    await db.init_db()


@app.get("/")
async def index():
    html = get_ui_html(_has_ga4, _has_sc, _has_ads, _has_semrush, _has_meta, _has_ig, _has_posthog)
    return HTMLResponse(html)


@app.get("/architecture")
async def architecture():
    from app.architecture import get_architecture_html
    return HTMLResponse(get_architecture_html())


# ─── Ticket REST API ──────────────────────────────────────────────────

@app.get("/api/tickets")
async def api_list_tickets(status: str = ""):
    tickets = await db.list_tickets(status)
    return JSONResponse(tickets)


@app.post("/api/tickets")
async def api_create_ticket(body: dict = {}):
    title = body.get("title", "New Analysis")
    created_by = body.get("created_by", "Unknown")
    ticket = await db.create_ticket(title, created_by)
    return JSONResponse(ticket)


@app.get("/api/tickets/{ticket_id}")
async def api_get_ticket(ticket_id: str):
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        return JSONResponse({"error": "Ticket not found"}, status_code=404)
    return JSONResponse(ticket)


@app.patch("/api/tickets/{ticket_id}")
async def api_update_ticket(ticket_id: str, body: dict = {}):
    if "status" in body:
        ticket = await db.update_ticket_status(ticket_id, body["status"])
    elif "title" in body:
        ticket = await db.update_ticket_title(ticket_id, body["title"])
    else:
        return JSONResponse({"error": "No valid fields to update"}, status_code=400)
    if not ticket:
        return JSONResponse({"error": "Ticket not found"}, status_code=404)
    return JSONResponse(ticket)


@app.delete("/api/tickets/{ticket_id}")
async def api_delete_ticket(ticket_id: str):
    await db.delete_ticket(ticket_id)
    return JSONResponse({"ok": True})


@app.get("/api/team")
async def api_team():
    return JSONResponse({"members": db.TEAM_MEMBERS})


@app.get("/api/reports")
async def list_reports():
    reports = sorted(config.OUTPUT_DIR.glob("*.html"), reverse=True)
    return [{"name": r.name, "url": f"/reports/{r.name}"} for r in reports[:20]]


# ─── Review Package Endpoints ─────────────────────────────────────────────────

@app.get("/api/reviews")
async def api_list_reviews():
    """List all pending review packages."""
    pending = await db.list_pending_reviews()
    return JSONResponse({"reviews": pending, "count": len(pending)})


@app.get("/api/tickets/{ticket_id}/review")
async def api_get_review(ticket_id: str):
    """Get review package for a ticket."""
    review = await db.get_review_package(ticket_id)
    if not review:
        return JSONResponse({"error": "No review package found"}, status_code=404)
    # Add index.html URL if package exists on disk
    pkg_path = config.REVIEWS_OUTPUT_DIR / ticket_id / "index.html"
    review["index_url"] = f"/reviews/{ticket_id}/index.html" if pkg_path.exists() else None
    return JSONResponse(review)


@app.post("/api/tickets/{ticket_id}/review/approve")
async def api_approve_review(ticket_id: str, body: dict = {}):
    """Mark a review package as approved."""
    reviewed_by = body.get("reviewed_by", "")
    notes = body.get("notes", "")
    updated = await db.update_review_status(ticket_id, "approved", reviewed_by, notes)
    if not updated:
        return JSONResponse({"error": "Review not found"}, status_code=404)
    return JSONResponse({"status": "approved", "review": updated})


@app.post("/api/tickets/{ticket_id}/review/request-changes")
async def api_request_changes(ticket_id: str, body: dict = {}):
    """Request changes on a review package."""
    reviewed_by = body.get("reviewed_by", "")
    notes = body.get("notes", "Changes needed — see notes.")
    updated = await db.update_review_status(ticket_id, "changes_requested", reviewed_by, notes)
    if not updated:
        return JSONResponse({"error": "Review not found"}, status_code=404)
    return JSONResponse({"status": "changes_requested", "review": updated})


# ─── Script Retry Endpoint ───────────────────────────────────────────────────

@app.get("/api/tickets/{ticket_id}/failed-script")
async def api_get_failed_script(ticket_id: str):
    """Return info about a failed build script for a ticket, if any."""
    info = await db.get_failed_script(ticket_id)
    if not info:
        return JSONResponse({"exists": False})
    # Also include the last few lines of the error sidecar if available
    script_name = Path(info["script_path"]).name
    error_path = SCRIPTS_DIR / f"{script_name}.error.json"
    traceback_snippet = ""
    if error_path.exists():
        try:
            err_data = json.loads(error_path.read_text())
            tb = err_data.get("traceback", "")
            # Return last 15 lines
            lines = [l for l in tb.split("\n") if l.strip()]
            traceback_snippet = "\n".join(lines[-15:])
        except Exception:
            pass
    return JSONResponse({
        "exists": True,
        "script_name": script_name,
        "script_path": info["script_path"],
        "error_msg": info["error_msg"],
        "traceback": traceback_snippet,
        "created_at": info["created_at"],
    })


@app.post("/api/tickets/{ticket_id}/retry-script")
async def api_retry_script(ticket_id: str):
    """Re-run a failed build script with the current fixed namespace. Registers artifact on success."""
    import importlib
    import tools.html_components as _hc
    import datetime as _dt
    from datetime import datetime as _datetime, timedelta
    importlib.reload(_hc)

    info = await db.get_failed_script(ticket_id)
    if not info:
        return JSONResponse({"success": False, "error": "No failed script found for this ticket"}, status_code=404)

    script_path = Path(info["script_path"])
    if not script_path.exists():
        return JSONResponse({"success": False, "error": f"Script file not found: {script_path.name}"}, status_code=404)

    script_code = script_path.read_text(encoding="utf-8")
    namespace = {
        "DATA": {}, "json": json, "datetime": _dt, "timedelta": timedelta,
        "title": "Sourcy Marketing Dashboard",
        "render_sparkline": _hc.render_sparkline, "render_kpi_card": _hc.render_kpi_card,
        "render_kpi_grid": _hc.render_kpi_grid, "render_weekly_line_chart": _hc.render_weekly_line_chart,
        "render_bar_chart": _hc.render_bar_chart, "render_funnel_chart": _hc.render_funnel_chart,
        "render_doughnut_chart": _hc.render_doughnut_chart, "render_heatmap_chart": _hc.render_heatmap_chart,
        "render_radar_chart": _hc.render_radar_chart, "render_sortable_table": _hc.render_sortable_table,
        "render_diagnosis_card": _hc.render_diagnosis_card, "render_creative_gallery": _hc.render_creative_gallery,
        "render_expandable": _hc.render_expandable, "render_so_what": _hc.render_so_what,
        "render_tab_section": _hc.render_tab_section, "render_tab_bar": _hc.render_tab_bar,
        "render_full_page": _hc.render_full_page, "render_decision_summary": _hc.render_decision_summary,
        "render_comparison_header": _hc.render_comparison_header, "render_before_after": _hc.render_before_after,
        "render_action_steps": _hc.render_action_steps, "render_action_item": _hc.render_action_item,
        "render_tooltip_label": _hc.render_tooltip_label, "render_score_breakdown": _hc.render_score_breakdown,
        "render_message_alignment_card": _hc.render_message_alignment_card,
        "render_conversion_funnel": _hc.render_conversion_funnel, "render_reasoning_chain": _hc.render_reasoning_chain,
        "RESULT_HTML": None,
    }

    try:
        exec(script_code, namespace)
    except Exception as e:
        tb = traceback.format_exc()
        lines = [l for l in tb.split("\n") if l.strip()]
        return JSONResponse({
            "success": False,
            "error": str(e),
            "traceback": "\n".join(lines[-15:]),
            "script_name": script_path.name,
        })

    result_html = namespace.get("RESULT_HTML")
    if not result_html or not isinstance(result_html, str):
        return JSONResponse({"success": False, "error": "Script ran but RESULT_HTML was not set."})

    # Save HTML
    ts = _datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{ticket_id[:8]}_{ts}.html"
    filepath = config.OUTPUT_DIR / filename
    filepath.write_text(result_html, encoding="utf-8")
    url = f"/reports/{filename}"

    # Register artifact in DB
    async with __import__("aiosqlite").connect(str(db.DB_PATH)) as conn:
        cursor = await conn.execute(
            "SELECT id FROM messages WHERE ticket_id = ? ORDER BY created_at DESC LIMIT 1", (ticket_id,)
        )
        row = await cursor.fetchone()
        msg_id = row[0] if row else None
        await conn.execute(
            "INSERT OR IGNORE INTO artifacts (ticket_id, file_path, message_id, created_at) VALUES (?,?,?,datetime('now'))",
            (ticket_id, url, msg_id)
        )
        await conn.commit()

    # Clear the failed script record
    await db.delete_failed_script(ticket_id)
    log.info(f"[{ticket_id[:8]}] Retry succeeded → {url}")

    return JSONResponse({"success": True, "url": url, "filename": filename})


# ─── Report URL Detection ─────────────────────────────────────────────

def _detect_report_url(text: str, created_after: float = 0) -> Optional[str]:
    """Extract report URL — first from text, then by checking for newly created files."""
    if text:
        match = re.search(r'((?:report|blog|landing-page|brief)_[a-zA-Z0-9_-]*\d{8}_\d{6}\.html)', text)
        if match:
            return f"/reports/{match.group(1)}"
        url_match = re.search(r'(/reports/[a-zA-Z0-9_-]+\.html)', text)
        if url_match:
            return url_match.group(1)

    # NOTE: Removed filesystem fallback — only detect from text to avoid cross-contamination
    return None


def _detect_all_artifacts(text: str, created_after: float = 0) -> list:
    """Detect ALL artifact URLs (HTML reports + content files + review packages) in response text."""
    urls = []
    seen = set()

    def _add(url: str):
        if url not in seen:
            seen.add(url)
            urls.append(url)

    if text:
        # HTML reports (report_, blog_, landing-page_, brief_, build_ timestamp patterns)
        for m in re.finditer(r'((?:report|blog|landing-page|brief|build)_[a-zA-Z0-9_-]*\d{8}_\d{6}\.html)', text):
            _add(f"/reports/{m.group(1)}")
        if not urls:
            for m in re.finditer(r'(/reports/[a-zA-Z0-9_-]+\.html)', text):
                _add(m.group(1))

        # Review packages — URL style: /reviews/<ticket_id>/index.html
        for m in re.finditer(r'/reviews/([a-zA-Z0-9_-]+)/index\.html', text):
            _add(m.group(0))

        # Review packages — full local path style: public/reviews/<ticket_id>/index.html
        for m in re.finditer(r'public/reviews/([a-zA-Z0-9_-]+)/index\.html', text):
            _add(f"/reviews/{m.group(1)}/index.html")

    # NOTE: Removed filesystem fallback scan — it caused cross-contamination when
    # multiple agents run in parallel (any agent's report got attached to all tickets).
    # Artifacts are now only detected from the agent's text output.
    # Content files (.md)
    for url in _detect_content_files(text):
        _add(url)

    return urls


def _detect_content_file(text: str) -> Optional[str]:
    """Detect first content file path in response text (backward compat)."""
    files = _detect_content_files(text)
    return files[0] if files else None


def _detect_content_files(text: str) -> list:
    """Detect ALL content file paths (blogs, briefs, landing pages, audits) in response text."""
    if not text:
        return []
    # Match both old output/content/... and new public/content/... paths
    matches = re.findall(
        r'(?:public|output)/content/(blogs|audits|briefs|landing-pages)/([a-zA-Z0-9_-]+\.md)',
        text
    )
    # Deduplicate while preserving order
    seen = set()
    result = []
    for type_dir, filename in matches:
        url = f"/content/{type_dir}/{filename}"
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result


def _tag_artifacts(ticket_id: str, artifact_urls: list) -> list:
    """Rename HTML report/blog/landing-page/brief files to include ticket ID prefix for traceability.

    /reports/report_20260415_145205.html → /reports/report_2a1a1194_20260415_145205.html
    /reports/blog_20260415_145205.html → /reports/blog_2a1a1194_20260415_145205.html
    Content files (.md) are left as-is — their names are already meaningful.
    """
    short_id = ticket_id[:8]
    tagged = []
    _html_artifact_pattern = re.compile(
        r'^/reports/((?:report|blog|landing-page|brief)_)([a-zA-Z0-9_-]*\d{8}_\d{6}\.html)$'
    )
    for url in artifact_urls:
        m = _html_artifact_pattern.match(url)
        if m:
            prefix = m.group(1)   # e.g. "report_" or "blog_"
            rest = m.group(2)     # e.g. "20260415_145205.html"
            old_name = f"{prefix}{rest}"
            new_name = f"{prefix}{short_id}_{rest}"
            old_path = config.OUTPUT_DIR / old_name
            new_path = config.OUTPUT_DIR / new_name
            try:
                if old_path.exists():
                    old_path.rename(new_path)
                    tagged.append(f"/reports/{new_name}")
                else:
                    tagged.append(url)  # Already renamed or missing — keep as-is
            except Exception:
                tagged.append(url)
        else:
            tagged.append(url)
    return tagged


# ─── Friendly Tool Name Map ───────────────────────────────────────────

FRIENDLY_MAP = {
    'data_analyst': 'Marketing Data Analyst',
    'seo_analysis': 'SEO Analyst',
    'geo_aeo_analysis': 'GEO/AEO Analyst',
    'competitor_analysis': 'Competitor Analyst',
    'traffic_analysis': 'Traffic Analyst',
    'paid_organic_overlap': 'Paid/Organic Overlap',
    'deep_recommendations': 'Recommendation Engine',
    'socials_analysis': 'Social Media Analyst',
    'report_builder': 'Report Builder',
    'knowledge_expert': 'Knowledge Expert',
    'generate_dynamic_artifact': 'Generating Artifact',
    'get_meta_campaigns': 'Fetching Meta Ads Campaigns',
    'get_meta_adset_targeting': 'Analyzing Ad Set Targeting',
    'get_meta_ad_performance': 'Analyzing Meta Ad Performance',
    'get_meta_ad_creatives': 'Reviewing Ad Creatives',
    'get_meta_spend_by_country': 'Analyzing Meta Spend by Country',
    'get_meta_audience_overlap': 'Checking Audience Config',
    'get_meta_campaign_trend': 'Analyzing Campaign Trends',
    'get_meta_wow_comparison': 'Comparing Week-over-Week',
    'get_meta_ad_level_performance': 'Ranking Creative Performance',
    'get_ig_account_overview': 'Fetching Instagram Account',
    'get_ig_posts_with_insights': 'Analyzing Instagram Posts',
    'get_posthog_session_stats': 'Fetching PostHog Sessions',
    'get_posthog_funnel': 'Analyzing Conversion Funnel',
    'get_posthog_user_paths': 'Mapping User Paths',
    'get_posthog_events': 'Fetching PostHog Events',
    'get_active_campaigns': 'Fetching Google Ads Campaigns',
    'get_google_ads_wow': 'Google Ads Week-over-Week',
    'get_google_ads_campaign_trend': 'Google Ads Trends',
    'get_google_ads_budget_overview': 'Google Ads Budget Overview',
    'fetch_reference_content': 'Fetching Reference Docs',
    # Content Engine skills
    'content_engine': 'Content Engine',
    'seo_content_analysis': 'SEO Content Analyst',
    'geo_content_analysis': 'GEO Content Analyst',
    'aeo_content_analysis': 'AEO Content Analyst',
    'eeat_audit': 'E-E-A-T Auditor',
    'entity_optimization': 'Entity Optimizer',
    'keyword_strategy': 'Keyword Strategist',
    'technical_seo_audit': 'Technical SEO Auditor',
    'write_blog': 'Blog Writer',
    'write_landing_page': 'Landing Page Writer',
    'generate_brief': 'Content Brief Generator',
    'score_content': 'Content Quality Scorer',
    'content_synthesize_and_build': 'Content Synthesis Agent',
    'crawl_page': 'Crawling Page',
    'crawl_robots_txt': 'Checking Robots.txt',
    'crawl_sitemap': 'Parsing Sitemap',
    'check_llms_txt': 'Checking llms.txt',
    'check_ai_crawler_access': 'Checking AI Crawler Access',
    'check_page_speed': 'Testing Page Speed',
    'save_content_file': 'Saving Content',
    'save_html_artifact': 'Saving HTML Artifact',
}


# ─── Reusable Streaming Runner ───────────────────────────────────────

async def _run_agent_stream(
    messages: list,
    _ws_send,
    ticket_id: str,
    request_start: float,
    task_label: str = "",
    timeout_seconds: int = 600,
) -> str:
    """
    Run master_agent with streaming, timeout, and retry.
    Returns the full text output.
    Sends stream events to _ws_send.
    """
    if task_label:
        await _ws_send({"type": "tool_status", "label": f"▶ {task_label}"})

    max_retries = 2
    current_agent = "Marketing Analyst"
    turn_count = 0

    async def _run_once():
        nonlocal current_agent, turn_count
        result = Runner.run_streamed(
            master_agent, messages, max_turns=50,
            error_handlers=_ERROR_HANDLERS,
            run_config=_run_config,
        )

        full_text = ""
        stop_keepalive = asyncio.Event()

        await _ws_send({"type": "stream_start", "agent": current_agent})

        async def keepalive():
            while not stop_keepalive.is_set():
                try:
                    await asyncio.wait_for(stop_keepalive.wait(), timeout=8)
                except asyncio.TimeoutError:
                    await _ws_send({
                        "type": "tool_status",
                        "label": f"Working: {current_agent}...",
                    })

        keepalive_task = asyncio.create_task(keepalive())

        try:
            async for event in result.stream_events():
                if isinstance(event, AgentUpdatedStreamEvent):
                    new_agent = getattr(event, 'new_agent', None)
                    if new_agent:
                        agent_name = getattr(new_agent, 'name', str(new_agent))
                        if agent_name != current_agent:
                            current_agent = agent_name
                            log.info(f"[{ticket_id[:8]}] Agent switch → {current_agent}")
                            await _ws_send({
                                "type": "agent_switch",
                                "agent": current_agent,
                            })

                elif isinstance(event, RawResponsesStreamEvent):
                    raw = event.data
                    if isinstance(raw, ResponseTextDeltaEvent):
                        delta = raw.delta or ""
                        if delta:
                            full_text += delta
                            await _ws_send({"type": "stream_delta", "data": delta})

                elif isinstance(event, RunItemStreamEvent):
                    item = event.item
                    item_type = getattr(item, 'type', '')
                    if item_type == 'tool_call_item':
                        turn_count += 1
                        raw_name = getattr(item, 'name', None) or ''
                        friendly = FRIENDLY_MAP.get(raw_name, raw_name.replace('_', ' ').title())
                        log.info(f"[{ticket_id[:8]}] Turn {turn_count}: tool_call → {friendly}")
                        await _ws_send({
                            "type": "tool_status",
                            "tool": raw_name,
                            "label": f"Running: {friendly}...",
                        })
                    elif item_type == 'tool_call_output_item':
                        log.info(f"[{ticket_id[:8]}] Turn {turn_count}: tool done")
                        await _ws_send({"type": "tool_done", "label": "Step completed"})
        finally:
            stop_keepalive.set()
            if keepalive_task:
                keepalive_task.cancel()

        elapsed = _time.time() - request_start
        log.info(f"[{ticket_id[:8]}] Stream loop ended in {elapsed:.1f}s. is_complete={result.is_complete}")

        # Get final output
        final_output = ""
        try:
            if result.is_complete:
                final_output = result.final_output or ""
        except Exception:
            pass
        if not final_output:
            final_output = full_text
        if not final_output:
            fallback_arts = _detect_all_artifacts("", created_after=request_start)
            if fallback_arts:
                final_output = f"Analysis complete. Generated {len(fallback_arts)} artifact(s):\n" + "\n".join(f"- {a}" for a in fallback_arts)
                log.info(f"[{ticket_id[:8]}] Using fallback output from detected artifacts")

        return final_output

    for attempt in range(max_retries + 1):
        try:
            return await asyncio.wait_for(_run_once(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            msg = "Task timed out after 10 min — try a more specific request."
            log.warning(f"[{ticket_id[:8]}] {msg}")
            await _ws_send({"type": "error", "error_type": "timeout", "message": msg})
            return msg
        except Exception as e:
            if attempt < max_retries and isinstance(e, _RETRYABLE_EXCEPTIONS):
                friendly = FRIENDLY_MAP.get(current_agent, current_agent)
                err_label = _classify_error(e, current_agent)["error_type"].upper()
                delay = _retry_delay(e)
                log.warning(f"[{ticket_id[:8]}] {err_label} on {friendly}, retry {attempt+1}/{max_retries}: {str(e)[:100]}")
                await _ws_send({
                    "type": "tool_status",
                    "label": f"{err_label} on {friendly} — retrying ({attempt+1}/{max_retries})...",
                })
                await asyncio.sleep(delay)
                continue
            raise


# ─── Ticket-Scoped WebSocket ──────────────────────────────────────────

@app.websocket("/ws/{ticket_id}")
async def websocket_ticket(websocket: WebSocket, ticket_id: str):
    """WebSocket for chatting within a specific ticket."""
    await websocket.accept()
    if not await require_session(websocket):
        return

    # Verify ticket exists
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await websocket.send_json({"type": "error", "data": "Ticket not found"})
        await websocket.close()
        return

    # Track connection state — agent keeps running even if client disconnects
    ws_alive = True

    async def _ws_send(payload: dict):
        """Send JSON to client, silently mark dead on disconnect."""
        nonlocal ws_alive
        if not ws_alive:
            return
        try:
            await websocket.send_json(payload)
        except Exception:
            ws_alive = False

    while True:
        try:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_input = msg.get("message", "")
            if not user_input:
                continue

            log.info(f"[{ticket_id[:8]}] Received message: {user_input[:80]}")

            # Save user message to DB
            await db.add_message(ticket_id, "user", user_input)

            # Build conversation history from DB
            all_messages = await db.get_messages(ticket_id)
            # Normalise to plain dicts (DB may return sqlite Row objects)
            all_messages = [{"role": m["role"], "content": m["content"]} for m in all_messages]
            log.info(f"[{ticket_id[:8]}] History: {len(all_messages)} messages. Decomposing tasks...")

            request_start = _time.time()

            try:
                # 1. Compress history
                compressed = compress_history(all_messages)

                # 2. Build recent_context string for decomposer (last 2 exchanges, text only)
                recent_context = " | ".join(
                    f"{m['role']}: {m['content'][:200]}"
                    for m in compressed[-4:]
                    if m['role'] in ('user', 'assistant')
                )

                # 3. Decompose tasks (non-deterministic LLM call)
                tasks = await decompose_tasks(user_input, recent_context)
                log.info(f"[{ticket_id[:8]}] Decomposed into {len(tasks)} task(s). Starting agent...")

                # 4. Run tasks
                if len(tasks) == 1:
                    # Single task — normal flow, pass compressed history
                    # Use longer timeout for complex tasks (implementation, content_write, content_audit)
                    _hint = tasks[0].get("agent_hint", "auto")
                    # Tier-based timeouts: content ops take longest (blogs, audits, overhauls)
                    # data_analysis is capped at 900s — deep dashboards still fit, simple queries won't hang
                    if _hint in ("implementation", "content_write", "content_audit", "report"):
                        _timeout = 1500
                    elif _hint == "data_analysis":
                        _timeout = 900
                    else:
                        _timeout = 600
                    brief_with_id = f"[ticket_id: {ticket_id}]\n\n{tasks[0]['brief']}"
                    task_messages = build_task_context(compressed, brief_with_id)
                    output = await _run_agent_stream(task_messages, _ws_send, ticket_id, request_start, timeout_seconds=_timeout)
                else:
                    # Multi-task flow
                    await _ws_send({"type": "tool_status", "label": f"🔀 Breaking into {len(tasks)} tasks..."})

                    phase1 = [t for t in tasks if t["phase"] == 1]
                    phase2 = [t for t in tasks if t["phase"] == 2]

                    all_outputs = []

                    # Phase 1: run sequentially (results inform phase 2)
                    phase1_results = []
                    for task in phase1:
                        brief_with_id = f"[ticket_id: {ticket_id}]\n\n{task['brief']}"
                        task_messages = build_task_context(compressed, brief_with_id)
                        result = await _run_agent_stream(
                            task_messages, _ws_send, ticket_id, request_start,
                            task_label=task["brief"][:60],
                        )
                        phase1_results.append(result)
                        all_outputs.append(result)

                    # Phase 2: run in parallel
                    if phase2:
                        # Add phase1 results as context for phase 2 tasks
                        phase1_summary = "\n\n---\n\n".join(phase1_results) if phase1_results else ""
                        phase2_compressed = compressed.copy()
                        if phase1_summary:
                            phase2_compressed = compress_history(
                                compressed + [{"role": "assistant", "content": phase1_summary}]
                            )

                        async def run_phase2_task(task, _ticket_id=ticket_id):
                            brief_with_id = f"[ticket_id: {_ticket_id}]\n\n{task['brief']}"
                            task_messages = build_task_context(phase2_compressed, brief_with_id)
                            return await _run_agent_stream(
                                task_messages, _ws_send, ticket_id, request_start,
                                task_label=task["brief"][:60],
                            )

                        phase2_results = await asyncio.gather(*[run_phase2_task(t) for t in phase2])
                        all_outputs.extend(phase2_results)

                    output = "\n\n---\n\n".join(all_outputs)

                log.info(f"[{ticket_id[:8]}] Output: {len(output)} chars. Saving to DB...")

                # 5. Save final output and mark completed
                assistant_msg = await db.add_message(ticket_id, "assistant", output)
                artifact_urls = _detect_all_artifacts(output, created_after=request_start)
                artifact_urls = _tag_artifacts(ticket_id, artifact_urls)
                for url in artifact_urls:
                    # Only register artifacts whose files actually exist on disk
                    if url.startswith("/reports/"):
                        file_path = config.OUTPUT_DIR / url[len("/reports/"):]
                        if not file_path.exists():
                            log.warning(f"[{ticket_id[:8]}] Artifact file not found, skipping: {url}")
                            continue
                    await db.add_artifact(ticket_id, url, assistant_msg["id"])

                # Detect failed build scripts in agent output (for retry UI)
                _failed_script_pat = re.compile(r'(build_\d{8}_\d{6}\.py)')
                script_matches = _failed_script_pat.findall(output)
                html_artifacts = [u for u in artifact_urls if u.endswith('.html')]
                if script_matches and not html_artifacts:
                    # Script was saved but no HTML produced — store for retry
                    script_name = script_matches[-1]  # most recent
                    error_path = SCRIPTS_DIR / f"{script_name}.error.json"
                    error_msg = "Script ran but produced no HTML artifact."
                    if error_path.exists():
                        try:
                            err_data = json.loads(error_path.read_text())
                            error_msg = err_data.get("error", error_msg)
                        except Exception:
                            pass
                    script_path = str(SCRIPTS_DIR / script_name)
                    await db.save_failed_script(ticket_id, script_path, error_msg)
                    log.info(f"[{ticket_id[:8]}] Failed script stored for retry: {script_name}")
                elif html_artifacts:
                    # Success — clear any previous failure
                    await db.delete_failed_script(ticket_id)

                # If a review package is present → set pending_review status
                review_urls = [u for u in artifact_urls if '/reviews/' in u and 'index.html' in u]
                if review_urls:
                    await db.create_review_package(ticket_id, review_urls[0], page_count=0)
                    log.info(f"[{ticket_id[:8]}] Review package detected → pending_review: {review_urls[0]}")
                else:
                    await db.update_ticket_status(ticket_id, "completed")
                log.info(f"[{ticket_id[:8]}] Saved: msg_id={assistant_msg['id']}, artifacts={artifact_urls}")

                await _ws_send({
                    "type": "stream_end",
                    "data": output,
                    "report_url": artifact_urls[0] if artifact_urls else None,
                    "artifact_urls": artifact_urls,
                    "message_id": assistant_msg["id"],
                })

            except Exception as e:
                tb = traceback.format_exc()
                log.error(f"[{ticket_id[:8]}] Agent error: {e}\n{tb}")
                err = _classify_error(e, "Marketing Analyst")
                await _ws_send({
                    "type": "error",
                    "error_type": err["error_type"],
                    "agent": err["agent"],
                    "message": err["message"],
                    "retryable": err["retryable"],
                    "detail": err["detail"],
                })

        except WebSocketDisconnect:
            log.info(f"[{ticket_id[:8]}] WebSocket disconnected")
            break
        except Exception as e:
            log.error(f"[{ticket_id[:8]}] Outer error: {e}")
            await _ws_send({"type": "error", "data": str(e)})
            if not ws_alive:
                break


# ─── Legacy WebSocket (backward compat) ───────────────────────────────

@app.websocket("/ws")
async def websocket_legacy(websocket: WebSocket):
    """Legacy WebSocket without ticket system — creates an auto-ticket."""
    await websocket.accept()
    if not await require_session(websocket):
        return

    # Auto-create a ticket for legacy connections
    ticket = await db.create_ticket("Quick Analysis", "Anonymous")
    ticket_id = ticket["id"]

    # Send ticket info so UI can track it
    await websocket.send_json({"type": "ticket_created", "ticket": ticket})

    history = []
    ws_alive = True

    async def _ws_send(payload: dict):
        nonlocal ws_alive
        if not ws_alive:
            return
        try:
            await websocket.send_json(payload)
        except Exception:
            ws_alive = False

    while True:
        try:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_input = msg.get("message", "")
            if not user_input:
                continue

            await db.add_message(ticket_id, "user", user_input)
            request_start = _time.time()

            try:
                # 1. Fetch and compress history
                all_messages_leg = await db.get_messages(ticket_id)
                all_messages_leg = [{"role": m["role"], "content": m["content"]} for m in all_messages_leg]
                compressed = compress_history(all_messages_leg)

                # 2. Build recent_context for decomposer
                recent_context = " | ".join(
                    f"{m['role']}: {m['content'][:200]}"
                    for m in compressed[-4:]
                    if m['role'] in ('user', 'assistant')
                )

                # 3. Decompose tasks
                tasks = await decompose_tasks(user_input, recent_context)
                log.info(f"[{ticket_id[:8]}] (legacy) Decomposed into {len(tasks)} task(s).")

                # 4. Run tasks
                if len(tasks) == 1:
                    brief_with_id = f"[ticket_id: {ticket_id}]\n\n{tasks[0]['brief']}"
                    task_messages = build_task_context(compressed, brief_with_id)
                    output = await _run_agent_stream(task_messages, _ws_send, ticket_id, request_start)
                else:
                    await _ws_send({"type": "tool_status", "label": f"🔀 Breaking into {len(tasks)} tasks..."})

                    phase1 = [t for t in tasks if t["phase"] == 1]
                    phase2 = [t for t in tasks if t["phase"] == 2]
                    all_outputs = []

                    phase1_results = []
                    for task in phase1:
                        brief_with_id = f"[ticket_id: {ticket_id}]\n\n{task['brief']}"
                        task_messages = build_task_context(compressed, brief_with_id)
                        res = await _run_agent_stream(
                            task_messages, _ws_send, ticket_id, request_start,
                            task_label=task["brief"][:60],
                        )
                        phase1_results.append(res)
                        all_outputs.append(res)

                    if phase2:
                        phase1_summary = "\n\n---\n\n".join(phase1_results) if phase1_results else ""
                        phase2_compressed = compressed.copy()
                        if phase1_summary:
                            phase2_compressed = compress_history(
                                compressed + [{"role": "assistant", "content": phase1_summary}]
                            )

                        async def run_phase2_task_leg(task, _ticket_id=ticket_id):
                            brief_with_id = f"[ticket_id: {_ticket_id}]\n\n{task['brief']}"
                            task_messages = build_task_context(phase2_compressed, brief_with_id)
                            return await _run_agent_stream(
                                task_messages, _ws_send, _ticket_id, request_start,
                                task_label=task["brief"][:60],
                            )

                        phase2_results = await asyncio.gather(*[run_phase2_task_leg(t) for t in phase2])
                        all_outputs.extend(phase2_results)

                    output = "\n\n---\n\n".join(all_outputs)

                # 5. Save and complete
                assistant_msg = await db.add_message(ticket_id, "assistant", output)
                artifact_urls = _detect_all_artifacts(output, created_after=request_start)
                artifact_urls = _tag_artifacts(ticket_id, artifact_urls)
                for url in artifact_urls:
                    if url.startswith("/reports/"):
                        file_path = config.OUTPUT_DIR / url[len("/reports/"):]
                        if not file_path.exists():
                            log.warning(f"[{ticket_id[:8]}] Artifact file not found, skipping: {url}")
                            continue
                    await db.add_artifact(ticket_id, url, assistant_msg["id"])

                # If a review package is present → set pending_review status
                review_urls = [u for u in artifact_urls if '/reviews/' in u and 'index.html' in u]
                if review_urls:
                    await db.create_review_package(ticket_id, review_urls[0], page_count=0)
                    log.info(f"[{ticket_id[:8]}] Review package detected → pending_review: {review_urls[0]}")
                else:
                    await db.update_ticket_status(ticket_id, "done")

                await _ws_send({
                    "type": "stream_end",
                    "data": output,
                    "report_url": artifact_urls[0] if artifact_urls else None,
                    "artifact_urls": artifact_urls,
                    "message_id": assistant_msg["id"],
                })

            except Exception as e:
                tb = traceback.format_exc()
                log.error(f"[{ticket_id[:8]}] (legacy) Agent error: {e}\n{tb}")
                err = _classify_error(e, "Marketing Analyst")
                await _ws_send({
                    "type": "error",
                    "error_type": err["error_type"],
                    "agent": err["agent"],
                    "message": err["message"],
                    "retryable": err["retryable"],
                    "detail": err["detail"],
                })

        except WebSocketDisconnect:
            break
        except Exception as e:
            await _ws_send({"type": "error", "data": str(e)})
            if not ws_alive:
                break
