# Sourcy Marketing Agent — Capabilities Menu

Use this to explain to users what analyses are available, set time expectations, and help them choose the right option.

---

## Analytics (data_analyst) — "How are we doing?"

These pull REAL data from connected APIs and produce interactive HTML dashboards.

### Quick Lookups (5-10 seconds, no dashboard)
- **Website overview**: Total sessions, users, bounce rate right now. Ask: "How many sessions this week?"
- **Traffic sources**: Top channels driving traffic. Ask: "Where is our traffic from?"
- **Country breakdown**: Sessions by target market. Ask: "Which countries visit us most?"
- **Top keywords**: Current organic keyword rankings. Ask: "Show our top keywords"

### Full Analysis (2-5 minutes → Interactive HTML Dashboard)

| Analysis | Best for | Data sources | Time |
|----------|----------|-------------|------|
| **Traffic Analysis** | "How are we doing overall?" | GA4 | 2-3 min |
| What you get: 5-week WoW trends, source breakdown, country performance, device split, engagement metrics |
| **SEO Analysis** | "How's our organic search?" | Search Console + SEMrush | 3-5 min |
| What you get: 100+ keyword rankings, branded vs non-branded split, content gaps, striking distance opportunities, CTR optimization |
| **Meta Ads Diagnostics** | "What's wrong with our ads?" | Meta Ads API | 3-5 min |
| What you get: Campaign performance, targeting deep-dive, creative ranking with images, spend by country, audience analysis, ad chain diagnosis |
| **Google Ads Analysis** | "Google Ads performance" | Google Ads API | 2-3 min |
| What you get: Campaign metrics, keyword performance, search terms, impression share, budget overview |
| **Competitor Intelligence** | "How do we compare?" | SEMrush | 3-5 min |
| What you get: Keyword gaps, traffic estimates, backlink profiles, competitive moat analysis |
| **GEO/AEO Visibility** | "Are we in AI search?" | SerpAPI + Perplexity + OpenAI | 2-3 min |
| What you get: Google AI Overview presence, ChatGPT mentions, Perplexity citations, structured data audit |
| **Social Media (Instagram)** | "How are our posts doing?" | Instagram Graph API | 2-3 min |
| What you get: Post performance, engagement by type, WoW trends, top/bottom performers |
| **Paid/Organic Overlap** | "Are we wasting ad spend?" | Search Console + Google Ads | 2-3 min |
| What you get: Keywords where you rank organically AND pay for ads, savings opportunities |
| **Complete Audit** | "Analyze everything" | All sources | 5-8 min |
| What you get: All of the above in one tabbed dashboard. Best for monthly reviews. |

---

## Content Engine (content_engine) — "What should we create/fix?"

These crawl pages, audit content quality, and can write content files.

### Content Audits (2-5 minutes → Interactive HTML Dashboard)

| Audit | Best for | What it checks | Time |
|-------|----------|---------------|------|
| **SEO Content Audit** | "Is this page well-optimized?" | Meta tags, headers, content quality, internal links, images, schema | 2-3 min |
| **E-E-A-T Audit** | "Is our site trustworthy?" | 80-item benchmark: Experience, Expertise, Authority, Trust signals | 3-4 min |
| **GEO Audit** | "Will AI cite our content?" | Citability blocks, AI crawler access, platform-specific visibility | 3-4 min |
| **AEO Audit** | "Can we win featured snippets?" | Snippet opportunities, PAA targeting, answer blocks, schema | 2-3 min |
| **Entity Audit** | "Does Google understand our brand?" | 47-signal entity checklist, Knowledge Panel, Wikidata status | 3-4 min |
| **Technical SEO Audit** | "Is our site crawlable?" | robots.txt, sitemap, Core Web Vitals, schema, AI crawler access | 2-3 min |
| **Full Content Audit** | "Comprehensive content review" | All audits above combined into one dashboard | 5-8 min |

### Content Strategy (2-5 minutes → content plan)

| Analysis | Best for | Output | Time |
|----------|----------|--------|------|
| **Keyword Strategy** | "What should we write about?" | 50+ keywords scored, topic clusters, content calendar | 3-5 min |
| **Content Gap Analysis** | "What are competitors writing that we're not?" | Gap keywords, content type recommendations | 3-4 min |

### Content Creation (3-5 minutes → .md files)

| Creator | Best for | Output | Time |
|---------|----------|--------|------|
| **Blog Writer** | "Write a blog post about [topic]" | Full SEO blog with GEO citability blocks, saved to output/content/blogs/ | 3-5 min |
| **Landing Page Writer** | "Write landing page for [product]" | Conversion-optimized copy with headlines, benefits, CTAs | 3-5 min |
| **Content Brief Generator** | "Create a brief for [topic]" | Detailed spec for writers with keywords, outline, competitor analysis | 2-3 min |
| **Social Post Ideator** | "Give me LinkedIn/IG/TikTok post ideas with visuals" | 3 post ideas + generated image for each + artifact URL | 2-4 min |

All content goes through quality scoring (0-100) before delivery. If score < 90, it's revised automatically.

### Content Calendar (content_calendar_planner) — "What should we post this week?"

| Feature | Best for | Output | Time |
|---------|----------|--------|------|
| **7-day calendar (default)** | Weekly planning standup | Markdown calendar: LinkedIn + ad tests + blogs with evidence & links | 3-6 min |
| **Monthly calendar** | Month-ahead planning | Week 1 detailed + weeks 2-4 themed (or full month on request) | 5-10 min |

**How it works:**
1. Agent asks 3 **content** questions (results you want, topics to highlight, what to create) — then clarifies LinkedIn length and blog aim when relevant
2. Pulls SEO, traffic, keyword data, plus **AI web research** for viral LinkedIn/IG/TikTok posts (Perplexity/OpenAI — no social APIs)
3. Proposes **three standard tables** — LinkedIn | Instagram/TikTok | Blog — with fixed columns (Content Idea and Focus, Body/Caption, Evidence, post references).
4. Waits for your **approve** before writing anything

**Example asks:**
- "Plan a 7-day content calendar for LinkedIn and blogs — focus on Indonesia"
- "Content calendar for next week: 3 LinkedIn posts, 1 blog, 2 Meta ad tests"
- "What should we post based on what's trending in B2B sourcing?"

**After approval:** "Write the Day 2 blog" or "Draft the Day 1 LinkedIn post" → routes to content_engine

---

## Strategy (knowledge_expert) — "How should we improve?"

For strategic advice and best practices. Does NOT analyze your specific data.

- "How to improve SEO for Indonesia?"
- "What keywords should we target?"
- "What is GEO/AEO?"
- "B2B sourcing keyword strategy"

Output: Text recommendations (no dashboard or files).

---

## How to choose

| Your question starts with... | Use |
|------------------------------|-----|
| "How are we..." / "What's our..." / "Show me data" | Analytics (data_analyst) |
| "Audit..." / "Is our site..." / "Check..." | Content Audits (content_engine) |
| "Write..." / "Create..." / "Generate..." | Content Creation (content_engine) |
| "What should we..." / "Recommend..." | Content Strategy (content_engine) |
| "How to..." / "What is..." / "Explain..." | Strategy (knowledge_expert) |
| "Generate report" / "Create report" | Report Builder |
