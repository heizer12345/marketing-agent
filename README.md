# Sourcy Marketing Agent

An agentic marketing intelligence platform for [sourcy.ai](https://sourcy.ai). It connects to your live data sources (GA4, Google Search Console, Google Ads, Meta Ads, Instagram, SEMrush, PostHog) and runs a hierarchy of AI agents to deliver interactive HTML dashboards, SEO/GEO/AEO audits, and on-brand content — all from a single chat interface.

---

## Product Workflow

```
User types a query in the chat UI
          │
          ▼
   Intent Router (CEO Agent)
   ├─ SIMPLE  ─► raw tool call (< 20s)       e.g. "top keywords right now"
   ├─ MEDIUM  ─► department head directly     e.g. "analyse our Meta Ads"
   │              ├─ Marketing Data Analyst   (analytics + ads)
   │              └─ Content Engine           (audits + writing)
   └─ COMPLEX ─► Project Manager             (multi-step checklist)
                  ├─ Marketing Data Analyst
                  ├─ Content Engine
                  ├─ Knowledge Expert
                  └─ Report Builder
          │
          ▼
   Skills run in parallel, return structured data + summaries
          │
          ▼
   Synthesis Agent
   └─ writes Python code → exec() → interactive HTML artifact saved to /public/reports
          │
          ▼
   Frontend streams the artifact URL; user opens a self-contained dashboard
```

---

## Architecture

### Layer 1 — Frontend (Next.js)

Located in `frontend/`. A four-tab Next.js app that streams responses over WebSocket.

| Tab | Purpose |
|---|---|
| **Home** | Dashboard overview and quick-start cards |
| **Chat** | Primary interface — send queries, receive streaming agent output + HTML artifact links |
| **Library** | Browse saved reports and content outputs |
| **Memory** | Manage persona, design system, marketing principles, winning ad examples |

WebSocket endpoint: `ws://localhost:8000/ws/{ticket_id}`
REST API: `/api/v2/*` (new frontend) + `/api/*` (legacy Kanban UI)

### Layer 2 — API Server (`app/`)

| File | Role |
|---|---|
| `server.py` | FastAPI app, WebSocket handler, streaming event loop, tier-based timeouts |
| `v2_api.py` | REST endpoints for the Next.js frontend (memory state, persona, library) |
| `database.py` | SQLite — tickets, messages, artifacts, review packages, prompt library |
| `streaming_events.py` | `StreamTracker` — normalises OpenAI Agents SDK events into frontend-friendly JSON |
| `auth.py` | Session middleware + login router |

### Layer 3 — Agent Hierarchy (`skills/`)

```
Intent Router  (intent_router.py)
├── Knowledge Expert        — pure strategy Q&A, no live data
├── Marketing Data Analyst  (marketing_data_analyst.py)
│   ├── seo_analyst             — 100+ keywords, CTR, weekly positions
│   ├── geo_aeo_analyst         — AI Overview, Perplexity, ChatGPT presence
│   ├── competitor_analyst      — keyword gaps, traffic, backlinks
│   ├── traffic_analyst         — sessions, demographics, 5-week trends
│   ├── paid_organic_overlap    — keyword overlap, savings opportunities
│   ├── recommendation_engine   — Meta Ads + Google Ads diagnostics
│   ├── socials_analyst         — Instagram WoW, content-type breakdown
│   └── synthesis_agent         — code-gen dashboard builder → HTML artifact
├── Content Engine          (content_engine.py)
│   ├── seo_content_analyst     — on-page SEO audit (meta, headers, schema)
│   ├── geo_content_analyst     — GEO citability scoring, AI crawler access
│   ├── aeo_content_analyst     — featured snippets, PAA, answer blocks
│   ├── eeat_auditor            — 80-item E-E-A-T benchmark
│   ├── entity_optimizer        — 47-signal entity checklist
│   ├── keyword_strategist      — intent clusters, topic gaps
│   ├── technical_seo_auditor   — Core Web Vitals, crawlability
│   ├── blog_writer             — on-brand long-form posts
│   ├── landing_page_writer     — conversion-focused pages
│   ├── content_brief_generator — structured briefs for human writers
│   ├── content_quality_scorer  — automated scoring on published content
│   ├── page_rewriter           — rewrite existing pages with SEO fixes
│   ├── ad_writer               — Meta/Google ad copy
│   ├── case_study_writer       — customer case studies
│   └── content_synthesis_agent — builds HTML audit artifact
└── Project Manager         (project_manager.py)
    └── checklist-driven executor for multi-step workflows
```

### Layer 4 — Tools (`tools/`)

Raw data connectors and utilities. Skills call these directly.

| Tool | Data Source |
|---|---|
| `google_analytics.py` | GA4 — sessions, channels, countries, devices |
| `search_console.py` | Google Search Console — keywords, CTR, positions |
| `google_ads.py` | Google Ads — spend, impressions, search terms, quality scores |
| `meta_ads.py` | Meta Ads — campaigns, creatives, demographics, funnel metrics |
| `instagram.py` | Instagram Business — reach, impressions, engagement, reel views |
| `semrush.py` | SEMrush — competitor traffic, backlinks, keyword gaps |
| `posthog.py` | PostHog — product analytics, event funnels |
| `ai_visibility.py` | SerpAPI / Perplexity / web — GEO/AEO brand mentions |
| `site_crawler.py` | Internal site crawl — page content, meta, schema |
| `artifact_generator.py` | `exec()` Python code written by Synthesis Agent → HTML file |
| `html_components.py` | Charting primitives (Chart.js) used in synthesis scripts |
| `persona_loader.py` | Loads brand persona, design system, principles from `/personas` |
| `schema_generator.py` | JSON-LD schema (FAQ, Article, Breadcrumb, Org, Service) |
| `image_gen.py` | DALL-E image generation for content |
| `content_writer.py` | File writer for blog/landing page/brief outputs |

---

## Key Design Decisions

**Synthesis via code-gen, not LLM HTML generation.** The Synthesis Agent writes a ~2-3K token Python script which calls `html_components.py` primitives. That script is `exec()`'d to produce the full HTML dashboard. This eliminates LLM output token limits and timeout risk on full audits.

**Three-tier routing.** Simple queries (`get_website_overview`) return in < 20s by calling raw tools directly. Medium queries call a department head. Complex multi-step work goes through the Project Manager with a checklist — so the CEO doesn't burn turns coordinating.

**Skills return summaries, not raw data.** Each skill returns structured JSON + a short summary (~1-2K tokens). The Synthesis Agent receives only summaries, keeping its context window small even after 7 parallel skills run.

**Parallel skill dispatch.** The Marketing Data Analyst and Content Engine dispatch all relevant skills in parallel via the OpenAI Agents SDK tool-call mechanism, then collect results before synthesis.

---

## Data Flow (Full Audit Example)

```
User: "Give me a complete audit"
  → Intent Router → Marketing Data Analyst

Data Analyst dispatches in parallel:
  ├─ seo_analysis      → Search Console + SEMrush → 100+ keywords, gaps
  ├─ geo_aeo_analysis  → SerpAPI + Perplexity → AI visibility score
  ├─ competitor_analysis → SEMrush → overlap, traffic delta
  ├─ traffic_analysis  → GA4 → 5-week sessions, channels, geo
  ├─ paid_organic_overlap → Ads + Search Console → keyword overlap
  ├─ deep_recommendations → Meta Ads + Google Ads → creative rankings
  └─ socials_analysis  → Instagram → WoW engagement

All summaries → Synthesis Agent
  → writes Python script using html_components.py
  → exec() produces /public/reports/<ticket_id>.html
  → frontend receives artifact URL → user opens interactive dashboard
```

---

## Project Structure

```
├── main.py                   Entry point (uvicorn)
├── config.py                 All env vars + knowledge loader
├── app/
│   ├── server.py             FastAPI + WebSocket streaming
│   ├── v2_api.py             REST API for Next.js frontend
│   ├── database.py           SQLite (tickets, messages, artifacts)
│   ├── streaming_events.py   StreamTracker for agent events
│   └── auth.py               Auth middleware
├── skills/
│   ├── intent_router.py      CEO Agent (3-tier router)
│   ├── marketing_data_analyst.py  Analytics orchestrator (7 sub-skills)
│   ├── content_engine.py     Content orchestrator (14 sub-skills)
│   ├── project_manager.py    Multi-step checklist executor
│   ├── synthesis_agent.py    Code-gen dashboard builder
│   ├── knowledge_expert.py   Strategy Q&A
│   ├── report_builder.py     Structured report generator
│   └── content_skills/       14 individual content sub-skills
├── tools/                    Raw data connectors + utilities
├── frontend/                 Next.js app (Home/Chat/Library/Memory)
├── personas/                 Brand persona, design system, principles
├── knowledge/                Domain knowledge files (md)
├── public/reports/           Generated HTML artifacts
├── public/content/           Generated blog/landing page files
└── scripts/                  Test scripts
```

---

## Setup

### Requirements

- Python 3.11+
- Node.js 18+ (for the frontend)
- OpenAI API key (GPT-4o used for all agents)

### Environment Variables

Copy `.env.example` to `.env` and fill in the keys you have. The agent degrades gracefully — missing integrations are skipped.

```env
OPENAI_API_KEY=

# Google (service account JSON or individual keys)
GOOGLE_APPLICATION_CREDENTIALS_JSON=
GA4_PROPERTY_ID=
SEARCH_CONSOLE_SITE_URL=
GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CLIENT_ID=
GOOGLE_ADS_CLIENT_SECRET=
GOOGLE_ADS_REFRESH_TOKEN=
GOOGLE_ADS_CUSTOMER_ID=

# Meta / Instagram
META_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=

# Optional
SEMRUSH_API_KEY=
SERPAPI_KEY=
PERPLEXITY_API_KEY=
POSTHOG_API_KEY=
POSTHOG_PROJECT_ID=
```

### Run locally

```bash
# Backend
pip install -r requirements.txt
python main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Backend: `http://localhost:8000`
Frontend: `http://localhost:3000`

### Deploy to Railway

The repo includes a `Procfile` and `runtime.txt` for Railway. Set all env vars in the Railway dashboard. The Next.js frontend can be deployed separately (Vercel) pointing to the Railway backend URL.
