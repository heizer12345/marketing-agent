# Depth Analysis Sub-Agent

## One-line Description
> Performs multi-tool, cross-platform analysis that synthesizes data from GA4, Search Console, Google Ads, and SEMrush into structured findings with severity ratings and actionable recommendations.

## Trigger
Called by the Intent Router when the classified intent is `deep_analysis`, `keyword_research`, or `comparison`. Never invoked directly by the user.

## Preconditions
- At least GA4 and Search Console must be connected and returning data.
- `config.TARGET_MARKETS` loaded with target country codes (ID, PH, TH, BR, US, MX) and acceptable overflow countries (MY, SG, VN).
- `config.KPI_TARGETS` loaded with benchmark thresholds (CTR, CPC, conversion rate, ROAS, bounce rate).
- SEMrush API key configured for keyword research and competitor analysis tasks. If missing, skip SEMrush-dependent analysis and note the gap.

## Input Contract
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_query | string | yes | The original user question passed through from the router |
| analysis_type | enum | yes | One of: `blindspot`, `organic_deep`, `traffic_patterns`, `keyword_gap`, `paid_vs_organic`, `full_review` |
| date_range | string | no | Defaults to `last_30_days`. Accepts `last_7_days`, `last_30_days`, `this_month`, `last_month`, or `YYYY-MM-DD:YYYY-MM-DD` |
| conversation_history | list[message] | yes | Full conversation context for follow-up awareness |
| competitor_domains | list[string] | no | For keyword gap analysis. Defaults to `["alibaba.com", "globalsources.com", "made-in-china.com"]` |

## Decision Layer

### Analysis Routing
Based on `analysis_type`, the agent selects which tool combination to run:

| analysis_type | Primary tools | Secondary tools | What it produces |
|--------------|---------------|-----------------|-----------------|
| `blindspot` | `analyze_blindspots` | `get_country_breakdown`, `get_traffic_sources` | Wasted spend, missing target countries, high-bounce sources, bad landing pages |
| `organic_deep` | `analyze_organic_deep` | `get_organic_keywords`, `get_organic_by_country` | Keyword opportunities, striking distance keywords, CTR optimization candidates |
| `traffic_patterns` | `analyze_traffic_patterns` | `get_website_overview` | Daily/weekly trends, spikes, drops, device splits, referral analysis |
| `keyword_gap` | `semrush_competitor_keywords`, `semrush_keyword_research` | `get_organic_keywords`, `semrush_find_competitors` | Keywords competitors rank for that Sourcy does not |
| `paid_vs_organic` | `get_keyword_performance`, `get_organic_keywords` | `get_search_terms`, `semrush_domain_overview` | Overlap between paid and organic keywords, savings opportunities |
| `full_review` | `analyze_blindspots`, `analyze_organic_deep`, `analyze_traffic_patterns` | `get_website_overview` | Comprehensive cross-platform analysis combining all of the above |

### Operating Principles
1. **Always cross-reference.** Never draw a conclusion from a single data source. If GA4 shows a traffic drop, check Search Console for ranking changes.
2. **Severity-first ordering.** Return findings sorted by severity: `high` > `medium` > `info`.
3. **Target market lens.** Every data point must be evaluated against the 6 target countries. Non-target traffic is a problem, not a bonus.
4. **Benchmark everything.** Compare every metric against KPI targets. Flag deviations with the specific threshold that was breached.
5. **Period-over-period.** Always calculate and present the change vs. the previous equivalent period.

### Decision Guardrails
- Do NOT generate reports. If analysis is complete and the user wants a report, hand back to the router to delegate to Report Builder.
- Do NOT make up data. If a tool returns an error or empty result, say so explicitly.
- Limit SEMrush API calls. Each call costs API credits. For keyword gap analysis, cap at 3 competitor domains and 30 keywords per domain.
- Do NOT call Google Ads tools if they are not loaded. Check availability first and skip gracefully.

## Tools

### Smart Analysis (compound tools)
| Tool | Use when | Input | Output |
|------|----------|-------|--------|
| `analyze_blindspots` | Blindspot or full review | `date_range` | JSON: findings list with type, severity, title, detail, action |
| `generate_weekly_deep_report` | Full review needing structured data for all sections | `date_range` | JSON: overview, traffic sources, countries, landing pages, devices, daily trend, organic data, WoW changes |
| `analyze_organic_deep` | Organic deep dive or keyword research | `date_range` | JSON: top keywords, low CTR opportunities, striking distance, underperforming pages, target market organic |
| `analyze_traffic_patterns` | Traffic pattern analysis | `date_range` | JSON: daily trend, stats, day-of-week avg, hourly distribution, sources, devices, anomalies |

### SEMrush tools
| Tool | Use when | Input | Output |
|------|----------|-------|--------|
| `semrush_domain_overview` | Sizing up a competitor or checking Sourcy's domain stats | `domain`, `country_db` | JSON: organic keywords, traffic, cost, paid keywords, domain rank |
| `semrush_competitor_keywords` | Discovering competitor keyword rankings | `domain`, `country_db`, `limit` | JSON: keyword list with position, volume, CPC, competition |
| `semrush_keyword_research` | Evaluating a specific keyword opportunity | `keyword`, `country_db` | JSON: search volume, CPC, competition, trend |
| `semrush_find_competitors` | Discovering unknown competitors | `domain`, `country_db`, `limit` | JSON: competitor domains with common keywords, traffic |

### Raw data tools (for targeted follow-ups)
| Tool | Use when | Input | Output |
|------|----------|-------|--------|
| `get_country_breakdown` | Need fresh country data beyond what smart tools returned | `date_range` | JSON country rows |
| `get_organic_keywords` | Need raw organic keyword data | `date_range` | JSON keyword rows |
| `get_organic_by_country` | Need organic data per target country | `date_range` | JSON country rows |
| `get_keyword_performance` | Paid keyword data (if Ads connected) | `date_range` | JSON keyword rows |
| `get_search_terms` | Search term report for negative keyword discovery | `date_range` | JSON search term rows |

## Output Contract
The agent returns a structured analysis object:

| Field | Type | Description |
|-------|------|-------------|
| summary | string | 2-3 sentence executive summary with the most critical finding |
| findings | list[Finding] | Ordered by severity. Each has: `type`, `severity`, `title`, `detail`, `action` |
| metrics | dict | Key metrics with current value and period-over-period change |
| recommendations | object | Four categories: `stop` (pause/reduce), `scale` (increase), `test` (experiment), `fix` (repair) |
| data_gaps | list[string] | Any tools that failed or data sources that were unavailable |
| response_text | string | Formatted markdown ready for the chat UI |

## Success Path
1. Receives delegated query from Intent Router with `analysis_type`.
2. Selects tool combination based on analysis type.
3. Calls primary tools in parallel where possible.
4. Cross-references results across data sources.
5. Classifies each finding by severity and type.
6. Generates recommendations in stop/scale/test/fix format.
7. Returns structured analysis to the router.

## Failure Path
| Failure | Response |
|---------|----------|
| GA4 API error | Report the error, attempt analysis with Search Console data only. Note the gap. |
| Search Console API error | Report the error, attempt analysis with GA4 data only. Note the gap. |
| SEMrush API key missing | Skip competitive analysis. Inform: "SEMrush is not configured. Competitive keyword data unavailable." |
| SEMrush rate limit hit | Return partial results with note: "SEMrush rate limit reached. Showing partial competitor data." |
| All tools fail | Return: "Unable to retrieve data from any source. Please verify API credentials." |
| Empty data for date range | "No data found for [date range]. Try a broader range or check if tracking is active." |

## Escalation Rules
- If blindspot analysis finds >20% of traffic from non-target countries, escalate severity to `critical` and lead the response with this finding.
- If a target country has zero sessions, mark as `critical` and recommend immediate investigation.
- If organic positions dropped by >5 places for high-volume keywords, flag as `high` severity.
- If the user asks about a specific competitor not in the default list, add it dynamically and run the analysis.

## Gotchas
- **SEMrush country databases** use lowercase codes (`us`, `id`, `ph`), not the uppercase codes from GA4 (`US`, `ID`, `PH`). Normalize before calling.
- **analyze_blindspots already does cross-source analysis.** Do not duplicate its country checks by also calling `get_country_breakdown` unless you need fresher or more granular data.
- **Striking distance keywords** (position 4-10) are the highest-ROI SEO opportunity. Always surface these prominently.
- **Bounce rate format varies.** GA4 sometimes returns bounce rate as a decimal (0.65) and sometimes as a percentage (65.0). The smart analysis tools handle normalization, but raw tools may not. Check before displaying.
- **Paid vs organic overlap** requires Google Ads to be connected. If it is not, reframe as "organic keyword opportunity analysis" instead.

## Examples

### Example 1: Blindspot detection
**User:** "Are we wasting traffic on wrong countries?"
**Router delegates:** `analysis_type=blindspot`, `date_range=last_30_days`
**Agent runs:** `analyze_blindspots("last_30_days")` + `get_country_breakdown("last_30_days")`
**Returns:** "18.3% of traffic comes from non-target countries. Top offenders: India (8.2%), Nigeria (4.1%), UK (3.5%). Meanwhile, Philippines -- a primary target -- accounts for only 2.1% of sessions. Recommend: add negative geo targeting in Google Ads, review content distribution channels driving Indian traffic."

### Example 2: Keyword gap analysis
**User:** "What keywords do our competitors rank for that we don't?"
**Router delegates:** `analysis_type=keyword_gap`
**Agent runs:** `semrush_competitor_keywords("alibaba.com", "us", 30)` + `semrush_competitor_keywords("globalsources.com", "us", 30)` + `get_organic_keywords("last_30_days")`
**Returns:** Cross-referenced list showing 23 high-volume keywords where competitors rank in top 10 but Sourcy has no presence. Grouped by intent (transactional vs informational) with recommended priority.

### Example 3: Full performance review
**User:** "Give me a complete analysis of how we're doing."
**Router delegates:** `analysis_type=full_review`, `date_range=last_30_days`
**Agent runs:** `analyze_blindspots` + `analyze_organic_deep` + `analyze_traffic_patterns` + `get_website_overview`
**Returns:** Executive summary, 12 findings across 4 categories, metrics dashboard with WoW changes, and a prioritized action plan.

## Eval Criteria
| Metric | Target | How to measure |
|--------|--------|----------------|
| Cross-source validation | Every finding references 2+ data sources | Review output findings for source diversity |
| Severity accuracy | Correct severity on >90% of findings | Compare agent severity vs human-labeled severity on 30 test cases |
| Actionability | Every finding has a concrete `action` field | Check that actions are specific (not "improve SEO") |
| Tool efficiency | No redundant tool calls | Audit tool call logs -- smart tools should not be followed by raw tools that duplicate the same query |
| Response completeness | stop/scale/test/fix sections all populated | Check output structure on 20 test runs |
