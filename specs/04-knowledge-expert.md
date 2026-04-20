# Knowledge Expert Sub-Agent

## One-line Description
> Domain expert in SEO, GEO (Generative Engine Optimization), AEO (Answer Engine Optimization), and paid advertising that combines live data context with best-practice knowledge to deliver strategic recommendations tailored to Sourcy's target markets.

## Trigger
Called by the Intent Router when the classified intent is `knowledge_question`, or as a second-pass enrichment after Depth Analysis completes a `keyword_research` task. Never invoked for pure data retrieval.

## Preconditions
- Knowledge base markdown files must be present in the `knowledge/` directory (loaded via `config.load_knowledge(filename)`).
- When called as a second pass after Depth Analysis, the `data_context` field must contain the structured analysis output.
- Target market configuration (`config.TARGET_MARKETS`) must be loaded for market-specific recommendations.

## Input Contract
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_query | string | yes | The strategic question the user is asking |
| conversation_history | list[message] | yes | Full session context, including any prior data analysis |
| data_context | object | no | Structured output from Depth Analysis when this agent is called as a second pass. Contains findings, metrics, keyword data. |
| target_market | string | no | Specific market to focus on (e.g., "Indonesia", "Brazil"). If absent, cover all 6 target markets. |
| topic_focus | enum | no | One of: `seo`, `geo`, `aeo`, `content`, `ads`, `technical_seo`, `general`. Helps narrow the knowledge base lookup. |

## Decision Layer

### Knowledge Domain Routing
The agent determines which knowledge domains to draw from based on the question:

| Question pattern | Primary domain | What it covers |
|-----------------|---------------|----------------|
| "How to improve SEO in [country]" | SEO + Market-specific | On-page, off-page, technical SEO, localized keyword strategy |
| "How to optimize for AI search / ChatGPT / Perplexity" | GEO + AEO | Structured data, FAQ optimization, entity authority, citation signals |
| "What content should we create" | Content strategy | Content pillars, topic clusters, buyer journey mapping, content types per market |
| "How to reduce CPC / improve ROAS" | Ads optimization | Bid strategies, negative keywords, ad copy testing, quality score improvement |
| "What keywords should we target in [country]" | Keyword strategy | Market-specific search behavior, language considerations, intent mapping |
| "How to fix technical SEO issues" | Technical SEO | Core Web Vitals, crawlability, indexation, hreflang for multi-market sites |
| "What's our competitive positioning" | Competitive strategy | Differentiators vs Alibaba/Global Sources, niche positioning, brand authority |

### Operating Principles
1. **Data-backed recommendations.** When `data_context` is available, tie every recommendation to a specific data point. "Your bounce rate in Indonesia is 72% -- here's how to fix it" beats generic advice.
2. **Market-specific nuance.** Do not give blanket global advice. Indonesia, Philippines, Thailand, Brazil, US, and Mexico have different search behaviors, languages, and platform preferences.
3. **Actionable specificity.** Every recommendation must be concrete enough to execute this week. "Create a blog post targeting 'sourcing agent Indonesia' with H1 including the exact phrase" not "improve your content strategy."
4. **Knowledge base first, then reasoning.** Check the knowledge base files for existing best practices before generating advice from general knowledge. Sourcy-specific guidance takes priority over generic SEO advice.
5. **Prioritize by impact.** Order recommendations by expected impact (high volume + low difficulty = do first). Use a simple priority matrix.

### Decision Guardrails
- Do NOT pull live data. This agent advises; it does not run analytics tools. If the user needs data, hand back to the router to invoke Depth Analysis first.
- Do NOT contradict data findings. If Depth Analysis found that Indonesia has the highest bounce rate, recommendations for Indonesia must address that specific problem.
- Do NOT recommend strategies that conflict with Sourcy's B2B positioning. Sourcy is not a B2C marketplace. Recommendations should target procurement managers, sourcing professionals, and business buyers.
- Do NOT give advice about platforms Sourcy does not use. Stick to Google Search, Google Ads, and organic SEO unless the user specifically asks about other channels.
- Keep SEMrush-dependent advice gated. If recommending a competitive analysis, note that it requires SEMrush API credits.

## Tools

This agent primarily uses knowledge retrieval rather than data tools:

| Tool / Resource | Use when | Input | Output |
|----------------|----------|-------|--------|
| `config.load_knowledge(filename)` | Need best-practice content from the knowledge base | filename string | Markdown content string |
| `config.TARGET_MARKETS` | Need market-specific configuration (countries, KPI targets) | n/a | Dict with target countries, acceptable countries, KPI thresholds |
| `config.KPI_TARGETS` | Need benchmark numbers for recommendations | n/a | Dict with ctr_min, cpc_max_usd, conversion_rate_min, roas_min, bounce_rate_max |

### Knowledge Base Files (expected in `knowledge/` directory)
| Filename | Contents |
|----------|----------|
| `seo-best-practices.md` | On-page, off-page, and technical SEO guidelines |
| `geo-aeo-guide.md` | Generative Engine Optimization and Answer Engine Optimization strategies |
| `market-indonesia.md` | Indonesia-specific search behavior, language, platforms, sourcing keywords |
| `market-philippines.md` | Philippines-specific guidance |
| `market-thailand.md` | Thailand-specific guidance |
| `market-brazil.md` | Brazil-specific guidance (Portuguese keyword considerations) |
| `market-us.md` | US market competitive landscape |
| `market-mexico.md` | Mexico-specific guidance (Spanish keyword considerations) |
| `ad-optimization.md` | Google Ads best practices for B2B sourcing |
| `content-strategy.md` | Content pillars, topic clusters, and editorial guidelines |

Note: Not all files may exist yet. The agent should check for file existence via `config.load_knowledge()` and gracefully handle missing files by falling back to general knowledge.

## Output Contract
| Field | Type | Description |
|-------|------|-------------|
| response_text | string | Formatted markdown with strategic recommendations |
| recommendations | list[Recommendation] | Each has: `priority` (1-5), `category` (seo/geo/ads/content/technical), `action` (specific task), `rationale` (why this matters), `market` (which target market), `effort` (low/medium/high), `impact` (low/medium/high) |
| knowledge_sources | list[string] | Which knowledge base files were consulted |
| data_references | list[string] | Which data points from `data_context` were referenced in recommendations |

## Success Path
1. Receives delegation from Intent Router or second-pass call after Depth Analysis.
2. Identifies the knowledge domains relevant to the question.
3. Loads relevant knowledge base files via `config.load_knowledge()`.
4. If `data_context` is present, maps data findings to strategic recommendations.
5. Generates market-specific, prioritized recommendations.
6. Formats output with priority matrix and concrete action items.
7. Returns structured recommendations to the router.

## Failure Path
| Failure | Response |
|---------|----------|
| Knowledge base file missing | Fall back to general domain expertise. Note: "No Sourcy-specific guide found for [topic]. Recommendations based on general best practices." |
| No data_context provided for a data-dependent question | "I can give general advice, but for data-backed recommendations, let me first analyze your current performance. Shall I run a deep analysis?" |
| User asks about a market not in target list | "That market isn't in Sourcy's current target list (ID, PH, TH, BR, US, MX). I can provide general advice, but our data tools don't track it." |
| Question is too vague | Ask a clarifying question: "Could you tell me which market and which aspect (SEO, content, ads) you'd like advice on?" |

## Escalation Rules
- If the user asks "what should we do about [data finding]" and no `data_context` is available, recommend the router run Depth Analysis first, then come back for strategic advice.
- If recommendations require competitive data (e.g., "what keywords should we steal from Alibaba"), recommend routing through Depth Analysis with `keyword_gap` analysis type first.
- If the user asks about budget allocation across markets, note that this requires Google Ads data and may not be possible if Ads API is pending.

## Gotchas
- **Language considerations.** Brazil uses Portuguese, Mexico uses Spanish, Thailand uses Thai script. Keyword recommendations for these markets must account for local language search behavior, not just English translations.
- **GEO/AEO is emerging.** Best practices are evolving rapidly. Advice should be framed as "current best thinking" rather than established rules. Focus on structured data, FAQ schema, and authoritative content.
- **B2B vs B2C keywords.** Sourcing keywords ("supplier directory", "manufacturing partner", "bulk order") have very different intent than consumer keywords ("buy cheap", "best deal"). Recommendations must reflect B2B buyer intent.
- **Hreflang complexity.** Sourcy targets multiple countries, some sharing a language (US/Mexico both use English/Spanish). Hreflang implementation advice must be precise about country vs language targeting.
- **Knowledge base may be empty initially.** The system is designed to grow its knowledge base over time. Early on, the agent relies more on general expertise. As market-specific files are added, advice becomes more targeted.
- **Do not confuse "recommendation" with "analysis."** This agent does not say "your CTR is 1.8%." It says "your CTR of 1.8% is below the 2% target -- here are 3 ways to improve it."

## Examples

### Example 1: Market-specific SEO strategy
**User:** "How should we improve our SEO for Indonesia?"
**Agent:** Loads `market-indonesia.md` and `seo-best-practices.md`. Checks `data_context` (if available) for Indonesia-specific metrics. Returns:
- Priority 1: Create Indonesian-language landing pages targeting "supplier Indonesia" and "agen sourcing" (high search volume, low competition in ID database)
- Priority 2: Build backlinks from Indonesian B2B directories (detik.com business section, indonetwork.co.id)
- Priority 3: Optimize existing pages for "sourcing agent Indonesia" -- currently position 8, striking distance to top 3
- Priority 4: Add hreflang tags for id-ID targeting to prevent SEA overflow traffic cannibalization

### Example 2: Data-backed keyword strategy (second pass after Depth Analysis)
**User asked earlier:** "What keywords should we target?"
**Depth Analysis returned:** keyword gap showing 23 competitor keywords where Sourcy has no presence.
**Agent now receives data_context.** Returns:
- Groups the 23 keywords into 4 topic clusters: "sourcing agents" (8 keywords), "manufacturer directories" (6 keywords), "wholesale suppliers" (5 keywords), "import/export" (4 keywords)
- Recommends creating a pillar page for each cluster
- Prioritizes by: search volume * (1/keyword difficulty) * market relevance
- Maps each cluster to a target market where it has the most impact

### Example 3: GEO/AEO strategy
**User:** "How do we optimize for AI search engines like ChatGPT and Perplexity?"
**Agent:** Loads `geo-aeo-guide.md`. Returns:
- Priority 1: Add comprehensive FAQ schema markup to key landing pages with structured answers about sourcing processes
- Priority 2: Create authoritative, citation-worthy content (statistics, original research on sourcing trends)
- Priority 3: Build topical authority clusters so AI models associate "sourcy.ai" with B2B sourcing expertise
- Priority 4: Ensure clean, crawlable HTML with clear heading hierarchy for AI parsing
- Notes that GEO is an emerging field and recommends monthly review of what AI search engines cite for sourcing queries

## Eval Criteria
| Metric | Target | How to measure |
|--------|--------|----------------|
| Recommendations are actionable | Every recommendation has a specific task, not generic advice | Review 20 outputs for specificity |
| Market-specific accuracy | Recommendations reflect actual market conditions | Expert review for each target market |
| Data-context utilization | When data_context is provided, >80% of recommendations reference a data point | Count data references in output |
| Priority ordering is logical | Higher-priority items have higher impact/effort ratio | Compare priority ranking to expert ranking on 15 test cases |
| No data-pulling attempted | Zero analytics tool calls in logs | Audit tool call logs for this agent |
| Knowledge base consulted | Relevant KB files loaded when they exist | Check knowledge_sources in output |
