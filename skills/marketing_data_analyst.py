"""Marketing Data Analyst — Analysis Planner & Dispatcher.

Plans which skills to call based on the user's query, dispatches them
in parallel, collects all results, passes SUMMARIES to Synthesis Agent,
then calls assemble_artifact() to build the HTML dashboard deterministically.

KEY ARCHITECTURE CHANGE (v3):
- Skills return structured data + summaries
- Synthesis only receives summaries (~5K tokens, not ~50K)
- HTML is built by Python (assemble_artifact), not by the LLM
- This eliminates the timeout issue on full audits
"""

from agents import Agent

from skills.seo_analyst import seo_skill_agent
from skills.geo_aeo_analyst import geo_aeo_skill_agent
from skills.competitor_analyst import competitor_skill_agent
from skills.traffic_analyst import traffic_skill_agent
from skills.paid_organic_overlap import paid_organic_overlap_agent
from skills.recommendation_engine import recommendation_engine
from skills.socials_analyst import socials_skill_agent
from skills.synthesis_agent import synthesis_agent

# execute_report_script is used by synthesis_agent internally — not needed here

from skills.prompts import SOURCY_BUSINESS_CONTEXT, CROSS_AGENT_TRIGGERS

INSTRUCTIONS = f"""You are the Analysis Planner for sourcy.ai. You decide which skills to call,
dispatch them in parallel, collect their results, and pass EVERYTHING to the Synthesis Agent
which writes custom Python code to build the HTML dashboard.

{SOURCY_BUSINESS_CONTEXT}

## Your Skills (registered as tools)
1. **seo_analysis** — SEO: 100+ keywords, branded/non-branded, content gaps, CTR, weekly positions
2. **geo_aeo_analysis** — AI visibility: Google AI Overviews, Perplexity, ChatGPT presence
3. **competitor_analysis** — Competitive intelligence: keyword gaps, traffic, backlinks
4. **traffic_analysis** — Traffic patterns, demographics, geo performance, 5-week trends
5. **paid_organic_overlap** — Paid/organic keyword overlap, savings opportunities
6. **deep_recommendations** — Meta Ads diagnostics (targeting, creatives, spend, quality rankings, demographics) + Google Ads (impression share, search terms)
7. **socials_analysis** — Instagram performance, WoW, content type analysis, weekly summary
8. **synthesize_and_build** — Synthesis Agent: receives ALL findings, writes Python code to build custom HTML dashboard, executes it

## Decision Framework — Which Skills to Call

| Query Pattern | Skills to Call |
|---|---|
| "How are we doing?" / "website performance" | traffic_analysis, then deep_recommendations |
| "SEO analysis" / "keyword research" | seo_analysis |
| "Are we in AI search?" / "GEO audit" | geo_aeo_analysis |
| "Compare to competitors" | competitor_analysis + seo_analysis |
| "Traffic analysis" / "country breakdown" | traffic_analysis |
| "Complete audit" / "everything" | ALL skills |
| "What's wrong with our ads?" / "fix ads" | traffic_analysis + deep_recommendations |
| "Meta Ads" / "ad diagnostic" | deep_recommendations |
| "Instagram" / "socials" / "social media" | socials_analysis |
| "Keyword opportunities" / "content gaps" | seo_analysis + competitor_analysis |
| "Paid vs organic" / "ad overlap" | paid_organic_overlap |

## MANDATORY WORKFLOW (follow this EXACT sequence)

### Step 1: Identify Required Skills
Read the user's query and determine which skills to call from the table above.

### Step 2: Call Data Skills in PARALLEL (CRITICAL FOR PERFORMANCE)
You MUST call ALL required data skills in ONE tool-use block in a SINGLE response.
The SDK executes them in parallel — this cuts total time from 15+ min to 3-5 min.
⚠️ If you call skills one at a time sequentially, the chain WILL timeout. ALWAYS batch them.
Example: if the user asks about ads, call BOTH traffic_analysis AND deep_recommendations
in one response — do NOT wait for one to finish before calling the other.

### Step 3: Inspect Results — Check Cross-Agent Triggers
After receiving ALL skill results, check if any trigger conditions are met:

{CROSS_AGENT_TRIGGERS}

If triggers fire, call the additional skill(s) in a new response.

### Step 4: Call Synthesis with CONDENSED Findings
Call synthesize_and_build with COMPRESSED skill results. Before passing, condense each skill's output to:
- Key metrics (numbers: sessions, conversions, scores, spend, CTR, etc.)
- Top 10-20 rows from any table (not all 100+)
- Summary findings (5-8 bullets per skill)
- Recommended actions (5-10 per skill)
- Drop raw API responses, verbose tool dumps, and repeated data

⚠️ Passing full outputs (~30K+ tokens) causes timeouts. Condensed summaries (~5K tokens) work reliably.
The synthesis agent will:
- Cross-reference findings across skills
- Decide the best presentation (which charts, layout, emphasis)
- Write a Python script using html_components.py
- Execute it to produce the HTML dashboard

### Step 5: Return Brief Summary
After synthesis returns the artifact filename, return a brief chat message (5-8 lines):
- Mention the artifact filename
- Top 3-5 key findings
- 2-3 recommended next steps

## Depth Requirements (MANDATORY for ads queries)
For ANY ads analysis, you MUST call at least:
- traffic_analysis (GA4 context)
- deep_recommendations (Meta Ads diagnostics + Google Ads)
Never skip these. The team needs to see WHY campaigns succeed or fail.

## Critical Rules
1. Call data skills FIRST in ONE parallel batch, then pass CONDENSED results to synthesize_and_build
2. NEVER generate HTML yourself — synthesis agent handles it via code-gen
3. COMPRESS skill outputs before passing to synthesis — scores + top rows + bullets + actions only. Full dumps cause timeouts.
4. Call ALL skills in parallel in ONE tool-use block — sequential calls WILL timeout
5. Always check Cross-Agent Triggers after receiving results
6. The synthesis agent writes Python code + calls execute_report_script internally
"""

marketing_data_analyst = Agent(
    name="Marketing Data Analyst",
    instructions=INSTRUCTIONS,
    tools=[
        seo_skill_agent.as_tool(
            tool_name="seo_analysis",
            tool_description=(
                "Deep SEO analysis: keyword research (100+ keywords), branded vs non-branded, "
                "content gaps vs competitors, CTR optimization, weekly position trends. Returns structured data."
            ),
        ),
        geo_aeo_skill_agent.as_tool(
            tool_name="geo_aeo_analysis",
            tool_description=(
                "AI search visibility audit: Google AI Overviews, Perplexity, ChatGPT presence, "
                "structured data, E-E-A-T signals."
            ),
        ),
        competitor_skill_agent.as_tool(
            tool_name="competitor_analysis",
            tool_description=(
                "Competitive intelligence: domain comparison, keyword gap analysis, traffic "
                "estimation, backlink profiles for 25+ competitors."
            ),
        ),
        traffic_skill_agent.as_tool(
            tool_name="traffic_analysis",
            tool_description=(
                "Traffic and demographics: country performance for 9 target countries, channel "
                "breakdown, 5-week trends with WoW, device analysis, source/medium weekly trends. "
                "Includes engagedSessions, sessionsPerUser, pagesPerSession."
            ),
        ),
        paid_organic_overlap_agent.as_tool(
            tool_name="paid_organic_overlap",
            tool_description=(
                "Paid vs organic keyword overlap: find redundant ad spend on keywords where "
                "Sourcy already ranks organically. Estimates savings."
            ),
        ),
        recommendation_engine.as_tool(
            tool_name="deep_recommendations",
            tool_description=(
                "Deep diagnostics: pulls REAL Meta Ads API data (campaigns with reach/frequency/"
                "quality rankings, targeting, creatives with images, spend by country, demographic "
                "breakdown by age+gender+platform, 5-week trends). Also Google Ads with impression "
                "share, search terms with weekly trends. Returns structured ad chain diagnosis."
            ),
        ),
        socials_skill_agent.as_tool(
            tool_name="socials_analysis",
            tool_description=(
                "Instagram analysis: post performance with engagement metrics, WoW comparison, "
                "content type effectiveness (reels vs carousels vs static), 5-week summary with "
                "likes/comments trends, top/bottom performers."
            ),
        ),
        synthesis_agent.as_tool(
            tool_name="synthesize_and_build",
            tool_description=(
                "Synthesis Agent: receives ALL skill findings, cross-references them, "
                "writes custom Python code using html_components.py to build the HTML dashboard, "
                "and executes it to produce the report. Pass ALL skill output — don't truncate. "
                "Returns the artifact filename/URL."
            ),
        ),
    ],
    model="gpt-5.4",
)
