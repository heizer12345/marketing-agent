# Intent Router (Master Orchestrator)

## One-line Description
> Classifies every user message into an intent type and either answers directly with raw tools or delegates to the correct specialist sub-agent.

## Trigger
Every inbound user message passes through the Intent Router first. It is the single entry point for the marketing agent system.

## Preconditions
- At least one data source must be connected (GA4, Search Console, or SEMrush). Google Ads is optional (pending API approval).
- Specialist sub-agents (Depth Analysis, Report Builder, Knowledge Expert) must be registered as callable tools via the "agents as tools" pattern.
- `config.TARGET_MARKETS` and `config.KPI_TARGETS` must be loaded.

## Input Contract
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_message | string | yes | Raw user text from the chat interface |
| conversation_history | list[message] | yes | Full message history for context-aware routing |

## Decision Layer

### Intent Classification
The router classifies each message into exactly one intent:

| Intent | Signal words / patterns | Action |
|--------|------------------------|--------|
| `quick_data` | "how many sessions", "what's our CTR", "show me traffic" -- single-metric or simple lookup questions | Answer directly using raw GA4, SC, or Ads tools. No delegation. |
| `deep_analysis` | "analyze", "deep dive", "find blindspots", "what's wrong", "performance review" | Delegate to **Depth Analysis** sub-agent |
| `report_request` | "generate report", "create report", "build a report", "weekly report" | Delegate to **Report Builder** sub-agent |
| `keyword_research` | "what keywords", "competitor keywords", "keyword gap", "SEMrush", "keyword opportunities" | Delegate to **Depth Analysis** (data gathering) then optionally **Knowledge Expert** (strategy layer) |
| `knowledge_question` | "how to improve", "best practices", "what should we do about", "SEO strategy", "GEO tips" | Delegate to **Knowledge Expert** sub-agent |
| `comparison` | "compare organic vs paid", "paid vs organic", "SEMrush vs Search Console", "channel comparison" | Delegate to **Depth Analysis** sub-agent |

When ambiguous, prefer `deep_analysis` over `quick_data`. When the user asks both a data question and a strategy question, route to `deep_analysis` first, then pass results to `knowledge_expert`.

### Operating Principles
1. **Classify before acting.** Never call a tool before determining intent.
2. **Minimum tool calls for quick_data.** One or two raw tools max. Do not over-fetch.
3. **Always pass conversation history** when delegating so sub-agents have full context.
4. **Never auto-generate reports.** Only route to Report Builder on explicit user request.
5. **Graceful degradation.** If Google Ads tools error, inform the user and reclassify using available sources.

### Decision Guardrails
- Do NOT delegate `quick_data` questions to Depth Analysis. Answer them inline.
- Do NOT call `generate_html_report` unless the classified intent is `report_request`.
- If the user asks a question unrelated to marketing data (e.g., "what's the weather"), respond politely that you only handle marketing analytics for Sourcy.
- If a sub-agent fails or times out, catch the error, inform the user, and suggest a simpler alternative.

## Tools

### Raw tools (used directly for `quick_data`)
| Tool | Use when | Input | Output |
|------|----------|-------|--------|
| `get_website_overview` | User asks about sessions, users, bounce rate | `date_range` | JSON overview metrics |
| `get_traffic_sources` | User asks "where is traffic coming from" | `date_range` | JSON channel breakdown |
| `get_country_breakdown` | User asks about a specific country or geo split | `date_range` | JSON country rows |
| `get_landing_pages` | User asks about page performance | `date_range` | JSON page rows |
| `get_audience_segments` | User asks about audience types | `date_range` | JSON segment rows |
| `get_conversion_paths` | User asks about conversion funnels | `date_range` | JSON path rows |
| `get_organic_keywords` | User asks about organic keyword rankings | `date_range` | JSON keyword rows |
| `get_organic_pages` | User asks about top organic pages | `date_range` | JSON page rows |
| `get_organic_by_country` | User asks about organic traffic by country | `date_range` | JSON country rows |

### Sub-agent tools (delegated via agents-as-tools)
| Sub-agent | Use when | What it receives | What it returns |
|-----------|----------|-----------------|-----------------|
| **Depth Analysis** | `deep_analysis`, `keyword_research`, `comparison` | User query + conversation history | Structured analysis with findings, severity, and recommendations |
| **Report Builder** | `report_request` | User query + conversation history + any prior analysis data | HTML report filename and URL |
| **Knowledge Expert** | `knowledge_question`, second pass on `keyword_research` | User query + conversation history + optional data context | Strategic recommendations with citations to knowledge base |

## Output Contract
| Field | Type | Description |
|-------|------|-------------|
| response_text | string | Markdown-formatted answer for the chat UI |
| report_url | string or null | Path to generated HTML report (only for `report_request` intent) |
| tools_called | list[string] | Audit log of which tools/sub-agents were invoked |

## Success Path
1. User sends message.
2. Router classifies intent (zero tool calls at this step -- pure LLM reasoning).
3a. **quick_data**: Router calls 1-2 raw tools, formats response, returns directly.
3b. **deep_analysis / comparison / keyword_research**: Router invokes Depth Analysis sub-agent. Receives structured findings. Formats and returns.
3c. **report_request**: Router invokes Report Builder sub-agent with full conversation context. Returns report URL.
3d. **knowledge_question**: Router invokes Knowledge Expert. Returns strategic advice.
4. Response sent to user via WebSocket.

## Failure Path
| Failure | Response |
|---------|----------|
| All data sources down | "I'm unable to reach any data source right now. Please check API credentials in .env." |
| Sub-agent timeout (>60s) | "The analysis is taking longer than expected. Let me try a simpler approach." Then fall back to raw tools. |
| Google Ads auth error | "Google Ads API isn't connected yet (pending Basic Access). I'll work with GA4 and Search Console." |
| Ambiguous intent | Default to `deep_analysis` and ask a clarifying follow-up at the end of the response. |

## Escalation Rules
- If the user asks the same question twice and gets different numbers, surface both data points and explain the discrepancy (e.g., date range differences, data source lag).
- If the user explicitly says "that's wrong" or "try again", re-run the tools with fresh calls (no caching).
- If a tool returns empty data, tell the user the specific date range and source that returned nothing.

## Gotchas
- **Search Console has a 3-day data lag.** `last_7_days` actually queries 10 days ago to 3 days ago. Do not promise "today's" organic data.
- **Google Ads tools may not be loaded** if `GOOGLE_ADS_REFRESH_TOKEN` is missing. Check `google_ads_tools` list length before routing paid-media questions.
- **Date range normalization.** Users say "this week", "last month", "past 30 days" in many ways. Normalize to the `date_range` enum: `last_7_days`, `last_30_days`, `this_month`, `last_month`, or `YYYY-MM-DD:YYYY-MM-DD`.
- **Report generation is expensive.** It calls `generate_weekly_deep_report` + `analyze_blindspots` + `generate_html_report` (3+ tool calls, heavy data). Never trigger this for a simple question.

## Examples

### Example 1: quick_data
**User:** "How many sessions did we get last week?"
**Router:** Classifies as `quick_data`. Calls `get_website_overview(date_range="last_7_days")`. Returns: "Last week (Mar 31 - Apr 7): 2,340 sessions, up 12% from the prior week."

### Example 2: deep_analysis
**User:** "Are we wasting money on non-target countries?"
**Router:** Classifies as `deep_analysis`. Delegates to Depth Analysis sub-agent. Depth Analysis calls `analyze_blindspots` + `get_country_breakdown`. Returns structured findings about non-target traffic with severity ratings and action items.

### Example 3: report_request
**User:** "Generate a weekly performance report."
**Router:** Classifies as `report_request`. Delegates to Report Builder. Report Builder calls `generate_weekly_deep_report`, `analyze_blindspots`, builds chart config, calls `generate_html_report`. Returns report URL.

## Eval Criteria
| Metric | Target | How to measure |
|--------|--------|----------------|
| Intent classification accuracy | >95% on test set | 50 labeled user messages, check classified intent matches expected |
| quick_data response time | <8 seconds | Measure from user send to response received |
| Correct tool selection | 100% for quick_data | Verify the right raw tool was called for the question type |
| No false report generation | 0 incidents | Reports should never generate unless user explicitly asked |
| Graceful Ads fallback | 100% | When Ads tools are unavailable, no error surfaces to user |
