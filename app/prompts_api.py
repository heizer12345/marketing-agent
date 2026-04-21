"""Prompt Library — view, edit and version-control agent & skill prompts."""

import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

BASE = Path(__file__).parent.parent
OVERRIDES_FILE = BASE / "data" / "prompt_overrides.json"
HISTORY_FILE   = BASE / "data" / "prompt_history.jsonl"

router = APIRouter()

# ─── Registry ────────────────────────────────────────────────────────────────
# Each entry: id (unique key), name, category, icon, file (relative to BASE), var (variable name)

PROMPT_REGISTRY = [
    # Orchestrators
    {"id": "intent_router",           "name": "CEO / Intent Router",       "category": "Orchestrators", "icon": "🎯", "file": "skills/intent_router.py",           "var": "INSTRUCTIONS"},
    {"id": "project_manager",         "name": "Project Manager",            "category": "Orchestrators", "icon": "📋", "file": "skills/project_manager.py",         "var": "INSTRUCTIONS"},

    # Analysis
    {"id": "marketing_data_analyst",  "name": "Marketing Data Analyst",     "category": "Analysis",      "icon": "📊", "file": "skills/marketing_data_analyst.py",  "var": "INSTRUCTIONS"},
    {"id": "synthesis_agent",         "name": "Synthesis Agent",            "category": "Analysis",      "icon": "🔬", "file": "skills/synthesis_agent.py",         "var": "INSTRUCTIONS"},
    {"id": "traffic_analyst",         "name": "Traffic Analyst",            "category": "Analysis",      "icon": "🌐", "file": "skills/traffic_analyst.py",         "var": "INSTRUCTIONS"},
    {"id": "paid_organic_overlap",    "name": "Paid / Organic Overlap",     "category": "Analysis",      "icon": "🔗", "file": "skills/paid_organic_overlap.py",    "var": "INSTRUCTIONS"},

    # Specialists
    {"id": "seo_analyst",             "name": "SEO Analyst",                "category": "Specialists",   "icon": "🔍", "file": "skills/seo_analyst.py",             "var": "INSTRUCTIONS"},
    {"id": "socials_analyst",         "name": "Social Media Analyst",       "category": "Specialists",   "icon": "📱", "file": "skills/socials_analyst.py",         "var": "INSTRUCTIONS"},
    {"id": "geo_aeo_analyst",         "name": "GEO / AEO Analyst",          "category": "Specialists",   "icon": "🤖", "file": "skills/geo_aeo_analyst.py",         "var": "INSTRUCTIONS"},
    {"id": "competitor_analyst",      "name": "Competitor Analyst",         "category": "Specialists",   "icon": "⚔️", "file": "skills/competitor_analyst.py",      "var": "INSTRUCTIONS"},
    {"id": "knowledge_expert",        "name": "Knowledge Expert",           "category": "Specialists",   "icon": "📚", "file": "skills/knowledge_expert.py",        "var": "INSTRUCTIONS"},

    # Content
    {"id": "content_engine",          "name": "Content Engine",             "category": "Content",       "icon": "✍️", "file": "skills/content_engine.py",          "var": "INSTRUCTIONS"},
    {"id": "recommendation_engine",   "name": "Recommendation Engine",      "category": "Content",       "icon": "💡", "file": "skills/recommendation_engine.py",   "var": "INSTRUCTIONS"},
    {"id": "report_builder",          "name": "Report Builder",             "category": "Content",       "icon": "📄", "file": "skills/report_builder.py",          "var": "INSTRUCTIONS"},
    {"id": "website_overhaul_agent",  "name": "Website Overhaul",           "category": "Content",       "icon": "🏗️", "file": "skills/website_overhaul_agent.py",  "var": "INSTRUCTIONS"},

    # Shared Blocks (skills/prompts/sourcy_context.py)
    {"id": "sourcy_business_context", "name": "Sourcy Business Context",    "category": "Shared Blocks", "icon": "🏢", "file": "skills/prompts/sourcy_context.py", "var": "SOURCY_BUSINESS_CONTEXT"},
    {"id": "so_what_instructions",    "name": "So-What Instructions",       "category": "Shared Blocks", "icon": "❓", "file": "skills/prompts/sourcy_context.py", "var": "SO_WHAT_INSTRUCTIONS"},
    {"id": "simple_language_rules",   "name": "Simple Language Rules",      "category": "Shared Blocks", "icon": "📝", "file": "skills/prompts/sourcy_context.py", "var": "SIMPLE_LANGUAGE_RULES"},
    {"id": "root_cause_reasoning",    "name": "Root Cause Reasoning",       "category": "Shared Blocks", "icon": "🔎", "file": "skills/prompts/sourcy_context.py", "var": "ROOT_CAUSE_REASONING"},
    {"id": "diagnostic_output",       "name": "Diagnostic Output Standard", "category": "Shared Blocks", "icon": "📐", "file": "skills/prompts/sourcy_context.py", "var": "DIAGNOSTIC_OUTPUT_STANDARD"},
    {"id": "message_alignment",       "name": "Message Alignment Framework","category": "Shared Blocks", "icon": "🎯", "file": "skills/prompts/sourcy_context.py", "var": "MESSAGE_ALIGNMENT_FRAMEWORK"},
    {"id": "channel_controllability", "name": "Channel Controllability",    "category": "Shared Blocks", "icon": "🎛️", "file": "skills/prompts/sourcy_context.py", "var": "CHANNEL_CONTROLLABILITY_RULES"},
    {"id": "target_countries",        "name": "Target Countries Block",     "category": "Shared Blocks", "icon": "🌍", "file": "skills/prompts/sourcy_context.py", "var": "TARGET_COUNTRIES_BLOCK"},
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _extract_var(file_rel: str, var_name: str) -> str:
    """Extract a string variable's content from a Python source file."""
    try:
        source = (BASE / file_rel).read_text(encoding="utf-8")
        # Match triple-double-quote strings (f-string or plain)
        pattern = rf'{re.escape(var_name)}\s*=\s*f?"""(.*?)"""'
        m = re.search(pattern, source, re.DOTALL)
        if m:
            return m.group(1)
        # Fallback: triple-single-quote
        pattern = rf"{re.escape(var_name)}\s*=\s*f?'''(.*?)'''"
        m = re.search(pattern, source, re.DOTALL)
        if m:
            return m.group(1)
    except Exception:
        pass
    return f"[Could not read {var_name} from {file_rel}]"


def _load_overrides() -> dict:
    if OVERRIDES_FILE.exists():
        try:
            return json.loads(OVERRIDES_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_overrides(overrides: dict):
    OVERRIDES_FILE.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDES_FILE.write_text(json.dumps(overrides, indent=2, ensure_ascii=False))


def _append_history(entry: dict):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _registry_by_id(prompt_id: str) -> dict | None:
    return next((p for p in PROMPT_REGISTRY if p["id"] == prompt_id), None)


# ─── API Routes ───────────────────────────────────────────────────────────────

@router.get("/api/prompts", response_class=JSONResponse)
async def list_prompts():
    overrides = _load_overrides()
    result = []
    for p in PROMPT_REGISTRY:
        original = _extract_var(p["file"], p["var"])
        is_overridden = p["id"] in overrides
        result.append({
            "id":           p["id"],
            "name":         p["name"],
            "category":     p["category"],
            "icon":         p["icon"],
            "file":         p["file"],
            "var":          p["var"],
            "content":      overrides[p["id"]] if is_overridden else original,
            "original":     original,
            "is_overridden": is_overridden,
        })
    return result


@router.put("/api/prompts/{prompt_id}", response_class=JSONResponse)
async def save_prompt(prompt_id: str, request: Request):
    body = await request.json()
    new_content = body.get("content", "")

    p = _registry_by_id(prompt_id)
    if not p:
        return JSONResponse({"error": "Prompt not found"}, status_code=404)

    overrides = _load_overrides()
    old_content = overrides.get(prompt_id, _extract_var(p["file"], p["var"]))

    overrides[prompt_id] = new_content
    _save_overrides(overrides)

    _append_history({
        "timestamp":   datetime.utcnow().isoformat() + "Z",
        "prompt_id":   prompt_id,
        "name":        p["name"],
        "action":      "edit",
        "old_len":     len(old_content),
        "new_len":     len(new_content),
        "old_preview": old_content[:120].strip(),
        "new_preview": new_content[:120].strip(),
    })

    return {"success": True, "is_overridden": True}


@router.post("/api/prompts/{prompt_id}/restore", response_class=JSONResponse)
async def restore_prompt(prompt_id: str):
    p = _registry_by_id(prompt_id)
    if not p:
        return JSONResponse({"error": "Prompt not found"}, status_code=404)

    overrides = _load_overrides()
    if prompt_id in overrides:
        removed = overrides.pop(prompt_id)
        _save_overrides(overrides)
        _append_history({
            "timestamp":   datetime.utcnow().isoformat() + "Z",
            "prompt_id":   prompt_id,
            "name":        p["name"],
            "action":      "restore",
            "old_preview": removed[:120].strip(),
        })

    original = _extract_var(p["file"], p["var"])
    return {"success": True, "content": original, "is_overridden": False}


@router.get("/api/prompts/history", response_class=JSONResponse)
async def get_history():
    if not HISTORY_FILE.exists():
        return []
    entries = []
    for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return list(reversed(entries))  # newest first


# ─── Page ─────────────────────────────────────────────────────────────────────

@router.get("/prompts", response_class=HTMLResponse)
async def prompts_page():
    return HTMLResponse(_render_page())


def _render_page() -> str:
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prompt Library — Sourcy</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --blue:      #2563eb;
    --blue-lt:   #eff6ff;
    --green:     #16a34a;
    --green-lt:  #f0fdf4;
    --amber:     #d97706;
    --amber-lt:  #fffbeb;
    --red:       #dc2626;
    --gray-50:   #f9fafb;
    --gray-100:  #f3f4f6;
    --gray-200:  #e5e7eb;
    --gray-300:  #d1d5db;
    --gray-400:  #9ca3af;
    --gray-500:  #6b7280;
    --gray-600:  #4b5563;
    --gray-700:  #374151;
    --gray-900:  #111827;
    --radius:    8px;
    --sidebar-w: 260px;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--gray-50);
    color: var(--gray-900);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* ── Top bar ── */
  .topbar {
    height: 52px;
    background: #fff;
    border-bottom: 1px solid var(--gray-200);
    display: flex;
    align-items: center;
    padding: 0 20px;
    gap: 12px;
    flex-shrink: 0;
    z-index: 10;
  }
  .back-btn {
    display: flex; align-items: center; gap: 6px;
    font-size: 13px; color: var(--gray-500);
    text-decoration: none; padding: 5px 10px;
    border-radius: 6px; border: 1px solid var(--gray-200);
    background: #fff; transition: background 0.15s;
  }
  .back-btn:hover { background: var(--gray-100); color: var(--gray-700); }
  .topbar-title { font-size: 15px; font-weight: 700; color: var(--gray-900); }
  .topbar-sub   { font-size: 12px; color: var(--gray-400); }
  .topbar-spacer { flex: 1; }
  .search-box {
    display: flex; align-items: center; gap: 8px;
    background: var(--gray-100); border-radius: 8px;
    padding: 6px 12px; border: 1px solid transparent;
    transition: border 0.15s;
  }
  .search-box:focus-within { border-color: var(--blue); background: #fff; }
  .search-box input {
    border: none; background: transparent; font-size: 13px;
    color: var(--gray-700); outline: none; width: 180px;
  }
  .search-box svg { color: var(--gray-400); flex-shrink: 0; }

  /* ── Layout ── */
  .layout {
    flex: 1;
    display: flex;
    overflow: hidden;
  }

  /* ── Sidebar ── */
  .sidebar {
    width: var(--sidebar-w);
    flex-shrink: 0;
    background: #fff;
    border-right: 1px solid var(--gray-200);
    overflow-y: auto;
    padding: 12px 0;
  }
  .sidebar-section { padding: 0; }
  .sidebar-section-title {
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.07em; color: var(--gray-400);
    padding: 12px 16px 4px;
  }
  .sidebar-item {
    display: flex; align-items: center; gap: 9px;
    padding: 8px 16px; cursor: pointer;
    font-size: 13px; color: var(--gray-700);
    border-left: 3px solid transparent;
    transition: background 0.12s, border-color 0.12s;
    user-select: none;
  }
  .sidebar-item:hover  { background: var(--gray-50); color: var(--gray-900); }
  .sidebar-item.active { background: var(--blue-lt); color: var(--blue);
    border-left-color: var(--blue); font-weight: 600; }
  .sidebar-item .dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--gray-300); flex-shrink: 0; margin-left: auto;
  }
  .sidebar-item.modified .dot { background: var(--amber); }
  .sidebar-item.active .dot { background: var(--blue); }
  .sidebar-item.active.modified .dot { background: var(--amber); }
  .item-icon { font-size: 14px; flex-shrink: 0; width: 18px; text-align: center; }
  .item-name { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* ── Editor panel ── */
  .editor-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: #fff;
  }

  .editor-header {
    padding: 16px 24px 12px;
    border-bottom: 1px solid var(--gray-200);
    flex-shrink: 0;
  }
  .editor-header-row {
    display: flex; align-items: center; gap: 10px; margin-bottom: 6px;
  }
  .editor-title { font-size: 17px; font-weight: 700; }
  .badge {
    font-size: 11px; font-weight: 600; padding: 2px 8px;
    border-radius: 4px; white-space: nowrap;
  }
  .badge-modified { background: var(--amber-lt); color: var(--amber); }
  .badge-original { background: var(--green-lt);  color: var(--green); }
  .editor-meta { font-size: 12px; color: var(--gray-400); }

  .editor-actions {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 24px;
    border-bottom: 1px solid var(--gray-200);
    flex-shrink: 0;
    flex-wrap: wrap;
  }
  .btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 14px; border-radius: 6px; border: 1px solid var(--gray-200);
    font-size: 13px; font-weight: 500; cursor: pointer;
    background: #fff; color: var(--gray-700); transition: all 0.15s;
    white-space: nowrap;
  }
  .btn:hover  { background: var(--gray-100); border-color: var(--gray-300); }
  .btn:active { transform: scale(0.98); }
  .btn-primary { background: var(--blue); color: #fff; border-color: var(--blue); }
  .btn-primary:hover { background: #1d4ed8; border-color: #1d4ed8; }
  .btn-danger  { background: #fff; color: var(--red); border-color: #fca5a5; }
  .btn-danger:hover { background: #fef2f2; }
  .btn-ghost   { border-color: transparent; color: var(--gray-500); }
  .btn-ghost:hover { background: var(--gray-100); }
  .btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
  .save-msg { font-size: 12px; color: var(--green); font-weight: 500; }

  /* ── Textarea ── */
  .editor-body {
    flex: 1; overflow: hidden; display: flex; flex-direction: column;
    padding: 0;
  }
  .prompt-display, .prompt-edit {
    flex: 1; overflow-y: auto; padding: 20px 24px;
    font-size: 13.5px; line-height: 1.7; color: var(--gray-700);
    white-space: pre-wrap; word-break: break-word;
    font-family: "SF Mono", "Fira Code", Consolas, monospace;
    background: var(--gray-50);
  }
  .prompt-edit {
    border: none; outline: none; resize: none;
    width: 100%; background: #fff;
    border-top: 2px solid var(--blue);
  }

  /* ── Empty state ── */
  .empty-state {
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    color: var(--gray-400); gap: 12px; padding: 40px;
    text-align: center;
  }
  .empty-state svg { opacity: 0.3; }
  .empty-state p { font-size: 14px; max-width: 280px; line-height: 1.5; }

  /* ── History panel (slide-in) ── */
  .history-overlay {
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.3); z-index: 100;
  }
  .history-overlay.open { display: flex; justify-content: flex-end; }
  .history-panel {
    width: 420px; max-width: 100vw; height: 100vh;
    background: #fff; display: flex; flex-direction: column;
    box-shadow: -4px 0 24px rgba(0,0,0,0.12);
  }
  .history-header {
    padding: 16px 20px; border-bottom: 1px solid var(--gray-200);
    display: flex; align-items: center; justify-content: space-between;
    flex-shrink: 0;
  }
  .history-header h3 { font-size: 15px; font-weight: 700; }
  .history-close {
    width: 28px; height: 28px; border-radius: 6px; border: none;
    background: var(--gray-100); cursor: pointer; font-size: 16px;
    display: flex; align-items: center; justify-content: center;
  }
  .history-close:hover { background: var(--gray-200); }
  .history-list { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
  .history-entry {
    border: 1px solid var(--gray-200); border-radius: 8px; padding: 12px;
    font-size: 12px; cursor: pointer; transition: border-color 0.15s;
  }
  .history-entry:hover { border-color: var(--blue); background: var(--blue-lt); }
  .history-entry-header {
    display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
  }
  .history-action {
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    padding: 2px 7px; border-radius: 4px;
  }
  .action-edit    { background: var(--blue-lt);  color: var(--blue); }
  .action-restore { background: var(--green-lt); color: var(--green); }
  .history-ts     { font-size: 11px; color: var(--gray-400); margin-left: auto; }
  .history-preview {
    color: var(--gray-500); font-family: monospace;
    white-space: pre-wrap; word-break: break-all; font-size: 11px;
    border-left: 3px solid var(--gray-200); padding-left: 8px; margin-top: 4px;
  }
  .history-empty { text-align: center; color: var(--gray-400); font-size: 13px; padding: 40px 16px; }

  /* ── Toast ── */
  .toast {
    position: fixed; bottom: 24px; right: 24px;
    background: var(--gray-900); color: #fff;
    padding: 10px 18px; border-radius: 8px; font-size: 13px;
    opacity: 0; transform: translateY(8px);
    transition: all 0.2s; z-index: 9999; pointer-events: none;
  }
  .toast.show { opacity: 1; transform: translateY(0); }
  .toast.error { background: var(--red); }
</style>
</head>
<body>

<!-- Top Bar -->
<div class="topbar">
  <a href="/" class="back-btn">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 5l-7 7 7 7"/></svg>
    Board
  </a>
  <div>
    <div class="topbar-title">🤖 Prompt Library</div>
    <div class="topbar-sub">Edit agent instructions · changes saved to overrides file</div>
  </div>
  <div class="topbar-spacer"></div>
  <div class="search-box">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    <input id="searchInput" type="text" placeholder="Search prompts…" oninput="filterSidebar(this.value)">
  </div>
</div>

<!-- Main Layout -->
<div class="layout">

  <!-- Sidebar -->
  <nav class="sidebar" id="sidebar">
    <div id="sidebarContent"><!-- injected by JS --></div>
  </nav>

  <!-- Editor -->
  <div class="editor-panel" id="editorPanel">
    <div class="empty-state" id="emptyState">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
      <p>Select a prompt from the sidebar to view and edit it</p>
    </div>

    <div id="editorContent" style="display:none;flex:1;flex-direction:column;overflow:hidden;display:none">
      <div class="editor-header">
        <div class="editor-header-row">
          <span id="editorIcon" style="font-size:18px"></span>
          <span class="editor-title" id="editorTitle"></span>
          <span id="editorBadge" class="badge badge-original">Original</span>
        </div>
        <div class="editor-meta" id="editorMeta"></div>
      </div>
      <div class="editor-actions">
        <button class="btn" id="editBtn" onclick="startEdit()">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          Edit
        </button>
        <button class="btn btn-primary" id="saveBtn" onclick="savePrompt()" style="display:none" disabled>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          Save Changes
        </button>
        <button class="btn" id="cancelBtn" onclick="cancelEdit()" style="display:none">Cancel</button>
        <button class="btn btn-danger" id="restoreBtn" onclick="restorePrompt()">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
          Restore Original
        </button>
        <div class="topbar-spacer"></div>
        <button class="btn btn-ghost" id="historyBtn" onclick="openHistory()">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          History
        </button>
        <span class="save-msg" id="saveMsg" style="display:none"></span>
      </div>
      <div class="editor-body">
        <pre class="prompt-display" id="promptDisplay"></pre>
        <textarea class="prompt-edit" id="promptEdit" style="display:none"
          oninput="onEditInput()" spellcheck="false"></textarea>
      </div>
    </div>
  </div>

</div>

<!-- History Panel -->
<div class="history-overlay" id="historyOverlay" onclick="if(event.target===this)closeHistory()">
  <div class="history-panel">
    <div class="history-header">
      <h3>📜 Edit History</h3>
      <button class="history-close" onclick="closeHistory()">✕</button>
    </div>
    <div class="history-list" id="historyList"></div>
  </div>
</div>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
'use strict';

let allPrompts   = [];   // loaded from /api/prompts
let activeId     = null; // currently selected prompt id
let isEditing    = false;
let originalContent = ''; // content before edit started

// ── Boot ──────────────────────────────────────────────────────────────────
async function boot() {
  const res = await fetch('/api/prompts');
  allPrompts = await res.json();
  renderSidebar(allPrompts);
  // Auto-select first item
  if (allPrompts.length > 0) selectPrompt(allPrompts[0].id);
}

// ── Sidebar ───────────────────────────────────────────────────────────────
function renderSidebar(prompts) {
  const groups = {};
  prompts.forEach(p => {
    if (!groups[p.category]) groups[p.category] = [];
    groups[p.category].push(p);
  });

  let html = '';
  for (const [cat, items] of Object.entries(groups)) {
    html += `<div class="sidebar-section">
      <div class="sidebar-section-title">${cat}</div>`;
    items.forEach(p => {
      const modClass = p.is_overridden ? ' modified' : '';
      html += `<div class="sidebar-item${modClass}" id="item-${p.id}" onclick="selectPrompt('${p.id}')">
        <span class="item-icon">${p.icon}</span>
        <span class="item-name">${p.name}</span>
        <span class="dot" title="${p.is_overridden ? 'Modified' : 'Original'}"></span>
      </div>`;
    });
    html += `</div>`;
  }
  document.getElementById('sidebarContent').innerHTML = html;
}

function filterSidebar(q) {
  const filtered = q
    ? allPrompts.filter(p =>
        p.name.toLowerCase().includes(q.toLowerCase()) ||
        p.category.toLowerCase().includes(q.toLowerCase()))
    : allPrompts;
  renderSidebar(filtered);
  // Re-highlight active
  if (activeId) {
    const el = document.getElementById('item-' + activeId);
    if (el) el.classList.add('active');
  }
}

// ── Select ────────────────────────────────────────────────────────────────
function selectPrompt(id) {
  if (isEditing && activeId !== id) {
    if (!confirm('You have unsaved changes. Discard and switch?')) return;
    cancelEdit(true);
  }
  activeId = id;

  // Sidebar highlight
  document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
  const item = document.getElementById('item-' + id);
  if (item) item.classList.add('active');

  const p = allPrompts.find(x => x.id === id);
  if (!p) return;

  // Header
  document.getElementById('emptyState').style.display = 'none';
  const ec = document.getElementById('editorContent');
  ec.style.display = 'flex';
  ec.style.flexDirection = 'column';
  ec.style.flex = '1';
  ec.style.overflow = 'hidden';

  document.getElementById('editorIcon').textContent  = p.icon;
  document.getElementById('editorTitle').textContent = p.name;
  document.getElementById('editorMeta').textContent  =
    `${p.file}  ·  ${p.var}  ·  ${p.content.trim().split('\n').length} lines`;

  // Badge
  const badge = document.getElementById('editorBadge');
  if (p.is_overridden) {
    badge.textContent = '✏️ Modified';
    badge.className = 'badge badge-modified';
  } else {
    badge.textContent = '✓ Original';
    badge.className = 'badge badge-original';
  }

  // Content
  document.getElementById('promptDisplay').textContent = p.content;
  document.getElementById('promptEdit').value          = p.content;

  // Restore button only if modified
  document.getElementById('restoreBtn').style.display = p.is_overridden ? 'inline-flex' : 'none';

  // Reset edit state
  isEditing = false;
  document.getElementById('promptDisplay').style.display = 'block';
  document.getElementById('promptEdit').style.display    = 'none';
  document.getElementById('editBtn').style.display   = 'inline-flex';
  document.getElementById('saveBtn').style.display   = 'none';
  document.getElementById('cancelBtn').style.display = 'none';
  document.getElementById('saveMsg').style.display   = 'none';
}

// ── Edit ──────────────────────────────────────────────────────────────────
function startEdit() {
  isEditing = true;
  originalContent = document.getElementById('promptEdit').value;

  document.getElementById('promptDisplay').style.display = 'none';
  document.getElementById('promptEdit').style.display    = 'block';
  document.getElementById('promptEdit').focus();

  document.getElementById('editBtn').style.display   = 'none';
  document.getElementById('saveBtn').style.display   = 'inline-flex';
  document.getElementById('cancelBtn').style.display = 'inline-flex';
  document.getElementById('saveBtn').disabled = true; // no changes yet
}

function onEditInput() {
  const current = document.getElementById('promptEdit').value;
  document.getElementById('saveBtn').disabled = (current === originalContent);
}

function cancelEdit(silent = false) {
  if (!silent && isEditing) {
    const current = document.getElementById('promptEdit').value;
    if (current !== originalContent && !confirm('Discard unsaved changes?')) return;
  }
  isEditing = false;
  document.getElementById('promptEdit').value = originalContent;

  document.getElementById('promptDisplay').style.display = 'block';
  document.getElementById('promptEdit').style.display    = 'none';
  document.getElementById('editBtn').style.display   = 'inline-flex';
  document.getElementById('saveBtn').style.display   = 'none';
  document.getElementById('cancelBtn').style.display = 'none';
}

// ── Save ──────────────────────────────────────────────────────────────────
async function savePrompt() {
  const newContent = document.getElementById('promptEdit').value;
  const res = await fetch(`/api/prompts/${activeId}`, {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({content: newContent}),
  });
  if (!res.ok) { toast('Save failed', true); return; }

  // Update local cache
  const p = allPrompts.find(x => x.id === activeId);
  if (p) { p.content = newContent; p.is_overridden = true; }

  // Update UI
  document.getElementById('promptDisplay').textContent = newContent;
  const badge = document.getElementById('editorBadge');
  badge.textContent = '✏️ Modified';
  badge.className   = 'badge badge-modified';
  document.getElementById('restoreBtn').style.display = 'inline-flex';

  // Update sidebar dot
  const item = document.getElementById('item-' + activeId);
  if (item) item.classList.add('modified');

  isEditing = false;
  document.getElementById('promptDisplay').style.display = 'block';
  document.getElementById('promptEdit').style.display    = 'none';
  document.getElementById('editBtn').style.display   = 'inline-flex';
  document.getElementById('saveBtn').style.display   = 'none';
  document.getElementById('cancelBtn').style.display = 'none';

  toast('✓ Saved — takes effect on next deploy');
}

// ── Restore ───────────────────────────────────────────────────────────────
async function restorePrompt() {
  const p = allPrompts.find(x => x.id === activeId);
  if (!p) return;
  if (!confirm(`Restore "${p.name}" to its original (committed) version? This cannot be undone.`)) return;

  const res = await fetch(`/api/prompts/${activeId}/restore`, {method: 'POST'});
  if (!res.ok) { toast('Restore failed', true); return; }
  const data = await res.json();

  p.content = data.content; p.is_overridden = false;

  document.getElementById('promptDisplay').textContent = data.content;
  document.getElementById('promptEdit').value          = data.content;
  const badge = document.getElementById('editorBadge');
  badge.textContent = '✓ Original'; badge.className = 'badge badge-original';
  document.getElementById('restoreBtn').style.display = 'none';

  const item = document.getElementById('item-' + activeId);
  if (item) item.classList.remove('modified');

  toast('✓ Restored to original');
}

// ── History ───────────────────────────────────────────────────────────────
async function openHistory() {
  const res = await fetch('/api/prompts/history');
  const history = await res.json();

  const list = document.getElementById('historyList');
  if (history.length === 0) {
    list.innerHTML = '<div class="history-empty">No changes recorded yet.</div>';
  } else {
    list.innerHTML = history.map(e => {
      const d   = new Date(e.timestamp);
      const ts  = d.toLocaleString('en-GB', {day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
      const cls = e.action === 'restore' ? 'action-restore' : 'action-edit';
      const lbl = e.action === 'restore' ? 'Restore' : 'Edit';
      const preview = e.action === 'edit'
        ? `<div class="history-preview">${esc(e.new_preview || '')}…</div>`
        : `<div class="history-preview" style="border-color:#bbf7d0">Restored to original</div>`;
      return `<div class="history-entry" onclick="loadHistoryEntry('${e.prompt_id}','${esc(e.new_preview||'')}')">
        <div class="history-entry-header">
          <span class="history-action ${cls}">${lbl}</span>
          <strong style="font-size:12px">${esc(e.name)}</strong>
          <span class="history-ts">${ts}</span>
        </div>
        ${preview}
      </div>`;
    }).join('');
  }

  document.getElementById('historyOverlay').classList.add('open');
}

function loadHistoryEntry(promptId) {
  closeHistory();
  selectPrompt(promptId);
}

function closeHistory() {
  document.getElementById('historyOverlay').classList.remove('open');
}

// ── Toast ─────────────────────────────────────────────────────────────────
function toast(msg, isError = false) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show' + (isError ? ' error' : '');
  setTimeout(() => el.classList.remove('show'), 3000);
}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                  .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ── Keyboard shortcut: Cmd/Ctrl+S to save ────────────────────────────────
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 's' && isEditing) {
    e.preventDefault();
    if (!document.getElementById('saveBtn').disabled) savePrompt();
  }
  if (e.key === 'Escape' && isEditing) cancelEdit();
});

boot();
</script>
</body>
</html>
"""
