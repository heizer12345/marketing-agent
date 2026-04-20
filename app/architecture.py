"""Architecture diagram page for Sourcy Marketing Agent."""


def get_architecture_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>How It Works — Sourcy Analyst</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #0f1117;
    color: #e2e8f0;
    min-height: 100vh;
  }

  /* ── Top nav ── */
  .topbar {
    background: #1a1d27;
    border-bottom: 1px solid #2d3148;
    padding: 14px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .topbar-brand { font-size: 18px; font-weight: 700; color: #fff; }
  .topbar-brand span { color: #f97316; }
  .topbar-back {
    color: #94a3b8;
    text-decoration: none;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: color .2s;
  }
  .topbar-back:hover { color: #fff; }

  /* ── Page layout ── */
  .page { max-width: 1200px; margin: 0 auto; padding: 48px 24px 80px; }

  /* ── TLDR ── */
  .tldr-card {
    background: linear-gradient(135deg, #1e293b 0%, #1a2236 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 32px 36px;
    margin-bottom: 56px;
    position: relative;
    overflow: hidden;
  }
  .tldr-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #f97316, #8b5cf6, #06b6d4);
  }
  .tldr-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #f97316;
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 16px;
  }
  .tldr-headline {
    font-size: 26px;
    font-weight: 800;
    color: #fff;
    margin-bottom: 14px;
    line-height: 1.3;
  }
  .tldr-body {
    font-size: 16px;
    color: #94a3b8;
    line-height: 1.8;
    max-width: 820px;
  }
  .tldr-body strong { color: #e2e8f0; }
  .tldr-bullets {
    margin-top: 20px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
  }
  .tldr-bullet {
    background: rgba(255,255,255,.04);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 14px 16px;
    display: flex;
    align-items: flex-start;
    gap: 10px;
  }
  .tldr-bullet-icon { font-size: 20px; flex-shrink: 0; margin-top: 1px; }
  .tldr-bullet-text { font-size: 13px; color: #cbd5e1; line-height: 1.5; }
  .tldr-bullet-text strong { color: #fff; display: block; margin-bottom: 2px; }

  /* ── Section label ── */
  .section-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1e293b;
  }

  /* ── Diagram container ── */
  .diagram-wrap { position: relative; }

  /* ── Flow column layout ── */
  .flow {
    display: flex;
    flex-direction: column;
    gap: 0;
    align-items: center;
    width: 100%;
  }

  /* ── Tier row ── */
  .tier-row {
    display: flex;
    align-items: center;
    gap: 0;
    width: 100%;
    position: relative;
  }

  .tier-label-col {
    width: 120px;
    flex-shrink: 0;
    text-align: right;
    padding-right: 18px;
  }
  .tier-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    padding: 5px 10px;
    border-radius: 20px;
    display: inline-block;
  }
  .tier-1-label { background: rgba(249,115,22,.15); color: #fb923c; border: 1px solid rgba(249,115,22,.3); }
  .tier-2-label { background: rgba(139,92,246,.15); color: #a78bfa; border: 1px solid rgba(139,92,246,.3); }
  .tier-3-label { background: rgba(6,182,212,.15); color: #22d3ee; border: 1px solid rgba(6,182,212,.3); }
  .tier-tools-label { background: rgba(16,185,129,.15); color: #34d399; border: 1px solid rgba(16,185,129,.3); }
  .tier-data-label { background: rgba(99,102,241,.15); color: #818cf8; border: 1px solid rgba(99,102,241,.3); }

  .tier-nodes {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: stretch;
    gap: 10px;
    padding: 0 4px;
  }

  /* ── Arrow connector ── */
  .arrow-row {
    display: flex;
    align-items: center;
    width: 100%;
  }
  .arrow-row .tier-label-col { visibility: hidden; }
  .arrow-center {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 6px 0;
  }
  .arrow-down {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
    color: #475569;
    font-size: 11px;
    font-weight: 600;
  }
  .arrow-line {
    width: 2px;
    height: 24px;
    background: linear-gradient(to bottom, #334155, #475569);
  }
  .arrow-head { color: #64748b; font-size: 16px; line-height: 1; margin-top: -4px; }
  .arrow-label {
    font-size: 10px;
    color: #475569;
    letter-spacing: .04em;
    margin-top: 2px;
  }

  /* ── Node cards ── */
  .node {
    border-radius: 12px;
    padding: 16px 18px;
    position: relative;
    cursor: default;
    transition: transform .2s, box-shadow .2s;
    flex: 1;
    min-width: 0;
  }
  .node:hover { transform: translateY(-2px); }

  .node-title {
    font-size: 13px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 7px;
  }
  .node-icon { font-size: 16px; }
  .node-desc { font-size: 11px; color: #94a3b8; line-height: 1.5; }
  .node-badge {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: .07em;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: 10px;
    display: inline-block;
    margin-top: 8px;
  }

  /* Tier 1 — Intent Router */
  .node-router {
    background: linear-gradient(135deg, #1c1a2e, #211d38);
    border: 1.5px solid #6d28d9;
    box-shadow: 0 0 20px rgba(109,40,217,.2);
    max-width: 380px;
    text-align: center;
  }
  .node-router:hover { box-shadow: 0 0 30px rgba(109,40,217,.35); }
  .node-router .node-title { justify-content: center; font-size: 15px; }
  .node-router .node-badge { background: rgba(139,92,246,.2); color: #a78bfa; border: 1px solid rgba(139,92,246,.3); }

  /* Tier 2 — Specialists */
  .node-specialist {
    background: #1a1d2e;
    border: 1.5px solid #334155;
    transition: border-color .2s, box-shadow .2s, transform .2s;
  }
  .node-specialist:hover { border-color: #8b5cf6; box-shadow: 0 4px 20px rgba(139,92,246,.15); }
  .node-s1 { border-top: 3px solid #f97316; }
  .node-s2 { border-top: 3px solid #06b6d4; }
  .node-s3 { border-top: 3px solid #10b981; }
  .node-s4 { border-top: 3px solid #f59e0b; }
  .node-s1 .node-badge { background: rgba(249,115,22,.15); color: #fb923c; }
  .node-s2 .node-badge { background: rgba(6,182,212,.15); color: #22d3ee; }
  .node-s3 .node-badge { background: rgba(16,185,129,.15); color: #34d399; }
  .node-s4 .node-badge { background: rgba(245,158,11,.15); color: #fbbf24; }

  /* Tier 3 — Skills */
  .skills-section {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-top: 0;
  }
  .skill-group {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 14px;
    transition: border-color .2s;
  }
  .skill-group:hover { border-color: #334155; }
  .skill-group-header {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e293b;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .sg-mda { color: #fb923c; border-bottom-color: rgba(249,115,22,.2); }
  .sg-content { color: #22d3ee; border-bottom-color: rgba(6,182,212,.2); }
  .sg-report { color: #34d399; border-bottom-color: rgba(16,185,129,.2); }
  .sg-know { color: #fbbf24; border-bottom-color: rgba(245,158,11,.2); }
  .skill-pill {
    font-size: 10px;
    color: #94a3b8;
    background: #1e293b;
    border-radius: 5px;
    padding: 4px 8px;
    margin-bottom: 5px;
    display: flex;
    align-items: center;
    gap: 5px;
    line-height: 1.4;
  }
  .skill-pill:last-child { margin-bottom: 0; }
  .skill-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .dot-mda { background: #fb923c; }
  .dot-content { background: #22d3ee; }
  .dot-report { background: #34d399; }
  .dot-know { background: #fbbf24; }

  /* Tools row */
  .tools-row {
    width: 100%;
    background: #0d1117;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 18px 20px;
  }
  .tools-row-title {
    font-size: 11px;
    font-weight: 700;
    color: #34d399;
    letter-spacing: .08em;
    text-transform: uppercase;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 7px;
  }
  .tools-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
  }
  .tool-chip {
    font-size: 10px;
    color: #64748b;
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 4px 10px;
    display: flex;
    align-items: center;
    gap: 5px;
    transition: border-color .2s, color .2s;
  }
  .tool-chip:hover { border-color: #334155; color: #94a3b8; }
  .tool-chip-icon { font-size: 12px; }

  /* Data sources */
  .data-row {
    width: 100%;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .data-chip {
    font-size: 11px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: transform .15s;
  }
  .data-chip:hover { transform: scale(1.03); }
  .dc-ga4 { background: rgba(249,115,22,.1); border: 1px solid rgba(249,115,22,.25); color: #fb923c; }
  .dc-sc { background: rgba(16,185,129,.1); border: 1px solid rgba(16,185,129,.25); color: #34d399; }
  .dc-meta { background: rgba(99,102,241,.1); border: 1px solid rgba(99,102,241,.25); color: #818cf8; }
  .dc-gads { background: rgba(6,182,212,.1); border: 1px solid rgba(6,182,212,.25); color: #22d3ee; }
  .dc-ig { background: rgba(236,72,153,.1); border: 1px solid rgba(236,72,153,.25); color: #f472b6; }
  .dc-ph { background: rgba(245,158,11,.1); border: 1px solid rgba(245,158,11,.25); color: #fbbf24; }
  .dc-web { background: rgba(139,92,246,.1); border: 1px solid rgba(139,92,246,.25); color: #a78bfa; }

  /* ── How a request flows ── */
  .flow-steps {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1px;
    background: #1e293b;
    border: 1px solid #1e293b;
    border-radius: 14px;
    overflow: hidden;
    margin-top: 16px;
  }
  .flow-step {
    background: #0f1117;
    padding: 20px 18px;
    position: relative;
  }
  .flow-step-num {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: #1e293b;
    color: #94a3b8;
    font-size: 12px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
  }
  .flow-step-title { font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 5px; }
  .flow-step-desc { font-size: 11px; color: #64748b; line-height: 1.5; }

  /* ── Output card ── */
  .output-card {
    background: linear-gradient(135deg, #0d1f12, #0f1a2e);
    border: 1.5px solid #166534;
    border-radius: 12px;
    padding: 20px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    max-width: 500px;
    margin: 0 auto;
  }
  .output-icon { font-size: 32px; }
  .output-text { }
  .output-title { font-size: 15px; font-weight: 700; color: #4ade80; margin-bottom: 4px; }
  .output-desc { font-size: 12px; color: #64748b; line-height: 1.5; }

  /* ── Legend ── */
  .legend {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid #1e293b;
  }
  .legend-item { display: flex; align-items: center; gap: 7px; font-size: 12px; color: #64748b; }
  .legend-dot { width: 10px; height: 10px; border-radius: 50%; }

  @media (max-width: 900px) {
    .skills-section { grid-template-columns: repeat(2, 1fr); }
    .tier-nodes { flex-wrap: wrap; }
  }
  @media (max-width: 600px) {
    .skills-section { grid-template-columns: 1fr; }
    .tier-label-col { display: none; }
    .tldr-bullets { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<!-- Top nav -->
<div class="topbar">
  <div class="topbar-brand">Sourcy <span>Analyst</span></div>
  <a href="/" class="topbar-back">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
    Back to Dashboard
  </a>
</div>

<div class="page">

  <!-- ══ TLDR ══ -->
  <div class="tldr-card">
    <div class="tldr-badge">🧠 TLDR — Read This First</div>
    <div class="tldr-headline">How Sourcy Analyst works — explained like you're 5</div>
    <div class="tldr-body">
      Imagine you have a <strong>super smart secretary</strong> at the front desk.
      You walk in and say <em>"How are our ads doing?"</em>
      The secretary doesn't know marketing — but they know <strong>exactly who to call</strong>.
      They pick up the phone and call the right expert (or a few at once).
      Each expert reads your data, writes a report, and hands it back.
      The secretary puts all the reports into one beautiful dashboard — and hands it to you. That's it.
    </div>
    <div class="tldr-bullets">
      <div class="tldr-bullet">
        <div class="tldr-bullet-icon">📬</div>
        <div class="tldr-bullet-text">
          <strong>You ask a question</strong>
          Type anything — "How are my ads doing?" or "Audit my SEO"
        </div>
      </div>
      <div class="tldr-bullet">
        <div class="tldr-bullet-icon">🧭</div>
        <div class="tldr-bullet-text">
          <strong>Router decides</strong>
          The Intent Router reads your question and picks the right specialist(s) — instantly
        </div>
      </div>
      <div class="tldr-bullet">
        <div class="tldr-bullet-icon">🔬</div>
        <div class="tldr-bullet-text">
          <strong>Specialists go to work</strong>
          Up to 4 specialists run in parallel, each calling the tools they need
        </div>
      </div>
      <div class="tldr-bullet">
        <div class="tldr-bullet-icon">📊</div>
        <div class="tldr-bullet-text">
          <strong>Dashboard appears</strong>
          Everything gets merged into an interactive HTML report — no manual work
        </div>
      </div>
    </div>
  </div>

  <!-- ══ Architecture Diagram ══ -->
  <div class="section-label">Architecture — Full System Map</div>

  <div class="diagram-wrap">
    <div class="flow">

      <!-- ─ USER ─ -->
      <div class="tier-row">
        <div class="tier-label-col"><span class="tier-label" style="background:rgba(255,255,255,.05);color:#475569;border-color:#2d3748">You</span></div>
        <div class="tier-nodes">
          <div class="node node-router" style="background:#111827;border-color:#334155;box-shadow:none;max-width:360px;">
            <div class="node-title" style="justify-content:center;">
              <span class="node-icon">💬</span> Your Question
            </div>
            <div class="node-desc" style="text-align:center;">"How are our ads doing?" · "Audit my SEO" · "Write a blog post"</div>
          </div>
        </div>
        <div style="width:120px;flex-shrink:0;"></div>
      </div>

      <!-- ─ Arrow ─ -->
      <div class="arrow-row">
        <div class="tier-label-col"></div>
        <div class="arrow-center">
          <div class="arrow-down">
            <div class="arrow-line"></div>
            <div class="arrow-head">▼</div>
            <div class="arrow-label">sent to</div>
          </div>
        </div>
        <div style="width:120px;"></div>
      </div>

      <!-- ─ TIER 1: INTENT ROUTER ─ -->
      <div class="tier-row">
        <div class="tier-label-col"><span class="tier-label tier-1-label">Tier 1</span></div>
        <div class="tier-nodes">
          <div class="node node-router">
            <div class="node-title"><span class="node-icon">🧭</span> Intent Router</div>
            <div class="node-desc">The brain that reads your question and decides which expert to call. It never answers itself — it just routes.</div>
            <span class="node-badge">gpt-5.4 · Always-on gateway</span>
          </div>
        </div>
        <div style="width:120px;flex-shrink:0;"></div>
      </div>

      <!-- ─ Arrow ─ -->
      <div class="arrow-row">
        <div class="tier-label-col"></div>
        <div class="arrow-center">
          <div class="arrow-down">
            <div class="arrow-line"></div>
            <div class="arrow-head">▼</div>
            <div class="arrow-label">delegates to one or more</div>
          </div>
        </div>
        <div style="width:120px;"></div>
      </div>

      <!-- ─ TIER 2: SPECIALISTS ─ -->
      <div class="tier-row">
        <div class="tier-label-col"><span class="tier-label tier-2-label">Tier 2</span></div>
        <div class="tier-nodes">

          <div class="node node-specialist node-s1">
            <div class="node-title"><span class="node-icon">📈</span> Marketing Data Analyst</div>
            <div class="node-desc">Handles all data questions — traffic, ads, SEO, competitors, paid/organic overlap. Runs 7 skills in parallel.</div>
            <span class="node-badge">Data &amp; Performance</span>
          </div>

          <div class="node node-specialist node-s2">
            <div class="node-title"><span class="node-icon">✍️</span> Content Engine</div>
            <div class="node-desc">Runs content audits, writes blogs &amp; landing pages, scores quality. Has 12 sub-skills for every content need.</div>
            <span class="node-badge">SEO · GEO · EEAT · Writing</span>
          </div>

          <div class="node node-specialist node-s3">
            <div class="node-title"><span class="node-icon">📋</span> Report Builder</div>
            <div class="node-desc">Builds standalone reports or combines output from other agents into a polished dashboard on demand.</div>
            <span class="node-badge">HTML Dashboards</span>
          </div>

          <div class="node node-specialist node-s4">
            <div class="node-title"><span class="node-icon">🎓</span> Knowledge Expert</div>
            <div class="node-desc">Answers strategic questions about SEO, GEO, AEO, and ads best practices — no data needed, just expertise.</div>
            <span class="node-badge">Strategy &amp; Advice</span>
          </div>

        </div>
        <div style="width:120px;flex-shrink:0;"></div>
      </div>

      <!-- ─ Arrow ─ -->
      <div class="arrow-row">
        <div class="tier-label-col"></div>
        <div class="arrow-center">
          <div class="arrow-down">
            <div class="arrow-line"></div>
            <div class="arrow-head">▼</div>
            <div class="arrow-label">each specialist calls its own skills</div>
          </div>
        </div>
        <div style="width:120px;"></div>
      </div>

      <!-- ─ TIER 3: SKILLS ─ -->
      <div class="tier-row" style="align-items:flex-start;">
        <div class="tier-label-col" style="padding-top:14px;"><span class="tier-label tier-3-label">Tier 3</span></div>
        <div class="tier-nodes" style="padding:0;">
          <div class="skills-section">

            <!-- MDA skills -->
            <div class="skill-group">
              <div class="skill-group-header sg-mda">📈 Data Analyst Skills</div>
              <div class="skill-pill"><span class="skill-dot dot-mda"></span>Traffic Analyst</div>
              <div class="skill-pill"><span class="skill-dot dot-mda"></span>SEO Analyst</div>
              <div class="skill-pill"><span class="skill-dot dot-mda"></span>GEO / AEO Analyst</div>
              <div class="skill-pill"><span class="skill-dot dot-mda"></span>Competitor Analyst</div>
              <div class="skill-pill"><span class="skill-dot dot-mda"></span>Paid/Organic Overlap</div>
              <div class="skill-pill"><span class="skill-dot dot-mda"></span>Socials Analyst</div>
              <div class="skill-pill"><span class="skill-dot dot-mda"></span>Recommendation Engine</div>
              <div class="skill-pill"><span class="skill-dot dot-mda"></span>Synthesis Agent</div>
            </div>

            <!-- Content engine skills -->
            <div class="skill-group">
              <div class="skill-group-header sg-content">✍️ Content Engine Skills</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>SEO Content Auditor</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>GEO Content Analyst</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>AEO Analyst</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>EEAT Auditor</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>Entity Optimizer</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>Keyword Strategist</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>Technical SEO Auditor</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>Blog Writer</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>Landing Page Writer</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>Content Brief Generator</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>Content Quality Scorer</div>
              <div class="skill-pill"><span class="skill-dot dot-content"></span>Content Synthesis Agent</div>
            </div>

            <!-- Report builder -->
            <div class="skill-group">
              <div class="skill-group-header sg-report">📋 Report Builder</div>
              <div class="skill-pill"><span class="skill-dot dot-report"></span>HTML Dashboard Builder</div>
              <div class="skill-pill"><span class="skill-dot dot-report"></span>Code-Gen Engine</div>
              <div class="skill-pill"><span class="skill-dot dot-report"></span>Chart Renderer (ECharts)</div>
              <div class="skill-pill"><span class="skill-dot dot-report"></span>Score Breakdowns</div>
              <div class="skill-pill"><span class="skill-dot dot-report"></span>Funnel Visualizer</div>
              <div class="skill-pill"><span class="skill-dot dot-report"></span>Reasoning Chain Cards</div>
              <div class="skill-pill"><span class="skill-dot dot-report"></span>Action Item Builder</div>
            </div>

            <!-- Knowledge expert -->
            <div class="skill-group">
              <div class="skill-group-header sg-know">🎓 Knowledge Expert</div>
              <div class="skill-pill"><span class="skill-dot dot-know"></span>SEO Best Practices</div>
              <div class="skill-pill"><span class="skill-dot dot-know"></span>GEO / AI Visibility</div>
              <div class="skill-pill"><span class="skill-dot dot-know"></span>AEO / Answer Engine</div>
              <div class="skill-pill"><span class="skill-dot dot-know"></span>Paid Ads Strategy</div>
              <div class="skill-pill"><span class="skill-dot dot-know"></span>Sourcy Business Context</div>
            </div>

          </div>
        </div>
        <div style="width:120px;flex-shrink:0;"></div>
      </div>

      <!-- ─ Arrow ─ -->
      <div class="arrow-row">
        <div class="tier-label-col"></div>
        <div class="arrow-center">
          <div class="arrow-down">
            <div class="arrow-line"></div>
            <div class="arrow-head">▼</div>
            <div class="arrow-label">skills call tools to fetch real data</div>
          </div>
        </div>
        <div style="width:120px;"></div>
      </div>

      <!-- ─ TOOLS ─ -->
      <div class="tier-row">
        <div class="tier-label-col"><span class="tier-label tier-tools-label">Tools</span></div>
        <div class="tier-nodes">
          <div class="tools-row">
            <div class="tools-row-title">🔧 Live Data Tools — called automatically by skills</div>
            <div class="tools-grid">
              <div class="tool-chip"><span class="tool-chip-icon">📊</span> Google Analytics 4</div>
              <div class="tool-chip"><span class="tool-chip-icon">🔍</span> Google Search Console</div>
              <div class="tool-chip"><span class="tool-chip-icon">💰</span> Google Ads API</div>
              <div class="tool-chip"><span class="tool-chip-icon">📘</span> Meta Ads API</div>
              <div class="tool-chip"><span class="tool-chip-icon">📸</span> Instagram Insights</div>
              <div class="tool-chip"><span class="tool-chip-icon">🦔</span> PostHog Analytics</div>
              <div class="tool-chip"><span class="tool-chip-icon">🌐</span> Web Crawler (requests + BS4)</div>
              <div class="tool-chip"><span class="tool-chip-icon">🤖</span> Robots.txt Checker</div>
              <div class="tool-chip"><span class="tool-chip-icon">🗺️</span> Sitemap Parser</div>
              <div class="tool-chip"><span class="tool-chip-icon">📝</span> HTML Component Builder</div>
              <div class="tool-chip"><span class="tool-chip-icon">⚙️</span> Report Script Executor</div>
              <div class="tool-chip"><span class="tool-chip-icon">🏎️</span> Core Web Vitals (CrUX)</div>
            </div>
          </div>
        </div>
        <div style="width:120px;flex-shrink:0;"></div>
      </div>

      <!-- ─ Arrow ─ -->
      <div class="arrow-row">
        <div class="tier-label-col"></div>
        <div class="arrow-center">
          <div class="arrow-down">
            <div class="arrow-line"></div>
            <div class="arrow-head">▼</div>
            <div class="arrow-label">everything gets assembled into</div>
          </div>
        </div>
        <div style="width:120px;"></div>
      </div>

      <!-- ─ OUTPUT ─ -->
      <div class="tier-row">
        <div class="tier-label-col"><span class="tier-label tier-data-label">Output</span></div>
        <div class="tier-nodes">
          <div class="output-card">
            <div class="output-icon">📊</div>
            <div class="output-text">
              <div class="output-title">Interactive HTML Dashboard</div>
              <div class="output-desc">Tabbed report with charts, KPIs, scorecards, reasoning chains, and action items. Auto-saved and linkable.</div>
            </div>
          </div>
        </div>
        <div style="width:120px;flex-shrink:0;"></div>
      </div>

    </div><!-- /flow -->
  </div><!-- /diagram-wrap -->

  <!-- ── How a request flows ── -->
  <div style="margin-top:56px;">
    <div class="section-label">A Request, Step by Step</div>
    <div class="flow-steps">
      <div class="flow-step">
        <div class="flow-step-num" style="background:rgba(249,115,22,.15);color:#fb923c;">1</div>
        <div class="flow-step-title">You type a question</div>
        <div class="flow-step-desc">"How are our Meta Ads performing?" — the ticket is created and sent to the WebSocket pipeline.</div>
      </div>
      <div class="flow-step">
        <div class="flow-step-num" style="background:rgba(139,92,246,.15);color:#a78bfa;">2</div>
        <div class="flow-step-title">Intent Router reads it</div>
        <div class="flow-step-desc">The router classifies intent in &lt;2s and picks Marketing Data Analyst + Recommendation Engine.</div>
      </div>
      <div class="flow-step">
        <div class="flow-step-num" style="background:rgba(6,182,212,.15);color:#22d3ee;">3</div>
        <div class="flow-step-title">Skills run in parallel</div>
        <div class="flow-step-desc">Traffic Analyst + Meta Ads tool + Recommendation Engine fire simultaneously — not one by one.</div>
      </div>
      <div class="flow-step">
        <div class="flow-step-num" style="background:rgba(16,185,129,.15);color:#34d399;">4</div>
        <div class="flow-step-title">Synthesis Agent codes the report</div>
        <div class="flow-step-desc">It writes ~200 lines of Python that call html_components functions, then exec()'s them to build the HTML.</div>
      </div>
      <div class="flow-step">
        <div class="flow-step-num" style="background:rgba(245,158,11,.15);color:#fbbf24;">5</div>
        <div class="flow-step-title">Dashboard appears in chat</div>
        <div class="flow-step-desc">The HTML file is saved to /reports/ and a live link appears in your ticket — click to open.</div>
      </div>
    </div>
  </div>

  <!-- ── Legend ── -->
  <div class="legend">
    <div class="legend-item"><span class="legend-dot" style="background:#f97316;"></span>Marketing Data Analyst track</div>
    <div class="legend-item"><span class="legend-dot" style="background:#06b6d4;"></span>Content Engine track</div>
    <div class="legend-item"><span class="legend-dot" style="background:#10b981;"></span>Report Builder</div>
    <div class="legend-item"><span class="legend-dot" style="background:#f59e0b;"></span>Knowledge Expert</div>
    <div class="legend-item"><span class="legend-dot" style="background:#6d28d9;"></span>Intent Router (entry point)</div>
    <div class="legend-item" style="margin-left:auto;color:#475569;font-size:11px;">Model: gpt-5.4 · Framework: OpenAI Agents SDK · Server: FastAPI + WebSocket</div>
  </div>

</div><!-- /page -->
</body>
</html>"""
