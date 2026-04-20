# Answer Engine Optimization (AEO) Knowledge Base for Sourcy Global

## How AI Search Engines Select Sources

### Source Selection Signals (Perplexity, ChatGPT Search, Gemini, AI Overviews)
- Topical authority: sites that cover a topic comprehensively across multiple pages rank higher as sources
- Direct, concise answers in the first 1-2 sentences of a section (AI extracts these as snippets)
- Structured content: H2/H3 headers that match common question patterns
- Factual density: pages with specific numbers, data points, comparisons are preferred over vague content
- Recency: AI models favor recently published or updated content, especially for market/pricing data
- Domain authority still matters: established domains are cited more frequently
- Schema markup helps AI engines parse content type and relationships

### How AI Search Differs from Traditional Search
- AI search synthesizes from multiple sources; you don't need position 1, you need to be a cited source
- Being cited in AI answers drives brand awareness even if users don't click through
- Long-tail conversational queries are increasing: "what's the best country to source textiles from if I need ISO certification and MOQ under 500 units"
- AI search rewards specificity: generic content gets ignored in favor of detailed, niche answers

## Featured Snippets Optimization

### Snippet Types and How to Win Them
- **Paragraph snippets** (most common): Answer the question in 40-60 words immediately after an H2/H3 that contains the question
- **List snippets**: Use ordered/unordered lists with 4-8 items for "best", "top", "steps" queries
- **Table snippets**: Use HTML tables for comparison queries (country vs country, supplier tiers, pricing)
- **Video snippets**: Less relevant for B2B sourcing, but YouTube videos can appear for "how to" queries

### Snippet-Winning Content Patterns for Sourcy
- "What is [sourcing concept]?" -> Define in 1-2 sentences immediately under matching H2
- "[Product] suppliers in [country]" -> Table with supplier tiers, MOQ, certifications
- "How to source [product] from [country]" -> Numbered step list (5-8 steps)
- "[Country A] vs [Country B] for manufacturing" -> Comparison table with clear dimensions
- "Average cost of [product] from [country]" -> Paragraph with specific price range and date

## People Also Ask (PAA) Optimization

### Strategy
- Each PAA question is a content section opportunity; answer it as an H2 + concise paragraph
- PAA questions cascade: answering one well leads Google to show your content for related PAAs
- Map PAA clusters for each target keyword; create content that addresses 5-8 related PAAs per page
- For Sourcy, common PAA patterns:
  - "Is it safe to source from [country]?"
  - "What is the MOQ for [product] from [country]?"
  - "How long does shipping take from [country]?"
  - "Do I need a sourcing agent in [country]?"
  - "What certifications should [product] suppliers have?"

## Structured Data for B2B Sourcing Platforms

### Priority Schema Types
- **Organization**: Company details, logo, contact for Sourcy itself
- **Product**: For supplier listings (name, description, brand, offers)
- **FAQPage**: For FAQ sections on category and guide pages (high snippet potential)
- **HowTo**: For step-by-step sourcing guides
- **BreadcrumbList**: For site navigation (improves sitelinks in search)
- **Review / AggregateRating**: For supplier ratings (shows stars in SERPs, increases CTR 15-25%)
- **LocalBusiness**: For suppliers with physical locations
- **WebPage / Article**: For blog content with datePublished and dateModified

### Implementation Priority
1. FAQPage schema on all category pages and guides (fastest snippet wins)
2. BreadcrumbList site-wide (easy, improves site structure signals)
3. AggregateRating on supplier profiles (CTR boost)
4. Product schema on supplier listings (rich results in search)
5. Organization schema on about/homepage (knowledge panel potential)

## Content Structure That Wins in AI-Generated Answers

### Page Architecture Template
- Open with a 2-3 sentence direct answer to the primary query (this gets extracted by AI)
- Follow with a structured breakdown using H2s that match question variants
- Include a comparison table early (AI loves structured data for synthesis)
- Add specific numbers: prices, timelines, MOQs, percentages
- Close each section with a clear takeaway or recommendation
- Include a "Key Takeaways" or "Quick Summary" section (bulleted, 5-7 points)

### Content Attributes That Get Cited by AI
- First-party data: Sourcy's own platform data (number of suppliers, average response times, RFQ volumes)
- Specificity: "Indonesian textile suppliers typically offer MOQs of 300-500 units" beats "MOQs vary by supplier"
- Timeliness: Include "As of [month] [year]" with current data
- Authoritative framing: "Based on analysis of [X] supplier transactions on Sourcy" signals original research
- Contrarian or nuanced takes: AI models surface non-obvious insights over generic advice

### What NOT to Do
- Avoid fluffy intro paragraphs (AI skips them; users skip them)
- Don't gate critical information behind login walls (AI can't access it, won't cite it)
- Don't use images for data that should be in text/tables (AI can't read images reliably)
- Avoid thin pages with <300 words; consolidate into comprehensive resources
- Don't keyword-stuff; AI models detect and penalize unnatural language patterns
