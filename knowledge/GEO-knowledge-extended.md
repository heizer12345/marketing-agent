# GEO Extended Knowledge -- Domain Knowledge Reference

Extended reference for Generative Engine Optimization (GEO). Covers GEO scoring framework, AI crawler registry, llms.txt standard, platform-specific citation patterns, and entity optimization for AI visibility. This extends the base GEO-knowledge.md with deeper tactical detail.

---

## GEO Scoring Framework

GEO readiness is scored across 5 weighted factors totaling 100 points.

### Factor 1: Citability Score (25% weight)

How easily can AI systems extract and quote passages from the content?

**Optimal passage length for AI citation: 134-167 words.** This is the sweet spot for AI systems to extract self-contained answer blocks.

**Strong citability signals:**
- Clear, quotable sentences with specific facts and statistics
- Self-contained answer blocks that can be extracted without surrounding context
- Direct answer in first 40-60 words of each section
- Claims attributed with specific sources and dates
- Definitions following "X is..." or "X refers to..." patterns
- Unique data points not found elsewhere on the web

**Weak citability signals:**
- Vague, general statements without specifics
- Opinion without supporting evidence
- Buried conclusions (answer at the end instead of the beginning)
- No specific data points or metrics

**Scoring rubric:**
- 90-100: Multiple self-contained, quotable passages with unique data
- 70-89: Some quotable passages but lacking unique data or specificity
- 50-69: Few extractable passages; content requires surrounding context
- 0-49: No quotable passages; content is not structured for AI extraction

### Factor 2: Structural Readability (20% weight)

Is the content structured so AI systems can parse and understand it?

**Key statistic:** 92% of AI Overview citations come from top-10 ranking pages, but 47% come from pages ranking below position 5 -- demonstrating that AI selection logic differs from traditional ranking.

**Strong structural signals:**
- Clean H1 to H2 to H3 heading hierarchy with no level skipping
- Question-based headings that match common query patterns
- Short paragraphs (2-4 sentences per paragraph)
- HTML tables for comparative data with clear column headers
- Ordered and unordered lists for step-by-step or multi-item content
- FAQ sections with clear question-answer format
- Summary/TL;DR boxes at the top of long content

**Weak structural signals:**
- Walls of text with no structure
- Inconsistent heading hierarchy
- No lists, tables, or structured formats
- Key information buried deep in paragraphs

### Factor 3: Multi-Modal Content (15% weight)

Does the content include multiple media types that reinforce the text?

**Key statistic:** Content with multi-modal elements sees 156% higher selection rates by AI systems.

**Check for:**
- Text paired with relevant (not decorative) images
- Video content embedded or linked with descriptive text
- Infographics and charts that visualize data discussed in text
- Interactive elements (calculators, configurators, tools)
- Structured data supporting multimedia (ImageObject, VideoObject schema)
- Alt text and captions that add information (not just repeat the image filename)

### Factor 4: Authority and Brand Signals (20% weight)

Is the content source recognized as authoritative?

**Critical insight: Brand mentions correlate 3x more strongly with AI visibility than backlinks.** (Ahrefs December 2025 study, 75,000 brands)

| Signal | Correlation with AI Citations |
|--------|------------------------------|
| YouTube mentions | ~0.737 (strongest single signal) |
| Reddit mentions | High |
| Wikipedia presence | High |
| LinkedIn presence | Moderate |
| Domain Rating (backlinks) | ~0.266 (weak) |

**Strong authority signals:**
- Author byline with verifiable credentials
- Publication date and last-updated date
- Citations to primary sources (studies, official documentation, data)
- Organization credentials and industry affiliations
- Expert quotes with named attribution
- Entity presence in Wikipedia, Wikidata
- Mentions on Reddit, YouTube, LinkedIn
- Brand has measurable search volume

**Weak authority signals:**
- Anonymous authorship
- No dates on content
- No sources cited
- No brand presence across platforms

### Factor 5: Technical Accessibility (20% weight)

Can AI crawlers actually access and process the content?

**Critical fact: AI crawlers do NOT execute JavaScript.** Server-side rendering is mandatory for AI visibility.

**Check for:**
- Server-side rendering (SSR) vs. client-only JavaScript content
- AI crawler access in robots.txt (see crawler registry below)
- llms.txt file presence and configuration
- RSL 1.0 licensing terms (if applicable)
- Clean HTML semantics (article, figure, time, cite tags)
- Fast page load (AI crawlers have timeout limits)

---

## AI Crawler Registry

Complete registry of AI crawlers with their User-Agent strings. Check robots.txt to verify which are allowed.

### Search and Citation Crawlers (ALLOW for AI visibility)

| Crawler | User-Agent String | Owner | Purpose |
|---------|------------------|-------|---------|
| GPTBot | `GPTBot` | OpenAI | ChatGPT web search and browsing |
| OAI-SearchBot | `OAI-SearchBot` | OpenAI | OpenAI search features |
| ChatGPT-User | `ChatGPT-User` | OpenAI | ChatGPT live browsing sessions |
| ClaudeBot | `ClaudeBot` | Anthropic | Claude web features |
| PerplexityBot | `PerplexityBot` | Perplexity | Perplexity AI search |
| Bytespider | `Bytespider` | ByteDance | TikTok/Douyin AI features |

### Training-Only Crawlers (BLOCK if you only want citation, not training)

| Crawler | User-Agent String | Owner | Purpose |
|---------|------------------|-------|---------|
| CCBot | `CCBot` | Common Crawl | Training data collection |
| anthropic-ai | `anthropic-ai` | Anthropic | Claude model training |
| cohere-ai | `cohere-ai` | Cohere | Cohere model training |
| Google-Extended | `Google-Extended` | Google | Gemini training |

### Recommended robots.txt Configuration

For maximum AI search visibility while blocking training-only crawlers:

```
# Allow AI search crawlers
User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

# Block training-only crawlers (optional)
User-agent: CCBot
Disallow: /

User-agent: Google-Extended
Disallow: /
```

---

## llms.txt Standard

The emerging llms.txt standard provides AI crawlers with structured content guidance -- a machine-readable site map specifically for AI systems.

### Location and Format

**File location:** `/llms.txt` at the root of the domain (e.g., `https://example.com/llms.txt`)

**Standard format:**
```
# Company/Site Name
> Brief one-line description of the company or site

## Main Sections
- [Page title](url): Short description of this page
- [Another page](url): What this page covers

## Key Facts
- Founded: 2020
- Industry: B2B sourcing technology
- Headquarters: San Francisco, CA

## Contact
- Website: https://example.com
- Email: hello@example.com
```

### What to Include in llms.txt

1. **Company identity** -- Name, one-line description, industry
2. **Key pages** -- Products, services, about, blog categories with descriptions
3. **Authority signals** -- Key facts, founding date, notable achievements
4. **Content structure** -- Main topic areas with representative URLs
5. **Contact information** -- Website, email, social links

### llms.txt Audit Checklist

- [ ] File exists at domain root `/llms.txt`
- [ ] Contains site name and description
- [ ] Lists key pages with descriptions
- [ ] Includes factual entity information
- [ ] URLs are valid and accessible
- [ ] Information matches website and other profiles
- [ ] Updated within the last 6 months

---

## RSL 1.0 (Really Simple Licensing)

New standard (December 2025) for machine-readable AI licensing terms. Backed by Reddit, Yahoo, Medium, Quora, Cloudflare, Akamai, and Creative Commons.

RSL provides a way for sites to communicate licensing terms to AI systems in a structured, machine-readable format. Check for RSL implementation if the site has specific terms for AI use of its content.

---

## Platform-Specific Citation Patterns

Each AI platform has distinct citation preferences and source priorities. Only 11% of domains are cited by both ChatGPT and Google AI Overviews for the same query, making platform-specific optimization essential.

### Google AI Overviews

**How it works:** Google AI Overviews extract content from pages already in the Google index, with heavy preference for top-ranking pages. They appear above organic results in standard search and are the sole result format in Google AI Mode.

**Key statistics:**
- Reaches 1.5 billion users/month across 200+ countries
- Covers 50%+ of all queries
- 92% of citations come from top-10 ranking pages
- 47% of citations come from pages ranking below position 5

**Citation preferences:**
- Snippet extraction from well-structured paragraphs
- Tables and comparison data
- Lists (ordered and unordered)
- FAQ-formatted content
- Content with schema markup (Article, FAQ, HowTo)

**Optimization strategy:**
1. Rank in top 10 first (traditional SEO still matters most)
2. Structure content with clear heading hierarchy
3. Include tables for comparative data
4. Write self-contained answer blocks in the 134-167 word range
5. Use schema markup matching content type
6. Include FAQ sections for long-tail coverage

### ChatGPT Web Search

**How it works:** ChatGPT Browse searches the web in real-time and synthesizes answers with links to sources. Citation is conversational -- it references sources inline rather than extracting snippets.

**Key statistics:**
- 900 million weekly active users
- Top citation sources: Wikipedia (47.9%), Reddit (11.3%)

**Citation preferences:**
- Authoritative, well-known sources
- Content with specific data points and statistics
- Original research and first-party data
- Wikipedia-style factual writing
- Clear entity definitions

**Optimization strategy:**
1. Build Wikipedia and Wikidata presence
2. Create original data and research that others cite
3. Ensure content has specific, verifiable facts
4. Write clear entity definitions in the first paragraph of key pages
5. Build presence on Reddit through genuine community participation
6. Allow GPTBot, OAI-SearchBot, and ChatGPT-User in robots.txt

### Perplexity AI

**How it works:** Perplexity synthesizes answers from multiple sources with inline citations. It heavily weights community validation and discussion-based content.

**Key statistics:**
- 500+ million monthly queries
- Top citation sources: Reddit (46.7%), Wikipedia

**Citation preferences:**
- Multi-source synthesis with inline citations
- Community-validated content (Reddit, forums)
- Content with clear methodology and reproducible findings
- Discussion-style content with multiple perspectives
- Well-structured data with clear sourcing

**Optimization strategy:**
1. Build genuine Reddit presence (participate in relevant subreddits)
2. Create content that presents multiple viewpoints with evidence
3. Include methodology transparency (sample sizes, process documentation)
4. Cite primary sources that Perplexity can cross-reference
5. Write content that other sources are likely to reference
6. Allow PerplexityBot in robots.txt

### Bing Copilot

**How it works:** Bing Copilot uses the Bing search index as its primary source, supplemented by authoritative websites.

**Optimization strategy:**
1. Submit site to Bing Webmaster Tools
2. Implement IndexNow for rapid indexing
3. Ensure Bing-specific SEO (meta tags, structured data)
4. Build entity presence through LinkedIn (Microsoft ecosystem)
5. Ensure content meets Bing's quality guidelines

---

## Entity Optimization for AI Visibility

Entity signals are the bridge between content quality and AI citation. AI systems must first recognize an entity before they can cite its content.

### Entity-Specific GEO Tactics

1. **Define clearly** -- First paragraph of About page and key pages should define the entity in a way AI can quote directly. Use the pattern: "[Entity] is a [type] that [does what] for [whom]."

2. **Be consistent** -- Use identical entity description across all platforms: website, LinkedIn, Wikidata, directories, social profiles. Inconsistency causes AI systems to lose confidence.

3. **Build topic associations** -- Create content that explicitly connects the entity to target topics. If you want AI to associate your brand with "B2B sourcing," you need multiple pages and external mentions connecting these concepts.

4. **Earn mentions** -- Third-party authoritative mentions are stronger entity signals than self-description. Get mentioned in industry publications, comparison articles, and community discussions.

5. **Stay current** -- Outdated entity information causes AI systems to lose confidence and stop citing. Update entity profiles and key content at least every 6 months.

### Schema.org Implementation for Entity Clarity

Minimum schema for AI entity recognition:

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#organization",
  "name": "Company Name",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "description": "One-sentence entity definition",
  "sameAs": [
    "https://www.wikidata.org/wiki/QXXXXX",
    "https://www.linkedin.com/company/example",
    "https://twitter.com/example",
    "https://www.crunchbase.com/organization/example"
  ],
  "foundingDate": "2020",
  "founder": {
    "@type": "Person",
    "name": "Founder Name"
  }
}
```

Always include sameAs with the Wikidata URL first -- this is the single most powerful structured data property for entity recognition.

---

## GEO Quick Wins (Ranked by Impact)

### Immediate (This Week)

1. Add "What is [topic]?" definition in first 60 words of key pages
2. Create 134-167 word self-contained answer blocks for target queries
3. Add question-based H2/H3 headings
4. Include specific statistics with named sources
5. Add publication and last-updated dates to all content
6. Implement Person schema for content authors
7. Allow key AI crawlers in robots.txt

### Medium Effort (This Month)

1. Create `/llms.txt` file at domain root
2. Add author bios with credentials and links to Wikipedia/LinkedIn
3. Ensure server-side rendering for all key content pages
4. Build entity presence on Reddit and YouTube
5. Add comparison tables with real data
6. Implement FAQ sections with clear Q&A format

### High Impact (This Quarter)

1. Create original research, surveys, or proprietary data sets
2. Build Wikipedia presence for brand and key people
3. Establish YouTube channel with content that mentions the brand
4. Implement comprehensive entity linking (sameAs across all platforms)
5. Develop unique interactive tools or calculators
6. Get mentioned in 3+ authoritative industry publications

---

## Key GEO Statistics Reference

| Metric | Value | Source |
|--------|-------|--------|
| AI Overviews reach | 1.5B users/month, 200+ countries | Google |
| AI Overviews query coverage | 50%+ of all queries | Industry data |
| AI-referred sessions growth | 527% (Jan-May 2025) | SparkToro |
| ChatGPT weekly active users | 900 million | OpenAI |
| Perplexity monthly queries | 500+ million | Perplexity |
| Brand mentions vs backlinks for AI | 3x stronger correlation | Ahrefs Dec 2025 |
| Optimal AI citation passage length | 134-167 words | GEO research |
| AI Overview citations from top 10 | 92% | Industry data |
| Domains cited by both ChatGPT and Google AIO | Only 11% | Ahrefs |
| Multi-modal content selection uplift | 156% higher | GEO research |

---

## Content Reformatting for GEO

Existing content can be reformatted to improve AI citability without full rewrites. These are the highest-ROI structural changes.

### Answer Block Insertion

For each key section of existing content, insert a self-contained answer block at the top:

1. Identify the question the section answers
2. Write a 134-167 word block that answers it completely
3. Place it immediately after the section heading
4. Keep the existing detailed content below for depth

**Before (buried answer):**
```
## Supplier Qualification

There are many factors to consider when evaluating potential suppliers.
Quality systems, production capacity, financial stability, and 
communication responsiveness all play important roles. After thoroughly
examining these dimensions across multiple candidates, buyers typically
find that the most reliable approach is a weighted scorecard method.
```

**After (answer-first):**
```
## How Do You Qualify a New Supplier?

The most reliable supplier qualification method is a weighted scorecard
evaluating quality systems (35%), production capacity (25%), pricing 
(20%), communication (10%), and financial stability (10%). Score each 
criterion 1-5 based on factory audits, sample orders, and reference 
checks. Suppliers scoring above 4.0 are qualified for production orders.
This process typically takes 4-8 weeks for B2B buyers.

Here is a detailed breakdown of each qualification criterion...
```

### Definition-First Rewriting

AI systems extract definitions from the first paragraph of pages and sections. Ensure every key concept page opens with a clear definition.

**Pattern:** "[Term] is [definition]. [Key characteristic]. [Scope/application]."

**Example:** "FOB (Free on Board) is an international trade term where the seller delivers goods onto the shipping vessel at the named port of origin. The buyer assumes all costs and risks from that point forward. FOB is the most common Incoterm for B2B sourcing from Asia, used in approximately 60% of import transactions."

### Table Conversion

Convert prose comparisons to HTML tables. AI systems extract tabular data at significantly higher rates than prose comparisons.

**Identify opportunities where content:**
- Compares 3+ options on the same criteria
- Lists features, pricing tiers, or specifications
- Presents data with multiple dimensions
- Describes before/after scenarios with metrics

### FAQ Section Addition

Add a structured FAQ section (5-10 questions) to the bottom of key content pages. Use questions mined from:
- Google's People Also Ask boxes for target keywords
- Search Console queries that trigger impressions but low clicks
- Customer support inquiries and sales objections
- Competitor content headings reformulated as questions

---

## GEO Monitoring Framework

### What to Track Weekly

| Metric | Tool/Method | Action Threshold |
|--------|-------------|------------------|
| AI Overview citations | Search target queries in Google | Citation lost -- review content freshness |
| ChatGPT brand recognition | Ask ChatGPT about your brand quarterly | Incorrect info -- update authoritative sources |
| Perplexity brand citations | Search brand-related queries | Not cited -- check Reddit/Wikipedia presence |
| robots.txt changes | Monitor robots.txt file | AI crawler access accidentally blocked |
| Content freshness | Check last-updated dates | Key pages older than 6 months -- update |

### GEO Audit Cadence

| Activity | Frequency | Focus |
|----------|-----------|-------|
| AI crawler access check | Monthly | Verify robots.txt still allows key crawlers |
| llms.txt validation | Monthly | Verify URLs work, info is current |
| AI recognition test | Quarterly | Ask all 4 platforms about your brand/topics |
| Content freshness sweep | Quarterly | Update any key pages older than 6 months |
| Entity consistency audit | Quarterly | Verify name/description matches across all platforms |
| Full GEO scoring audit | Semi-annually | Score all key pages against the 5-factor framework |

### Attribution Tracking for AI Traffic

AI-referred traffic is growing rapidly (527% growth Jan-May 2025 per SparkToro). To track it:

1. **Server log analysis** -- Look for AI crawler User-Agent strings in access logs
2. **Referrer tracking** -- Monitor referrals from chat.openai.com, perplexity.ai, and Google AI mode
3. **UTM parameters** -- Some AI platforms pass referrer data; capture it in analytics
4. **Brand search correlation** -- Increases in branded search after AI mentions indicate AI-driven discovery
5. **Direct traffic spikes** -- AI citations often drive direct visits (users copy URLs from AI answers)

---

## B2B Sourcing GEO Playbook

### High-Priority GEO Content Types for Sourcing

1. **Comparison pages** -- "[Supplier A] vs [Supplier B]" or "[Country A] vs [Country B] for Manufacturing" with structured data tables
2. **Process guides** -- "How to [sourcing activity]" with step-by-step format and original data
3. **Benchmark reports** -- Original data on pricing, lead times, defect rates (highly citable by AI)
4. **Glossary/definition pages** -- Clear definitions of trade terms (Incoterms, AQL, MOQ) that AI systems frequently need
5. **Decision frameworks** -- "When to use [approach A] vs [approach B]" with clear criteria

### Entity Building for Sourcing Brands

Sourcing is a niche B2B space where many brands lack entity presence. This creates opportunity:

1. **Create a Wikidata entry** -- Few sourcing companies have one; early movers gain disproportionate AI recognition
2. **Build Reddit presence** -- Subreddits like r/supplychain, r/ecommerce, r/FulfillmentByAmazon are citation sources for Perplexity
3. **Publish original data** -- Annual sourcing benchmarks, pricing indexes, or quality data become go-to AI citation sources
4. **Establish YouTube presence** -- YouTube mentions have the strongest correlation with AI visibility (0.737); factory tours, process videos, and explainer content all count
5. **Get listed in industry directories** -- ThomasNet, Kompass, and industry-specific platforms feed into knowledge graphs
