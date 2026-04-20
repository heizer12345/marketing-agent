# AEO Extended Knowledge -- Domain Knowledge Reference

Extended reference for Answer Engine Optimization (AEO). Covers featured snippet types and targeting strategies, PAA optimization, answer block best practices, structured data for AI answers, voice search optimization, and SERP feature taxonomy. This extends the base AEO-knowledge.md with deeper tactical detail.

---

## Featured Snippet Types and Targeting Strategies

Featured snippets display at Position 0 (above organic results) and are the primary AEO target. They are also a strong signal for AI Overview citation since Google reuses snippet-winning content.

### Snippet Type Reference

| Type | Format | Typical Trigger Queries | Optimal Length |
|------|--------|------------------------|----------------|
| Paragraph | 40-60 word text block | "What is...", "Why is...", definitions, explanations | 40-60 words |
| Ordered List | Numbered steps | "How to...", process queries, step-by-step | 5-8 steps |
| Unordered List | Bulleted list | "Types of...", "best...", collections, features | 5-10 items |
| Table | Data in rows/columns | Comparisons, data queries, pricing, specifications | 3-5 columns, 4-8 rows |
| Video | YouTube clip with timestamp | "How to..." with visual component | First 60 seconds with timestamp |

### Paragraph Snippet Targeting

**How to win paragraph snippets:**

1. Use the target question as an H2 or H3 heading (match the query closely)
2. Answer the question directly in the first sentence immediately after the heading
3. Keep the answer to 40-60 words -- concise and self-contained
4. Include the trigger keyword in both the heading and the answer
5. Elaborate with supporting detail after the snippet-eligible block
6. Use declarative language: "X is..." rather than "X can be described as..."

**Template for paragraph snippet targeting:**

```
## What Is [Target Query]?

[Target query] is [clear 1-sentence definition]. [1-2 supporting sentences 
with specific details, numbers, or context]. [Optional: brief qualification 
or scope statement].

[Expanded explanation continues below for readers who want depth...]
```

**B2B sourcing example:**

```
## What Is Supplier Qualification?

Supplier qualification is the process of evaluating and approving a 
manufacturer or vendor before placing production orders. It typically 
involves factory audits, sample testing, financial assessment, and 
compliance verification. The process takes 4-8 weeks for most B2B buyers.

The full supplier qualification process includes these steps...
```

### List Snippet Targeting

**How to win ordered list snippets (step-by-step):**

1. Use "How to..." as the H2 heading
2. Immediately follow with a numbered list using proper HTML `<ol>` tags
3. Each step should be a single clear sentence (8-15 words)
4. Include 5-8 steps (Google rarely shows more than 8)
5. Bold the action verb at the start of each step
6. After the list, provide detailed explanations of each step

**How to win unordered list snippets (collections):**

1. Use "Types of..." or "Best..." as the H2 heading
2. Follow with a bulleted list using proper HTML `<ul>` tags
3. Each item should be descriptive but concise
4. Target 5-10 items for optimal display
5. Ensure items are parallel in structure

### Table Snippet Targeting

**How to win table snippets:**

1. Use comparison-style H2 headings (e.g., "[X] vs [Y]", "[Category] Comparison")
2. Use proper HTML `<table>` tags with `<thead>` and `<tbody>`
3. Include clear column headers
4. Keep tables to 3-5 columns and 4-8 rows for display
5. Include data with specific values (numbers, prices, metrics)
6. Place the table immediately after the triggering heading

**B2B sourcing example table:**

```html
<table>
  <thead>
    <tr>
      <th>Incoterm</th>
      <th>Seller Responsibility</th>
      <th>Buyer Responsibility</th>
      <th>Best For</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>FOB</td>
      <td>Delivery to port</td>
      <td>Freight + insurance</td>
      <td>Experienced importers</td>
    </tr>
    ...
  </tbody>
</table>
```

---

## People Also Ask (PAA) Optimization

PAA boxes appear on nearly all informational queries and many commercial queries. They represent validated search demand and are a high-volume AEO opportunity.

### PAA Mining Workflow

1. Search your target keyword in Google
2. Note all 4 visible PAA questions
3. Click each one to reveal 2-4 additional questions
4. Repeat to collect 15-20 related questions
5. Group questions by subtopic cluster
6. Create content addressing each cluster with dedicated H2/H3 headings

### PAA Answer Optimization

**Winning PAA answers follow this pattern:**

- **Length:** 40-60 words (concise, complete)
- **Structure:** Direct answer first, supporting detail second
- **Format:** Match the question type (definition question = paragraph, "how many" = number, list question = list)
- **Heading:** Use the exact PAA question (or close variant) as your H2/H3
- **Schema:** FAQ schema markup increases PAA eligibility

**PAA Answer Template:**

```
## [Exact PAA Question]?

[Direct 1-sentence answer]. [1-2 supporting sentences with specific 
details or data]. [Optional brief context or qualification].
```

### PAA Cascade Strategy

When users click one PAA answer, Google reveals additional related questions. This "cascade" represents deeper user intent. Cover the cascade questions to:

1. Increase the total number of PAA positions your content can win
2. Demonstrate topical comprehensiveness to Google
3. Capture long-tail traffic from follow-up searches
4. Build topical authority signals

### PAA by Intent Type

| Query Intent | Typical PAA Pattern | Content Strategy |
|-------------|-------------------|-----------------|
| Informational | "What is...", "How does...", "Why..." | Definition + explanation content |
| Commercial Investigation | "Is [X] worth it?", "Best [X] for...", "[X] vs [Y]" | Comparison + review content |
| Navigational | "How to use [brand]...", "[Brand] features" | Product/service documentation |
| Transactional | "How much does [X] cost?", "Where to buy [X]" | Pricing + purchase guide content |

---

## Answer Block Best Practices

Answer blocks are self-contained passages optimized for extraction by both traditional search features and AI systems. They serve as the atomic unit of AEO.

### Optimal Answer Block Structure

**Target length: 134-167 words** for AI citation. For featured snippets, the target is 40-60 words for paragraphs.

**Structure:**
1. **Lead sentence** (direct answer) -- Answers the question in 15-25 words
2. **Evidence sentence** -- Supports the answer with data, source, or example
3. **Context sentence** -- Adds scope, qualification, or practical implication
4. **Bridge sentence** -- Connects to the next section or deeper content

### Answer-First Formatting

Every section should front-load the answer. Do not bury conclusions at the end.

**Wrong (conclusion-last):**
> There are many factors to consider when choosing a supplier. Quality, price, lead time, and communication all play important roles. After evaluating these factors against your specific requirements and volume needs, you can determine that FOB pricing is generally best for orders over 5,000 units.

**Right (answer-first):**
> FOB pricing is generally best for orders over 5,000 units. At this volume, you benefit from lower per-unit freight costs and greater control over shipping logistics. For smaller orders, CIF pricing simplifies the process by including freight and insurance in the supplier's quote.

### Quotability Checklist

For each key section of content, verify:

- [ ] First sentence directly answers a question someone would ask
- [ ] Contains at least 1 specific data point (number, percentage, date)
- [ ] Can be extracted and read independently without surrounding context
- [ ] Uses declarative statements, not hedging ("X is..." not "X might be...")
- [ ] Includes source attribution for factual claims
- [ ] Length is 40-60 words for snippet targeting or 134-167 words for AI citation

---

## Structured Data for AI Answers

Schema markup helps both traditional search features and AI systems understand and extract content.

### Priority Schema Types for AEO

| Schema Type | AEO Purpose | When to Use |
|-------------|-------------|-------------|
| FAQPage | Powers FAQ rich results and PAA eligibility | Any page with Q&A content |
| HowTo | Powers how-to rich results and step extraction | Process/tutorial content |
| Article | Helps AI identify content type and metadata | Blog posts, guides, reports |
| Review / AggregateRating | Powers review stars and comparison data | Product/service reviews |
| ItemList | Powers list-based rich results | Best-of pages, ranked lists |
| BreadcrumbList | Shows content hierarchy in search results | All pages |
| Organization | Entity recognition for author/publisher | Homepage |
| Person | Author credentials and entity linking | Author pages |

### FAQPage Schema for AEO

FAQPage schema directly increases eligibility for both FAQ rich results and PAA positions. Implement on any page that contains Q&A content.

**Key rules:**
- Only mark up Q&A content that is actually visible on the page
- Each question must have a complete answer
- Do not use FAQPage for a single question -- use it for 3+ questions
- Google may stop showing FAQ rich results for some site types (they reduced display in late 2023 for many commercial sites) but the schema still helps AI systems parse content

### HowTo Schema for AEO

HowTo schema is particularly valuable for step-by-step content. It enables how-to rich results with step previews directly in search results.

**Key rules:**
- Each step must have a name and description
- Include estimated time and tools/materials if applicable
- Steps must be in the correct order
- Images for individual steps increase rich result visual appeal

---

## Voice Search Optimization

Voice search queries tend to be longer, more conversational, and question-formatted. Optimizing for voice search aligns closely with AEO best practices.

### Voice Search Query Characteristics

| Characteristic | Text Search | Voice Search |
|---------------|-------------|--------------|
| Average length | 2-4 words | 6-10 words |
| Format | Keywords | Full questions/sentences |
| Intent | Mixed | Heavily informational |
| Local component | Sometimes | Frequently ("near me") |
| Conversational | Rarely | Almost always |

### Voice Search Optimization Tactics

1. **Target question keywords** -- "How do I...", "What is the best...", "Where can I find..."
2. **Write conversational answers** -- Match the natural language of voice queries
3. **Optimize for featured snippets** -- Voice assistants read snippet content as answers
4. **Target long-tail keywords** -- Voice queries are longer and more specific
5. **Optimize for local** -- Many voice searches have local intent
6. **Keep answers concise** -- Voice assistants prefer 29-word average answers
7. **Use natural language** -- Write how people speak, not how they type
8. **Implement speakable schema** -- Helps voice assistants identify content to read aloud

### Speakable Schema

The Speakable schema type identifies sections of content that are best suited for text-to-speech playback by voice assistants.

```json
{
  "@type": "WebPage",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [".article-summary", ".key-answer"]
  }
}
```

---

## SERP Feature Prioritization for AEO

### Feature Priority by Content Type

| Content Type | Primary AEO Target | Secondary Target | Effort Level |
|-------------|-------------------|-----------------|-------------|
| How-to guides | Featured Snippet (list) | AI Overview citation | Medium |
| Comparison pages | Featured Snippet (table) | AI Overview citation | Medium |
| Definition content | Featured Snippet (paragraph) | PAA answers | Low |
| FAQ pages | PAA positions | FAQ rich results | Low |
| Product reviews | Review stars rich result | AI Overview citation | Medium |
| Best-of lists | Featured Snippet (list) | Shopping rich results | Medium |
| Local service pages | Local Pack | Knowledge Panel | Medium-High |

### AEO Impact Assessment

| SERP Feature | Traffic Impact | AEO Relevance | Win Difficulty |
|-------------|---------------|---------------|---------------|
| Featured Snippet | Very High | Core AEO target | Medium |
| AI Overview Citation | High (growing) | Core AEO target | Medium-High |
| People Also Ask | Medium-High | High -- multiple positions possible | Low-Medium |
| FAQ Rich Result | Medium | High -- direct answer display | Low |
| Video Featured Snippet | High | Medium -- requires video | High |
| Review Stars | Medium-High | Medium -- trust signal | Low-Medium |
| Knowledge Panel | Medium | Medium -- entity/brand queries | High (long-term) |

---

## AEO Content Audit Checklist

Use this checklist to audit any page for answer engine readiness.

### Structure and Format
- [ ] H1 includes or closely matches the primary target query
- [ ] H2/H3 headings use question format matching PAA and voice queries
- [ ] Direct answer appears in first 60 words of each section
- [ ] Content includes at least 1 comparison table
- [ ] Content includes at least 1 numbered or bulleted list
- [ ] FAQ section with 5-10 questions at the end of the article
- [ ] Table of contents with anchor links for long content

### Snippet Eligibility
- [ ] Paragraph answer blocks are 40-60 words (snippet length)
- [ ] List items use proper HTML list tags (ol/ul)
- [ ] Tables use proper HTML table tags with thead/tbody
- [ ] Each snippet-targeted section has the question as the heading

### AI Citation Readiness
- [ ] Self-contained answer blocks in 134-167 word range
- [ ] Specific data points with sources in every section
- [ ] Declarative language (no excessive hedging)
- [ ] Schema markup matches content type (FAQPage, HowTo, Article)
- [ ] Content can be extracted and understood without surrounding context

### Voice Search Readiness
- [ ] Conversational question headings (How, What, Why, Where, When)
- [ ] Concise answers (target 29-word average for voice)
- [ ] Natural language that matches how people speak
- [ ] Local information included if relevant
- [ ] Speakable schema implemented on key answer sections

### Technical Foundation
- [ ] Page loads in under 3 seconds
- [ ] Mobile-responsive layout
- [ ] Server-side rendered content (not JavaScript-only)
- [ ] AI crawlers allowed in robots.txt
- [ ] Schema markup validates in Google Rich Results Test
- [ ] No duplicate content issues

---

## Quick Wins for B2B Sourcing Content

### Immediate AEO Improvements

1. **Add question-format H2 headings** -- Convert "Supplier Qualification Process" to "How Do You Qualify a New Supplier?"
2. **Front-load answers** -- Move conclusions from the end of sections to the beginning
3. **Add a comparison table** -- Create tables comparing sourcing options, pricing tiers, or supplier criteria
4. **Implement FAQ schema** -- Add FAQPage markup to any page with Q&A content
5. **Write 40-60 word answer blocks** -- For each H2, write a concise answer paragraph that could stand alone as a snippet

### High-Impact AEO Strategies

1. **Create original data content** -- Survey your customers, analyze your transaction data, publish original benchmarks
2. **Build comprehensive comparison pages** -- "[Product A] vs [Product B]" with structured tables and clear recommendations
3. **Develop process guides** -- Step-by-step sourcing guides with HowTo schema
4. **Mine PAA questions** -- Search your target keywords and create content answering every PAA question
5. **Optimize for voice** -- B2B buyers increasingly use voice search; target conversational long-tail queries
