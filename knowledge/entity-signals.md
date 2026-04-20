# Entity Signal Checklist -- Domain Knowledge Reference

Complete 47-signal entity checklist for auditing and building entity presence across search engines and AI systems. Entities -- the people, organizations, products, and concepts that search engines and AI systems recognize as distinct things -- are the foundation of how both Google and LLMs decide what a brand is and whether to cite it.

**Why entities matter:**
- **SEO**: Google's Knowledge Graph powers Knowledge Panels, rich results, and entity-based ranking signals. A well-defined entity earns SERP real estate.
- **GEO**: AI systems resolve queries to entities before generating answers. If an AI cannot identify an entity, it cannot cite it -- no matter how good the content is.

---

## Priority 1: Identity Signals (12 Items) -- Foundation

These signals form the minimum viable entity identity. Without them, search engines and AI systems cannot reliably identify the entity. Complete this tier first.

### On-Site Structured Data (5 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 1 | Organization/Person Schema | Run Google Rich Results Test on homepage | Schema present with name, url, logo, description |
| 2 | sameAs Property Links | Inspect schema markup for sameAs | Links to Wikipedia, Wikidata, LinkedIn, social profiles |
| 3 | Consistent @id Across Pages | Inspect schema on 5+ pages | Same @id (typically homepage URL + #organization) on every page |
| 4 | Entity-Rich About Page | Manual review of About page | First paragraph defines entity clearly; includes founding date, key people, mission |
| 5 | Verifiable Contact Page | Manual review of Contact page | Physical address, phone, email -- matches other directory listings |

### Key External Profiles (5 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 6 | Wikidata Entry | Search wikidata.org for entity | Entry with label, description, key properties, and references |
| 7 | Google Business Profile | Search "[entity] Google Business" | Claimed, verified, complete profile (if applicable) |
| 8 | LinkedIn Company/Person Page | Search LinkedIn | Complete profile matching entity name and description |
| 9 | CrunchBase Profile | Search crunchbase.com (for companies/products) | Entry with description, founding info, key people |
| 10 | Industry Directory Listing | Search top 3 industry directories | Listed with correct entity information |

### Branded Search Presence (2 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 11 | Branded Search Returns Correct Entity | Google "[entity name]" | Entity's website is #1; Knowledge Panel appears or SERP clearly identifies entity |
| 12 | No Disambiguation Confusion | Google "[entity name]" | No other prominent entity dominates results for the same name |

**For B2B sourcing brands:** Ensure your brand name does not conflict with common industry terms. If your company name is generic (e.g., "Global Supply" or "FastTrade"), disambiguation becomes the top priority before other entity work.

---

## Priority 2: Content Signals (12 Items) -- Authority Building

These signals establish the entity as recognized and authoritative. They separate a "registered entity" from a "known entity."

### Knowledge Graph Depth (5 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 13 | Google Knowledge Panel Present | Google "[entity name]" | Knowledge Panel displayed with correct information |
| 14 | Knowledge Panel Attributes Complete | Review Knowledge Panel details | Key attributes filled (founded, CEO, location, industry) |
| 15 | Knowledge Panel Image Correct | Review Knowledge Panel | Preferred image displayed |
| 16 | Wikipedia Article or Notability Path | Search Wikipedia | Article exists, or entity has 3+ independent reliable sources for future article |
| 17 | Wikidata Properties Complete | Review Wikidata entry | 10+ properties with references |

### Content Authority (4 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 18 | Topical Content Depth | Site search for target topics | 10+ pages covering target topics in depth |
| 19 | Author Pages with Credentials | Review author pages | Author schema, credentials, sameAs to external profiles |
| 20 | Original Research Published | Review content assets | At least 1 piece of original data/research cited by others |
| 21 | Entity Name Used Naturally in Content | Search site for entity name | Entity name appears contextually (not just in header/footer) |

### Third-Party Validation (3 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 22 | Authoritative Media Mentions | Google News search for entity | 3+ mentions in recognized publications |
| 23 | Industry Awards or Recognition | Search "[entity] award" | At least 1 verifiable award or recognition |
| 24 | Reviews on Third-Party Platforms | Check G2, Trustpilot, Capterra | Reviews exist with reasonable volume and rating |

---

## Priority 3: Authority Signals (12 Items) -- AI-Specific

These signals specifically help AI systems recognize, understand, and cite the entity.

### AI Recognition (5 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 25 | ChatGPT Recognizes Entity | Ask ChatGPT "What is [entity]?" | Correct description returned |
| 26 | Perplexity Recognizes Entity | Ask Perplexity "What is [entity]?" | Correct description with source citations |
| 27 | Google AI Overview Mentions Entity | Search branded + topical queries | Entity appears in AI-generated overview |
| 28 | AI Description Is Accurate | Compare AI output to entity's self-description | No factual errors in AI's response |
| 29 | AI Associates Entity with Correct Topics | Ask "[entity] expertise areas" | Correct topic associations returned |

### AI Optimization (5 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 30 | Entity Definition Is Quotable | Review About page and key pages | Clear, factual, self-contained definition suitable for AI quotation in first paragraph |
| 31 | Factual Claims Are Verifiable | Cross-reference claims with external sources | All claims about entity can be verified via third-party sources |
| 32 | Entity Name Used Consistently | Audit all platforms | Identical name format everywhere (no abbreviations on some, full name on others) |
| 33 | Content Crawlable by AI Systems | Check robots.txt for AI bot access | Not blocking GPTBot, ClaudeBot, or other AI crawlers (unless intentional) |
| 34 | Fresh Information Available | Check update dates on key entity pages | Key entity pages updated within last 6 months |

### Co-citation and Association (2 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 35 | Co-citation with Established Entities | Search for entity alongside competitors | Appears in "X vs Y" comparisons, listicles, or industry roundups |
| 36 | Speaking Engagements or Publications | Search event/conference sites | Appears as speaker, author, or contributor |

---

## Priority 4: Technical Signals (11 Items) -- Advanced

These signals provide marginal gains but demonstrate thoroughness and maturity.

### Extended Knowledge Base (4 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 37 | Multiple Language Entries in Wikidata | Check Wikidata labels | Labels and descriptions in languages matching target markets |
| 38 | DBpedia Entry | Search dbpedia.org | Entry exists (auto-generated from Wikipedia) |
| 39 | Google Knowledge Graph ID Known | Search Google Knowledge Graph API | Entity has a kg: identifier |
| 40 | ISNI or VIAF Identifier (for persons) | Search isni.org or viaf.org | Identifier exists and links correctly |

### Social Entity Signals (3 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 41 | Bidirectional Social Profile Links | Check website links to social AND social links to website | Both directions verified on all platforms |
| 42 | Consistent Entity Description Across Social | Compare bios on all platforms | Same core description, adapted for platform length limits |
| 43 | Social Engagement Demonstrates Real Audience | Review engagement metrics | Engagement patterns consistent with genuine audience (not bot-like) |

### Technical Entity Signals (4 signals)

| # | Signal | What to Check | Pass Criteria |
|---|--------|---------------|---------------|
| 44 | Strong Backlink Profile on Homepage | Check link database tool | Homepage DR/DA above industry median |
| 45 | Branded Anchor Text in Backlinks | Analyze anchor text distribution | Entity name appears naturally in inbound link anchor text |
| 46 | Entity Subdomain Consistency | Check all subdomains | Same entity schema and branding across all subdomains |
| 47 | Branded Search Volume Exists | Check SEO tool | Measurable branded search volume (any amount > 0) |

---

## Knowledge Panel Optimization

### How to Get a Knowledge Panel

1. **Build Wikidata entry** -- Most influential single action; a complete entry with references often triggers Knowledge Panel creation within weeks
2. **Implement Organization/Person schema** with sameAs pointing to Wikidata, Wikipedia, LinkedIn
3. **Get mentioned in authoritative sources** -- 3+ independent publications
4. **Claim via Google** -- Search for entity, click "Claim this knowledge panel" if it appears

### Common Knowledge Panel Problems and Fixes

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| No panel appears | Entity not in Knowledge Graph | Build Wikidata entry + structured data + authoritative mentions |
| Wrong image displayed | Image sourced from incorrect page | Update Wikidata image; ensure preferred image on About page and social profiles |
| Wrong description | Description pulled from wrong source | Edit Wikidata description; ensure About page has clear entity description in first paragraph |
| Missing attributes | Incomplete structured data | Add properties to Schema.org markup and Wikidata entry |
| Wrong entity shown | Disambiguation failure | Strengthen unique signals; add qualifiers; resolve Wikidata disambiguation |
| Outdated information | Source data not updated | Update Wikidata, About page, and all profile pages |

### Bing Knowledge Panel

Bing Knowledge Panels are driven by Wikidata and LinkedIn. To optimize for Bing:
- Ensure Wikidata entry is complete and accurate
- Keep LinkedIn company/person page fully updated
- Both Wikidata and LinkedIn changes propagate to Bing panels over time

---

## Wikidata Best Practices

### Creating a Wikidata Entry

1. **Check notability** -- Entity must have at least one authoritative reference
2. **Create item** -- Add label, description, and aliases in relevant languages
3. **Add statements** -- instance of, official website, social media links, founding date, founders, industry
4. **Add identifiers** -- official website (P856), social media IDs, CrunchBase ID, ISNI, VIAF
5. **Add references** -- Every statement should have a reference to an authoritative source

**Conflict of Interest warning:** Wikipedia's COI policy prohibits individuals and organizations from creating or editing articles about themselves. For Wikipedia (not Wikidata): (1) Build notability through independent reliable sources first; (2) If warranted, request an independent editor through the Requested Articles process; (3) Ensure all claims are verifiable through third-party sources.

### Key Wikidata Properties by Entity Type

| Property | Code | Person | Organization | Brand | Product |
|----------|------|--------|--------------|-------|---------|
| instance of | P31 | human | org type | brand | product type |
| official website | P856 | yes | yes | yes | yes |
| occupation / industry | P106/P452 | yes | yes | -- | -- |
| founded by | P112 | -- | yes | yes | -- |
| inception | P571 | -- | yes | yes | yes |
| country | P17 | yes | yes | -- | -- |
| social media | various | yes | yes | yes | yes |
| employer | P108 | yes | -- | -- | -- |
| developer | P178 | -- | -- | -- | yes |

---

## AI Entity Resolution Pipeline

AI systems follow this pipeline when processing queries:

```
User query --> Entity extraction --> Entity resolution --> Knowledge retrieval --> Answer generation
```

1. **Extract** entity mentions from the query
2. **Resolve** each mention to a known entity (or fail with "I'm not sure")
3. **Retrieve** associated knowledge about the entity
4. **Generate** response citing sources that confirmed the entity's attributes

### What AI Systems Check During Resolution

| Signal Type | What AI Checks | How to Optimize |
|-------------|---------------|-----------------|
| Training data presence | Was entity in pre-training corpus? | Get mentioned in high-quality, widely-crawled sources |
| Retrieval augmentation | Does entity appear in live search results? | Strong SEO presence for branded queries |
| Structured data | Can entity be matched to Knowledge Graph? | Complete Wikidata + Schema.org |
| Contextual co-occurrence | What topics/entities appear alongside? | Build consistent topic associations across content |
| Source authority | Are sources about entity trustworthy? | Get mentioned by authoritative, well-known sources |
| Recency | Is information current? | Keep all entity profiles and content updated |

---

## Priority Action Matrix

| Current State | Focus Area | Expected Timeline |
|--------------|-----------|-------------------|
| Most Priority 1 signals missing | Priority 1 foundation signals only | 2-4 weeks |
| Priority 1 mostly passing, Priority 2 mixed | Priority 2 authority signals | 1-2 months |
| Priority 1-2 mostly passing | Priority 3 AI-specific signals | 2-3 months |
| Priority 1-3 mostly passing | Selective Priority 4 for completeness | Ongoing |
| All tiers mostly passing | Maintenance + quarterly re-audit | Quarterly review |

### Entity Audit Scoring

For each signal, mark status as:
- PASS (present and correct)
- PARTIAL (present but incomplete)
- FAIL (absent)

Focus on completing each priority tier before moving to the next. Entity signals compound -- 5 weak signals together are stronger than 1 strong signal alone. Consistency beats completeness.

---

## Tips for B2B Sourcing Brands

1. **Start with Wikidata** -- Even if your company is small, a Wikidata entry with verifiable references establishes entity identity
2. **sameAs is the most powerful Schema.org property** -- It directly tells search engines "I am this entity in the Knowledge Graph"; always include Wikidata URL first
3. **Test AI recognition quarterly** -- Ask ChatGPT, Claude, Perplexity, and Google about your brand before and after optimization
4. **Consistency is everything** -- Use the exact same company name, description, and founding year on every platform
5. **Disambiguation first** -- If your company name is common or shared with another entity, resolve this before doing anything else
6. **Industry directories matter** -- For sourcing, get listed on relevant directories (e.g., ThomasNet, Kompass, industry-specific platforms)
7. **Build co-citation** -- Get mentioned alongside established competitors in comparison articles and industry roundups
