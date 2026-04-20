# SEO Knowledge Base for Sourcy Global

## Search Console Data Interpretation

### CTR Benchmarks by Position (Google Organic)
- Position 1: 25-35% CTR (branded can hit 50%+)
- Position 2: 12-18% CTR
- Position 3: 8-12% CTR
- Position 4-5: 5-8% CTR
- Position 6-10: 2-4% CTR
- Position 11-20: 0.5-1.5% CTR
- If CTR is significantly below these ranges at a given position, the title/meta description needs work
- If CTR is above these ranges, the snippet is compelling or query is branded

### Reading Search Console Signals
- Impressions rising but clicks flat = ranking for queries you don't satisfy (content gap or poor snippet)
- Clicks rising but impressions flat = CTR improving (good title tag / snippet optimization)
- Position improving but CTR dropping = moving into more competitive SERPs with rich results stealing clicks
- High impressions + low position (15-30) = topic authority exists, content needs strengthening
- Sudden impression drops = indexing issue, penalty, or algorithm update impact

### Striking Distance Strategy (Positions 4-20)
- Priority 1: Pages at positions 4-10 with >500 monthly impressions (quick wins)
- Priority 2: Pages at positions 11-15 with >1000 monthly impressions (moderate effort, high payoff)
- Priority 3: Pages at positions 15-20 with >2000 monthly impressions (need significant content improvement)
- Actions for striking distance keywords:
  - Add missing subtopics competitors cover (use People Also Ask as guide)
  - Improve internal linking from high-authority pages
  - Enhance content depth: add data tables, comparisons, pricing context
  - Optimize title tag to include exact match keyword
  - Add FAQ schema for long-tail variations

## On-Page SEO Factors

### Critical On-Page Elements (Priority Order)
- Title tag: Include primary keyword within first 60 chars; for Sourcy, format as "[Keyword] | Sourcy - [Value Prop]"
- H1: One per page, should closely match title tag intent but not be identical
- URL structure: /[market]/[category]/[subcategory] for marketplace pages
- Meta description: 150-160 chars, include CTA language ("Compare suppliers", "Get quotes")
- H2/H3 hierarchy: Use for subtopics, each should target a related keyword cluster
- Internal links: Every key page should have 3-5 contextual internal links pointing to it
- Image alt text: Descriptive, include product/category keywords for supplier images

### Content Signals That Matter for B2B Sourcing
- Word count is less important than topic coverage completeness
- Comparison tables outperform paragraphs for sourcing queries (supplier vs supplier, country vs country)
- Data freshness signals: include dates, "updated [month] [year]", recent pricing data
- E-E-A-T signals for sourcing: author expertise, company credentials, supplier verification badges
- User-generated content (reviews, ratings) creates unique content at scale

## Technical SEO Signals

### Core Web Vitals Targets
- LCP (Largest Contentful Paint): <2.5s (critical for marketplace listing pages)
- INP (Interaction to Next Paint): <200ms (important for filter/search interactions)
- CLS (Cumulative Layout Shift): <0.1 (watch for lazy-loaded supplier images)

### Technical Issues Common to Marketplace Platforms
- Faceted navigation creating duplicate content (use canonical tags or noindex for filter combinations)
- Thin content on category pages with few suppliers (add editorial content above listings)
- Pagination: use rel="next/prev" or infinite scroll with proper crawlable links
- Hreflang implementation: critical for Sourcy's multi-country setup (en-us, en-ph, id-id, pt-br, th-th, es-mx)
- Dynamic rendering may be needed if JS-heavy supplier pages aren't being indexed
- XML sitemap: separate sitemaps per content type (suppliers, categories, blog, country pages)

### Indexation Health Checks
- Coverage report: aim for >90% of submitted URLs indexed
- "Discovered - not indexed" growing = quality signal issue, Google doesn't see value
- "Crawled - not indexed" = content quality problem, improve or consolidate these pages
- Soft 404s on empty category pages = add content or noindex until suppliers are listed

## Keyword Intent Mapping for B2B Sourcing

### Intent Categories
- **Informational**: "how to source [product] from [country]", "best countries for [material] manufacturing"
  - Content type: Blog posts, guides, country sourcing reports
  - Conversion expectation: Low direct, high for email capture / lead nurture
- **Commercial Investigation**: "[product] suppliers in [country]", "[material] manufacturer comparison"
  - Content type: Category pages, comparison pages, supplier directories
  - Conversion expectation: Medium, these users are evaluating options
- **Transactional**: "[specific supplier] contact", "get quote for [product]", "[product] MOQ pricing"
  - Content type: Supplier profile pages, RFQ forms, pricing pages
  - Conversion expectation: High, ready to engage
- **Navigational**: "sourcy [product]", "sourcy login", "[specific supplier name]"
  - Content type: Homepage, login page, supplier profiles
  - Conversion expectation: Very high for branded, protect these rankings

### B2B Sourcing Keyword Clusters (Sourcy-Specific)
- Product + Country: "textile suppliers Indonesia", "auto parts manufacturers Thailand"
- Product + Qualification: "ISO certified [product] manufacturers", "FDA approved [product] suppliers"
- Process queries: "how to import from [country]", "sourcing agent vs direct manufacturer"
- Comparison: "[country A] vs [country B] for [product] manufacturing"
- Cost queries: "[product] manufacturing cost in [country]", "[product] MOQ"

## Content Gap Analysis Methodology

### Step-by-Step Process
1. Identify top 5 competitors ranking for target keyword clusters
2. Extract their ranking keywords using Search Console (own) and estimated tools (competitors)
3. Map keywords into a matrix: keywords YOU rank for vs keywords COMPETITORS rank for
4. Gaps = keywords competitors rank for that you don't (new content needed)
5. Weaknesses = keywords both rank for but competitor outranks you (content improvement needed)
6. Strengths = keywords you rank well for that competitors don't (protect and expand)

### Prioritization Framework for Gaps
- Score each gap: Search Volume x Business Relevance (1-3) x Ranking Difficulty Inverse
- Business Relevance 3: Directly leads to supplier connection / RFQ (transactional)
- Business Relevance 2: Evaluating sourcing options (commercial investigation)
- Business Relevance 1: Early research phase (informational)
- Tackle high-volume transactional gaps first, then build supporting informational content

### Common Gaps for B2B Sourcing Platforms
- Country-specific sourcing guides (Indonesia manufacturing guide, Thailand export regulations)
- Product category deep-dives with pricing benchmarks
- Supplier evaluation criteria / checklists
- Import/export compliance content per country pair
- Industry trend reports (these attract backlinks naturally)

## Link Building Signals for B2B Sourcing
- Domain Rating / Authority: Aim for links from DR 40+ domains
- Relevance matters more than authority: A link from a trade publication at DR 30 beats a generic site at DR 70
- Natural link targets for Sourcy: trade associations, chambers of commerce, export promotion agencies
- Content that earns links: original data (sourcing cost indexes), country reports, industry benchmarks
- Disavow spammy links from low-quality directories that are common in sourcing space
