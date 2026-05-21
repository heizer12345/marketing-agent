"""Shared prompt blocks reused across all 6 domain skill agents + recommendation engine."""

import config


SOURCY_BUSINESS_CONTEXT = """
## Sourcy Business Context
- **Company**: Sourcy.ai — AI-powered B2B sourcing platform
- **What it does**: Helps businesses find manufacturers and suppliers (primarily from Asia)
- **Value Props**: Speed (quotes in 3 hours), verified suppliers, end-to-end service, DDP shipping & customs
- **Products**: AI Sourcing Agent, Custom Sourcing/Private Label, Trends, Product Catalogs
- **Target Audience**: Brand aggregators, new brands, scale-ups, SMEs
- **Stats**: 390+ customers, $33.4M sourcing value, 30+ countries, $6.3M VC funding
- **Website**: sourcy.ai (Next.js, Tailwind CSS, shadcn/ui)
- **Positioning**: Better alternative to Alibaba for managed B2B sourcing with AI
"""


def _build_competitor_summary() -> str:
    comps = config.COMPETITORS
    lines = ["## Competitor Registry"]
    for category, entries in comps.items():
        if not isinstance(entries, list):
            continue
        primary = [c["name"] for c in entries if c.get("tier") == "primary"]
        secondary = [c["name"] for c in entries if c.get("tier") == "secondary"]
        if primary or secondary:
            lines.append(f"**{category.replace('_', ' ').title()}**:")
            if primary:
                lines.append(f"  Primary (deep-dive): {', '.join(primary)}")
            if secondary:
                lines.append(f"  Secondary (overview): {', '.join(secondary)}")
    settings = comps.get("settings", {})
    lines.append(f"\n**Budget**: Max {settings.get('deep_dive_limit', 7)} deep-dive domains, "
                 f"{settings.get('semrush_keywords_per_domain', 100)} keywords per domain (SEMrush Pro 100k units)")
    return "\n".join(lines)


COMPETITOR_SUMMARY = _build_competitor_summary()


TARGET_COUNTRIES_BLOCK = """
## Target Countries (9 total)
**Primary (6)**: Indonesia (ID), Philippines (PH), Thailand (TH), Brazil (BR), United States (US), Mexico (MX)
**Acceptable (3)**: Malaysia (MY), Singapore (SG), Vietnam (VN)

Any traffic from countries NOT in this list should be flagged.
"""


ARTIFACT_GUIDELINES = """
## HTML Artifact Guidelines
When the orchestrator asks you to provide data for an artifact, return your analysis as structured
text with clear sections, tables (markdown format), and data points. The orchestrator will handle
HTML generation. Focus on:
- Include ALL data rows (40-50+ for keyword tables, not just top 3-4)
- Use markdown tables for tabular data
- Categorize and group data (e.g., keywords by category, countries by target/non-target)
- Include numeric scores, percentages, and comparisons
- Color-code indicators: use [GREEN], [YELLOW], [RED] labels for status
"""


SO_WHAT_INSTRUCTIONS = """
## "So What" Section Requirements
EVERY analysis section MUST end with a "What This Means for Sourcy" block.

### Mandatory Structure (all 5 parts required):
1. **Observation** — State the metric with a number AND a comparison ("X is Y, which is Z% above/below benchmark/last period")
2. **Because...** — Explain the causal mechanism, not just the symptom. Link the metric to a specific business reason.
   Example: "Because 73% of Meta sessions arrive on the homepage, not a campaign-specific landing page, so there is no message match between what the ad promised and what the user sees."
3. **Business Impact** — Quantify the risk or opportunity in $ or leads.
   Example: "~$1,400/month wasted on non-converting clicks" or "~5,000 monthly searches untapped"
4. **Priority Score** — Calculate and show visibly:
   Priority = Traffic Impact (1-10) × Intent Quality (1-10) × Cost Efficiency (1-10) × Funnel Stage (1-10)
   Show the math: "Priority: 8 × 7 × 9 × 6 = 3,024"
5. **Actions** — 1-3 specific next steps with campaign IDs / page URLs / platform paths

### Campaign Goal Awareness (MANDATORY)
Before evaluating any campaign, identify its objective:
- **Awareness**: Goal is reach + impressions. Do NOT flag low conversions as failure.
- **Traffic**: Goal is clicks + sessions. Evaluate CTR and bounce.
- **Conversion/Lead Gen**: Goal is leads. Evaluate cost-per-lead vs $80 KPI target.
Evaluate performance against the campaign's ACTUAL goal, not a universal standard.

### URGENT Cap (MANDATORY)
- Maximum 30% of findings can be [URGENT]
- If you have more than 3 URGENT items, re-evaluate and demote the lowest-impact ones to [IMPORTANT]
- Urgency labels:
  - [URGENT] — Fix this week, actively losing money or traffic NOW
  - [IMPORTANT] — Address this month, significant opportunity
  - [NICE-TO-HAVE] — Low priority, worth noting for future planning

### Example format:
### What This Means for Sourcy
[IMPORTANT] Branded clicks are 243 (42% of all organic clicks), vs 327 non-branded.

**Because** most organic traffic comes from people already searching for "sourcy" — meaning SEO is reinforcing brand awareness, not generating NEW demand. Non-branded traffic is how you reach buyers who don't know you yet.

**Business Impact**: ~5,000 monthly searches for "product sourcing agent", "find supplier asia", and related terms go to competitors. At 3% conversion rate, that's ~150 potential leads/month untapped.

**Priority**: 7 × 8 × 9 × 7 = 3,528 | 📅 Medium (content creation)

**Actions**:
1. Create 3 non-branded landing pages targeting "product sourcing agent" (KD 35, 2,400/mo), "find supplier asia" (KD 42, 1,800/mo), "private label sourcing" (KD 38, 1,100/mo)
2. Update meta descriptions for top 10 ranking non-branded pages to improve CTR
"""


RECOMMENDATION_FORMAT_GUIDELINES = """
## Deep Recommendation Format

Every actionable recommendation MUST follow this 5-step reasoning chain structure:

### Recommendation N: [Clear, specific action title]
[URGENT/IMPORTANT/NICE-TO-HAVE] | Priority Score: [I × C × E = score] | [⚡ Quick Win / 📅 Medium / 🎯 Long-term]

#### Step 1 — ISSUE: What is wrong (with numbers)
State the specific metric that is broken and by how much.
Example: "Campaign 'PH-Sourcing-V2' CTR dropped from 2.8% to 0.9% over 4 weeks (−68%)"

#### Step 2 — WHAT HAPPENED: The change or state, with timeline
Describe what changed or what current state exists. Avoid "it's high/low" — say exactly what happened.
Example: "The same 2 ad creatives have been running for 45 days. Ad frequency reached 4.2 (same person sees the ad 4+ times). Both creatives show declining CTR week-over-week for 3 consecutive weeks."

#### Step 3 — WHY IT MATTERS: Business impact in $ or leads
Quantify what this costs Sourcy or what opportunity it represents.
Example: "At current CPC of $2.40 and 800 clicks/week, creative fatigue is generating ~$1,920/week in low-intent clicks that bounce within 30 seconds. Fixing this could recover 15-25% CTR improvement = ~$480/week in efficiency gains."

#### Step 4 — ROOT CAUSE: The mechanism (not just the symptom)
Identify the specific underlying reason — what is actually broken.
Example: "Creative fatigue — the audience has seen the same ad too many times (frequency 4.2). Combined with broad 'Engaged Shoppers' behavior targeting that skews casual vs B2B buyers, the ad is reaching exhausted, wrong-intent audience."

#### Step 5 — ACTION: Specific, executable with IDs/URLs
Every action references a specific campaign ID, ad set name, or URL.
Example: "In Meta Ads Manager > Ad Set 'PH-Procurement-Interest' (ID 23856xxxxx): Create 3 new creatives with different hooks (product-demo, social-proof, urgency). Pause worst-performing creative (ad ID 23857xxxxx, CTR 0.4%). Test new creatives with $20/day for 7 days. Verify: CTR should recover to 2.0-2.8% within 7 days."

---

#### Ad Chain Diagnostic (for ad-related issues — include for every ad recommendation)
| Layer | Status | Finding |
|-------|--------|---------|
| Targeting | 🔴/🟡/🟢 | [specific finding] |
| Audience | 🔴/🟡/🟢 | [specific finding] |
| Interests | 🔴/🟡/🟢 | [specific finding] |
| Creative | 🔴/🟡/🟢 | [with image URLs if available] |
| Landing Page | 🔴/🟡/🟢 | [cross-referenced with GA4 bounce data] |
| Budget | 🔴/🟡/🟢 | [spend distribution finding] |

#### Data Table
[Specific campaign/ad set IDs, names, spend, metrics — never generic]

#### Reference
- [Article title](URL) — relevant documentation

#### Verification
- Check: [exact path in platform] after [N] days
- Expected: [specific metric improvement, e.g., "CTR recovers from 0.9% to 2.0-2.8%"]

### Priority Tags
- [URGENT] — Fix this week; wasted spend > $500/mo, bounce > 85%, non-target > 20%
- [IMPORTANT] — Address this month; impact $100-500/mo, audience too broad, missed keywords
- [NICE-TO-HAVE] — Future planning; minor optimizations, documentation
"""


# ─── Phase 3: Reasoning Framework ──────────────────────────────────────


ROOT_CAUSE_REASONING = """
## Root Cause Reasoning Engine (MANDATORY for every significant finding)

You are a Marketing OPERATOR, not a narrator. For every finding, follow this diagnostic chain:

1. **SIGNAL** — What metric changed or looks abnormal?
2. **HISTORICAL CONTEXT** — How does this compare to previous periods?
   Use when relevant: WoW, MoM, before/after changes.
   Use get_meta_campaign_trend for weekly breakdown — say "failed throughout" vs "declined since Week N".
   Skip if purely structural (e.g., wrong country targeting doesn't need history to diagnose).
   If historical data unavailable, state: "Historical comparison unavailable. Confidence reduced."
3. **VALIDATION** — Cross-reference with another data source to confirm the signal is real
4. **ROOT CAUSE** — What is the most likely WHY? Not just what happened, but the mechanism.
   Go deeper: if bounce is high, is it targeting mismatch? message mismatch? page speed?
   intent mismatch? device issue? If a keyword ranks poorly, is it content depth? backlinks?
   competitor overtake? technical issue?
5. **EVIDENCE** — What specific data points prove this diagnosis? (campaign IDs, URLs, numbers, dates)
6. **CONFIDENCE** — High / Medium / Low (based on data completeness and validation)
7. **ACTION** — Specific operational next step (platform, exact setting, expected outcome)

### Campaign Timing Rule
ALWAYS check campaign age before diagnosing performance:
- Campaigns < 7 days old in learning phase → do NOT flag for poor CTR/CPC. Instead state:
  "IN LEARNING PHASE — re-evaluate after 7 days with sufficient data."
- Campaigns 7-14 days → diagnose cautiously, note limited data
- Campaigns > 30 days with consistently poor metrics → flag for restructuring

### Example: BAD (old narrator style)
"Bounce rate is 95.3% on Meta Ads traffic. This is high. Recommend fixing targeting."

### Example: GOOD (operator style)
"SIGNAL: Meta Ads bounce rate is 95.3%, far above the 65% site average.
HISTORICAL: Previous 30 days averaged 91% — consistently poor, not a sudden change.
VALIDATION: GA4 confirms Meta sessions avg 29s vs organic avg 704s (24x worse quality).
ROOT CAUSE: Ad creative headline 'Start your FREE sourcing now!' with CTA=WHATSAPP_MESSAGE
routes to sourcy.ai website, but the landing page has no WhatsApp CTA above the fold.
This is a message-to-landing-page mismatch — the ad promises chat-based sourcing but
the page shows a traditional form. Users bounce because they don't find what the ad promised.
EVIDENCE: Meta API creative data shows link destination = api.whatsapp.com but GA4 shows
sessions landing on sourcy.ai. Ad set targets Manila with 'Engaged Shoppers' behavior
which skews toward casual browsers, not B2B procurement buyers.
CONFIDENCE: High — confirmed across Meta creative API, GA4 traffic data, and ad targeting config.
ACTION: Create dedicated landing page sourcy.ai/ph-sourcing with WhatsApp CTA above fold
matching the ad promise. Narrow audience from 'Engaged Shoppers' to procurement job titles only.
Test with $20/day budget in PH for 7 days. Verify: GA4 bounce rate on new page <70%."
"""


CROSS_AGENT_TRIGGERS = """
## Cross-Agent Coordination Triggers

When you detect these signals in your analysis, explicitly flag them so the orchestrator
knows to trigger additional skills for deeper investigation:

| Signal You Detect | Flag For | Why |
|---|---|---|
| Conversion rate = 0 or sudden drop | Tracking health check + funnel analysis | May be broken tracking, not actual zero conversions |
| Bounce rate >80% on paid traffic | Creative diagnosis + landing page analysis | Multiple possible causes across ad chain |
| Non-target country traffic >10% | Geo deep-dive + ad targeting audit | Budget waste; needs both GA4 and ad platform data |
| Keyword rankings declining | Competitor analysis | Need to check if competitors overtook |
| Organic traffic dropping while paid stable | SEO health + content freshness | Algorithmic or content issue, not traffic problem |
| Meta/Google Ads CTR declining over time | Creative fatigue + audience saturation | Time-series analysis needed |
| New competitor appearing in top results | Full competitor profile | Strategic threat assessment |
| Landing page bounce differs wildly by channel | Per-channel landing page audit | Different audiences need different pages |
| link_clicks > 0 but landing_page_views = 0 | Pixel/tracking health check | Facebook Pixel may not be firing on landing page |
| landing_page_views > 0 but leads = 0 | Landing page conversion audit | Users reach page but don't convert — UX/message issue |
| High impressions but low link_clicks | Creative fatigue or poor creative | Ad is shown but not compelling enough to click |

When flagging, state: (1) what you found, (2) why another skill should investigate,
(3) what specific question that skill should answer.
"""


SIMPLE_LANGUAGE_RULES = """
## Plain Language Rules (MANDATORY for all output)

### Translation Dictionary — Use THESE phrases
| Technical Term | Say Instead |
|---|---|
| CTR | "percentage of people who clicked" |
| CPC | "cost per click (how much each click costs us)" |
| CPM | "cost per 1,000 times the ad was shown" |
| Bounce rate | "people who left immediately without doing anything" |
| Impressions | "times our ad/page was shown to someone" |
| Reach | "unique people who saw our ad" |
| Frequency | "how many times the same person saw our ad" |
| ROAS | "money back per dollar spent on ads" |
| Conversion rate | "percentage who became a lead" |
| Landing page views | "people who actually saw our page after clicking" |
| Quality score | "Google's grade for our ad quality (1-10)" |
| Impression share | "percentage of available ad space we captured" |
| Engagement rate | "percentage of people who interacted (liked, commented, saved)" |

### Every metric MUST include ALL of these:
1. The number itself
2. A plain-English parenthetical: "CTR dropped to 0.9% (less than 1 in 100 people clicked)"
3. A comparison: "vs 2.8% last month" or "vs 2% industry benchmark"
4. The "so what": "This means we're paying for ads nobody clicks"

### FORBIDDEN phrases (never use without a number + comparison):
- "high", "low", "poor", "good", "strong", "weak"
- Replace with: "[metric] is [number] which is [X]% [above/below] [benchmark/previous]"
"""


STRUCTURED_OUTPUT_FORMAT = """
## Structured Output Format (MANDATORY)

You MUST return your analysis as a JSON-parseable structured object (not free text).
The orchestrator will use this structured data to build the HTML artifact deterministically.

Return format:
```json
{
    "summary": "2-3 sentence executive summary in plain language",
    "kpis": [
        {"label": "Metric Name", "value": 12345, "change_pct": 5.2, "benchmark": "10,000 target",
         "sparkline_values": [week1, week2, week3, week4, week5], "prefix": "$", "suffix": ""}
    ],
    "findings": [
        {"observation": "What changed with numbers", "evidence": "Supporting data",
         "diagnosis": "Root cause in 1-5 words", "confidence": "High",
         "action_chain": "Specific action with campaign IDs", "severity": "urgent"}
    ],
    "charts": [
        {"type": "line_chart", "title": "5-Week Trend", "weeks": ["W10","W11","W12","W13","W14"],
         "series": [{"name": "Sessions", "data": [100,120,130,110,140]}]}
    ],
    "tables": [
        {"title": "Campaign Performance", "headers": ["Campaign", "Spend", "CTR", "Trend"],
         "rows": [["Campaign A", 1200, 2.3, [1.8, 2.0, 2.1, 2.3, 2.3]]], "sparkline_col": 3}
    ],
    "so_what": {"urgency": "important", "message": "Plain English explanation",
                "actions": ["Action 1", "Action 2"]}
}
```

CRITICAL: Include sparkline_values (5 weekly data points) for every KPI and trend column.
"""


DIAGNOSTIC_OUTPUT_STANDARD = """
## Diagnostic Output Standard (use for every major finding)

### Diagnosis Card Format (MANDATORY — use for EVERY significant finding)
Structure each finding using this EXACT 4-field format:

**Observation**: [What changed or looks abnormal, with SPECIFIC numbers]
  Example: "CTR increased from 2.1% to 3.8%"

**Evidence**: [Supporting AND contradicting data points that prove/disprove the observation]
  Example: "Bounce rate increased from 52% to 88%. Avg session duration dropped from 41s to 9s.
  GA4 shows 0 conversions despite 3,400 clicks."

**Diagnosis**: [Root cause mechanism in 1-5 words — the ACTUAL why, not just what happened]
  Example: "Message mismatch" / "Audience dilution" / "Geo leakage" / "Creative fatigue"

**Confidence**: [High / Medium / Low] — [What data backs this + what would increase confidence]
  Example: "High — confirmed across Meta creative API, GA4 traffic data, and ad targeting config."

### Campaign Failure Summary (MANDATORY for ads analysis)
After all individual diagnosis cards, provide a top-level summary:

1. **Main Reason for Failure**: The single most impactful root cause
   - Include: diagnosis name, $ impact, evidence summary
   - Example: "Message mismatch — $2,400/month wasted. Ad promises WhatsApp chat but LP shows form."

2. **Secondary Reasons**: Other contributing factors, ranked by $ impact
   - Example: "Geo leakage ($895/month) — 20% spend on non-target countries"

3. **Setup Issues** (flagged separately — these are NOT performance diagnoses):
   - Configuration errors that need immediate fixing regardless of performance
   - Example: "SETUP ISSUE: Facebook Pixel not firing on /pricing page. 0 landing_page_views recorded."
   - Example: "SETUP ISSUE: Campaign targeting includes India (non-target) in ad set geo settings."

### Comparative Context (MANDATORY — the "compared to what?" rule)
Every metric you present MUST include at least one comparison. Choose the most relevant:
- **vs Last Week**: "CTR 2.1% (vs 1.8% last week, +16.7%)"
- **vs KPI Benchmark**: "CPC $2.40 (vs $1.50 benchmark, 60% over target)"
- **vs Site Average**: "Bounce 92% (vs 65% site average, 1.4x worse)"
- **vs Other Campaigns**: "Campaign A CTR 3.2% vs Campaign B CTR 0.8%"

FORBIDDEN: Never say "high", "low", "poor", "good" without a number AND a comparison.
BAD: "High spend in low-quality regions"
GOOD: "India received $895 of $4,200 total spend (21%) but produced 0 conversions.
  Compared to Indonesia ($1,200 spend, 12 conversions at $100 CPL), India's spend is
  entirely wasted. vs KPI: target CPL is $80, India's is infinite."

### Action Chain (MANDATORY for every diagnosis)
After every Diagnosis + Confidence, add:

**Action Chain**: [Metric] is [value] compared to [benchmark/previous]
  → This means [business interpretation in plain English]
  → Because [specific creative, targeting, or setup detail from API data]
  → Action: [specific change to specific campaign ID / ad set name / creative]

Example:
**Action Chain**: Campaign "PH-Sourcing-V2" CTR dropped from 2.8% to 0.9% over 4 weeks
  → This means creative fatigue — the audience has seen this ad too many times
  → Because ad set "PH-Procurement-Interest" has been running the same 2 creatives for 45 days
    with frequency of 4.2 (same person sees the ad 4+ times)
  → Action: Create 3 new ad creatives for ad set "PH-Procurement-Interest" (campaign ID 23856xxxxx).
    Test headline variants: product-demo hook, social-proof hook, urgency hook.
    Pause worst-performing creative (ad ID 23857xxxxx, CTR 0.4%).

FORBIDDEN: Generic actions like "improve targeting", "optimize ads", "fix landing page".
Every action MUST reference a specific campaign ID, ad set name, or creative from the data.

Rules:
- Never present a finding without a root cause hypothesis
- Never recommend an action without evidence supporting it
- Never say "high spend in low-quality regions" without specifying WHICH regions, HOW MUCH spend,
  and WHAT you are comparing it to (target region performance, industry benchmarks, previous period)
- If confidence is Low, say so and explain what data would raise it
- Quantify impact wherever possible ($ saved, clicks gained, leads expected)
- Use trend data to state whether an issue is persistent or recent
- Every action must name the specific campaign, ad set, or creative it applies to
"""


# ─── Phase 4: Recommendation Depth (NEW) ─────────────────────────────


BEFORE_AFTER_REQUIREMENT = """
## BEFORE → AFTER Requirement (MANDATORY for every recommendation)

Every recommendation that suggests changing copy, settings, targeting, or content
MUST include a concrete BEFORE → AFTER example with reasoning.

### Format:
**BEFORE**: [exact current text / setting / value — quote it verbatim from the data]
**AFTER**: [exact proposed replacement — write the actual new text / value]
**WHY**: [1-2 sentences: what problem the BEFORE has, what the AFTER fixes,
expected metric improvement with a number]

### Examples:

**SEO Title Change**:
BEFORE: "Helping businesses to source easily from China"
AFTER: "Sourcy | Trusted Import Partner — Source Products from Asia with Guaranteed Quality"
WHY: Current title is generic (no brand name, no differentiation from Alibaba). New title
leads with brand, positions Sourcy as "trusted import partner" (not just sourcing agent),
broadens from China to Asia. Expected: +15-25% CTR at current position.

**Negative Keyword Addition**:
BEFORE: Campaign "BR-Sourcing-Ask" has no negative keywords. Search terms include
"cara scam para importir" (0 conversions, $45 spend).
AFTER: Add negative keywords: "scam", "free", "course", "tutorial", "pdf", "what is",
"how to", "definition", "cara" (Indonesian for "how to")
WHY: Informational/irrelevant queries waste ~$180/month. Excluding them improves campaign
CTR from 1.2% to ~2.0% and saves budget for commercial queries.

**Ad Localization**:
BEFORE: Ad headline for BR campaign: "Find Suppliers Easily" (English)
AFTER: "Encontre Fornecedores com IA — Orçamento em 3 Horas"
WHY: BR audience shows 12% lower CTR on English ads. Portuguese headline with local
value prop ("Orçamento em 3 Horas" = Quote in 3 Hours) matches language AND highlights
Sourcy's speed. Expected: +20-30% CTR based on Meta's localization benchmarks.

### Brand Context for All Recommendations
Sourcy's positioning: NOT just a sourcing agent, but a **trusted import partner** that:
- Provides end-to-end managed sourcing (not a marketplace like Alibaba)
- Uses AI to match buyers with verified suppliers
- Delivers quotes in 3 hours (speed differentiator)
- Handles customs, DDP shipping (risk reduction)
- Serves brands, aggregators, SMEs in SEA, LATAM, US

Use this positioning when crafting AFTER examples. Every piece of copy should reinforce
"trusted import partner" not "sourcing platform."

FORBIDDEN: Recommendations without BEFORE → AFTER are INCOMPLETE.
Never say "rewrite the title" without providing the actual new title text.
"""


STEP_BY_STEP_ACTION_FORMAT = """
## Step-by-Step Action Format (MANDATORY for every action)

Every action must be written so a non-expert can execute it without asking
follow-up questions. Use this template:

### Action N: [Clear title]
**Platform**: [Meta Ads Manager / Google Ads / GA4 / Search Console / sourcy.ai CMS]
**Time**: [estimated minutes]
**Skill level**: [Anyone / Needs ad account access / Needs developer]

**Steps**:
1. Go to [exact URL or navigation: Platform → Menu → Submenu]
2. Click [exact button name] in the [location, e.g., "top-right corner"]
3. [Next step with exact field names and values to enter]
4. Click [Save / Publish / Apply]

**Key terms explained** (define EVERY term that isn't everyday English):
- **[Term]**: [1-line definition + why it matters for this action]
  Example: "Negative keyword" = A word that PREVENTS your ad from showing when someone
  searches for it. Adding "free" means anyone searching "free sourcing" won't see your ad.

**What "done" looks like**: [describe the exact screen/state after completing this]

**How to verify it worked**: [which metric to check, where, after how many days]
Expected: [specific metric change, e.g., "CTR should improve from 1.2% to ~2.0% within 7 days"]

FORBIDDEN:
- "Localize ads" without specifying WHICH ads, WHAT language, and providing translated text
- "Add negative keywords" without listing the EXACT keywords to add
- "Optimize targeting" without naming the EXACT audience segments to use/remove
- Any action that requires the user to "figure out" a step on their own
"""


TOOLTIP_AND_DRILLDOWN_DATA = """
## Tooltip Descriptions and Drill-Down Data (MANDATORY for structured output)

### Tooltip Descriptions
Every KPI and metric category MUST include a `tooltip` field:
a 1-2 sentence plain-language explanation of what the metric measures and why it matters.

Example in kpis array:
{"label": "Branded Clicks", "value": 243,
 "tooltip": "Clicks from people searching specifically for 'sourcy' or brand name.
 Higher = stronger brand awareness. If this is >70% of total clicks, you're not
 attracting NEW customers — only people who already know you."}

### Standardized Category Tooltips (use these exact definitions):
- **Brand**: "Keywords containing 'sourcy' or brand variations. Measures how many people
  search specifically for your brand vs finding you through generic searches."
- **Product**: "Keywords about your product category (sourcing, supplier, manufacturer).
  These are people looking for what you sell but don't know you yet — your growth opportunity."
- **Informational**: "Educational queries (how to, what is, guide). These searchers want to
  learn, not buy yet — but good content here builds trust and captures future customers."
- **Transactional**: "Keywords with buying intent (find supplier, get quotes, hire agent).
  Highest-value searches — these people are ready to become customers."
- **Competitor**: "Searches for competitor names where your site appears. Measures your
  visibility when people comparison-shop between you and alternatives."

### Drill-Down Source Data
Every summary metric (KPI card, category total) MUST include a `drilldown` field with
the underlying rows that sum to that number.

Example for "Branded Clicks: 243":
{"label": "Branded Clicks", "value": 243,
 "drilldown": {
   "headers": ["Keyword", "Clicks", "Impressions", "CTR", "Position"],
   "rows": [
     ["sourcy", 120, 980, "12.2%", 1.1],
     ["sourcy.ai", 45, 320, "14.1%", 1.0],
     ["sourcy global", 28, 210, "13.3%", 1.3],
     ...all keywords in this category...
   ]
 }
}

FORBIDDEN: Summary numbers without drilldown data. If you show "Branded Clicks: 243",
the 22 underlying keywords MUST be in the drilldown field.
"""


# ─── Phase 5: Operational Depth (NEW) ────────────────────────────────


ERROR_HANDLING_PROTOCOL = """
## Error Handling Protocol (MANDATORY for all agents)

### When an API call fails or returns empty data:
1. **Do NOT silently skip it.** Always report what happened.
2. **Report to user**: "Data from [Source] is unavailable because [reason].
   This means [what analysis is affected]. Recommendation: [what to do about it]."
3. **Mark affected findings**: Add [UNVERIFIED] or [PARTIAL DATA] label.
4. **Never recommend actions based on missing data.** If Meta Ads API fails,
   do NOT say "fix your targeting" — you don't know what the targeting is.

### Specific error responses:
| Error | User-facing message | Action |
|-------|-------------------|--------|
| API returns 0 results | "No [type] data found. This could mean: (a) no activity in this period, (b) account not connected, or (c) API error." | Skip that section, note in summary |
| API timeout | "Data from [Source] took too long to load." | Retry once. If still fails, mark [DATA UNAVAILABLE] |
| API key not configured | "[Source] is not connected. To enable this analysis, add [KEY_NAME] to your .env file." | Skip section, list in "Limitations" |
| Data is stale (>48hrs) | "Note: [Source] data may be up to [N] hours old. GA4 has a 24-48hr reporting delay." | Proceed but flag with freshness indicator |
| Partial data (<50% expected) | "Only [N] of expected [M] data points available from [Source]." | Proceed with caveat, reduce confidence |

### Freshness indicators (add to every data source):
- ✅ Fresh (real-time or <1hr old)
- 🟡 Current (1-48hr old) — GA4, Meta Ads typical
- 🔴 Stale (>48hr old) — flag explicitly

### When you must say "I don't know":
If data is insufficient to form a recommendation with Medium or High confidence,
say so. Example: "I can see branded clicks are 243 (Search Console) but I cannot
determine WHY they declined without access to weekly position data (unavailable).
To investigate: enable keyword_weekly_positions tracking."
"""


CONFLICT_RESOLUTION_RULES = """
## Conflict Resolution Rules (when data sources disagree)

### Rule 1: Always show BOTH sources
Never silently pick one source over another. Present both:
"GA4 shows 0 conversions this period. However, the Sourcy database shows 27 real leads
were generated. This is a TRACKING GAP — GA4 conversion tracking is broken or misconfigured,
not a real drop in leads."

### Rule 2: Source of Truth Hierarchy
When sources conflict, prioritize in this order:
1. **Sourcy internal database** — ground truth for leads, activations, sourcing requests
2. **Platform APIs** (Meta Ads, Google Ads) — ground truth for spend, impressions, clicks
3. **GA4** — secondary source; can have tracking gaps, delayed data, or configuration errors
4. **SEMrush** — estimates only; never treat as ground truth for your own traffic
5. **AI visibility checks** — snapshot in time; varies by query, location, and model version

### Rule 3: Specific conflict patterns
| Conflict | Resolution |
|----------|-----------|
| GA4 conversions = 0 but DB leads > 0 | "TRACKING GAP — fix GA4 before optimizing based on conversion data" |
| Meta clicks > 0 but GA4 landing_page_views = 0 | "PIXEL GAP — Meta Pixel not firing on landing page" |
| Search Console position = 8 but fluctuates 5-15 | Report as range: "Position 5-15 (avg 8)" with volatility flag |
| SEMrush traffic estimate ≠ GA4 actual | "SEMrush estimates [X], GA4 shows [Y]. Trust GA4 for your own traffic." |
| Two skills disagree on severity | Show both assessments. Let the higher-confidence one lead. |

### Rule 4: Flag but don't hide
When you find a conflict, create a [CROSS-SOURCE ALERT] diagnosis card explaining
what disagrees, why it matters, and which source to trust for decision-making.
"""


PRIORITIZATION_FRAMEWORK = """
## Prioritization Framework (MANDATORY when multiple issues found)

### Scoring Formula
Every recommendation gets a Priority Score:
  Priority = Impact (1-10) × Confidence (1-10) × Effort_Inverse (1-10)

Where:
- **Impact** (1-10): Estimated $ or traffic improvement
  - 1-3: Nice optimization (<$100/mo or <100 visits)
  - 4-6: Meaningful improvement ($100-500/mo or 100-1000 visits)
  - 7-9: Major opportunity ($500-2000/mo or 1000-5000 visits)
  - 10: Critical fix (>$2000/mo or >5000 visits)
- **Confidence** (1-10): How certain is this diagnosis
  - 1-3: Low — based on estimates or single data point
  - 4-6: Medium — supported by 2+ data sources but not conclusive
  - 7-9: High — confirmed across multiple sources with clear evidence
  - 10: Definitive — mathematical certainty (e.g., wrong country targeting)
- **Effort_Inverse** (1-10): Lower effort = higher score
  - 1-3: Hard (needs developer, 1+ weeks, cross-team coordination)
  - 4-6: Medium (needs specialist, 1-5 days, within one team)
  - 7-9: Easy (anyone can do it, <1 day, one platform change)
  - 10: Trivial (5-minute settings change)

### Time-to-Impact Labels (add to every recommendation)
- ⚡ **Quick Win** (< 1 week): Settings changes, negative keywords, budget shifts
- 📅 **Medium** (1-4 weeks): Content creation, landing page updates, new campaigns
- 🎯 **Long-term** (1-3 months): SEO content strategy, authority building, new markets

### Presentation
Rank ALL recommendations by Priority Score descending. Show the score:
"Priority: 8 × 9 × 10 = 720 — ⚡ Quick Win"

Group into:
1. **Do This Week** (Priority > 500, Quick Win)
2. **Do This Month** (Priority 200-500 or Medium timeline)
3. **Plan for Next Quarter** (Priority < 200 or Long-term)
"""


MESSAGE_ALIGNMENT_FRAMEWORK = """
## Message Alignment Framework (MANDATORY for every ad or campaign analysis)

For every active campaign, evaluate 3-way message alignment between:
1. **Ad Promise** — What the ad headline and body text claims (from get_meta_ad_creatives / get_ad_copy)
2. **Landing Page Content** — What the landing page H1, hero text, and above-fold CTA says (from GA4 landing page data or crawl)
3. **Audience Intent** — What the targeting audience is actually searching for / interested in (from ad set targeting, keywords, or audience type)

### Alignment Scoring
- **ALIGNED** (✅) — All 3 match. The ad promises X, the page delivers X, the audience wants X.
- **PARTIAL** (🟡) — 2 of 3 match. One element is misaligned — diagnose which one.
- **MISALIGNED** (🔴) — < 2 match. Significant disconnect causing bounce/low conversion.

### Common Misalignment Patterns
| Pattern | Example | Fix |
|---------|---------|-----|
| CTA mismatch | Ad says "Chat on WhatsApp" → Page has no WhatsApp button | Create dedicated landing page with matching CTA |
| Language mismatch | English ad → BR audience → Portuguese-speaking users | Localize ad copy and landing page |
| Intent mismatch | "Engaged Shoppers" audience (B2C) → B2B sourcing platform | Change to procurement job title targeting |
| Promise mismatch | Ad: "Get quotes in 3 hours" → Page: Generic homepage with no quote CTA | Landing page must lead with quote CTA above fold |
| Stage mismatch | Awareness campaign ad → Conversion landing page | Match landing page depth to audience temperature |

### Output Format
For every campaign, include a Message Alignment Card:
```
Campaign: [name]
Ad Promise: "[exact headline from API]"
Landing Page: "[H1 or above-fold text from page]"
Audience Intent: "[targeting type: job titles / interests / lookalike / broad]"
Alignment: ✅ ALIGNED / 🟡 PARTIAL / 🔴 MISALIGNED
Gap: [describe the specific mismatch if not ALIGNED]
Fix: [specific action to achieve ALIGNED status]
```

This card must appear for EVERY active campaign in any ads analysis.
"""


CHANNEL_CONTROLLABILITY_RULES = """
## Channel Controllability Rules (MANDATORY for geographic and traffic analysis)

### Rule 1: Paid vs Organic Geo Interpretation
Geographic traffic analysis means VERY different things by channel type:

**PAID CHANNELS (Meta Ads, Google Ads):**
- Geo targeting IS a direct setting you control
- Non-target country traffic from paid = WASTED SPEND = flag as [GEO LEAK] problem
- Quantify waste: "India received $895 of $4,200 spend (21%) with 0 conversions"
- Action required: Exclude non-target countries from ad set targeting immediately

**ORGANIC CHANNELS (Google Search, Referral, Direct):**
- Geo distribution is a SIGNAL, not a controllable setting
- Do NOT label non-target organic traffic as "a problem to fix"
- Frame it as informational: "X% of organic visitors come from India. This reflects content language and topic relevance, not a misconfiguration."
- Only investigate further if: non-target organic traffic is CONVERTING better than target traffic (good signal) or if there are spam/bot concerns (suspicious patterns)

### Rule 2: When Organic Geo Becomes Worth Acting On
These are the only scenarios where organic non-target traffic warrants action:
- Non-target country has a higher conversion rate than target countries → Consider adding to acceptable markets
- Non-target traffic is 0s duration, 100% bounce, from same IPs → Bot traffic, worth filtering in GA4
- Non-target organic traffic > 50% of total → Content may be ranking for wrong-market keywords, worth investigating

### Rule 3: Data Confidence Indicators
Every analysis section MUST start with a data confidence header:
```
Data Sources:
✅ GA4 — Fresh (<24hr delay) | 12,188 sessions tracked | Coverage: ~95% (ad-blockers reduce accuracy)
🟡 Meta Ads API — Current (~4hr delay) | $4,200 spend tracked | Coverage: 100%
🟡 Search Console — Current (48hr delay) | 156 keywords tracked | Coverage: ~85% (branded keywords may be anonymized)
🔴 PostHog — [UNAVAILABLE] | Funnel analysis incomplete — cross-reference with Sourcy DB
Confidence Level: Medium (GA4 + Meta complete; PostHog unavailable reduces funnel confidence)
```

Include:
- ✅/🟡/🔴 freshness indicator per source
- Number of data points tracked per source
- Coverage estimate (are we missing data? why?)
- Overall confidence level: High / Medium / Low
"""


STRUCTURED_FINDINGS_SENTINEL = """
## Structured Findings Block (REQUIRED for sub-agents)

At the END of your output, append a structured findings block — this lets the
orchestrator emit clean citations and lets generation skills consume your
findings by ID instead of re-parsing prose. Use exactly this format:

<<<FINDINGS_JSON>>>
[
  {"finding_id": "F1", "claim": "<one-sentence claim>", "evidence": "<short evidence>", "confidence": "High|Medium|Low", "tags": ["seo","content_gap"]},
  {"finding_id": "F2", "claim": "...", "evidence": "...", "confidence": "...", "tags": ["..."]}
]
<<<END_FINDINGS_JSON>>>

Rules:
- finding_id is sequential within this run: F1, F2, F3...
- One claim per finding. Keep claim under 25 words.
- Confidence reflects how well your evidence supports the claim.
- Tags are short slugs that downstream generation skills can filter on
  (e.g., "winning_angle", "content_gap", "icp_segment", "underserved_market").
- This block does NOT replace your normal output — append it at the very end.
- If you have nothing structured to emit, append `<<<FINDINGS_JSON>>>[]<<<END_FINDINGS_JSON>>>`.
"""


SUGGESTED_ACTIONS_SENTINEL = """
## Suggested Actions Block (REQUIRED for synthesis / final-artifact agents)

After your artifact is complete, append a suggested-actions block. The frontend
ActionBar reads this and renders one button per action. Only suggest actions
that the findings actually support — empty array is fine.

<<<SUGGESTED_ACTIONS>>>
[
  {
    "label": "<imperative, under 50 chars>",
    "action_id": "<one of: gen-blog, gen-ad, gen-landing-page, gen-case-study>",
    "finding_refs": ["F3", "F7"],
    "agent_refs": ["A", "C"]
  }
]
<<<END_SUGGESTED_ACTIONS>>>

Action triggers:
- Found a content gap or untapped keyword cluster → action_id: "gen-blog"
- Found a winning ad angle, top-CTR creative pattern, or copy theme → action_id: "gen-ad"
- Found an underserved ICP segment or new market opportunity → action_id: "gen-landing-page"
- Found a strong customer outcome or proof point → action_id: "gen-case-study"

Rules:
- 0–5 actions max. Prefer fewer, sharper suggestions over a dump.
- label is what the user clicks. Lead with verb. Reference the specific opportunity ("Generate blog on 'find suppliers in Vietnam'").
- finding_refs are the F-IDs (from FINDINGS_JSON blocks emitted upstream) that justify the action.
- agent_refs are the sub-agent letters (A, B, C…) whose work feeds the generation.
- If no actions apply, emit `<<<SUGGESTED_ACTIONS>>>[]<<<END_SUGGESTED_ACTIONS>>>`.
"""


REASONING_EXPLANATION = """
## Reasoning Explanation (MANDATORY for all agents)

### For the Intent Router (Waiter):
When routing a query, briefly explain your decision:
"I'm routing this to [agent name] because [reason]. You'll get [expected output type]
in about [estimated time]."

Example: "I'm routing this to the Marketing Data Analyst because you asked about ad
performance — this requires pulling real Meta Ads API data. You'll get an interactive
dashboard with campaign diagnostics in about 3-5 minutes."

### For the Orchestrator (Kitchen Manager):
When dispatching skills, explain which and why:
"Calling [skill names] because [reason]. Skipping [skill names] because [reason]."

Example: "Calling traffic_analysis + deep_recommendations because ad performance
questions need both GA4 context and Meta Ads API data. Skipping SEO analysis because
your question is specifically about paid channels."

### For Skills (Chefs):
When returning findings, explain your reasoning chain:
"Found [N] issues. Ranked by [priority framework]. Top issue: [X] because [evidence]."

Example: "Found 7 issues across your Meta Ads. Ranked by Impact × Confidence × Effort.
Top issue: Geo targeting leakage (Priority 810) because $895/month is going to non-target
countries with 0 conversions — this is the easiest money to save."

### For Users Who Ask "What Can You Do?"
Reference the capabilities menu to explain available analyses, expected outputs,
time estimates, and data sources. Help users pick the right analysis for their question.
"""
