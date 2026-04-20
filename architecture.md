# Sourcy Marketing Agent — Full System Architecture

> **Last updated**: 2026-04-17
> **Version**: v3.2 (Report quality overhaul — reasoning chains, funnel, score breakdowns, action items, message alignment)

---

## System Overview

A 3-tier hierarchical agent system for marketing analytics and content operations. Built on the OpenAI Agents SDK (`from agents import Agent`), running on a FastAPI WebSocket server.

- **Tier 1**: Intent Router (master) — classifies queries, delegates to specialists
- **Tier 2**: 4 specialist agents — Data Analyst, Content Engine, Report Builder, Knowledge Expert
- **Tier 3**: 19 domain skills + 2 synthesis agents — the actual workers

**Entry point**: `main.py` → FastAPI on `:8000` → WebSocket at `/ws/ticket/{id}`

---

## Tier 1: Intent Router

**File**: `skills/intent_router.py`
**Agent name**: "Marketing Analyst"
**Model**: gpt-5.4

The single entry point for all user messages. Routes to 4 Tier 2 agents + has 4 raw tools for quick lookups.

### Routing Logic

| Query Type | Route To | Example |
|------------|----------|---------|
| **Quick lookup** (single metric) | Raw tools directly | "How many sessions this week?" |
| **Analytics** (backward-looking, dashboards) | `data_analyst` | "How are we doing?", "Fix our ads" |
| **Content** (forward-looking, audits, writing) | `content_engine` | "Audit this URL", "Write a blog post" |
| **Strategy** (pure education, no data needed) | `knowledge_expert` | "How to improve SEO for Indonesia?" |
| **Report** (explicit request only) | `report_builder` | "Generate a report" |

### Routing Boundary: data_analyst vs content_engine

| data_analyst | content_engine |
|-------------|----------------|
| "How is our SEO performing?" | "Audit this URL's SEO" |
| "Show keyword data" | "Research keywords for new content" |
| "Traffic overview" | "Technical SEO crawl" |
| "What's wrong with our ads?" | "Write a blog post" |
| "Compare us to competitors" | "E-E-A-T audit" |
| Quantitative, backward-looking | Qualitative, forward-looking |

### Registered Tools

```
Tier 2 Agents (as tools):
├── data_analyst          → marketing_data_analyst
├── content_engine        → content_engine
├── report_builder        → report_builder_agent
└── knowledge_expert      → knowledge_expert_agent

Raw Tools (quick lookups):
├── get_website_overview  → GA4
├── get_traffic_sources   → GA4
├── get_country_breakdown → GA4
└── get_organic_keywords  → Search Console
```

---

## Tier 2A: Marketing Data Analyst

**File**: `skills/marketing_data_analyst.py`
**Agent name**: "Marketing Data Analyst"
**Model**: gpt-5.4
**Role**: Plans which skills to call, dispatches in parallel, collects results, routes to Synthesis Agent for HTML artifact.

### Dispatch Decision Table

| Query Pattern | Skills Called |
|---|---|
| "How are we doing?" / "website performance" | traffic_analysis → deep_recommendations |
| "SEO analysis" / "keyword research" | seo_analysis |
| "Are we in AI search?" / "GEO audit" | geo_aeo_analysis |
| "Compare to competitors" | competitor_analysis + seo_analysis |
| "What's wrong with our ads?" | traffic_analysis + deep_recommendations |
| "Instagram" / "socials" | socials_analysis |
| "Full audit" / "everything" | ALL skills |

### 7 Domain Skills (Tier 3)

| # | Skill | File | Data Sources | What It Does |
|---|-------|------|-------------|--------------|
| 1 | `seo_analysis` | `skills/seo_analyst.py` | Search Console, SEMrush | 100+ keywords, branded/non-branded, content gaps, CTR, weekly positions |
| 2 | `geo_aeo_analysis` | `skills/geo_aeo_analyst.py` | SerpAPI, Perplexity, OpenAI | AI Overviews presence, Perplexity/ChatGPT citations |
| 3 | `competitor_analysis` | `skills/competitor_analyst.py` | SEMrush | Keyword gaps, traffic estimates, backlinks for 9+ competitors |
| 4 | `traffic_analysis` | `skills/traffic_analyst.py` | GA4 | Sources, countries, device, 5-week WoW trends |
| 5 | `paid_organic_overlap` | `skills/paid_organic_overlap.py` | Search Console, Google Ads | Keyword cannibalization, savings opportunities |
| 6 | `deep_recommendations` | `skills/recommendation_engine.py` | Meta Ads API, Google Ads API | Campaigns, targeting, creatives, spend, demographics, quality rankings |
| 7 | `socials_analysis` | `skills/socials_analyst.py` | Instagram Graph API | Posts, engagement, content type analysis, WoW |

### Synthesis Agent

**File**: `skills/synthesis_agent.py`
**Agent name**: "Synthesis Agent"
**Tool**: `execute_report_script` (from `tools/artifact_generator.py`)

- Receives ALL skill findings
- Cross-references findings across skills (patterns no single skill sees)
- Writes Python code (~2-3K tokens) using `tools/html_components.py`
- Code is `exec()`'d to produce HTML dashboard
- Output: `public/reports/report_YYYYMMDD_HHMMSS.html`
- Build script audit trail: `public/scripts/build_YYYYMMDD_HHMMSS.py`

### Cross-Agent Triggers

| Signal Detected | Triggers |
|---|---|
| Bounce >80% on paid traffic | Creative diagnosis + landing page analysis |
| Conversion rate = 0 or sudden drop | Tracking health check + funnel analysis |
| Non-target country traffic >10% | Geo deep-dive + ad targeting audit |
| Keyword rankings declining | Competitor analysis |
| Meta/Google Ads CTR declining over time | Creative fatigue + audience saturation |
| link_clicks > 0 but landing_page_views = 0 | Pixel/tracking health check |

---

## Tier 2B: Content Engine

**File**: `skills/content_engine.py`
**Agent name**: "Content Engine"
**Model**: gpt-5.4
**Role**: Plans which content skills to call, dispatches in parallel, routes to either Content Synthesis Agent (HTML artifacts) or content creation pipeline (files).

### Dispatch Decision Table

| Query Pattern | Skills Called |
|---|---|
| "SEO audit of [URL]" | seo_content_analysis |
| "GEO audit" / "AI visibility" | geo_content_analysis |
| "AEO analysis" / "featured snippets" | aeo_content_analysis |
| "E-E-A-T audit" | eeat_audit |
| "Entity optimization" / "Knowledge Panel" | entity_optimization |
| "Keyword research" / "content gaps" | keyword_strategy |
| "Technical SEO audit" / "site crawl" | technical_seo_audit |
| "Full content audit" | ALL 7 analysis skills → content_synthesize_and_build |
| "Write blog post about [topic]" | keyword_strategy → write_blog → score_content |
| "Create landing page" | keyword_strategy → write_landing_page → score_content |
| "Content brief for [topic]" | keyword_strategy → generate_brief |
| "Score this content" | score_content |
| "What content should we create?" | analytics_data → keyword_strategy |

### 7 Analysis Skills (Tier 3)

| # | Skill | File | Data Sources | What It Does |
|---|-------|------|-------------|--------------|
| 1 | `seo_content_analysis` | `skills/content_skills/seo_content_analyst.py` | Site Crawler, Search Console, SEMrush | On-page audit: meta tags, headers, content quality, linking, images, schema. SEO Health Score (0-100) |
| 2 | `geo_content_analysis` | `skills/content_skills/geo_content_analyst.py` | Site Crawler, SerpAPI, Perplexity, OpenAI | GEO score (5 weighted factors), citability blocks, AI crawler access, platform citations |
| 3 | `aeo_content_analysis` | `skills/content_skills/aeo_content_analyst.py` | Site Crawler, SerpAPI, Search Console | Featured snippet opportunities, PAA targeting, answer block optimization, schema recs |
| 4 | `eeat_audit` | `skills/content_skills/eeat_auditor.py` | Site Crawler | 80-item E-E-A-T benchmark: Experience(20), Expertise(20), Authority(20), Trust(20). Score 0-100 |
| 5 | `entity_optimization` | `skills/content_skills/entity_optimizer.py` | Site Crawler, SerpAPI, SEMrush | 47-signal entity checklist, Knowledge Panel strategy, Wikidata optimization |
| 6 | `keyword_strategy` | `skills/content_skills/keyword_strategist.py` | Search Console, SEMrush, Site Crawler | 8-phase: seed → intent → scoring → clusters → gaps → striking distance → cannibalization → calendar |
| 7 | `technical_seo_audit` | `skills/content_skills/technical_seo_auditor.py` | Site Crawler (all 6 functions) | robots.txt, sitemap, Core Web Vitals, schema, AI crawler access, redirects |

### 3 Content Creation Skills (Tier 3)

| # | Skill | File | Output Directory |
|---|-------|------|-----------------|
| 8 | `write_blog` | `skills/content_skills/blog_writer.py` | `output/content/blogs/` |
| 9 | `write_landing_page` | `skills/content_skills/landing_page_writer.py` | `output/content/landing-pages/` |
| 10 | `generate_brief` | `skills/content_skills/content_brief_generator.py` | `output/content/briefs/` |

### Quality Gate

| # | Skill | File | How It Works |
|---|-------|------|-------------|
| 11 | `score_content` | `skills/content_skills/content_quality_scorer.py` | Scores 0-100 (Hook/Voice/Value/Engagement x 25pts). 24 AI writing detection patterns. If <90 → loops back to writer (max 2x) |

### Content Synthesis Agent

**File**: `skills/content_skills/content_synthesis_agent.py`
**Agent name**: "Content Synthesis Agent"
**Tool**: `execute_report_script` (same as data_analyst's synthesis)

Content-specific HTML artifacts with:
- EEAT radar charts
- GEO scorecards (5 weighted factors)
- Keyword opportunity heatmaps
- Entity signal checklists
- AI crawler access matrix tables

### Cross-Agent Bridge

| # | Skill | What It Does |
|---|-------|-------------|
| 13 | `analytics_data` | Calls the existing Marketing Data Analyst for GA4/Meta Ads/traffic context when content decisions need analytics data |

### Content Engine Cross-Agent Triggers

| Signal Detected | Triggers |
|---|---|
| EEAT score < 50% | entity_optimizer |
| No citability blocks found | geo_content_analyst |
| Missing FAQ schema on key pages | aeo_content_analyst |
| Keyword cannibalization detected | seo_content_analyst |
| AI crawlers blocked in robots.txt | technical_seo_auditor |
| Thin content (<500 words) on key pages | blog_writer flagged |
| No structured data / schema markup | technical_seo_auditor |
| Content gaps vs competitors | keyword_strategist |

---

## Tier 2C: Report Builder

**File**: `skills/report_builder.py`
**Agent name**: "Report Builder"
**Model**: gpt-5.4
**Role**: Generates formal HTML reports. ONLY called when user explicitly asks for "report".

**Tools**: GA4 (overview, traffic, countries, landing pages, audience, conversions), Search Console, smart_analysis functions, `generate_html_report()`

**Output**: `public/reports/` (Chart.js-based HTML)

---

## Tier 2D: Knowledge Expert

**File**: `skills/knowledge_expert.py`
**Agent name**: "Knowledge Expert"
**Model**: gpt-5.4
**Role**: Pure strategy and education. Combines data from tools with best practices from knowledge base.

**Tools**: SEMrush, Search Console, GA4 (overview, countries, landing pages)

**Knowledge Base**: SEO-knowledge.md, GEO-knowledge.md, AEO-knowledge.md, Ads-knowledge.md, Analytics-knowledge.md

**Output**: Text recommendations (no artifacts)

---

## Tools Layer

### API Integration Tools (19 files in `tools/`)

| Tool File | APIs | Key Functions |
|-----------|------|---------------|
| `google_analytics.py` | GA4 API | `get_website_overview`, `get_traffic_sources`, `get_country_breakdown`, `get_landing_pages`, `get_audience_segments`, `get_conversion_paths` |
| `search_console.py` | Google Search Console | `get_organic_keywords`, `get_organic_pages`, `get_organic_by_country`, `get_organic_keywords_by_page`, `get_keyword_weekly_positions` |
| `google_ads.py` | Google Ads API | `get_active_campaigns`, `get_google_ads_wow`, `get_google_ads_campaign_trend`, `get_google_ads_budget_overview` |
| `meta_ads.py` | Meta Graph API | `get_meta_campaigns`, `get_meta_adset_targeting`, `get_meta_ad_performance`, `get_meta_ad_creatives`, `get_meta_spend_by_country`, `get_meta_campaign_trend`, `get_meta_wow_comparison`, `get_meta_ad_level_performance`, `get_meta_audience_overlap` |
| `instagram.py` | Instagram Graph API | `get_ig_account_overview`, `get_ig_posts_with_insights` |
| `posthog.py` | PostHog API | `get_posthog_session_stats`, `get_posthog_funnel`, `get_posthog_user_paths`, `get_posthog_events` |
| `semrush.py` | SEMrush API | `semrush_domain_overview`, `semrush_competitor_keywords`, `semrush_keyword_research`, `semrush_find_competitors`, `semrush_keyword_gap`, `semrush_backlinks_overview` |
| `ai_visibility.py` | SerpAPI, Perplexity, OpenAI | `check_google_ai_overview`, `check_perplexity_citation`, `check_chatgpt_mention`, `analyze_structured_data`, `check_eeat_signals` |
| `site_crawler.py` | httpx + BeautifulSoup (free) | `crawl_page`, `crawl_robots_txt`, `crawl_sitemap`, `check_llms_txt`, `check_ai_crawler_access`, `check_page_speed` |
| `content_writer.py` | Local filesystem | `save_content_file`, `list_content_files` |
| `sourcy_activation.py` | Sourcy internal DB | Internal lead/sourcing data |
| `web_reference.py` | Web scraping | Reference content fetching |
| `technical_seo.py` | (stub) | Placeholder — replaced by site_crawler.py |

### Infrastructure Tools

| Tool File | Purpose |
|-----------|---------|
| `artifact_generator.py` | `execute_report_script()` — exec's Python code to generate HTML. Used by both synthesis agents |
| `html_components.py` | Component library: KPIs (WoW + MoM), charts (line/bar/funnel/doughnut/heatmap/radar), tables, diagnosis cards, tab assembly, full page rendering. **v3.2 additions**: `render_reasoning_chain`, `render_conversion_funnel`, `render_action_item`, `render_score_breakdown`, `render_message_alignment_card` |
| `report_generator.py` | Legacy Chart.js HTML generation (used by report_builder) |
| `smart_analysis.py` | Statistical analysis: blindspots, deep reports, organic analysis, traffic patterns |
| `scheduled_reports.py` | Cron-based report scheduling |

---

## Knowledge Layer

### 10 Knowledge Files in `knowledge/`

| File | Size | Used By | Content |
|------|------|---------|---------|
| `SEO-knowledge.md` | 7KB | seo_analyst, keyword_strategist, knowledge_expert | CTR benchmarks, strategies, content gaps methodology |
| `GEO-knowledge.md` | 7KB | geo_aeo_analyst, geo_content_analyst, knowledge_expert | Geographic optimization tactics |
| `AEO-knowledge.md` | 5KB | geo_aeo_analyst, aeo_content_analyst, knowledge_expert | AI search visibility strategies |
| `Ads-knowledge.md` | 13KB | recommendation_engine, knowledge_expert | Google/Meta Ads strategies |
| `Analytics-knowledge.md` | 12KB | traffic_analyst, knowledge_expert | GA4 metrics interpretation |
| `EEAT-knowledge.md` | 35KB | eeat_auditor | 80-item E-E-A-T benchmark with pass/fail criteria |
| `entity-signals.md` | 15KB | entity_optimizer | 47-signal entity checklist, Knowledge Panel, Wikidata |
| `GEO-knowledge-extended.md` | 21KB | geo_content_analyst | GEO scoring (5 factors), AI crawler registry, llms.txt standard, platform citation patterns |
| `AEO-knowledge-extended.md` | 15KB | aeo_content_analyst | Featured snippets, PAA, answer blocks, schema for AI answers |
| `content-quality.md` | 18KB | content_quality_scorer | Expert panel rubric, 24 AI writing patterns, recursive improvement |

---

## Shared Prompts

### `skills/prompts/sourcy_context.py` (used by data_analyst skills)

| Prompt Block | Purpose |
|-------------|---------|
| `SOURCY_BUSINESS_CONTEXT` | Company info, value props, stats |
| `COMPETITOR_SUMMARY` | 9 competitors by tier (auto-built from config) |
| `TARGET_COUNTRIES_BLOCK` | 6 primary + 3 acceptable countries |
| `ROOT_CAUSE_REASONING` | SIGNAL → VALIDATION → ROOT CAUSE → EVIDENCE → CONFIDENCE → ACTION |
| `DIAGNOSTIC_OUTPUT_STANDARD` | Diagnosis card format, comparison context, action chains |
| `SO_WHAT_INSTRUCTIONS` | 5-part structure: Observation → Because clause → Business Impact → Priority Score (Traffic × Intent × Cost × Funnel) → Actions. Hard cap: max 30% URGENT |
| `RECOMMENDATION_FORMAT_GUIDELINES` | 5-step reasoning chain: Issue → What Happened → Why It Matters → Root Cause → Action |
| `MESSAGE_ALIGNMENT_FRAMEWORK` | 3-way alignment scoring: Ad Promise × Landing Page × Audience Intent → ALIGNED/PARTIAL/MISALIGNED per campaign |
| `CHANNEL_CONTROLLABILITY_RULES` | Paid non-target = wasted spend (flag + quantify). Organic non-target = informational signal only (never flag as problem) |
| `SIMPLE_LANGUAGE_RULES` | "for a 5-year-old CEO" translation dictionary |
| `STRUCTURED_OUTPUT_FORMAT` | JSON output schema with sparklines |
| `CROSS_AGENT_TRIGGERS` | Analytics cross-agent signal table |
| `ARTIFACT_GUIDELINES` | HTML artifact formatting rules |

### `skills/prompts/content_engine_context.py` (used by content_engine skills)

| Prompt Block | Purpose |
|-------------|---------|
| `CONTENT_ENGINE_BUSINESS_CONTEXT` | Content-specific Sourcy context |
| `CONTENT_QUALITY_RUBRIC` | 4x25 scoring (Hook/Voice/Value/Engagement) + 24 AI patterns |
| `GEO_CITABILITY_RULES` | 134-167 word blocks, AI platform citation patterns |
| `EEAT_SCORING_GUIDE` | 80-item evaluation guide by category |
| `CONTENT_CROSS_AGENT_TRIGGERS` | Content-specific trigger signals |
| `CONTENT_OUTPUT_FORMAT` | Structured analysis output format |

---

## Output Structure

```
public/
├── reports/              HTML dashboard artifacts (from both synthesis agents)
│   └── report_YYYYMMDD_HHMMSS.html
└── scripts/              Python build scripts (audit trail)
    └── build_YYYYMMDD_HHMMSS.py

output/content/           Content files (from content_engine)
├── blogs/                Full blog posts (.md with YAML frontmatter)
├── audits/               Audit reports (.md)
├── briefs/               Content briefs (.md)
└── landing-pages/        Landing page copy (.md)
```

---

## Configuration

| File | Purpose |
|------|---------|
| `config.py` | Central config loader: API keys from .env, paths, knowledge loading |
| `config/competitors.json` | 9 competitors with tier (primary/secondary), domains, categories |
| `config/target_markets.json` | 6 primary + 3 acceptable countries, KPI targets |
| `.env` | API keys: OpenAI, GA4, Search Console, Google Ads, Meta Ads, Instagram, PostHog, SEMrush, SerpAPI, Perplexity |

---

## Application Layer

| File | Purpose |
|------|---------|
| `main.py` | Entry point: starts FastAPI server on :8000 |
| `app/server.py` | WebSocket endpoint, REST APIs, tool status streaming, artifact detection |
| `app/database.py` | SQLite: tickets, messages, artifacts persistence |
| `app/ui.py` | HTML UI template for the ticket/chat interface |

### WebSocket Flow
1. User creates ticket → sends message via WebSocket
2. Server runs Intent Router agent with message
3. Agent delegates to Tier 2 → Tier 3 skills execute
4. Tool calls stream as `tool_status` events (friendly names from `FRIENDLY_MAP`)
5. Synthesis agent produces HTML artifact → filename detected by regex
6. Final response + artifact URL returned to UI

---

## Workflow Examples

### Example 1: Analytics Dashboard
```
"How are we doing?"
→ Intent Router → data_analyst
  → [traffic_analysis + deep_recommendations] (parallel)
  → synthesis_agent (Python code-gen)
  → HTML dashboard artifact
```

### Example 2: Content Audit
```
"Run a full SEO audit of sourcy.ai"
→ Intent Router → content_engine
  → [seo + geo + aeo + eeat + entity + keyword + technical] (parallel)
  → content_synthesis_agent (Python code-gen)
  → HTML audit artifact with radar charts, scorecards, checklists
```

### Example 3: Content Creation
```
"Write a blog post about sustainable sourcing in Southeast Asia"
→ Intent Router → content_engine
  → keyword_strategy (research)
  → write_blog (generates post with GEO citability blocks)
  → score_content (quality check — if <90, loops back)
  → save_content_file → output/content/blogs/
```

### Example 4: Combined Analysis + Creation
```
"Audit SEO and write top 3 recommended blog posts"
→ Intent Router → content_engine
  Step 1: [all 7 analysis skills] → content_synthesis_agent → Artifact 1 (dashboard)
  Step 2: keyword_strategy → write_blog (x3) → score_content → 3 files in output/
```

### Example 5: Cross-Agent Collaboration
```
"What content should we create next?"
→ Intent Router → content_engine
  → analytics_data (calls data_analyst for GA4 traffic + keyword trends)
  → keyword_strategy (uses analytics context to find gaps)
  → content calendar with prioritized recommendations
```

---

## Reference Repos

Cloned to `reference/` for code reuse:

| Repo | Key Content |
|------|-------------|
| `reference/seo-geo-claude-skills/` | 20 skills, EEAT benchmark, entity checklist, keyword frameworks, topic cluster templates |
| `reference/claude-seo/` | 16 sub-skills, GEO scoring framework, AI crawler registry, industry-specific SEO templates |
| `reference/ai-marketing-skills/` | Expert panel scoring engine, content quality rubrics, 24 humanizer patterns |
| `reference/brightbean-studio/` | Social media management, content approval workflows, calendar patterns |

---

## File Inventory

### Skills (Tier 2 + Tier 3): 21 files

```
skills/
├── intent_router.py              Tier 1: Master router
├── marketing_data_analyst.py     Tier 2A: Analytics orchestrator
├── content_engine.py             Tier 2B: Content orchestrator
├── report_builder.py             Tier 2C: Report generation
├── knowledge_expert.py           Tier 2D: Strategy expert
├── seo_analyst.py                Tier 3: SEO keywords (data_analyst)
├── geo_aeo_analyst.py            Tier 3: AI visibility (data_analyst)
├── competitor_analyst.py         Tier 3: Competitors (data_analyst)
├── traffic_analyst.py            Tier 3: Traffic (data_analyst)
├── paid_organic_overlap.py       Tier 3: Paid/organic (data_analyst)
├── recommendation_engine.py      Tier 3: Ads diagnostics (data_analyst)
├── socials_analyst.py            Tier 3: Instagram (data_analyst)
├── synthesis_agent.py            Tier 3: HTML code-gen (data_analyst)
├── content_skills/
│   ├── seo_content_analyst.py    Tier 3: On-page SEO (content_engine)
│   ├── geo_content_analyst.py    Tier 3: GEO scoring (content_engine)
│   ├── aeo_content_analyst.py    Tier 3: AEO snippets (content_engine)
│   ├── eeat_auditor.py           Tier 3: EEAT 80-item (content_engine)
│   ├── entity_optimizer.py       Tier 3: Entity 47-signal (content_engine)
│   ├── keyword_strategist.py     Tier 3: Keyword research (content_engine)
│   ├── technical_seo_auditor.py  Tier 3: Technical audit (content_engine)
│   ├── blog_writer.py            Tier 3: Blog creation (content_engine)
│   ├── landing_page_writer.py    Tier 3: Landing pages (content_engine)
│   ├── content_brief_generator.py Tier 3: Briefs (content_engine)
│   ├── content_quality_scorer.py Tier 3: Quality gate (content_engine)
│   └── content_synthesis_agent.py Tier 3: HTML code-gen (content_engine)
└── prompts/
    ├── sourcy_context.py         Shared prompts (data_analyst)
    └── content_engine_context.py  Shared prompts (content_engine)
```

### Tools: 19 files in `tools/`
### Knowledge: 10 files in `knowledge/`
### Config: 2 JSON files in `config/`
### App: 3 files in `app/`
### Specs: 4 files in `specs/`

---

## Adopted Scripts & Reference Materials

Pulled from 4 GitHub repos and organized into project directories for direct use and improvement.

### `scripts/autoresearch/` — Variant Generation + Expert Panel Scoring
Source: `ai-marketing-skills/autoresearch/`

| File | Purpose |
|------|---------|
| `autoresearch.py` | Karpathy-style iterative optimization. Generates 50+ variants, scores with 5-expert panel, evolves winners through rounds. Works on landing pages, emails, ad copy. |
| `SKILL.md` | Full framework documentation |

**Key concept**: 95x concept brainstorm — generates many variants, scores them, evolves the best.

### `scripts/content-ops/` — Content Quality & Transformation Scripts
Source: `ai-marketing-skills/content-ops/scripts/`

| File | Purpose |
|------|---------|
| `content-quality-scorer.py` | Pre-publish QA: voice similarity, specificity, AI slop penalty, length check, engagement potential |
| `content-quality-gate.py` | Quality gate automation for content pipeline |
| `content-transform.py` | Content format transformation (long-form → short-form, etc.) |
| `editorial-brain.py` | LLM-powered clip discovery from transcripts (2-pass scoring) |
| `quote-mining-engine.py` | Extract quotable moments from content |

### `scripts/seo-ops/` — SEO Python Utilities
Source: `ai-marketing-skills/seo-ops/` + `claude-seo/scripts/`

| File | Purpose |
|------|---------|
| `content_attack_brief.py` | Full keyword intelligence pipeline |
| `gsc_client.py` | Google Search Console API client |
| `trend_scout.py` | Multi-source trend detection (Google Trends, HN, Reddit, Twitter, YouTube) |
| `pagespeed_check.py` | Core Web Vitals check |
| `parse_html.py` | HTML parsing utilities |
| `ga4_report.py` | GA4 API reporting |
| `gsc_query.py` | GSC querying |
| + 15 more utilities | Backlinks, Moz API, NLP, screenshots, indexing, etc. |

### `docs/scoring-rubrics/` — Quality Evaluation Frameworks
Source: `ai-marketing-skills/content-ops/scoring-rubrics/` + `seo-geo-claude-skills/references/`

| File | Purpose |
|------|---------|
| `content-quality.md` | Content scoring: clarity, depth, specificity, tone (0-100) |
| `conversion-quality.md` | Landing page scoring: headline, CTA, social proof, friction (0-100) |
| `strategic-quality.md` | Strategy doc scoring |
| `keyword-prioritization-framework.md` | 5-factor scoring: Volume(20%), KD(25%), Relevance(30%), Intent(15%), Trend(10%) |
| `keyword-intent-taxonomy.md` | Complete intent classification with signal words |
| `topic-cluster-templates.md` | Hub-and-spoke content architecture templates |

### `docs/expert-panels/` — Channel-Specific Expert Personas
Source: `ai-marketing-skills/content-ops/experts/`

| File | Experts Defined |
|------|----------------|
| `humanizer.md` | AI-slop detection (24 patterns) — **used across all content** |
| `linkedin.md` | 11 experts: thought leader, algorithm specialist, storytelling coach, etc. |
| `instagram.md` | Instagram content experts |
| `newsletter.md` | Newsletter experts |
| `youtube-shorts.md` | Short-form video experts |
| `x-articles.md` | Twitter/X content experts |
| `seo-strategy.md` | SEO content experts |

### `docs/industry-templates/` — SEO Site Architecture Templates
Source: `claude-seo/skills/seo-plan/assets/`

| File | Template |
|------|----------|
| `saas.md` | SaaS site architecture + content priorities (most relevant for Sourcy) |
| `ecommerce.md` | E-commerce structure |
| `agency.md` | Service agency structure |
| `publisher.md` | Content publisher structure |
| `local-service.md` | Local business structure |

### `docs/skill-patterns/` — Architecture Patterns & Frameworks
Source: `seo-geo-claude-skills/references/` + `ai-marketing-skills/`

| File | Pattern |
|------|---------|
| `skill-contract.md` | Standardized skill format: Reads/Writes/Promotes/Handoff |
| `state-model.md` | HOT/WARM/COLD memory tiers for multi-turn workflows |
| `core-eeat-benchmark.md` | 80-item EEAT evaluation (original source) |
| `entity-signal-checklist.md` | 47-signal entity audit (original source) |
| `knowledge-panel-wikidata-guide.md` | Knowledge Panel claiming + Wikidata optimization |
| `growth-engine.md` | A/B test framework + playbook auto-building |
| `conversion-ops.md` | Landing page audit + pain point clustering |

---

## Changelog

### v3.2 — 2026-04-17 — Report Quality Overhaul

**Goal**: Close the gap between "answers" and "reasoning" — every finding now explains *why* it matters, not just *what* it is.

#### New HTML Components (`tools/html_components.py`)

| Component | Purpose |
|-----------|---------|
| `render_reasoning_chain(issue, what_happened, why_it_matters, root_cause, action, confidence, priority_score)` | 5-step vertical arrow flow card. Color-coded by severity. Used for every major recommendation. |
| `render_conversion_funnel(stages)` | Horizontal funnel with inter-stage conversion rates calculated deterministically. Color-coded: red <5%, yellow <20%, green ≥20%. |
| `render_action_item(title, priority_score, owner, timeline, expected_outcome, platform, steps, status)` | Action card with priority badge, owner, timeline, outcome. Groups into Do This Week / Month / Quarter. |
| `render_score_breakdown(title, total_score, max_score, factors, benchmark, benchmark_score, source, impact_chain)` | Circular gauge + per-factor bars + benchmark gap + impact chain. Used for GEO, EEAT, SEO Health, Entity scores. |
| `render_message_alignment_card(campaign, ad_promise, landing_page, audience_intent, alignment, gap, fix)` | 3-way alignment (Ad × Landing × Intent) → ALIGNED/PARTIAL/MISALIGNED. Color-coded card per campaign. |
| `render_kpi_card()` | Updated with `mom_change_pct` parameter — shows WoW + MoM change badges side by side. |

#### New Prompt Blocks (`skills/prompts/sourcy_context.py`)

| Block | Change |
|-------|--------|
| `SO_WHAT_INSTRUCTIONS` | Rewrote: now mandates 5-part structure with Because clause, Priority Score formula (Traffic × Intent × Cost Efficiency × Funnel Stage), campaign goal awareness, and hard cap of max 30% URGENT |
| `RECOMMENDATION_FORMAT_GUIDELINES` | Rewrote: 5-step reasoning chain (Issue → What Happened → Why It Matters → Root Cause → Action) |
| `MESSAGE_ALIGNMENT_FRAMEWORK` | New: 3-way alignment scoring per campaign |
| `CHANNEL_CONTROLLABILITY_RULES` | New: paid non-target = flag as waste; organic non-target = informational signal only |

#### Skill Prompt Upgrades

| File | Changes |
|------|---------|
| `skills/seo_analyst.py` | SEO Validation Checklist (4 steps before any CTR/ranking rec), position change notation "X→Y", ranking URL required for top 50 keywords, [INTENT MISMATCH] / [CANNIBALIZATION] flags, traffic vs conversion quadrant |
| `skills/traffic_analyst.py` | WoW + MoM mandatory on every KPI, target vs non-target split, volume vs quality segmentation, CHANNEL_CONTROLLABILITY_RULES injected |
| `skills/synthesis_agent.py` | 14 mandatory rules: funnel in every Overview, reasoning chains for every recommendation, action items grouped by urgency, ads+GA4 cross-reference table, data confidence header per tab |
| `skills/recommendation_engine.py` | Creative effectiveness 5-dimension scoring (Headline/Proof/CTA-Landing/Language/Image → REPLACE/IMPROVE/KEEP), ads-to-GA4 cross-reference, MESSAGE_ALIGNMENT_FRAMEWORK injected |
| `skills/content_skills/geo_content_analyst.py` | Score decomposition: each factor contribution, benchmark source, impact chain |
| `skills/content_skills/eeat_auditor.py` | Score decomposition: category breakdown (E/E/A/T each X/20), structured priority labels |

#### New Routes (`app/server.py`, `app/architecture.py`)

| Route | Description |
|-------|-------------|
| `GET /architecture` | Interactive architecture diagram — TLDR, full tier map with boxes/arrows, step-by-step request flow |

#### Bug Fixes

| Fix | Detail |
|-----|--------|
| Python 3.9 compatibility | Replaced all `X \| None` union hints with `Optional[X]` across `html_components.py`, `google_analytics.py`, `meta_ads.py`, `app/server.py`. Also fixed `list[float \| int]` and `str \| int \| float` inside generics. |
| f-string escaping in synthesis agents | Dict literals in f-string prompt examples now use `{{}}` double braces to prevent `ValueError: Single '}' encountered` |
| Nested f-string quote conflict | `render_conversion_funnel` sub-label HTML extracted to pre-computed variable to avoid `unexpected character after line continuation` |

### v3.1 — 2026-04-15 — Content Engine Added

- Tier 2B: Content Engine with 12 sub-skills (SEO/GEO/AEO/EEAT/Entity/Keyword/Technical + 3 writers + quality scorer + synthesis)
- Instagram + PostHog integrations
- Tabbed dashboard layout
- WoW comparison engine

### v3.0 — 2026-04-14 — Marketing Data Analyst Overhaul

- Replaced `depth_analysis` with 5-skill orchestrator
- Dynamic HTML artifacts via code-gen (exec'd Python → HTML)
- ECharts for all chart rendering
