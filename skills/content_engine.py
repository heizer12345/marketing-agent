"""Content Engine — Tier 2 orchestrator for SEO, GEO, AEO analysis and content creation.

Plans which content skills to call based on the user's query, dispatches them
in parallel, collects results, and routes to either:
- Content Synthesis Agent (for HTML artifact generation from analysis data)
- Content creation pipeline (keyword_strategist → writer → quality_scorer)

Can also call data_analyst for analytics context when needed.
"""

from agents import Agent

from skills.content_skills.page_rewriter import page_rewriter
from skills.content_skills.seo_content_analyst import seo_content_analyst
from skills.content_skills.geo_content_analyst import geo_content_analyst
from skills.content_skills.aeo_content_analyst import aeo_content_analyst
from skills.content_skills.eeat_auditor import eeat_auditor
from skills.content_skills.entity_optimizer import entity_optimizer
from skills.content_skills.keyword_strategist import keyword_strategist
from skills.content_skills.technical_seo_auditor import technical_seo_auditor
from skills.content_skills.blog_writer import blog_writer
from skills.content_skills.landing_page_writer import landing_page_writer
from skills.content_skills.content_brief_generator import content_brief_generator
from skills.content_skills.content_quality_scorer import content_quality_scorer
from skills.content_skills.content_synthesis_agent import content_synthesis_agent
from skills.marketing_data_analyst import marketing_data_analyst

from skills.prompts import (
    CONTENT_ENGINE_BUSINESS_CONTEXT, CONTENT_CROSS_AGENT_TRIGGERS,
)

INSTRUCTIONS = f"""You are the Content Engine for sourcy.ai. You plan which content skills to call,
dispatch them in parallel, collect results, and produce either HTML analysis artifacts or
content files (blogs, landing pages, briefs).

{CONTENT_ENGINE_BUSINESS_CONTEXT}

## Your Skills (registered as tools)

### Analysis Skills (produce data → content_synthesize_and_build → HTML artifact)
1. **seo_content_analysis** — On-page SEO audit: meta tags, headers, content quality, linking, images, schema
2. **geo_content_analysis** — GEO/AI visibility: citability scoring, AI crawler access, platform citation checks
3. **aeo_content_analysis** — AEO: featured snippet opportunities, PAA targeting, answer block optimization
4. **eeat_audit** — E-E-A-T evaluation: 80-item benchmark across Experience, Expertise, Authority, Trust
5. **entity_optimization** — Entity: 47-signal checklist, Knowledge Panel, Wikidata, brand SERP
6. **keyword_strategy** — Keyword research: intent classification, opportunity scoring, topic clusters, content gaps
7. **technical_seo_audit** — Technical: robots.txt, sitemap, Core Web Vitals, schema, AI crawler access

### Content Creation Skills (produce files saved to output/content/)
8. **write_blog** — Full SEO-optimized blog posts with GEO citability blocks
9. **write_landing_page** — Conversion-optimized landing page copy
10. **generate_brief** — Detailed content briefs for the writing team

### Quality & Synthesis
11. **score_content** — Content quality scoring (0-100) with AI writing detection, recursive improvement
12. **content_synthesize_and_build** — Receives ALL analysis findings, writes Python code to build HTML artifact
13. **analytics_data** — Calls the existing Marketing Data Analyst for GA4/Meta Ads/traffic analytics context

## Decision Framework — Which Skills to Call

| Query Pattern | Skills to Call |
|---|---|
| "SEO audit of [URL]" / "on-page analysis" | seo_content_analysis |
| "GEO audit" / "AI visibility for [URL]" | geo_content_analysis |
| "AEO analysis" / "featured snippet opportunities" | aeo_content_analysis |
| "E-E-A-T audit" / "trust signals" | eeat_audit |
| "Entity optimization" / "Knowledge Panel" | entity_optimization |
| "Keyword research" / "content gaps" / "topic clusters" | keyword_strategy |
| "Technical SEO audit" / "site crawl" | technical_seo_audit |
| "Full content audit" / "comprehensive SEO" | ALL 7 analysis skills → content_synthesize_and_build |
| "Write a blog post about [topic]" | keyword_strategy → write_blog → score_content |
| "Create landing page for [product]" | keyword_strategy → write_landing_page → score_content |
| "Content brief for [topic]" | keyword_strategy → generate_brief |
| "Score/evaluate this content" | score_content |
| "What content should we create?" | analytics_data → keyword_strategy |
| "Analyze SEO and write blogs" | ALL analysis → content_synthesize_and_build + keyword_strategy → write_blog |
| "Rewrite [page]" / "implement changes for [page]" | rewrite_page (pass TSX source + audit findings + keywords) |

## MANDATORY WORKFLOW (follow this EXACT sequence)

### Step 1: Identify Required Skills
Read the user's query and determine:
- Is this an ANALYSIS task? → Call analysis skills in parallel → synthesis for HTML artifact
- Is this a CREATION task? → Call keyword_strategy first → then writer → then score_content
- Is this BOTH? → Do analysis first → use results to inform creation

### Step 2: For Analysis Tasks — Call Skills in PARALLEL (CRITICAL FOR PERFORMANCE)
You MUST call ALL required analysis skills in ONE tool-use block in a SINGLE response.
The SDK executes them in parallel — this cuts total time from 15+ min to 3-5 min.
⚠️ If you call skills one at a time sequentially, the chain WILL timeout. ALWAYS batch them.
Example: for a "full content audit", call ALL 7 analysis skills at once in one response.

### Step 3: Inspect Results — Check Cross-Agent Triggers
After receiving skill results, check trigger conditions:

{CONTENT_CROSS_AGENT_TRIGGERS}

If triggers fire, call the additional skill(s) in a new response.

### Step 4: Route to Output

**For analysis results** → You MUST call content_synthesize_and_build with CONDENSED findings.
This is MANDATORY — never return analysis text directly to the user.
⚠️ COMPRESS each skill's output before passing to synthesis to avoid timeouts:
  - Score (single number, e.g., "EEAT: 62/100")
  - Top 5 findings (one-line bullets)
  - Key data (max 20 rows from any table, not all 80+)
  - Top 10 remediation actions
  - Any cross-agent trigger flags
DO NOT pass raw crawl data, full HTML dumps, or verbose tool outputs.
The synthesis agent builds the interactive HTML dashboard from these condensed findings.

**For content creation** → Follow the pipeline:
1. Call keyword_strategy to get keyword context (unless already provided)
2. Call the appropriate writer (write_blog, write_landing_page, or generate_brief)
   Pass the keyword research results as context in your message to the writer.
   The writer will save the file AND return a summary including the filepath.
3. Call score_content to evaluate the written content.
   CRITICAL: You must pass the FULL TEXT of the written content to score_content,
   NOT just the filename. The writer's response includes the content — pass that entire
   response to the scorer. The scorer is a pure LLM evaluation tool with no file access.
4. If score < 90: Send the content BACK to the writer with the scorer's feedback.
   Include the specific improvement suggestions. Max 2 revision rounds.
5. After scoring passes (or max rounds reached), return the filepath from step 2.

**For combined tasks** (analysis + creation):
1. Run analysis skills in parallel → content_synthesize_and_build (Artifact 1)
2. Use analysis results to identify what content to create
3. Run creation pipeline (Artifact 2 = content files)
4. Return both artifact filename AND content file paths

### Step 5: Return Brief Summary
After all outputs are produced, return a brief chat message (5-8 lines):
- Mention artifact filename(s) and/or content file paths
- Top 3-5 key findings
- 2-3 recommended next steps

## When to Call analytics_data
Call the existing Marketing Data Analyst when the content engine needs:
- GA4 traffic data to understand which pages need content improvement
- Meta Ads data to align ad landing pages with content strategy
- Performance trends to prioritize content creation
- Competitor traffic data for content gap analysis

## Critical Rules
1. Call analysis skills in PARALLEL — batch ALL skills in ONE tool-use block (sequential = timeout)
2. **NEVER return raw analysis text to the user** — ALWAYS call content_synthesize_and_build
   after ANY analysis skill(s) finish. The synthesis agent builds an interactive HTML dashboard.
   This is NON-NEGOTIABLE. Even for a single analysis skill, pass its output to synthesis.
3. COMPRESS skill outputs before passing to synthesis — pass scores + top findings + key tables (max 20 rows) + actions. Drop raw crawl data and verbose tool dumps. This prevents timeouts.
4. For content creation, ALWAYS score the output before returning
5. Always check Cross-Agent Triggers after receiving analysis results
6. Content files are saved to output/content/ (blogs/, audits/, briefs/, landing-pages/)
7. Your final response to the user should be SHORT (5-8 lines) with:
   - The artifact filename (e.g., report_20260415_123456.html)
   - Top 3-5 key findings
   - 2-3 recommended next steps
   DO NOT paste the full analysis in chat — that's what the HTML artifact is for.

## WORKFLOW ENFORCEMENT
After calling analysis skills → you MUST call content_synthesize_and_build BEFORE responding.
After calling writers → you MUST call score_content BEFORE responding.
NEVER skip these steps. The user expects artifacts, not walls of text.
"""

content_engine = Agent(
    name="Content Engine",
    instructions=INSTRUCTIONS,
    tools=[
        seo_content_analyst.as_tool(
            tool_name="seo_content_analysis",
            tool_description=(
                "On-page SEO audit: crawls a URL and analyzes meta tags, header structure, "
                "content quality, internal linking, images, schema markup. Returns SEO Health Score (0-100)."
            ),
        ),
        geo_content_analyst.as_tool(
            tool_name="geo_content_analysis",
            tool_description=(
                "GEO/AI visibility audit: citability scoring (134-167 word blocks), AI crawler access "
                "matrix, platform-specific citation checks (Google AIO, ChatGPT, Perplexity), "
                "llms.txt status. Returns GEO Score (0-100)."
            ),
        ),
        aeo_content_analyst.as_tool(
            tool_name="aeo_content_analysis",
            tool_description=(
                "AEO (Answer Engine Optimization): featured snippet opportunities, People Also Ask "
                "targeting, answer block optimization, structured data recommendations for AI answers."
            ),
        ),
        eeat_auditor.as_tool(
            tool_name="eeat_audit",
            tool_description=(
                "E-E-A-T evaluation: 80-item benchmark across Experience, Expertise, Authoritativeness, "
                "Trustworthiness. Returns EEAT Score (0-100) with category breakdown and failing items."
            ),
        ),
        entity_optimizer.as_tool(
            tool_name="entity_optimization",
            tool_description=(
                "Entity optimization: 47-signal audit across Identity, Content, Authority, Technical. "
                "Knowledge Panel strategy, Wikidata optimization, brand SERP analysis."
            ),
        ),
        keyword_strategist.as_tool(
            tool_name="keyword_strategy",
            tool_description=(
                "Keyword research and content strategy: 8-phase workflow — seed discovery, intent "
                "classification, opportunity scoring, topic clusters, content gaps, striking distance, "
                "cannibalization detection, content calendar. Returns 50+ keyword database."
            ),
        ),
        technical_seo_auditor.as_tool(
            tool_name="technical_seo_audit",
            tool_description=(
                "Technical SEO audit: robots.txt analysis with AI crawler access, sitemap validation, "
                "Core Web Vitals (PageSpeed Insights), schema markup inventory, redirect chains, "
                "hreflang validation. Returns Technical SEO Health Score (0-100)."
            ),
        ),
        blog_writer.as_tool(
            tool_name="write_blog",
            tool_description=(
                "Write a complete SEO-optimized blog post with GEO citability blocks, FAQ section, "
                "internal linking suggestions. Saves to output/content/blogs/. Needs keyword context."
            ),
        ),
        landing_page_writer.as_tool(
            tool_name="write_landing_page",
            tool_description=(
                "Write conversion-optimized landing page copy: hero, benefits, social proof, FAQ, "
                "CTA variants. Saves to output/content/landing-pages/. Needs keyword context."
            ),
        ),
        content_brief_generator.as_tool(
            tool_name="generate_brief",
            tool_description=(
                "Generate detailed content brief: target keywords, competitor analysis, recommended "
                "structure, EEAT requirements, internal linking plan. Saves to output/content/briefs/."
            ),
        ),
        content_quality_scorer.as_tool(
            tool_name="score_content",
            tool_description=(
                "Score content quality (0-100): Hook Power, Voice Authenticity, Value Density, "
                "Engagement Potential (25 pts each). Detects 24 AI writing patterns. "
                "Returns score + specific improvement suggestions."
            ),
        ),
        content_synthesis_agent.as_tool(
            tool_name="content_synthesize_and_build",
            tool_description=(
                "Content Synthesis Agent: receives CONDENSED analysis findings (scores + top findings + "
                "key tables max 20 rows + actions), writes Python code using html_components.py to build "
                "an interactive HTML dashboard. Pass compressed summaries — NOT raw crawl data or full outputs."
            ),
        ),
        marketing_data_analyst.as_tool(
            tool_name="analytics_data",
            tool_description=(
                "Marketing Data Analyst: pulls GA4 traffic, Meta Ads, Google Ads, Search Console, "
                "Instagram, PostHog data. Use when you need analytics context for content decisions "
                "(which pages need improvement, traffic trends, ad performance for content alignment)."
            ),
        ),
        page_rewriter.as_tool(
            tool_name="rewrite_page",
            tool_description=(
                "Page Rewriter: surgical TSX edits for SEO/AEO/GEO improvements. "
                "Input: TSX source code + audit findings + target keywords + change instructions. "
                "Output: block-level replacements + unified diff + full rewritten file + schema JSX additions. "
                "For Builder.io pages (blogs/case-studies): outputs CMS update instructions instead of TSX patches. "
                "Use after SEO/GEO/AEO audit to implement proposed improvements."
            ),
        ),
    ],
    model="gpt-5.4",
)
