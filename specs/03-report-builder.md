# Report Builder Sub-Agent

## One-line Description
> Generates self-contained HTML reports with Chart.js visualizations, KPI cards, data tables, and insight boxes -- activated only on explicit user request.

## Trigger
Called by the Intent Router exclusively when the classified intent is `report_request`. The user must explicitly say "generate report", "create report", "build a report", or similar. This agent is never auto-triggered.

## Preconditions
- Conversation history must be available. Reports incorporate insights from the current session, not just raw data.
- The `generate_html_report` tool must be available and the `public/reports/` output directory must exist and be writable.
- At least GA4 and Search Console must be returning data. Google Ads data is included when available.
- The Jinja2-based report template (in `tools/report_generator.py`) must be loaded.

## Input Contract
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_query | string | yes | The report request (may specify scope: "weekly report", "organic report", "country report") |
| conversation_history | list[message] | yes | Full session history. Insights from earlier analysis are woven into the report. |
| date_range | string | no | Defaults to `last_7_days` for weekly reports, `last_30_days` for monthly. Inferred from user request or conversation context. |
| prior_analysis | object | no | If Depth Analysis was already run this session, its structured output is passed to avoid redundant tool calls. |

## Decision Layer

### Report Type Selection
The agent infers which report to build based on the user request and conversation history:

| Report type | Trigger phrases | Data tools called | Sections included |
|------------|----------------|-------------------|-------------------|
| **Weekly Performance** | "weekly report", "performance report", default | `generate_weekly_deep_report` + `analyze_blindspots` | KPI cards, traffic trend, source breakdown, country table, organic keywords, blindspot findings |
| **Organic/SEO Focus** | "organic report", "SEO report" | `analyze_organic_deep` + `analyze_blindspots` | Organic KPIs, keyword rankings, striking distance, CTR opportunities, page performance |
| **Country/Geo Focus** | "country report", "geo report" | `generate_weekly_deep_report` + `analyze_blindspots` | Country comparison table, target vs non-target breakdown, per-country organic data |
| **Custom/Session Summary** | "report on what we discussed", "summarize our analysis" | Minimal (reuses prior_analysis) | Whatever was analyzed in the session, packaged as a report |

### Operating Principles
1. **Conversation-aware.** The report is a formatted summary of the analysis session, not just a data dump. Reference specific findings from earlier in the conversation.
2. **Data freshness.** If `prior_analysis` data is from the same session and same date range, reuse it. Do not re-fetch unless the user specifies a different date range.
3. **Visual-first.** Every report must include at least 2 Chart.js visualizations. Charts make the report shareable with stakeholders who do not read raw numbers.
4. **Self-contained HTML.** Reports load Chart.js from CDN. No other external dependencies. The file must render correctly when opened directly in a browser.
5. **Consistent design system.** Follow the existing template styles: dark gradient header, KPI grid cards, white section cards with subtle shadows, color-coded insight boxes.

### Decision Guardrails
- Do NOT generate a report if the user did not explicitly ask for one.
- Do NOT include raw JSON in the report. All data must be formatted into tables, cards, or charts.
- Do NOT generate empty sections. If a data source is unavailable, omit that section and note it in the report header.
- Limit report size. Cap at 15 sections max. For very large datasets, show top 10 rows with a note.

## Tools

| Tool | Use when | Input | Output |
|------|----------|-------|--------|
| `generate_weekly_deep_report` | Need comprehensive multi-section data | `date_range` | JSON with overview, previous period, traffic sources, countries, landing pages, devices, daily trend, organic queries/countries/pages, WoW changes |
| `analyze_blindspots` | Need findings for insight boxes | `date_range` | JSON with findings list (type, severity, title, detail, action) |
| `analyze_organic_deep` | SEO-focused report | `date_range` | JSON with keywords, opportunities, striking distance, pages |
| `generate_html_report` | Final report assembly | `report_json` (string) | Filename of generated HTML report |

### Report JSON Structure (input to generate_html_report)
The agent must construct a complete JSON object with these fields:

```
{
  "title": "Weekly Performance Report",
  "subtitle": "Sourcy Global - sourcy.ai",
  "date_range": "Apr 1 - Apr 7, 2026",
  "kpi_cards": [
    {"label": "Sessions", "value": "2,340", "change": "+12%", "change_class": "positive"}
  ],
  "sections": [
    {
      "title": "Traffic Sources",
      "type": "table",
      "headers": ["Source", "Sessions", "Bounce Rate"],
      "rows": [["Organic", "1,200", "42%"]]
    },
    {
      "title": "Sessions Trend",
      "type": "chart",
      "chart_id": "trendChart"
    },
    {
      "title": "Geo Targeting Issue",
      "type": "insight_box",
      "severity": "warning",
      "content": "18% of traffic from non-target countries."
    }
  ],
  "charts_js": "new Chart(document.getElementById('trendChart'), { ... });"
}
```

## Output Contract
| Field | Type | Description |
|-------|------|-------------|
| report_filename | string | Generated filename, e.g. `report_20260408_143022.html` |
| report_url | string | Relative URL path: `/reports/report_20260408_143022.html` |
| response_text | string | Chat message confirming report generation with a link |
| sections_included | list[string] | Audit list of what sections made it into the report |

## Success Path
1. Receives delegation from Intent Router with `report_request` intent.
2. Determines report type from user query and conversation context.
3. Checks if `prior_analysis` data is available and fresh.
4. Calls data tools for any missing sections (typically `generate_weekly_deep_report` + `analyze_blindspots`).
5. Constructs the full report JSON with: KPI cards (4-6), data tables (2-4), Chart.js code (2-3 charts), insight boxes (1-5).
6. Calls `generate_html_report` with the JSON string.
7. Returns the report filename and URL to the router.
8. Router sends chat message with the report link to the user.

## Failure Path
| Failure | Response |
|---------|----------|
| `generate_html_report` tool errors | Return the error message. Suggest the user try again. Do not return partial HTML. |
| Data tools return empty results | Generate a minimal report with available data. Add an insight box noting missing sections. |
| Chart.js code has syntax error | The report will render but charts will be blank. Validate JS syntax before passing. |
| Output directory not writable | "Unable to save the report file. Check that `public/reports/` exists and is writable." |
| JSON too large (>100KB of chart data) | Reduce dataset: use top 10 rows instead of full dataset, aggregate daily data into weekly. |

## Escalation Rules
- If the user says "include everything we discussed", scan the full conversation history and extract all findings, metrics, and recommendations mentioned.
- If the user asks for a specific chart type not in the standard set, attempt it with Chart.js (supports line, bar, doughnut, radar, pie, polar area).
- If the report takes >30 seconds to generate, send a progress status message via the router.

## Gotchas
- **Chart IDs must be unique** within a single report. If you define two line charts, use `trendChart1` and `trendChart2`, not both `trendChart`.
- **Chart.js is loaded from CDN.** Reports require internet access to render charts. This is acceptable for the internal dashboard use case.
- **change_class values** must be exactly `"positive"`, `"negative"`, or `"neutral"`. These map to CSS classes for green/red/gray coloring.
- **The charts_js field is a single string** containing all Chart.js initialization code. Multiple `new Chart()` calls are concatenated with semicolons.
- **Insight box severity values:** `"success"` (green), `"warning"` (amber), `"danger"` (red), `"info"` (blue). These map to the CSS classes in the template.
- **Date formatting in report headers** should be human-readable ("Apr 1 - Apr 7, 2026"), not API format ("2026-04-01:2026-04-07").
- **Previous period comparison** is critical. KPI cards without a change percentage look incomplete. Always calculate WoW or MoM changes.

## Examples

### Example 1: Standard weekly report
**User:** "Generate a weekly performance report."
**Agent:** Calls `generate_weekly_deep_report("last_7_days")` + `analyze_blindspots("last_7_days")`. Builds JSON with 5 KPI cards (sessions, users, bounce rate, conversions, organic clicks), 3 tables (traffic sources, country breakdown, top keywords), 3 charts (sessions trend line, source split doughnut, country bar), 4 insight boxes from blindspot findings. Calls `generate_html_report`. Returns: "Report generated: report_20260408_143022.html"

### Example 2: Session summary report
**User (after a deep analysis conversation):** "Great, now put all of this into a report."
**Agent:** Reuses `prior_analysis` from the Depth Analysis run earlier in the session. Adds chart visualizations for the key findings. Incorporates the specific recommendations discussed. Calls `generate_html_report`. Returns a report that reads as a narrative summary of the analysis session, not just raw data tables.

### Example 3: Organic-focused report
**User:** "Create an SEO report for the last 30 days."
**Agent:** Calls `analyze_organic_deep("last_30_days")`. Builds JSON focused on keyword rankings, striking distance opportunities, CTR optimization candidates, page performance. Charts: keyword position distribution (bar), organic clicks trend (line), impressions by country (doughnut). Returns report URL.

## Eval Criteria
| Metric | Target | How to measure |
|--------|--------|----------------|
| Report renders correctly | 100% | Open generated HTML in Chrome, Safari, Firefox -- no JS errors, all charts visible |
| KPI cards present | Every report has 4+ KPI cards | Inspect HTML output |
| Charts render | Every report has 2+ working charts | Visual inspection + browser console check |
| Conversation context included | Reports reference session findings | Compare report insight boxes to conversation history |
| No raw JSON in output | 0 instances | Search report HTML for unformatted JSON blocks |
| File size reasonable | <500KB per report | Check file sizes in output directory |
