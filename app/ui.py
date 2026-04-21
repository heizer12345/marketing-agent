"""Web UI — Kanban board with ticket popup (chat + artifact split view)."""


def get_ui_html(status_ga4: bool, status_sc: bool, status_ads: bool,
                 status_semrush: bool, status_meta: bool = False,
                 status_ig: bool = False, status_posthog: bool = False) -> str:
    def pill(name: str, on: bool) -> str:
        cls = "on" if on else "off"
        return f'<span class="status-pill {cls}">{name}</span>'

    pills = (
        pill("GA4", status_ga4)
        + pill("Search Console", status_sc)
        + pill("Google Ads", status_ads)
        + pill("Meta Ads", status_meta)
        + pill("Instagram", status_ig)
        + pill("PostHog", status_posthog)
        + pill("SEMrush", status_semrush)
    )

    return r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sourcy Marketing Analyst</title>
    <style>
        :root {
            --navy: #0f172a; --navy-light: #1e293b; --navy-mid: #162033;
            --blue: #3b82f6; --blue-hover: #2563eb; --blue-light: #eff6ff;
            --gray-50: #f8fafc; --gray-100: #f1f5f9; --gray-200: #e2e8f0;
            --gray-300: #cbd5e1; --gray-400: #94a3b8; --gray-500: #64748b;
            --gray-600: #475569; --gray-700: #334155; --gray-800: #1e293b;
            --green: #10b981; --yellow: #f59e0b; --red: #ef4444;
            --radius: 10px;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            background:var(--gray-50); color:var(--gray-800); min-height:100vh; }

        /* ── Top Nav ── */
        .topnav { background:var(--navy); padding:12px 24px; display:flex; align-items:center; gap:16px;
            position:sticky; top:0; z-index:100; }
        .topnav-logo { color:#fff; font-weight:700; font-size:16px; }
        .topnav-logo span { color:var(--blue); }
        .topnav-spacer { flex:1; }
        .topnav .status-pills { display:flex; gap:4px; }
        .status-pill { font-size:10px; padding:2px 8px; border-radius:10px; font-weight:500; }
        .status-pill.on { background:rgba(16,185,129,0.2); color:#10b981; }
        .status-pill.off { background:rgba(255,255,255,0.05); color:var(--gray-500); }
        .user-select { background:var(--navy-light); color:#fff; border:1px solid rgba(255,255,255,0.1);
            border-radius:6px; padding:5px 10px; font-size:12px; cursor:pointer; }
        .arch-btn { display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.06);
            color:#94a3b8; border:1px solid rgba(255,255,255,0.1); border-radius:6px;
            padding:5px 12px; font-size:12px; font-weight:500; text-decoration:none;
            transition:all .2s; white-space:nowrap; }
        .arch-btn:hover { background:rgba(255,255,255,0.1); color:#fff; border-color:rgba(255,255,255,0.2); }

        /* ── Create Ticket Bar ── */
        .create-bar { max-width:1200px; margin:20px auto; padding:0 24px; }
        .create-card { background:#fff; border-radius:var(--radius); padding:16px 20px;
            box-shadow:0 1px 3px rgba(0,0,0,.06); display:flex; gap:12px; align-items:flex-start; }
        .create-card textarea { flex:1; border:1px solid var(--gray-200); border-radius:8px;
            padding:10px 14px; font-size:14px; font-family:inherit; resize:none; min-height:44px;
            max-height:80px; outline:none; }
        .create-card textarea:focus { border-color:var(--blue); }
        .create-btn { background:var(--blue); color:#fff; border:none; border-radius:8px;
            padding:10px 20px; font-size:13px; font-weight:600; cursor:pointer; white-space:nowrap; }
        .create-btn:hover { background:var(--blue-hover); }

        /* ── Kanban Board ── */
        .kanban { max-width:1200px; margin:0 auto; padding:0 24px 40px;
            display:grid; grid-template-columns:1fr 1fr 1fr; gap:20px; }
        .kanban-col { background:var(--gray-100); border-radius:var(--radius); padding:12px;
            min-height:200px; }
        .kanban-col-header { font-size:12px; font-weight:700; text-transform:uppercase;
            letter-spacing:0.05em; padding:8px 8px 12px; display:flex; align-items:center; gap:8px; }
        .kanban-col-header .count { background:var(--gray-200); color:var(--gray-600);
            font-size:11px; padding:1px 8px; border-radius:10px; }
        .col-open .kanban-col-header { color:var(--blue); }
        .col-active .kanban-col-header { color:#d97706; }
        .col-done .kanban-col-header { color:var(--green); }

        /* ── Ticket Cards ── */
        .ticket-card { background:#fff; border-radius:8px; padding:14px 16px; margin-bottom:8px;
            cursor:pointer; border:1px solid var(--gray-200); transition:all 0.15s; }
        .ticket-card:hover { border-color:var(--blue); box-shadow:0 2px 8px rgba(59,130,246,0.12); transform:translateY(-1px); }
        .tc-title { font-size:14px; font-weight:600; color:var(--gray-800); margin-bottom:6px;
            white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .tc-preview { font-size:12px; color:var(--gray-500); margin-bottom:8px;
            display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; line-height:1.4; }
        .tc-meta { display:flex; align-items:center; gap:6px; font-size:11px; color:var(--gray-400); }
        .tc-avatar { width:20px; height:20px; border-radius:50%; background:var(--blue-light);
            color:var(--blue); display:flex; align-items:center; justify-content:center;
            font-size:10px; font-weight:700; flex-shrink:0; }
        .tc-badge { font-size:10px; padding:2px 6px; border-radius:4px; font-weight:500; }
        .tc-badge.has-artifact { background:#ecfdf5; color:var(--green); }
        .tc-badge.waiting { background:#fef3c7; color:#d97706; }
        .tc-badge.waiting::before { content:''; display:inline-block; width:6px; height:6px;
            border-radius:50%; background:#d97706; margin-right:4px; animation:pulse 1.5s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

        /* ── Fullscreen Popup ── */
        .popup-overlay { display:none; position:fixed; inset:0; z-index:200;
            background:rgba(0,0,0,0.5); backdrop-filter:blur(2px); }
        .popup-overlay.open { display:flex; }
        .popup { width:95vw; height:92vh; margin:auto; background:#fff;
            border-radius:12px; display:flex; flex-direction:column; overflow:hidden;
            box-shadow:0 20px 60px rgba(0,0,0,0.3); }

        /* Popup Header */
        .popup-header { padding:12px 20px; border-bottom:1px solid var(--gray-200);
            display:flex; align-items:center; gap:12px; background:var(--gray-50); flex-shrink:0; }
        .popup-title { font-size:15px; font-weight:600; flex:1; }
        .popup-status { font-size:12px; padding:4px 10px; border-radius:6px; border:1px solid var(--gray-200);
            background:#fff; cursor:pointer; }
        .popup-close { width:32px; height:32px; border:none; background:var(--gray-100);
            border-radius:8px; cursor:pointer; font-size:18px; color:var(--gray-500);
            display:flex; align-items:center; justify-content:center; }
        .popup-close:hover { background:var(--gray-200); }

        /* Popup Body: Split View */
        .popup-body { flex:1; display:flex; overflow:hidden; }

        /* Chat Panel (Left) — expands to full width when no artifact */
        .chat-panel { width:42%; display:flex; flex-direction:column; border-right:1px solid var(--gray-200);
            transition:width 0.3s ease; }
        .popup-body.no-artifact .chat-panel { width:100%; border-right:none; }
        .chat-messages { flex:1; overflow-y:auto; padding:16px; }
        .chat-empty-state { display:flex; flex-direction:column; align-items:center; justify-content:center;
            height:100%; color:var(--gray-400); font-size:13px; }

        .msg { margin-bottom:20px; max-width:92%; }
        .msg.user { margin-left:auto; }
        .msg.assistant { margin-right:auto; max-width:100%; }
        .msg-header { font-size:10px; color:var(--gray-400); margin-bottom:4px; font-weight:500;
            display:flex; align-items:center; gap:6px; }
        .msg.user .msg-header { justify-content:flex-end; }
        .msg-bubble { padding:10px 14px; border-radius:12px; font-size:13px; line-height:1.6; }
        .msg.user .msg-bubble { background:var(--blue); color:#fff; border-bottom-right-radius:4px; }

        /* Assistant bubble — Claude.ai style: clean white, no background box */
        .msg.assistant .msg-bubble { background:transparent; color:var(--gray-800); padding:2px 0;
            font-size:14px; line-height:1.75; }

        /* Typography — scannable, high-contrast headings */
        .msg.assistant .msg-bubble h1 { font-size:18px; font-weight:700; color:var(--navy); margin:20px 0 8px;
            padding-bottom:6px; border-bottom:2px solid var(--gray-200); }
        .msg.assistant .msg-bubble h2 { font-size:16px; font-weight:700; color:var(--navy); margin:20px 0 6px;
            padding-bottom:4px; border-bottom:1px solid var(--gray-200); }
        .msg.assistant .msg-bubble h3 { font-size:14px; font-weight:700; color:var(--gray-700); margin:16px 0 4px; }
        .msg.assistant .msg-bubble h4 { font-size:13px; font-weight:600; color:var(--gray-600); margin:12px 0 4px; }

        /* Paragraphs with proper spacing */
        .msg.assistant .msg-bubble p { margin:8px 0; }

        /* Lists — indented, spaced, with muted bullets */
        .msg.assistant .msg-bubble ul, .msg.assistant .msg-bubble ol { margin:8px 0 8px 4px; padding-left:16px; }
        .msg.assistant .msg-bubble li { margin:4px 0; padding-left:4px; }
        .msg.assistant .msg-bubble li::marker { color:var(--gray-400); }

        /* Bold — slightly darker for emphasis */
        .msg.assistant .msg-bubble strong { color:var(--navy); font-weight:600; }

        /* Inline code */
        .msg.assistant .msg-bubble code { background:var(--gray-100); color:#d946ef; padding:1px 5px;
            border-radius:4px; font-size:12px; font-family:'SF Mono',Monaco,Menlo,monospace; }

        /* Code blocks */
        .msg.assistant .msg-bubble pre { background:#1e293b; color:#e2e8f0; padding:14px 16px;
            border-radius:8px; overflow-x:auto; margin:12px 0; font-size:12.5px; line-height:1.5;
            border:1px solid var(--gray-200); }
        .msg.assistant .msg-bubble pre code { background:none; color:inherit; padding:0; font-size:inherit; }

        /* Tables — clean borders, zebra striping */
        .msg.assistant .msg-bubble table { border-collapse:collapse; width:100%; margin:12px 0;
            font-size:13px; border-radius:8px; overflow:hidden; }
        .msg.assistant .msg-bubble th { background:var(--gray-100); font-weight:600; color:var(--gray-700);
            padding:8px 12px; text-align:left; border-bottom:2px solid var(--gray-200); }
        .msg.assistant .msg-bubble td { padding:7px 12px; border-bottom:1px solid var(--gray-100); }
        .msg.assistant .msg-bubble tr:hover td { background:var(--blue-light); }

        /* Blockquotes — accent bar */
        .msg.assistant .msg-bubble blockquote { border-left:3px solid var(--blue); padding:6px 14px;
            margin:10px 0; background:var(--blue-light); border-radius:0 6px 6px 0; font-style:italic;
            color:var(--gray-600); }

        /* Horizontal rules */
        .msg.assistant .msg-bubble hr { border:none; border-top:1px solid var(--gray-200); margin:16px 0; }

        /* Links */
        .msg.assistant .msg-bubble a { color:var(--blue); text-decoration:none; }
        .msg.assistant .msg-bubble a:hover { text-decoration:underline; }

        .artifact-link { display:inline-flex; align-items:center; gap:5px; padding:5px 10px;
            margin-top:6px; background:var(--blue-light); color:var(--blue); border-radius:6px;
            font-size:11px; font-weight:500; cursor:pointer; border:1px solid rgba(59,130,246,0.2); }
        .artifact-link:hover { background:rgba(59,130,246,0.15); }

        /* Artifact Tabs */
        .artifact-tab { font-size:11px; padding:4px 10px; border-radius:6px; border:1px solid var(--gray-200);
            background:#fff; cursor:pointer; color:var(--gray-600); white-space:nowrap; transition:all 0.15s; }
        .artifact-tab:hover { background:var(--blue-light); color:var(--blue); border-color:rgba(59,130,246,0.3); }
        .artifact-tab.active { background:var(--blue); color:#fff; border-color:var(--blue); font-weight:500; }

        /* Error Messages */
        .error-bubble { background:#fef2f2; border:1px solid #fecaca; border-left:3px solid #ef4444;
            border-radius:8px; padding:12px 14px; margin-top:4px; font-size:13px; line-height:1.5; }
        .error-top { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
        .error-badge { display:inline-block; font-size:10px; font-weight:700; color:#fff; background:#ef4444;
            padding:2px 7px; border-radius:10px; letter-spacing:0.5px; text-transform:uppercase; }
        .error-agent { font-size:12px; color:#b91c1c; font-weight:600; }
        .error-message { color:#7f1d1d; margin-bottom:8px; }
        .error-detail-toggle { font-size:11px; color:#9ca3af; cursor:pointer; text-decoration:underline; }
        .error-detail-toggle:hover { color:#6b7280; }
        .error-detail { display:none; font-size:11px; color:#9ca3af; background:#fef2f2; padding:6px 8px;
            border-radius:4px; margin-top:4px; font-family:monospace; word-break:break-all; }
        .retry-btn { display:inline-flex; align-items:center; gap:5px; margin-top:8px; padding:6px 14px;
            background:#3b82f6; color:#fff; border:none; border-radius:6px; font-size:12px;
            font-weight:500; cursor:pointer; transition:background 0.15s; }
        .retry-btn:hover { background:#2563eb; }
        .retry-btn svg { width:14px; height:14px; }

        /* Typing Indicator */
        .typing { display:none; margin-bottom:16px; max-width:90%; }
        .typing.visible { display:block; }
        .typing-bubble { background:var(--gray-100); padding:10px 14px; border-radius:12px; border-bottom-left-radius:4px; }
        .typing-label { font-size:12px; color:var(--gray-500); font-style:italic; }
        .agent-badge { font-size:10px; color:var(--blue); font-weight:600; }

        /* Chat Input */
        .chat-input { padding:10px 16px 14px; border-top:1px solid var(--gray-200); background:#fff; }
        .chat-input-row { display:flex; gap:8px; align-items:flex-end; }
        .chat-input-row textarea { flex:1; resize:none; border:1px solid var(--gray-300); border-radius:10px;
            padding:9px 12px; font-size:13px; font-family:inherit; min-height:40px; max-height:100px; outline:none; }
        .chat-input-row textarea:focus { border-color:var(--blue); }
        .send-btn { width:36px; height:36px; background:var(--blue); color:#fff; border:none;
            border-radius:8px; cursor:pointer; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .send-btn:hover { background:var(--blue-hover); }
        .send-btn:disabled { background:var(--gray-300); cursor:not-allowed; }

        /* Artifact Panel (Right) — hidden when no artifact */
        .artifact-panel { flex:1; background:var(--gray-50); display:flex; flex-direction:column;
            transition:all 0.3s ease; }
        .popup-body.no-artifact .artifact-panel { display:none; }
        .artifact-empty { display:flex; flex-direction:column; align-items:center; justify-content:center;
            height:100%; color:var(--gray-400); }
        .artifact-empty-icon { font-size:48px; margin-bottom:12px; opacity:0.5; }
        .artifact-frame { width:100%; flex:1; border:none; }
        /* Markdown content renderer */
        .md-content { flex:1; overflow-y:auto; padding:32px 40px; font-size:14px; line-height:1.7;
            color:var(--gray-800); }
        .md-content h1 { font-size:22px; margin:0 0 16px; color:var(--navy); }
        .md-content h2 { font-size:18px; margin:24px 0 12px; color:var(--navy); border-bottom:1px solid var(--gray-200); padding-bottom:6px; }
        .md-content h3 { font-size:15px; margin:16px 0 8px; color:var(--gray-700); }
        .md-content p { margin:8px 0; }
        .md-content ul, .md-content ol { margin:8px 0 8px 20px; }
        .md-content li { margin:4px 0; }
        .md-content strong { color:var(--navy); }
        .md-content code { background:var(--gray-100); padding:1px 4px; border-radius:3px; font-size:12px; }
        .md-content pre { background:#1e293b; color:#e2e8f0; padding:14px; border-radius:8px; overflow-x:auto; margin:10px 0; }
        .md-content blockquote { border-left:3px solid var(--blue); padding:8px 16px; margin:10px 0; background:var(--blue-light); border-radius:0 6px 6px 0; }
        .md-content table { border-collapse:collapse; width:100%; margin:10px 0; }
        .md-content th, .md-content td { border:1px solid var(--gray-200); padding:6px 10px; text-align:left; font-size:13px; }
        .md-content th { background:var(--gray-100); font-weight:600; }
        .md-content hr { border:none; border-top:1px solid var(--gray-200); margin:20px 0; }
        .artifact-toolbar { display:flex; align-items:center; gap:8px; padding:8px 16px; border-bottom:1px solid var(--gray-200);
            background:#fff; flex-shrink:0; }
        .artifact-toolbar .artifact-type { font-size:11px; font-weight:600; color:var(--blue); background:var(--blue-light);
            padding:3px 8px; border-radius:4px; }
        .artifact-toolbar .artifact-name { font-size:12px; color:var(--gray-500); flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

        /* ── Responsive ── */
        @media (max-width: 900px) {
            .kanban { grid-template-columns:1fr; }
            .chat-panel { width:50%; }
            .popup { width:98vw; height:96vh; }
        }
        @media (max-width: 600px) {
            .popup-body { flex-direction:column; }
            .chat-panel { width:100% !important; height:50%; border-right:none; border-bottom:1px solid var(--gray-200); }
        }
    </style>
</head>
<body>

<!-- Top Navigation -->
<nav class="topnav">
    <div class="topnav-logo">Sourcy <span>Analyst</span></div>
    <div class="topnav-spacer"></div>
    <div class="status-pills">""" + pills + r"""</div>
    <a href="/architecture" class="arch-btn" title="How it works">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        Architecture
    </a>
    <select class="user-select" id="userSelect" onchange="setUser(this.value)">
        <option value="">Who are you?</option>
        <option value="Eugene">Eugene</option>
        <option value="Nadia">Nadia</option>
        <option value="Afrah">Afrah</option>
    </select>
</nav>

<!-- Create Ticket Bar -->
<div class="create-bar">
    <div class="create-card">
        <textarea id="createInput" placeholder="What do you want to analyze? (e.g., 'Full marketing audit', 'Analyze our Meta Ads', 'SEO keyword analysis')" rows="1"
            onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();createAndSend()}"
            oninput="autoResize(this)"></textarea>
        <button class="create-btn" onclick="createAndSend()">Create Ticket</button>
    </div>
</div>

<!-- Kanban Board -->
<div class="kanban" id="kanban">
    <div class="kanban-col col-open">
        <div class="kanban-col-header">Open <span class="count" id="countOpen">0</span></div>
        <div id="colOpen"></div>
    </div>
    <div class="kanban-col col-active">
        <div class="kanban-col-header">Active <span class="count" id="countActive">0</span></div>
        <div id="colActive"></div>
    </div>
    <div class="kanban-col col-done">
        <div class="kanban-col-header">Done <span class="count" id="countDone">0</span></div>
        <div id="colDone"></div>
    </div>
</div>

<!-- Fullscreen Ticket Popup -->
<div class="popup-overlay" id="popupOverlay" onclick="if(event.target===this)closePopup()">
    <div class="popup">
        <div class="popup-header">
            <div class="popup-title" id="popupTitle">Ticket</div>
            <select class="popup-status" id="popupStatus" onchange="updateStatus(this.value)">
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="pending_review">⏳ Pending Review</option>
                <option value="completed">Completed</option>
            </select>
            <button id="reviewTabBtn" onclick="toggleReviewPanel()" style="display:none;background:#7c3aed;color:#fff;border:none;padding:6px 12px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;">📋 Review Package</button>
            <button class="popup-close" onclick="closePopup()">&times;</button>
        </div>
        <div class="popup-body no-artifact">
            <!-- Chat (Left) -->
            <div class="chat-panel">
                <div class="chat-messages" id="chatMessages">
                    <div class="chat-empty-state" id="chatEmpty">
                        <p>Start your analysis by typing below</p>
                    </div>
                </div>
                <div class="typing" id="typingIndicator">
                    <div class="msg-header"><span class="agent-badge" id="agentBadge">Analyst</span></div>
                    <div class="typing-bubble">
                        <span class="typing-label" id="typingLabel">Thinking...</span>
                    </div>
                </div>
                <div class="chat-input">
                    <div class="chat-input-row">
                        <textarea id="chatInput" placeholder="Ask a follow-up question..." rows="1"
                            onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendMessage()}"
                            oninput="autoResize(this)"></textarea>
                        <button class="send-btn" id="sendBtn" onclick="sendMessage()">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
            <!-- Artifact (Right) — hidden by default, appears when artifact is generated -->
            <div class="artifact-panel" id="artifactPanel">
                <div class="artifact-toolbar" id="artifactToolbar" style="display:none">
                    <span class="artifact-type">Report</span>
                    <span class="artifact-name"></span>
                </div>
                <div class="artifact-empty" id="artifactEmpty">
                    <div class="artifact-empty-icon">📊</div>
                    <p>Report will appear here after analysis</p>
                </div>
                <div class="artifact-empty" id="scriptErrorPanel" style="display:none;padding:24px;text-align:left;max-width:600px;margin:0 auto">
                    <div style="font-size:20px;margin-bottom:8px">⚠️ Report script failed</div>
                    <p id="scriptErrorMsg" style="color:#ef4444;font-size:13px;margin-bottom:12px;word-break:break-all"></p>
                    <details style="margin-bottom:16px">
                        <summary style="cursor:pointer;font-size:12px;color:#6b7280;user-select:none">Show traceback</summary>
                        <pre id="scriptErrorTrace" style="font-size:11px;background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:6px;overflow:auto;max-height:240px;margin-top:8px;white-space:pre-wrap"></pre>
                    </details>
                    <p id="scriptNameLabel" style="font-size:11px;color:#9ca3af;margin-bottom:12px"></p>
                    <button id="retryScriptBtn" class="retry-btn" onclick="retryScript()" style="background:#2563eb">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
                        Retry Script
                    </button>
                    <span id="retryStatusMsg" style="font-size:12px;color:#6b7280;margin-left:10px"></span>
                </div>
                <iframe class="artifact-frame" id="artifactFrame" style="display:none"></iframe>
                <div class="md-content" id="mdContent" style="display:none"></div>
            </div>
        </div>
    </div>
</div>

<script>
// ─── State ───
let currentUser = localStorage.getItem('sourcyUser') || '';
let currentTicketId = null;
let streaming = false;
let streamBubble = null;
let lastUserMessage = '';
let currentArtifacts = [];
const ticketSockets = {};
let pollTimer = null;
let lastMsgCount = 0;

document.getElementById('userSelect').value = currentUser;
loadTickets();

function setUser(name) {
    currentUser = name;
    localStorage.setItem('sourcyUser', name);
}

// ─── Kanban Board ───
async function loadTickets() {
    const res = await fetch('/api/tickets');
    const tickets = await res.json();
    renderKanban(tickets.filter(t => t.status !== 'deleted'));
}

function renderKanban(tickets) {
    const cols = { open: [], in_progress: [], completed: [] };
    tickets.forEach(t => {
        const col = cols[t.status] || cols['open'];
        col.push(t);
    });

    document.getElementById('countOpen').textContent = cols.open.length;
    document.getElementById('countActive').textContent = cols.in_progress.length;
    document.getElementById('countDone').textContent = cols.completed.length;

    document.getElementById('colOpen').innerHTML = cols.open.map(cardHtml).join('');
    document.getElementById('colActive').innerHTML = cols.in_progress.map(cardHtml).join('');
    document.getElementById('colDone').innerHTML = cols.completed.map(cardHtml).join('');
}

function cardHtml(t) {
    const time = formatTime(t.updated_at);
    const preview = t.last_message
        ? (t.last_role === 'user' ? 'You: ' : '') + esc(t.last_message).substring(0, 80)
        : 'No messages yet';
    const initials = (t.created_by || '?')[0].toUpperCase();
    const artBadge = t.artifact_count > 0
        ? '<span class="tc-badge has-artifact">📊 Report</span>' : '';
    const reviewBadge = t.status === 'pending_review'
        ? '<span class="tc-badge" style="background:#ede9fe;color:#7c3aed;">⏳ Review</span>' : '';
    // Badge based on DB status: if last message is from user and ticket is in_progress, agent is working
    const isProcessing = (t.last_role === 'user' && t.message_count > 0 && t.status === 'in_progress');
    const waitBadge = isProcessing
        ? '<span class="tc-badge waiting">Processing...</span>'
        : '';
    return `<div class="ticket-card" onclick="openPopup('${t.id}')">
        <div class="tc-title">${esc(t.title)}</div>
        <div class="tc-preview">${preview}</div>
        <div class="tc-meta">
            <span class="tc-avatar">${initials}</span>
            <span>${esc(t.created_by)}</span>
            <span>&middot;</span>
            <span>${time}</span>
            <span>&middot;</span>
            <span>${t.message_count || 0} msgs</span>
            ${waitBadge}${artBadge}${reviewBadge}
        </div>
    </div>`;
}

// ─── Create Ticket & Send First Message ───
let pendingFirstMessage = null;

async function createAndSend() {
    const input = document.getElementById('createInput');
    const text = input.value.trim();
    if (!text) { input.focus(); return; }
    if (!currentUser) { alert('Please select your name first'); return; }

    // Save the message text BEFORE clearing input
    pendingFirstMessage = text;

    // Create ticket with the query as title
    const title = text.length > 60 ? text.substring(0, 57) + '...' : text;
    const res = await fetch('/api/tickets', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ title, created_by: currentUser }),
    });
    const ticket = await res.json();
    input.value = '';
    autoResize(input);

    // Open popup — this sets up the WebSocket
    await openPopup(ticket.id);

    // Now send the first message directly via the WebSocket
    if (pendingFirstMessage) {
        const msg = pendingFirstMessage;
        pendingFirstMessage = null;
        sendDirectMessage(msg);
    }
}

function sendDirectMessage(text) {
    if (!text || !currentTicketId) return;
    lastUserMessage = text;
    const state = getOrCreateSocket(currentTicketId);

    function doSend() {
        if (state.ws.readyState === 1) {
            const emptyEl = document.querySelector('.chat-empty-state');
            if (emptyEl) emptyEl.remove();
            appendMessage('user', text, false);
            scrollChat();
            state.ws.send(JSON.stringify({ message: text }));
            streaming = true;
            state.streaming = true;
            document.getElementById('sendBtn').disabled = true;
            loadTickets();
        } else if (state.ws.readyState === 0) {
            setTimeout(doSend, 300);
        }
    }
    doSend();
}

// ─── Popup ───
async function openPopup(ticketId) {
    // Reset state
    streaming = false;
    streamBubble = null;
    currentTicketId = ticketId;
    stopPolling();

    // Fetch ticket data
    const res = await fetch(`/api/tickets/${ticketId}`);
    const ticket = await res.json();

    // Update header
    document.getElementById('popupTitle').textContent = ticket.title;
    document.getElementById('popupStatus').value = ticket.status;

    // Show Review tab button if pending_review
    const reviewBtn = document.getElementById('reviewTabBtn');
    if (ticket.status === 'pending_review') {
        reviewBtn.style.display = 'inline-block';
        reviewBtn._ticketId = ticket.id;
    } else {
        reviewBtn.style.display = 'none';
    }

    // Render messages and loading state
    renderTicketChat(ticket);

    // Show artifacts — if multiple, build switcher tabs
    const arts = ticket.artifacts || [];
    currentArtifacts = arts.map(a => a.file_path);
    if (arts.length > 0) {
        buildArtifactSwitcher(arts);
        showArtifact(arts[arts.length - 1].file_path);
        hideScriptError();
    } else {
        hideArtifact();
        // Check for failed script
        if (ticket.status === 'completed' || ticket.status === 'done') {
            checkFailedScript(ticketId);
        } else {
            hideScriptError();
        }
    }

    // Open overlay
    document.getElementById('popupOverlay').classList.add('open');
    document.body.style.overflow = 'hidden';
    scrollChat();

    // Setup WebSocket (still needed for sending messages)
    getOrCreateSocket(ticketId);

    // Start polling if ticket is being processed
    const isProcessing = ticket.status === 'in_progress' && ticket.messages.length > 0
        && ticket.messages[ticket.messages.length - 1].role === 'user';
    if (isProcessing) {
        lastMsgCount = ticket.messages.length;
        startPolling(ticketId);
    }
}

function renderTicketChat(ticket) {
    const chatEl = document.getElementById('chatMessages');
    const indicator = document.getElementById('typingIndicator');

    if (ticket.messages.length) {
        chatEl.innerHTML = '';
        for (const msg of ticket.messages) {
            appendMessage(msg.role, msg.content, false);
            ticket.artifacts.filter(a => a.message_id === msg.id).forEach(a => addArtifactLink(a.file_path));
        }
    } else {
        chatEl.innerHTML = '<div class="chat-empty-state"><p>Start your analysis by typing below</p></div>';
    }

    // Show loading indicator if agent is still working (last msg is user, status in_progress)
    const lastMsg = ticket.messages[ticket.messages.length - 1];
    const isProcessing = ticket.status === 'in_progress' && lastMsg && lastMsg.role === 'user';
    if (isProcessing) {
        indicator.classList.add('visible');
        document.getElementById('typingLabel').textContent = 'Agent is working...';
        document.getElementById('sendBtn').disabled = true;
        streaming = true;
    } else {
        indicator.classList.remove('visible');
        document.getElementById('sendBtn').disabled = false;
        streaming = false;
    }
}

function startPolling(ticketId) {
    stopPolling();
    pollTimer = setInterval(async () => {
        if (currentTicketId !== ticketId) { stopPolling(); return; }
        try {
            const res = await fetch(`/api/tickets/${ticketId}`);
            const ticket = await res.json();
            const newCount = ticket.messages.length;

            // Check if new messages arrived
            if (newCount > lastMsgCount) {
                lastMsgCount = newCount;
                renderTicketChat(ticket);

                // Update artifacts
                const arts = ticket.artifacts || [];
                currentArtifacts = arts.map(a => a.file_path);
                if (arts.length > 0) {
                    buildArtifactSwitcher(arts);
                    showArtifact(arts[arts.length - 1].file_path);
                }
                scrollChat();
                loadTickets();
            }

            // Stop polling if no longer processing
            const lastMsg = ticket.messages[ticket.messages.length - 1];
            if (!lastMsg || lastMsg.role === 'assistant') {
                stopPolling();
                loadTickets();
            }
        } catch (e) {
            console.error('Poll error:', e);
        }
    }, 3000);
}

function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

function closePopup() {
    stopPolling();
    document.getElementById('popupOverlay').classList.remove('open');
    document.body.style.overflow = '';
    currentTicketId = null;
    loadTickets();
}

// ─── Review Panel ──────────────────────────────────────────────────────────
async function toggleReviewPanel() {
    if (!currentTicketId) return;
    const existing = document.getElementById('reviewPanel');
    if (existing) { existing.remove(); return; }

    const res = await fetch(`/api/tickets/${currentTicketId}/review`);
    if (!res.ok) { alert('No review package found for this ticket.'); return; }
    const review = await res.json();

    const panel = document.createElement('div');
    panel.id = 'reviewPanel';
    panel.style.cssText = 'position:fixed;top:0;right:0;width:420px;height:100vh;background:#1e293b;border-left:1px solid #334155;z-index:10000;overflow-y:auto;display:flex;flex-direction:column;';

    const indexUrl = review.index_url;
    panel.innerHTML = `
      <div style="padding:20px;border-bottom:1px solid #334155;display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:15px;font-weight:700;color:#f8fafc;">Review Package</div>
          <div style="font-size:11px;color:#94a3b8;margin-top:2px;">${review.page_count || 0} pages · ${review.status}</div>
        </div>
        <button onclick="document.getElementById('reviewPanel').remove()" style="background:none;border:none;color:#64748b;font-size:20px;cursor:pointer;">&times;</button>
      </div>
      <div style="padding:20px;flex:1;">
        ${indexUrl ? `<a href="${indexUrl}" target="_blank" style="display:block;background:#7c3aed;color:#fff;text-align:center;padding:10px;border-radius:8px;text-decoration:none;font-weight:600;margin-bottom:16px;">Open Review Dashboard →</a>` : '<p style="color:#94a3b8;">Review package not yet ready on disk.</p>'}
        <div style="font-size:12px;color:#64748b;margin-top:8px;">Created: ${review.created_at?.split('T')[0] || '—'}</div>
        ${review.notes ? `<div style="margin-top:12px;padding:10px;background:#0f172a;border-radius:6px;font-size:12px;color:#94a3b8;">${review.notes}</div>` : ''}
        <div style="margin-top:20px;display:flex;gap:8px;">
          <button onclick="approveReview()" style="flex:1;padding:10px;background:#16a34a;color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer;">✓ Approve</button>
          <button onclick="requestChanges()" style="flex:1;padding:10px;background:#b45309;color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer;">✎ Request Changes</button>
        </div>
        <div style="margin-top:12px;font-size:11px;color:#475569;text-align:center;">Approving marks the review as accepted.<br>No changes auto-apply to the live site.</div>
      </div>`;
    document.body.appendChild(panel);
}

async function approveReview() {
    if (!currentTicketId) return;
    const notes = prompt('Approval notes (optional):') || '';
    await fetch(`/api/tickets/${currentTicketId}/review/approve`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ reviewed_by: currentUser, notes }),
    });
    document.getElementById('reviewPanel')?.remove();
    document.getElementById('popupStatus').value = 'approved';
    loadTickets();
    alert('Review approved. Apply patches per changes.md instructions.');
}

async function requestChanges() {
    if (!currentTicketId) return;
    const notes = prompt('What changes are needed?');
    if (!notes) return;
    await fetch(`/api/tickets/${currentTicketId}/review/request-changes`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ reviewed_by: currentUser, notes }),
    });
    document.getElementById('reviewPanel')?.remove();
    document.getElementById('popupStatus').value = 'in_progress';
    loadTickets();
}

async function updateStatus(status) {
    if (!currentTicketId) return;
    await fetch(`/api/tickets/${currentTicketId}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ status }),
    });
}

// ─── WebSocket ───
function getOrCreateSocket(ticketId) {
    if (ticketSockets[ticketId] && ticketSockets[ticketId].ws.readyState <= 1) {
        return ticketSockets[ticketId];
    }
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socket = new WebSocket(`${proto}//${location.host}/ws/${ticketId}`);
    const state = { ws: socket, streaming: false, pendingMessages: [] };

    socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        state.pendingMessages.push(msg);
        if (ticketId === currentTicketId) {
            processPendingMessages(ticketId);
        } else if (msg.type === 'stream_end') {
            state.streaming = false;
            loadTickets();
        }
    };
    socket.onclose = () => {
        state.streaming = false;
        if (ticketId === currentTicketId) {
            streaming = false;
            document.getElementById('sendBtn').disabled = false;
            document.getElementById('typingIndicator').classList.remove('visible');
        }
        delete ticketSockets[ticketId];
    };
    socket.onerror = () => { socket.onclose(); };

    ticketSockets[ticketId] = state;
    return state;
}

function processPendingMessages(ticketId) {
    const state = ticketSockets[ticketId];
    if (!state) return;
    while (state.pendingMessages.length > 0) {
        handleWSMessage(state.pendingMessages.shift());
    }
}

// ─── Chat ───
function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text || !currentTicketId || streaming) return;

    const state = getOrCreateSocket(currentTicketId);
    if (state.ws.readyState === 0) { setTimeout(sendMessage, 500); return; }
    if (state.ws.readyState > 1) {
        delete ticketSockets[currentTicketId];
        getOrCreateSocket(currentTicketId);
        setTimeout(sendMessage, 500);
        return;
    }

    // Clear empty state if present
    const emptyEl = document.querySelector('.chat-empty-state');
    if (emptyEl) emptyEl.remove();
    appendMessage('user', text, false);
    input.value = '';
    autoResize(input);
    scrollChat();

    lastUserMessage = text;
    state.ws.send(JSON.stringify({ message: text }));
    streaming = true;
    state.streaming = true;
    document.getElementById('sendBtn').disabled = true;
    document.getElementById('typingIndicator').classList.add('visible');
    document.getElementById('typingLabel').textContent = 'Agent is working...';
    lastMsgCount = document.getElementById('chatMessages').querySelectorAll('.msg').length;
    startPolling(currentTicketId);
}

function handleWSMessage(msg) {
    const indicator = document.getElementById('typingIndicator');

    switch (msg.type) {
        case 'stream_start':
            indicator.classList.add('visible');
            document.getElementById('agentBadge').textContent = msg.agent;
            document.getElementById('typingLabel').textContent = 'Thinking...';
            streamBubble = null;
            break;
        case 'agent_switch':
            indicator.classList.add('visible');
            document.getElementById('agentBadge').textContent = msg.agent;
            document.getElementById('typingLabel').textContent = msg.agent + ' is analyzing...';
            break;
        case 'tool_status':
            indicator.classList.add('visible');
            document.getElementById('typingLabel').textContent = msg.label;
            break;
        case 'stream_delta':
            indicator.classList.remove('visible');
            if (!streamBubble) streamBubble = appendMessage('assistant', '', true);
            streamBubble.innerHTML += msg.data;
            scrollChat();
            break;
        case 'stream_end':
            indicator.classList.remove('visible');
            if (streamBubble) {
                streamBubble.innerHTML = formatMd(msg.data);
            } else if (msg.data) {
                appendMessage('assistant', msg.data, false);
            }
            const urls = msg.artifact_urls || (msg.report_url ? [msg.report_url] : []);
            if (urls.length) {
                urls.forEach(u => {
                    addArtifactLink(u);
                    currentArtifacts.push(u);
                });
                buildArtifactSwitcher(currentArtifacts);
                showArtifact(urls[0]);
            }
            streaming = false;
            streamBubble = null;
            if (currentTicketId && ticketSockets[currentTicketId])
                ticketSockets[currentTicketId].streaming = false;
            document.getElementById('sendBtn').disabled = false;
            scrollChat();
            loadTickets();
            break;
        case 'error':
            indicator.classList.remove('visible');
            if (msg.error_type) {
                appendErrorMessage(msg);
            } else {
                appendMessage('assistant', '\u26a0\ufe0f ' + (msg.data || msg.message || 'Unknown error'), false);
            }
            streaming = false;
            if (currentTicketId && ticketSockets[currentTicketId])
                ticketSockets[currentTicketId].streaming = false;
            document.getElementById('sendBtn').disabled = false;
            break;
    }
}

function appendMessage(role, content, isStream) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'msg ' + role;

    const hdr = document.createElement('div');
    hdr.className = 'msg-header';
    hdr.textContent = role === 'user' ? (currentUser || 'You') : 'Sourcy Analyst';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerHTML = isStream ? content : formatMd(content);

    div.appendChild(hdr);
    div.appendChild(bubble);
    container.appendChild(div);
    return bubble;
}

function appendErrorMessage(msg) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'msg assistant';

    const hdr = document.createElement('div');
    hdr.className = 'msg-header';
    hdr.textContent = 'Sourcy Analyst';

    const bubble = document.createElement('div');
    bubble.className = 'error-bubble';

    const top = document.createElement('div');
    top.className = 'error-top';
    const badge = document.createElement('span');
    badge.className = 'error-badge';
    badge.textContent = (msg.error_type || 'error').replace('_', ' ');
    top.appendChild(badge);
    if (msg.agent) {
        const agent = document.createElement('span');
        agent.className = 'error-agent';
        agent.textContent = 'While running: ' + msg.agent;
        top.appendChild(agent);
    }
    bubble.appendChild(top);

    const message = document.createElement('div');
    message.className = 'error-message';
    message.textContent = msg.message || msg.data || 'Something went wrong.';
    bubble.appendChild(message);

    if (msg.detail) {
        const detailId = 'err-' + Date.now();
        const toggle = document.createElement('span');
        toggle.className = 'error-detail-toggle';
        toggle.textContent = 'Show details';
        toggle.onclick = () => {
            const el = document.getElementById(detailId);
            const hidden = el.style.display === 'none';
            el.style.display = hidden ? 'block' : 'none';
            toggle.textContent = hidden ? 'Hide details' : 'Show details';
        };
        bubble.appendChild(toggle);
        const detail = document.createElement('div');
        detail.className = 'error-detail';
        detail.id = detailId;
        detail.textContent = msg.detail;
        bubble.appendChild(detail);
    }

    if (msg.retryable && lastUserMessage) {
        const btn = document.createElement('button');
        btn.className = 'retry-btn';
        btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg> Retry';
        btn.onclick = retryLastMessage;
        bubble.appendChild(btn);
    }

    div.appendChild(hdr);
    div.appendChild(bubble);
    container.appendChild(div);
    scrollChat();
}

function retryLastMessage() {
    if (!lastUserMessage || !currentTicketId || streaming) return;
    sendDirectMessage(lastUserMessage);
}

// ─── Script Error / Retry ───
async function checkFailedScript(ticketId) {
    try {
        const res = await fetch(`/api/tickets/${ticketId}/failed-script`);
        const data = await res.json();
        if (data.exists) {
            showScriptError(data);
        } else {
            hideScriptError();
        }
    } catch (e) {
        hideScriptError();
    }
}

function showScriptError(data) {
    document.getElementById('artifactEmpty').style.display = 'none';  // hide placeholder
    document.getElementById('artifactFrame').style.display = 'none';  // hide any stale iframe
    document.getElementById('scriptErrorPanel').style.display = '';
    document.getElementById('scriptErrorMsg').textContent = data.error_msg || 'Unknown error';
    document.getElementById('scriptErrorTrace').textContent = data.traceback || '(no traceback)';
    document.getElementById('scriptNameLabel').textContent = `Script: ${data.script_name}`;
    document.getElementById('retryStatusMsg').textContent = '';
    document.getElementById('retryScriptBtn').disabled = false;
    document.getElementById('retryScriptBtn').textContent = '⟳ Retry Script';
}

function hideScriptError() {
    document.getElementById('scriptErrorPanel').style.display = 'none';
    // Do NOT touch artifactEmpty here — showArtifact/hideArtifact own that element
}

async function retryScript() {
    if (!currentTicketId) return;
    const btn = document.getElementById('retryScriptBtn');
    const statusMsg = document.getElementById('retryStatusMsg');
    btn.disabled = true;
    btn.textContent = 'Running...';
    statusMsg.textContent = 'Re-running script with fixed components...';
    try {
        const res = await fetch(`/api/tickets/${currentTicketId}/retry-script`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            statusMsg.textContent = '✅ Success!';
            hideScriptError();
            // Show the new artifact
            showArtifact(data.url);
            addArtifactLink(data.url);
            // Refresh board
            loadTickets();
        } else {
            // Update error panel with new error
            document.getElementById('scriptErrorMsg').textContent = data.error || 'Retry failed';
            document.getElementById('scriptErrorTrace').textContent = data.traceback || '(no traceback)';
            btn.disabled = false;
            btn.textContent = '⟳ Retry Script';
            statusMsg.textContent = '❌ Still failing — see updated error above';
        }
    } catch (e) {
        btn.disabled = false;
        btn.textContent = '⟳ Retry Script';
        statusMsg.textContent = `❌ Network error: ${e.message}`;
    }
}

function addArtifactLink(url) {
    const container = document.getElementById('chatMessages');
    const lastMsg = container.lastElementChild;
    if (lastMsg) {
        const link = document.createElement('div');
        link.className = 'artifact-link';
        const isMd = url && url.endsWith('.md');
        let label = '\ud83d\udcca View Report';
        if (isMd) {
            if (url.includes('/blogs/')) label = '\ud83d\udcdd View Blog Post';
            else if (url.includes('/briefs/')) label = '\ud83d\udccb View Brief';
            else if (url.includes('/landing-pages/')) label = '\ud83d\udcc4 View Landing Page';
            else if (url.includes('/audits/')) label = '\ud83d\udcca View Audit';
            else label = '\ud83d\udcc4 View Content';
        }
        link.innerHTML = label;
        link.onclick = () => showArtifact(url);
        lastMsg.appendChild(link);
    }
}

// ─── Artifact ───
function showArtifact(url) {
    const body = document.querySelector('.popup-body');
    const panel = document.getElementById('artifactPanel');
    const empty = document.getElementById('artifactEmpty');
    const frame = document.getElementById('artifactFrame');
    const mdDiv = document.getElementById('mdContent');
    const toolbar = document.getElementById('artifactToolbar');

    // Show artifact panel
    body.classList.remove('no-artifact');
    empty.style.display = 'none';

    if (url && url.endsWith('.md')) {
        // Render .md content inline
        frame.style.display = 'none';
        if (mdDiv) mdDiv.style.display = 'block';
        if (toolbar) toolbar.style.display = 'flex';

        // Determine artifact type from path
        let artType = 'Content';
        if (url.includes('/blogs/')) artType = 'Blog Post';
        else if (url.includes('/briefs/')) artType = 'Content Brief';
        else if (url.includes('/landing-pages/')) artType = 'Landing Page';
        else if (url.includes('/audits/')) artType = 'Audit Report';
        if (toolbar) {
            toolbar.querySelector('.artifact-type').textContent = artType;
            toolbar.querySelector('.artifact-name').textContent = url.split('/').pop();
        }

        fetch(url)
            .then(r => r.text())
            .then(text => {
                // Strip YAML frontmatter
                let content = text;
                if (content.startsWith('---')) {
                    const endIdx = content.indexOf('---', 3);
                    if (endIdx > 0) content = content.substring(endIdx + 3).trim();
                }
                if (mdDiv) mdDiv.innerHTML = renderMarkdown(content);
            })
            .catch(() => {
                if (mdDiv) mdDiv.innerHTML = '<p style="color:var(--gray-400)">Could not load content file.</p>';
            });
    } else {
        // HTML report — use iframe
        if (mdDiv) mdDiv.style.display = 'none';
        if (toolbar) {
            toolbar.style.display = 'flex';
            toolbar.querySelector('.artifact-type').textContent = 'Report';
            toolbar.querySelector('.artifact-name').textContent = (url || '').split('/').pop();
        }
        frame.style.display = 'block';
        frame.src = url;
    }
}

function hideArtifact() {
    const body = document.querySelector('.popup-body');
    body.classList.add('no-artifact');
    // Only show empty placeholder if error panel isn't taking over
    const errPanel = document.getElementById('scriptErrorPanel');
    const showEmpty = !errPanel || errPanel.style.display === 'none';
    document.getElementById('artifactEmpty').style.display = showEmpty ? 'flex' : 'none';
    document.getElementById('artifactFrame').style.display = 'none';
    document.getElementById('artifactFrame').src = '';
    const mdDiv = document.getElementById('mdContent');
    if (mdDiv) { mdDiv.style.display = 'none'; mdDiv.innerHTML = ''; }
    const toolbar = document.getElementById('artifactToolbar');
    if (toolbar) toolbar.style.display = 'none';
}

function _friendlyArtifactName(url) {
    const name = url.split('/').pop().replace(/\.md$|\.html$/,'');
    // Strip trailing timestamp like _20260415_124025
    const clean = name.replace(/_\d{8}_\d{6}$/, '');
    // Convert kebab/snake to title case
    return clean.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

async function buildArtifactSwitcher(arts) {
    const toolbar = document.getElementById('artifactToolbar');
    if (!toolbar || arts.length < 1) return;

    // Remove old switcher if exists
    const old = toolbar.querySelector('.artifact-switcher');
    if (old) old.remove();

    // Filter to only artifacts that actually exist on disk (HEAD check)
    const checks = await Promise.all(
        arts.map(async (a) => {
            const url = a.file_path || a;
            try { const r = await fetch(url, { method: 'HEAD' }); return r.ok ? a : null; }
            catch { return null; }
        })
    );
    const validArts = checks.filter(Boolean);

    if (validArts.length <= 1) return; // No tabs needed for 0 or 1 valid artifact

    const switcher = document.createElement('div');
    switcher.className = 'artifact-switcher';
    switcher.style.cssText = 'display:flex;gap:4px;margin-left:auto;flex-wrap:wrap;';
    validArts.forEach((a, i) => {
        const btn = document.createElement('button');
        const url = a.file_path || a;
        const isMd = url.endsWith('.md');
        const label = isMd ? _friendlyArtifactName(url) : 'Report ' + (i + 1);
        btn.textContent = label.length > 28 ? label.substring(0, 25) + '...' : label;
        btn.title = label;
        btn.className = 'artifact-tab';
        btn.onclick = () => {
            switcher.querySelectorAll('.artifact-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            showArtifact(url);
        };
        if (i === validArts.length - 1) btn.classList.add('active');
        switcher.appendChild(btn);
    });
    toolbar.appendChild(switcher);
}

function renderMarkdown(text) {
    let h = text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
        .replace(/^---$/gm, '<hr>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
        .replace(/\[IMAGE: ([^\]]+)\]/g, '<div style="background:var(--gray-100);padding:16px;border-radius:8px;margin:10px 0;text-align:center;color:var(--gray-400);font-size:12px">Image: $1</div>');
    // Wrap consecutive <li> in <ul>
    h = h.replace(/(<li>.*?<\/li>\n?)+/g, '<ul>$&</ul>');
    // Handle table rows
    h = h.replace(/\|(.+)\|/g, (match) => {
        const cells = match.split('|').filter(c => c.trim());
        if (cells.every(c => /^[\s-:]+$/.test(c))) return '';
        return '<tr>' + cells.map(c => '<td>' + c.trim() + '</td>').join('') + '</tr>';
    });
    h = h.replace(/(<tr>.*<\/tr>\n?)+/g, '<table>$&</table>');
    h = h.replace(/\n\n/g, '</p><p>');
    h = h.replace(/\n/g, '<br>');
    return '<p>' + h + '</p>';
}

// ─── Utilities ───
function scrollChat() {
    const c = document.getElementById('chatMessages');
    setTimeout(() => { c.scrollTop = c.scrollHeight; }, 50);
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 100) + 'px';
}

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function formatTime(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff/60) + 'm';
    if (diff < 86400) return Math.floor(diff/3600) + 'h';
    return d.toLocaleDateString();
}

function formatMd(text) {
    if (!text) return '';

    // Split into lines for block-level processing
    const lines = text.split('\n');
    let html = '';
    let inCode = false;
    let codeBlock = '';
    let inList = false;
    let listType = '';
    let inTable = false;
    let tableRows = [];
    let isFirstTableRow = true;

    function closeList() {
        if (inList) { html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false; }
    }
    function closeTable() {
        if (inTable && tableRows.length) {
            html += '<table>';
            tableRows.forEach((row, i) => {
                const tag = i === 0 ? 'th' : 'td';
                html += '<tr>' + row.map(c => `<${tag}>${inlineFmt(c.trim())}</${tag}>`).join('') + '</tr>';
            });
            html += '</table>';
            tableRows = []; inTable = false; isFirstTableRow = true;
        }
    }

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Code blocks
        if (line.startsWith('```')) {
            if (inCode) {
                closeList(); closeTable();
                html += '<pre><code>' + esc(codeBlock) + '</code></pre>';
                codeBlock = ''; inCode = false;
            } else {
                closeList(); closeTable();
                inCode = true; codeBlock = '';
            }
            continue;
        }
        if (inCode) { codeBlock += (codeBlock ? '\n' : '') + line; continue; }

        // Blank line — close lists/tables, add spacing
        if (!line.trim()) {
            closeList(); closeTable();
            html += '';
            continue;
        }

        // Table rows
        if (line.includes('|') && line.trim().startsWith('|')) {
            closeList();
            const cells = line.split('|').filter(c => c !== '');
            // Skip separator row (---|---|---)
            if (cells.every(c => /^[\s-:]+$/.test(c))) { continue; }
            if (!inTable) { inTable = true; tableRows = []; isFirstTableRow = true; }
            tableRows.push(cells);
            continue;
        } else {
            closeTable();
        }

        // Headings
        if (line.startsWith('#### ')) { closeList(); closeTable(); html += '<h4>' + inlineFmt(line.slice(5)) + '</h4>'; continue; }
        if (line.startsWith('### '))  { closeList(); closeTable(); html += '<h3>' + inlineFmt(line.slice(4)) + '</h3>'; continue; }
        if (line.startsWith('## '))   { closeList(); closeTable(); html += '<h2>' + inlineFmt(line.slice(3)) + '</h2>'; continue; }
        if (line.startsWith('# '))    { closeList(); closeTable(); html += '<h1>' + inlineFmt(line.slice(2)) + '</h1>'; continue; }

        // Horizontal rule
        if (/^[-*_]{3,}\s*$/.test(line)) { closeList(); closeTable(); html += '<hr>'; continue; }

        // Blockquote
        if (line.startsWith('> ')) { closeList(); closeTable(); html += '<blockquote>' + inlineFmt(line.slice(2)) + '</blockquote>'; continue; }

        // Unordered list
        if (/^\s*[-*] /.test(line)) {
            closeTable();
            if (!inList || listType !== 'ul') { closeList(); html += '<ul>'; inList = true; listType = 'ul'; }
            html += '<li>' + inlineFmt(line.replace(/^\s*[-*] /, '')) + '</li>';
            continue;
        }

        // Ordered list
        if (/^\s*\d+\.\s/.test(line)) {
            closeTable();
            if (!inList || listType !== 'ol') { closeList(); html += '<ol>'; inList = true; listType = 'ol'; }
            html += '<li>' + inlineFmt(line.replace(/^\s*\d+\.\s/, '')) + '</li>';
            continue;
        }

        // Regular paragraph
        closeList(); closeTable();
        html += '<p>' + inlineFmt(line) + '</p>';
    }

    closeList(); closeTable();
    if (inCode) html += '<pre><code>' + esc(codeBlock) + '</code></pre>';
    return html;
}

function inlineFmt(text) {
    let h = esc(text);
    // Bold + italic
    h = h.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Inline code
    h = h.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Links
    h = h.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    return h;
}
</script>
</body>
</html>"""
