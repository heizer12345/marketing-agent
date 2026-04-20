# E-E-A-T Content Benchmark -- Domain Knowledge Reference

Complete 80-item E-E-A-T benchmark for evaluating content quality across AI engines (GEO) and search engines (SEO). Based on the CORE-EEAT Content Benchmark v3.0 framework.

---

## Framework Architecture

The benchmark uses a two-system architecture with 8 dimensions, 10 items each = 80 total evaluation criteria.

| System | Focus | Dimensions | Items | Boundary |
|--------|-------|------------|-------|----------|
| CORE | GEO (AI Engine Optimization) | C, O, R, E | 40 | Content body |
| EEAT | SEO (Search Engine Optimization) | Exp, Ept, A, T | 40 | Author / Organization / Site |

**MECE Boundary Rule:** CORE evaluates the content body itself. EEAT evaluates the source -- author, organization, and site credibility. No overlap between the two systems.

### Priority Tags

- **GEO-First** = Critical for AI engine citation (ChatGPT, Perplexity, Google AI Overviews)
- **SEO-First** = Critical for traditional search ranking
- **Dual** = Important for both systems

### Scoring

| Result | Score |
|--------|-------|
| Pass | 10 |
| Partial | 5 |
| Fail | 0 |

- **Dimension score** = sum of 10 items (0-100)
- **GEO Score** = (C + O + R + E) / 4
- **SEO Score** = (Exp + Ept + A + T) / 4
- **Total Score** = (GEO + SEO) / 2

| Score Range | Rating |
|-------------|--------|
| 90-100 | Excellent |
| 75-89 | Good |
| 60-74 | Medium |
| 40-59 | Low |
| 0-39 | Poor |

### Veto Items (Critical Fails)

Failing any veto item caps the overall score regardless of other results.

| Veto ID | Dimension | Check | What Triggers It |
|---------|-----------|-------|------------------|
| T04 | Trust | Disclosure Statements | Affiliate links present without disclosure |
| C01 | Contextual Clarity | Intent Alignment | Clickbait -- title promises something the page does not deliver |
| R10 | Referenceability | Content Consistency | Data on the page contradicts itself |

---

## CATEGORY 1: EXPERIENCE (10 Items)

Experience evaluates whether the author demonstrates real-world, first-hand involvement with the topic. This is the "source credibility" dimension that separates practitioners from aggregators.

### Exp01: First-Person Narrative | SEO-First

**What to check:** Does the content contain first-person language with action verbs demonstrating direct involvement?

**Pass:** Contains "I tested" or "We found" combined with action verbs describing direct activity.
**Partial:** Only one of first-person OR action verbs present; indirect experience language.
**Fail:** Entirely third-person; reads like aggregated research with no personal involvement.

**B2B sourcing example:**
- Pass: "We ran a 90-day pilot with 3 suppliers in Shenzhen and tracked defect rates across 12 shipments."
- Fail: "Companies that work with Asian suppliers often find quality varies."

### Exp02: Sensory Details | SEO-First

**What to check:** Does the content include specific sensory or observational details that could only come from direct experience?

**Pass:** 10 or more sensory/observational words (smooth, heavy, bright, noisy, responsive, sluggish).
**Partial:** 5-9 sensory details present.
**Fail:** Fewer than 5; content reads like it was written from a product spec sheet.

**B2B sourcing example:**
- Pass: "The injection-molded housing felt noticeably lighter than the CNC version -- about the weight of a smartphone. The surface finish was glossy but showed fingerprints immediately."
- Fail: "The product has high-quality materials and a professional finish."

### Exp03: Process Documentation | Dual

**What to check:** Does the content document a step-by-step process with timeline and decision points?

**Pass:** Detailed process with numbered steps, timeline markers, and decision rationale at each stage.
**Partial:** Partial process documented; some steps missing or timeline unclear.
**Fail:** No process documentation; only outcomes described.

**B2B sourcing example:**
- Pass: "Week 1-2: We shortlisted 8 factories from Alibaba. Week 3: Sent RFQs with our spec sheet. Week 4-5: Received samples from 5 factories. Week 6: Lab-tested samples for tensile strength (ISO 527). Selected Factory C based on 15% better yield and 20-day lead time."
- Fail: "We found a good supplier after researching several options."

### Exp04: Tangible Proof | SEO-First

**What to check:** Does the content include original photos, screenshots, or documentation with timestamps that prove direct experience?

**Pass:** 2 or more original images/screenshots with timestamps or contextual metadata.
**Partial:** 1 original image or images without clear provenance.
**Fail:** No original visual evidence; only stock photos or no images.

**B2B sourcing example:**
- Pass: Photos of factory floor visits with date stamps, screenshots of actual inspection reports, images of sample products next to measurement tools.
- Fail: Stock photos of generic warehouses or shipping containers.

### Exp05: Usage Duration | SEO-First

**What to check:** Does the author explicitly state how long they have used, tested, or worked with the subject?

**Pass:** Explicitly states duration -- "after 6 months of use," "over 3 production runs," "across 2 years of sourcing."
**Partial:** Duration implied but not stated explicitly.
**Fail:** No mention of usage duration.

**B2B sourcing example:**
- Pass: "After 18 months and 14 orders with this supplier, here is what we have learned about their consistency."
- Fail: "This supplier is reliable and delivers quality products."

### Exp06: Problems Encountered | Dual

**What to check:** Does the content share real problems, failures, or unexpected issues along with solutions?

**Pass:** 2 or more specific problems described with solutions or workarounds.
**Partial:** 1 problem mentioned.
**Fail:** Everything presented as positive; no setbacks or challenges mentioned.

**B2B sourcing example:**
- Pass: "Our first batch had a 12% defect rate on the hinge mechanism. We worked with the factory to add a torque test at the assembly line (added $0.03/unit) which brought defects to under 2%. The second issue was shipping -- our first 3 FCL shipments arrived 5-8 days late because the forwarder was consolidating loads."
- Fail: "Our supplier consistently delivers excellent products on time."

### Exp07: Before/After Comparison | SEO-First

**What to check:** Does the content show measurable change, improvement, or difference through direct comparison?

**Pass:** Clear before/after or side-by-side comparison with measurable metrics.
**Partial:** Comparison implied but not quantified.
**Fail:** No comparative element.

**B2B sourcing example:**
- Pass: "Before switching to Factory B: $4.20/unit, 35-day lead time, 8% defect rate. After: $3.85/unit, 22-day lead time, 1.5% defect rate."
- Fail: "The new supplier was much better than the old one."

### Exp08: Quantified Metrics | Dual

**What to check:** Does the content include measurable data points from the author's direct experience?

**Pass:** Multiple quantified data points from personal experience (cost, time, rates, percentages).
**Partial:** Some quantified data but limited.
**Fail:** Purely subjective assessments; no numbers from experience.

**B2B sourcing example:**
- Pass: "Our RFQ process yielded quotes ranging from $2.10 to $4.75/unit across 8 suppliers. Tooling costs ranged from $3,200 to $12,000. Average sample turnaround was 14 days."
- Fail: "Prices varied widely among suppliers, and tooling was expensive."

### Exp09: Repeated Testing | SEO-First

**What to check:** Has the author conducted multiple tests or tracked results over time, not just a single observation?

**Pass:** Multiple test iterations or longitudinal tracking documented.
**Partial:** Implied repeated testing but not explicitly documented.
**Fail:** Single test or single observation presented as conclusive.

**B2B sourcing example:**
- Pass: "We have run QC inspections on every shipment for 2 years (24 inspections total). Defect rates by quarter: Q1 2024: 6.2%, Q2: 4.1%, Q3: 3.8%, Q4: 2.1%, Q1 2025: 1.9%."
- Fail: "The inspection showed good quality."

### Exp10: Limitations Acknowledged | GEO-First

**What to check:** Does the author explicitly state the boundaries of their experience and what they did not test?

**Pass:** Explicitly states limitations -- "we only tested X scenario," "this applies to Y industry but may differ for Z."
**Partial:** Partially acknowledges constraints.
**Fail:** No limitations stated; experience presented as universally applicable.

**B2B sourcing example:**
- Pass: "This comparison only covers suppliers in Guangdong province. Pricing and lead times may differ significantly for factories in Zhejiang or Jiangsu. We also only tested plastic injection molding -- metal parts sourcing follows different dynamics."
- Fail: "This guide covers everything you need to know about sourcing from China."

---

## CATEGORY 2: EXPERTISE (10 Items)

Expertise evaluates whether the author demonstrates professional-level knowledge and analytical capability. This is about depth of understanding, not just experience.

### Ept01: Author Identity | SEO-First

**What to check:** Is the author clearly identified with a byline, photo/avatar, and substantive bio?

**Pass:** Full byline + avatar/headshot + bio exceeding 30 words with professional context.
**Partial:** 1-2 of the three elements present.
**Fail:** No author information; anonymous content.

**B2B sourcing example:**
- Pass: "By Sarah Chen, Supply Chain Director at [Company]. Sarah has managed sourcing operations across 6 Asian markets for 12 years, specializing in electronics and consumer goods. Previously at Foxconn and Flex."
- Fail: "By Admin" or no author attribution.

### Ept02: Credentials Display | SEO-First

**What to check:** Are relevant professional qualifications, certifications, or experience years displayed?

**Pass:** Relevant degrees, certifications, or years of experience prominently displayed.
**Partial:** Credentials present but weakly relevant to the topic.
**Fail:** No credentials displayed.

**B2B sourcing example:**
- Pass: "CSCP certified (APICS), MBA in Supply Chain Management, 15 years managing $50M+ annual procurement budgets."
- Fail: Generic "industry expert" with no specific credentials.

### Ept03: Professional Vocabulary | Dual

**What to check:** Does the content use accurate industry terminology without misuse?

**Pass:** Industry jargon used accurately and appropriately for the audience level.
**Partial:** Moderate use of professional terms; some oversimplification.
**Fail:** Terms too simple for the audience, or industry terms misused.

**B2B sourcing example:**
- Pass: Correctly uses terms like MOQ, FOB, CIF, AQL, first article inspection, tooling amortization, Incoterms, bill of materials.
- Fail: Refers to "minimum orders" instead of MOQ, confuses FOB with CIF pricing, uses "quality check" when discussing AQL sampling plans.

### Ept04: Technical Depth | Dual

**What to check:** Are technical details accurate, with actionable parameters, thresholds, and specific examples?

**Pass:** Technical details include specific parameters, thresholds, and actionable examples.
**Partial:** Surface-level technical information; lacks specificity.
**Fail:** Superficial treatment or contains technical errors.

**B2B sourcing example:**
- Pass: "Set your AQL to 2.5 for major defects and 4.0 for minor defects on consumer electronics. For a batch of 5,000 units, this means inspecting 200 samples per General Inspection Level II (ISO 2859-1). Reject the lot if major defects exceed 10 in the sample."
- Fail: "Make sure to inspect your products before shipping."

### Ept05: Methodology Rigor | GEO-First

**What to check:** Is the analysis methodology clearly described and reproducible by another professional?

**Pass:** Methodology is clear, follows recognized standards, and could be reproduced.
**Partial:** Some methodology described but not rigorous enough to reproduce.
**Fail:** No methodology described; conclusions appear without supporting process.

**B2B sourcing example:**
- Pass: "We evaluated suppliers using a weighted scorecard: Quality (35%), Price (25%), Lead Time (20%), Communication (10%), Financial Stability (10%). Each criterion scored 1-5. Data sources: 3 sample orders per supplier, Dun & Bradstreet financial reports, 30-day email response time tracking."
- Fail: "We picked the best supplier based on our analysis."

### Ept06: Edge Case Awareness | Dual

**What to check:** Does the content discuss exceptions, caveats, or scenarios where standard advice does not apply?

**Pass:** 2 or more edge cases or exceptions discussed with guidance.
**Partial:** 1 edge case mentioned.
**Fail:** No exceptions acknowledged; advice presented as universally applicable.

**B2B sourcing example:**
- Pass: "This pricing model breaks down for orders under 500 units -- at that volume, most factories will either decline or charge a 30-40% small-batch premium. Also, if your product requires FDA-regulated materials, add 4-6 weeks for compliance documentation that standard timelines do not account for."
- Fail: "Follow these steps to source any product from any supplier."

### Ept07: Historical Context | SEO-First

**What to check:** Does the content demonstrate knowledge of how the field has evolved over time?

**Pass:** Shows understanding of the field's development, key inflection points, or historical shifts.
**Partial:** Some background context provided.
**Fail:** No historical perspective; treats current state as if it always existed.

**B2B sourcing example:**
- Pass: "Before 2018 tariffs, most US importers treated China as a default. Post-tariffs, the 'China+1' strategy became standard -- companies maintained Chinese suppliers for complex assemblies while shifting simpler components to Vietnam or India. The 2020-2022 supply chain disruptions further accelerated this diversification."
- Fail: "Many companies source from multiple countries to reduce risk."

### Ept08: Reasoning Transparency | GEO-First

**What to check:** Does the content explain the "why" behind recommendations, including tradeoffs considered?

**Pass:** Explicit cause-effect reasoning with tradeoff analysis -- "We chose A over B because..."
**Partial:** Some reasoning provided but tradeoffs not fully explored.
**Fail:** Conclusions stated without supporting reasoning.

**B2B sourcing example:**
- Pass: "We chose a trading company over dealing direct with the factory because our order volume (2,000 units) was below most factories' MOQ. The trading company added 8-12% to the unit price but handled QC, consolidation, and customs documentation -- saving us an estimated 40 hours per order cycle."
- Fail: "Using a trading company is a good option for small orders."

### Ept09: Cross-domain Integration | Dual

**What to check:** Does the content connect knowledge from multiple fields to generate insights neither field alone would produce?

**Pass:** Cross-domain knowledge synthesis producing genuinely new perspectives.
**Partial:** References multiple domains but does not synthesize them.
**Fail:** Single-domain perspective only.

**B2B sourcing example:**
- Pass: Article on sourcing strategy combines supply chain economics (landed cost modeling), behavioral negotiation research (BATNA theory), and logistics data (shipping route optimization) to propose a multi-variable supplier scoring framework.
- Fail: Article discusses sourcing purely from a procurement checklist perspective with no adjacent domain integration.

### Ept10: Editorial Process | SEO-First

**What to check:** Is there visible evidence of editorial oversight -- "Reviewed by," "Fact-checked by," or editorial standards?

**Pass:** "Reviewed by" or "Fact-checked by" labels visible with reviewer credentials.
**Partial:** Editorial review happened but is not labeled.
**Fail:** No visible editorial process.

**B2B sourcing example:**
- Pass: "Reviewed by James Park, VP of Procurement at [Company]. Fact-checked against ISO 9001:2015 standards."
- Fail: No editorial attribution.

---

## CATEGORY 3: AUTHORITATIVENESS (10 Items)

Authoritativeness evaluates whether the author and organization are recognized as leaders in their field by external parties. This is the "what others say about you" dimension.

### A01: Backlink Profile | SEO-First

**What to check:** Is the content or domain cited by authoritative external sites?

**Pass:** Cited by authoritative sites (.edu, .gov, major industry publications, recognized leaders).
**Partial:** Some backlinks from moderate-authority sites.
**Fail:** No notable external citations.

**B2B sourcing example:**
- Pass: Cited by trade publications like Supply Chain Dive, referenced by university supply chain programs, linked from government trade resources.
- Fail: Only self-referencing links or links from low-authority guest post networks.

### A02: Media Mentions | SEO-First

**What to check:** Has the author or organization been featured in recognized media outlets?

**Pass:** "Featured in" section with recognizable media logos and links to actual coverage.
**Partial:** Minor mentions or unverifiable media claims.
**Fail:** No media mentions.

**B2B sourcing example:**
- Pass: "As featured in Supply Chain Management Review, Forbes Supply Chain section, and Import/Export Magazine" with links to the actual articles.
- Fail: No media coverage or unverifiable claims.

### A03: Industry Awards | SEO-First

**What to check:** Does the author or organization display relevant industry awards or formal recognition?

**Pass:** Relevant industry awards displayed (e.g., Top 50 Supply Chain Companies, Procurement Leader of the Year).
**Partial:** Awards present but weakly relevant to the topic.
**Fail:** No awards or recognition.

**B2B sourcing example:**
- Pass: "Gartner Top 25 Supply Chain (2024), CIPS Corporate Award for Procurement Excellence."
- Fail: Generic "Best Website" awards with no industry relevance.

### A04: Publishing Record | SEO-First

**What to check:** Does the author have a track record of conference presentations, publications, or patents?

**Pass:** Conference talks, peer-reviewed publications, whitepapers, or patents on record.
**Partial:** Some publishing activity.
**Fail:** No publishing record.

**B2B sourcing example:**
- Pass: "Presented at ISM World (2024), published in Journal of Supply Chain Management, authored 3 industry whitepapers on Asia-Pacific sourcing."
- Fail: No speaking or publishing history.

### A05: Brand Recognition | Dual

**What to check:** Does the brand have measurable search volume -- do people actively search for it?

**Pass:** Brand name generates measurable search volume in keyword tools.
**Partial:** Some brand awareness but minimal search volume.
**Fail:** Brand is unknown; no branded search volume.

**B2B sourcing example:**
- Pass: "[Brand name] sourcing" shows 500+ monthly searches; brand appears in Google autocomplete.
- Fail: Zero branded search volume; brand does not appear in any autocomplete suggestions.

### A06: Social Proof | SEO-First

**What to check:** Are there authentic testimonials or reviews with verifiable real-world details?

**Pass:** Testimonials include real names, companies, specific outcomes, and verifiable details.
**Partial:** Reviews exist but credibility is uncertain (anonymous, generic).
**Fail:** No social proof.

**B2B sourcing example:**
- Pass: "Using Sourcy, we reduced our supplier qualification time from 6 weeks to 10 days and cut per-unit costs by 14% across our top 5 SKUs." -- Maria Torres, Procurement Manager, TechParts Inc.
- Fail: "Great service! Highly recommended." -- Anonymous

### A07: Knowledge Graph Presence | Dual

**What to check:** Does the brand or author have a Wikipedia entry, Google Knowledge Panel, or Wikidata listing?

**Pass:** Wikipedia article exists or Google Knowledge Panel displays for the entity.
**Partial:** Partially indexed -- mentioned in Wikipedia articles but no dedicated page; Wikidata entry exists.
**Fail:** Not present in any knowledge graph system.

**B2B sourcing example:**
- Pass: Company has a Wikidata entry with verified properties, Knowledge Panel appears on branded searches.
- Fail: No knowledge graph presence; Google shows only organic results for branded searches.

### A08: Entity Consistency | GEO-First

**What to check:** Is brand/author information consistent across all web properties (name, description, credentials)?

**Pass:** Identical name format, description, and credentials across website, LinkedIn, Wikidata, industry directories, and social profiles.
**Partial:** Mostly consistent with minor discrepancies.
**Fail:** Contradictions across platforms (different founding dates, inconsistent descriptions, name variations).

**B2B sourcing example:**
- Pass: Company name, founding year, description, and key people are identical across the website About page, LinkedIn, Crunchbase, G2, and Wikidata.
- Fail: Website says "Founded 2018," LinkedIn says "Founded 2019," Crunchbase lists a different CEO.

### A09: Partnership Signals | SEO-First

**What to check:** Does the organization display partnerships with authoritative entities?

**Pass:** Verifiable partnerships with recognized industry organizations or companies.
**Partial:** Some partnership signals but not prominently displayed or verified.
**Fail:** No partnership signals.

**B2B sourcing example:**
- Pass: "Official partner of Alibaba.com Verified Supplier program. Member of the Chartered Institute of Procurement & Supply (CIPS). Integration partner with SAP Ariba."
- Fail: No visible partnerships or affiliations.

### A10: Community Standing | SEO-First

**What to check:** Is the author or organization active and influential in relevant professional communities?

**Pass:** Active participation in industry communities with evidence of influence (moderator, frequent contributor, large following).
**Partial:** Some community participation but limited influence.
**Fail:** No visible community engagement.

**B2B sourcing example:**
- Pass: Active contributor on r/supplychain with 5K+ karma, moderator of a sourcing professionals LinkedIn group with 20K+ members, regular contributor to Supply Chain Brain.
- Fail: No community presence.

---

## CATEGORY 4: TRUSTWORTHINESS (10 Items)

Trustworthiness evaluates whether the site meets basic trust and safety standards. This is the foundational dimension -- without trust, the other three dimensions are weakened.

### T01: Legal Compliance | SEO-First

**What to check:** Are Privacy Policy and Terms of Service present? Are additional compliance documents (GDPR, Cookie Policy) available?

**Pass:** Privacy Policy + Terms of Service present, plus bonus compliance docs (Cookie Policy, GDPR notice).
**Partial:** Only required minimum (Privacy Policy and TOS) present.
**Fail:** Missing Privacy Policy or Terms of Service.

**B2B sourcing example:**
- Pass: Privacy Policy, Terms of Service, Cookie Policy, and GDPR compliance notice all accessible from footer. Data processing agreements available for B2B clients.
- Fail: No Privacy Policy; only a generic "Contact Us" page.

### T02: Contact Transparency | SEO-First

**What to check:** Can users verify the organization exists through physical address, phone, or multiple contact methods?

**Pass:** Physical address displayed OR 2 or more contact methods (phone + email + chat).
**Partial:** Email address only.
**Fail:** No contact information.

**B2B sourcing example:**
- Pass: Office addresses in both the US and Hong Kong listed with phone numbers, email, WhatsApp, and a contact form. Google Maps embed showing office location.
- Fail: Only a generic contact form with no identifying information.

### T03: Security Standards | SEO-First

**What to check:** Is the entire site served over HTTPS with no security warnings?

**Pass:** Site-wide HTTPS with valid certificate; no mixed content warnings.
**Partial:** HTTPS on most pages but some insecure content.
**Fail:** HTTP site or expired/invalid SSL certificate.

**B2B sourcing example:**
- Pass: Valid SSL certificate, HTTPS across all pages including supplier portals and document downloads.
- Fail: Supplier documents served over HTTP; browser shows "Not Secure" warning.

### T04: Disclosure Statements | Dual -- VETO ITEM

**What to check:** If affiliate links, sponsored content, or material relationships exist, are they clearly disclosed?

**Pass:** All affiliate links and sponsored content clearly disclosed with FTC-compliant language.
**Partial:** No affiliate links present (not applicable).
**Fail:** Affiliate links or sponsored content present without disclosure. **THIS IS A VETO ITEM -- triggers score cap regardless of other results.**

**B2B sourcing example:**
- Pass: "Disclosure: We earn a commission when you sign up through our referral links. This does not affect our ratings or recommendations."
- Fail: Recommending specific suppliers with hidden affiliate relationships.

### T05: Editorial Policy | SEO-First

**What to check:** Are content standards and editorial review processes publicly documented?

**Pass:** Published editorial policy describing content standards, review process, and correction procedures.
**Partial:** Some editorial guidelines mentioned but not formally published.
**Fail:** No editorial policy.

**B2B sourcing example:**
- Pass: "Our Editorial Standards" page explaining that all supplier reviews are based on direct experience, independently verified, and reviewed by a procurement professional before publishing.
- Fail: No editorial policy; unclear how content is produced or verified.

### T06: Correction and Update Policy | Dual

**What to check:** Does the site have a mechanism for corrections, update logs, or revision history?

**Pass:** Dedicated corrections page, clear update principles, or visible revision history on articles.
**Partial:** Articles show "Last updated" dates but no formal correction mechanism.
**Fail:** No correction or update policy; no visible update dates.

**B2B sourcing example:**
- Pass: Each supplier review shows "Last verified: March 2026" with a changelog noting what was updated. Corrections page lists any factual errors that were fixed.
- Fail: Articles from 2022 with no update dates; no way to know if pricing or supplier information is current.

### T07: Ad Experience | SEO-First

**What to check:** Are ads non-intrusive and do they occupy less than 30% of visible page area?

**Pass:** Ads occupy less than 30% of page; no intrusive popups, interstitials, or autoplay video ads.
**Partial:** Ads at 30-50% of page area; minor intrusions.
**Fail:** Ads exceed 50% of page or deceptive ad patterns present.

**B2B sourcing example:**
- Pass: One banner ad from a logistics partner, clearly labeled as advertising, non-intrusive.
- Fail: Multiple popup ads, autoplay video, and interstitial ads that obscure content.

### T08: Risk Disclaimers | Dual

**What to check:** For YMYL (Your Money or Your Life) topics, are appropriate risk disclaimers present?

**Pass:** Content covering financial, legal, health, or safety topics includes necessary disclaimers.
**Partial:** Some disclaimers but incomplete coverage.
**Fail:** YMYL content with no disclaimers.

**B2B sourcing example:**
- Pass: Import/export guidance includes: "This content is for informational purposes. Tariff rates and trade regulations change frequently. Consult a licensed customs broker before making import decisions."
- Fail: Providing specific tariff advice or legal guidance on trade compliance without disclaimers.

### T09: Review Authenticity | Dual

**What to check:** Do reviews and testimonials show verifiable authenticity signals?

**Pass:** Reviews include specific details, verifiable identities, varied writing styles, and a mix of positive/negative feedback.
**Partial:** Reviews present but authenticity uncertain.
**Fail:** Obviously fabricated reviews or no reviews at all.

**B2B sourcing example:**
- Pass: Supplier reviews include specific order details (product type, quantity, dates), reviewer's company and role, both positives and negatives, and varied writing styles.
- Fail: All reviews are 5 stars, written in identical style, with no specific details.

### T10: Customer Support | SEO-First

**What to check:** Is there a clear return policy, complaint channel, and response time commitment?

**Pass:** Published return/refund policy, clear complaint escalation path, and stated response SLA.
**Partial:** Some support information but unclear processes.
**Fail:** No visible customer support infrastructure.

**B2B sourcing example:**
- Pass: "Dispute resolution process: Step 1 -- Contact your account manager within 48 hours of delivery. Step 2 -- If unresolved within 5 business days, escalate to our Quality Assurance team. Step 3 -- Third-party inspection arranged within 10 business days. Full refund or re-production guaranteed for verified defects."
- Fail: No dispute resolution process documented.

---

## Content-Type Weight Table

Different content types weight the 8 dimensions differently. Use the weighted score for content-type-specific evaluation.

| Dim | Product Review | How-to Guide | Comparison | Landing Page | Blog Post | FAQ Page | Alternative | Best-of | Testimonial |
|-----|---------------|--------------|------------|--------------|-----------|----------|-------------|---------|-------------|
| C | 10% | 20% | 10% | 20% | 25% | 25% | 10% | 10% | 10% |
| O | 10% | 20% | 20% | 10% | 10% | 25% | 15% | 25% | 5% |
| R | 15% | 10% | 25% | 5% | 10% | 15% | 25% | 20% | 15% |
| E | 20% | 5% | 10% | 5% | 20% | 5% | 5% | 15% | 10% |
| Exp | 20% | 5% | 5% | 5% | 10% | 5% | 15% | 5% | 30% |
| Ept | 5% | 20% | 15% | 5% | 10% | 10% | 5% | 10% | 5% |
| A | 5% | 5% | 5% | 25% | 5% | 5% | 5% | 5% | 5% |
| T | 15% | 15% | 10% | 25% | 10% | 10% | 20% | 10% | 20% |

---

## AI Engine Citation Preferences

Different AI engines prioritize different CORE-EEAT items when selecting content to cite.

| Engine | Citation Style | Priority Items |
|--------|---------------|----------------|
| Google AI Overview | Snippet extraction from paragraphs, lists, tables, FAQs | C02, O03, O05, C09 |
| ChatGPT Browse | Conversational with links | C02, R01, R02, E01 |
| Perplexity AI | Multi-source synthesis + inline citations | E01, R03, R05, Ept05 |
| Claude | Precision-first with nuanced arguments | R04, Ept08, Exp10, R03 |

### Top 6 GEO-First Priority Items

| Rank | ID | Name | Why It Matters |
|------|----|------|----------------|
| 1 | C02 | Direct Answer | All engines extract from first paragraph |
| 2 | C09 | FAQ Coverage | FAQ structure directly matches user follow-ups |
| 3 | O03 | Data Tables | Comparison data is the most extractable format |
| 4 | O05 | Schema Markup | JSON-LD helps AI understand content type |
| 5 | E01 | Original Data | AI prefers citing exclusive sources |
| 6 | O02 | Summary Box | Key Takeaways are often the first choice for AI summary |

---

## Quick Reference: CORE Items (Content Body)

### C -- Contextual Clarity (10 items)

| ID | Check | Priority | Pass Criteria |
|----|-------|----------|---------------|
| C01 | Intent Alignment | Dual | Title promise = content delivery (VETO if clickbait) |
| C02 | Direct Answer | GEO | Core answer in first 150 words |
| C03 | Query Coverage | Dual | Covers 3+ query variants (synonyms, long-tail) |
| C04 | Definition First | GEO | Key terms defined on first use |
| C05 | Topic Scope | GEO | Explicitly states what is and is not covered |
| C06 | Audience Targeting | Dual | States "this article is for..." |
| C07 | Semantic Coherence | GEO | Logical flow; no jumps between paragraphs |
| C08 | Use Case Mapping | GEO | Decision framework: when to choose A vs B |
| C09 | FAQ Coverage | GEO | Structured FAQ covering long-tail follow-ups |
| C10 | Semantic Closure | Dual | Conclusion answers opening question + next steps |

### O -- Organization (10 items)

| ID | Check | Priority | Pass Criteria |
|----|-------|----------|---------------|
| O01 | Heading Hierarchy | Dual | H1 to H2 to H3, no level skipping |
| O02 | Summary Box | GEO | Has TL;DR or Key Takeaways section |
| O03 | Data Tables | GEO | Comparisons in HTML tables with clear headers |
| O04 | List Formatting | GEO | ~1-2 lists per 500 words; parallel items listed |
| O05 | Schema Markup | GEO | Correct JSON-LD matching content type |
| O06 | Section Chunking | GEO | Each section single topic; paragraphs 3-5 sentences |
| O07 | Visual Hierarchy | SEO | Key concepts bolded or highlighted |
| O08 | Anchor Navigation | Dual | Table of contents with jump links |
| O09 | Information Density | GEO | No filler; consistent terminology |
| O10 | Multimedia Structure | Dual | Images/videos have captions and carry information |

### R -- Referenceability (10 items)

| ID | Check | Priority | Pass Criteria |
|----|-------|----------|---------------|
| R01 | Data Precision | GEO | 5+ precise numbers with units (%, $, ms) |
| R02 | Citation Density | GEO | 1+ external citation per 500 words |
| R03 | Source Hierarchy | GEO | Primary sources first; 3+ Tier 1-2 sources |
| R04 | Evidence-Claim Mapping | GEO | Every claim backed by evidence immediately after |
| R05 | Methodology Transparency | GEO | Sample size, steps, criteria documented |
| R06 | Timestamp and Versioning | Dual | Updated within 1 year; date visible |
| R07 | Entity Precision | GEO | Full names for people/orgs/products |
| R08 | Internal Link Graph | SEO | Descriptive anchor texts forming topic clusters |
| R09 | HTML Semantics | GEO | Uses article, figure, time, cite tags |
| R10 | Content Consistency | Dual | No self-contradicting data; no broken links (VETO) |

### E -- Exclusivity (10 items)

| ID | Check | Priority | Pass Criteria |
|----|-------|----------|---------------|
| E01 | Original Data | GEO | First-party surveys, experiments, statistics |
| E02 | Novel Framework | GEO | Named, citable original framework or model |
| E03 | Primary Research | GEO | Original experiments with documented process |
| E04 | Contrarian View | GEO | Challenges consensus with evidence |
| E05 | Proprietary Visuals | Dual | 2+ original infographics, charts, diagrams |
| E06 | Gap Filling | GEO | Covers questions competitors miss |
| E07 | Practical Tools | Dual | Downloadable templates, checklists, calculators |
| E08 | Depth Advantage | GEO | Deeper than competing content on same topic |
| E09 | Synthesis Value | GEO | Cross-domain knowledge producing new insights |
| E10 | Forward Insights | GEO | Data-backed predictions and trend analysis |

---

## Schema by Content Type

| Content Type | Required Schema | Conditional Schema |
|-------------|----------------|-------------------|
| Blog (guides) | Article, Breadcrumb | FAQ, HowTo |
| Blog (tools) | Article, Breadcrumb | FAQ, Review |
| Blog (insights) | Article, Breadcrumb | FAQ |
| Alternative page | Comparison*, Breadcrumb, FAQ | AggregateRating |
| Best-of page | ItemList, Breadcrumb, FAQ | AggregateRating per tool |
| Use-case page | WebPage, Breadcrumb, FAQ | -- |
| FAQ page | FAQPage, Breadcrumb | -- |
| Landing page | SoftwareApplication, Breadcrumb, FAQ | WebPage |
| Testimonial | Review, Breadcrumb | FAQ, Person |
