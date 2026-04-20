"""Shared prompt blocks for all Content Engine skill agents (SEO/GEO/AEO/content creation)."""


CONTENT_ENGINE_BUSINESS_CONTEXT = """
## Sourcy Content Context
- **Company**: Sourcy.ai — AI-powered B2B sourcing platform
- **Mission**: Help businesses find manufacturers and suppliers (primarily from Asia)
- **Website**: sourcy.ai (Next.js, Tailwind CSS, shadcn/ui)
- **Content Goals**: Drive organic traffic from B2B buyers searching for sourcing solutions
- **Key Topics**: Product sourcing, manufacturing, supply chain, private label, OEM, wholesale
- **Target Audience**: Brand owners, e-commerce sellers, procurement managers, SMEs
- **Geographic Focus**: Indonesia, Philippines, Thailand, Brazil, US, Mexico (primary); Malaysia, Singapore, Vietnam (secondary)
- **Content Tone**: Professional but approachable, data-driven, action-oriented
- **Competitive Positioning**: Better alternative to Alibaba for managed B2B sourcing with AI
"""


CONTENT_QUALITY_RUBRIC = """
## Content Quality Scoring Rubric (0-100)

Score every piece of content against these 4 categories (25 points each):

### Hook Power (0-25)
- 0-5: Generic opening, no reason to keep reading
- 6-15: Interesting but not compelling, could be any website
- 16-20: Strong hook with data, story, or provocative angle
- 21-25: Impossible to scroll past — specific, surprising, creates urgency
Sub-criteria: First sentence hooks (5), title/headline quality (5), opening paragraph value (5), unique angle (5), emotional/logical appeal (5)

### Voice Authenticity (0-25)
- 0-5: Sounds AI-generated, corporate, or templated
- 6-15: Professional but lacking personality
- 16-20: Sounds like a real person with opinions
- 21-25: Distinct voice — short punchy sentences, specific numbers, personal framing, contrarian but backed by data
Sub-criteria: Natural sentence variation (5), specific numbers not vague claims (5), contrarian or unique takes (5), no corporate jargon (5), reads like speech not essay (5)

### Value Density (0-25)
- 0-5: Filler content, obvious statements
- 6-15: Some useful info buried in fluff
- 16-20: Every paragraph earns its place
- 21-25: Every sentence delivers actionable insight with data
Sub-criteria: Specific data points (5), actionable not just observational (5), no filler paragraphs (5), unique information (5), reader learns something new (5)

### Engagement Potential (0-25)
- 0-5: No one would share this
- 6-15: Useful but not shareable
- 16-20: Would get saves/bookmarks
- 21-25: Would get shares, comments, spark debate
Sub-criteria: Shareability (5), CTA invites response (5), sparks debate/discussion (5), platform-native formatting (5), visual/structural appeal (5)

### Quality Gate
- Score >= 90: PASS — publish-ready
- Score 70-89: NEEDS WORK — send back with specific feedback for revision
- Score < 70: REWRITE — fundamental issues, start over with new approach

### Humanizer Detection (1.5x weight penalty)
Flag and penalize these AI writing patterns:
1. "Delve", "dive into", "unlock", "leverage", "harness"
2. "In today's fast-paced world", "In the ever-evolving landscape"
3. "It's important to note that", "It's worth mentioning"
4. Excessive hedging: "might", "could potentially", "may or may not"
5. Lists of exactly 3 or 5 items with parallel structure
6. Every paragraph same length (3-4 sentences)
7. Formulaic transitions: "Furthermore", "Moreover", "Additionally"
8. No contractions (always "do not" never "don't")
9. No idioms, slang, or colloquialisms
10. Absence of personal anecdotes or first-person perspective
11. Over-qualified statements: "This comprehensive guide will..."
12. Symmetrical pros/cons with equal weight
13. "In conclusion" or "To sum up"
14. Perfect grammar with no sentence fragments
15. Overuse of em-dashes for dramatic effect
16. Starting paragraphs with "When it comes to..."
17. Excessive use of superlatives: "revolutionary", "game-changing"
18. Robotic question-answer format throughout
19. Lack of humor, sarcasm, or personality
20. Generic examples instead of real company/product names
21. Perfectly balanced sentence lengths
22. "Here's the thing" or "The truth is" as fillers
23. Ending with a question to "engage" the reader
24. Using "we" without establishing who "we" is
"""


GEO_CITABILITY_RULES = """
## GEO Citability Rules for AI Search Engines

### Citability Block Format (134-167 words optimal)
- Direct answer in first 40-60 words
- Self-contained — makes sense without surrounding context
- Includes specific data, numbers, or examples
- Attribution signals: "According to [source]", "Research shows", "As of [date]"
- Question-based H2/H3 headers that match search queries exactly
- Definition patterns: "[Term] is [definition]" for entity recognition

### GEO Scoring Framework (5 factors)
| Factor | Weight | What It Measures |
|--------|--------|-----------------|
| Citability | 25% | Answer blocks, quotable sentences, self-contained passages |
| Structural Readability | 20% | H1→H2→H3 hierarchy, short paragraphs, tables/lists, FAQ sections |
| Multi-Modal Content | 15% | Images, videos, infographics alongside text (156% higher AI selection) |
| Authority & Brand Signals | 20% | Author bylines, dates, citations, entity presence, social mentions |
| Technical Accessibility | 20% | Server-side rendering, AI crawler access, llms.txt, schema markup |

### AI Platform Citation Patterns
- **Google AI Overviews**: Pulls from top-10 ranking pages (92%). Prefers structured data + authoritative sources.
- **ChatGPT**: Wikipedia (47.9%), Reddit (11.3%), well-known brands. Prefers comprehensive, well-cited content.
- **Perplexity**: Reddit (46.7%), Wikipedia, recent articles. Prefers cited sources + fresh content.

### Key Insight
Brand mentions correlate 3x more strongly with AI visibility than backlinks (Ahrefs study).
"""


EEAT_SCORING_GUIDE = """
## E-E-A-T Evaluation Guide (80-item benchmark)

Score each item as: PASS (1 point) / PARTIAL (0.5 points) / FAIL (0 points)
Maximum score: 80. Calculate percentage: (score / 80) × 100

### Experience (20 items) — Does the content show first-hand experience?
Items: original research, case studies, customer stories, process documentation, before/after evidence,
user-generated content, real data citations, industry participation, hands-on demonstrations,
product usage evidence, field testing, customer interaction evidence, implementation guides,
troubleshooting from experience, workflow documentation, real-world examples, comparative testing,
timeline documentation, outcome tracking, feedback incorporation

### Expertise (20 items) — Does the creator have knowledge/skill?
Items: author credentials, publication history, topical depth, technical accuracy, primary source citation,
peer validation, specialized vocabulary used correctly, methodology transparency, data-backed claims,
comprehensive coverage, nuanced analysis, current/updated knowledge, formal qualifications,
conference/event participation, industry awards, research citations, tool proficiency,
cross-domain synthesis, educational content structure, analytical frameworks

### Authoritativeness (20 items) — Is the source recognized as authoritative?
Items: domain authority, backlink quality, brand mentions, press coverage, industry recognition,
social proof, expert endorsements, institutional affiliations, editorial standards, citation by others,
thought leadership, community recognition, conference speaking, authoritative publication,
partnership signals, market position, longevity signals, scope of coverage, geographic authority,
topical authority

### Trustworthiness (20 items) — Is the page/site trustworthy?
Items: HTTPS, privacy policy, terms of service, contact information, physical address, transparency,
editorial policy, correction policy, author attribution, factual accuracy, source citation,
conflict of interest disclosure, security signals, accessibility, regulatory compliance,
customer service, refund policy, data handling disclosure, copyright respect, community trust
"""


CONTENT_CROSS_AGENT_TRIGGERS = """
## Content Engine Cross-Agent Triggers

When you detect these signals, flag them for the Content Engine orchestrator:

| Signal Detected | Trigger | Why |
|---|---|---|
| EEAT score < 50% | entity_optimizer | Weak authority signals need entity strengthening |
| No citability blocks found | geo_content_analyst | Content not optimized for AI citation |
| Missing FAQ schema on key pages | aeo_content_analyst | Missed featured snippet opportunities |
| Keyword cannibalization detected | seo_content_analyst | Multiple pages competing for same keyword |
| AI crawlers blocked in robots.txt | technical_seo_auditor | Content invisible to AI search engines |
| Thin content (< 500 words) on key pages | blog_writer | Content creation needed |
| No structured data / schema markup | technical_seo_auditor | Missing technical foundation |
| Content gaps vs top competitors | keyword_strategist | Need content plan for gap keywords |
| High impressions but low CTR on pages | seo_content_analyst | Title/meta description optimization needed |
| No author pages or bios | eeat_auditor | Missing expertise signals |
"""


CONTENT_OUTPUT_FORMAT = """
## Content Analysis Output Format (MANDATORY for analysis skills)

Return your analysis as structured text with clear sections and tables.
The Content Synthesis Agent will handle HTML artifact generation.

### Required Sections:
1. **Executive Summary** — 2-3 sentences in plain language
2. **Score/Grade** — Numeric score with breakdown by category
3. **Key Findings** — Top 5 findings with severity labels [URGENT/IMPORTANT/NICE-TO-HAVE]
4. **Data Tables** — Markdown tables with ALL data rows (not just top 3-4)
5. **Recommendations** — Prioritized by impact, with specific actions
6. **Cross-Agent Flags** — Any triggers for other skills (see CONTENT_CROSS_AGENT_TRIGGERS)

### Include Data for Charts:
- Weekly trend data (5 data points) for any time-series metrics
- Score breakdowns for radar/bar charts
- Comparison data (current vs benchmark vs competitor)

### Source Attribution (MANDATORY):
Every data point must include its source: (Search Console), (SEMrush), (Crawl), (PageSpeed API), etc.
"""
