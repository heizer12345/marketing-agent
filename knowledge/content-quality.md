# Content Quality -- Domain Knowledge Reference

Comprehensive reference for content quality scoring, AI writing detection, and recursive improvement protocols. Covers the expert panel scoring rubric, 24 AI writing detection patterns with examples, the recursive improvement loop, and content quality gates.

---

## Expert Panel Scoring Rubric

Content is scored on 4 dimensions, each worth 0-25 points, for a total of 0-100. The target score for publication-ready content is 90/100. Content below 90 enters a recursive improvement loop (max 3 rounds).

### Dimension 1: Hook Power (0-25)

Does the opening make it impossible to stop reading?

| Score Range | Description | Characteristics |
|-------------|-------------|-----------------|
| 0-5 | Generic, no reason to keep reading | Opens with a definition, truism, or "In today's world..." |
| 6-15 | Interesting but not urgent | Has a topic but no tension, curiosity gap, or stakes |
| 16-20 | Strong curiosity gap or contrarian claim | Opens with a surprising fact, bold claim, or specific story |
| 21-25 | Impossible to scroll past | Specific, surprising, personal; combines data with narrative tension |

**What makes a 21-25 hook:**
- Starts with a specific, unexpected data point
- Creates a curiosity gap the reader must resolve
- Uses first-person or second-person perspective
- Combines personal experience with broader implications
- Makes a contrarian claim backed by evidence

**B2B sourcing hook examples:**

- Score 5: "Finding the right supplier is important for your business."
- Score 15: "Most businesses waste months on supplier qualification. Here is a better approach."
- Score 23: "We rejected 47 factories before finding the one that cut our defect rate from 12% to 0.3%. The deciding factor was not what you would expect."

### Dimension 2: Voice Authenticity (0-25)

Does this sound like a real person wrote it?

| Score Range | Description | Characteristics |
|-------------|-------------|-----------------|
| 0-5 | Obviously AI-generated | Banned vocabulary, generic structure, no personality |
| 6-15 | Corporate but human | Clean writing but lacks edge, humor, or personal voice |
| 16-20 | Distinct voice emerging | Has opinions, specific examples, some personality |
| 21-25 | Unmistakably human | Strong personality, varied rhythm, specific details, acknowledges uncertainty |

**What to check:**
- Short punchy sentences mixed with longer ones? (Varied rhythm)
- Specific numbers and names instead of vague claims?
- Personal framing ("I found..." / "We tested...")?
- No corporate jargon or filler words?
- Contrarian takes backed by data?
- Humor, edge, or personality present?
- Acknowledges uncertainty or mixed feelings?

**Voice authenticity signals (positive):**
- Opinions stated directly: "This approach is wrong. Here is why."
- Specific details: "We tested 8 factories over 14 weeks"
- Simple verbs: "is", "has", "does" instead of "serves as", "represents"
- Humor or self-deprecation: "I wish I had known this before losing $40K"
- Acknowledging limits: "This worked for us, but may not work for everyone"

### Dimension 3: Value Density (0-25)

Does every sentence earn its place?

| Score Range | Description | Characteristics |
|-------------|-------------|-----------------|
| 0-5 | Mostly filler | Repeats known information, no specific data |
| 6-15 | Some value but padded | Good insights buried in unnecessary context |
| 16-20 | Consistently valuable | Most sentences add information; some redundancy |
| 21-25 | Every sentence earns its place | Specific data points, actionable insights, zero filler |

**What to check:**
- Every sentence adds new information (not restating what was said)
- Specific data points present, not vague claims
- Actionable insights the reader can use immediately
- Reader should think "I learned something I can use today"
- No throat-clearing introductions or filler paragraphs

**Value density test:** Read each paragraph and ask "If I deleted this, would the reader miss anything?" If no, cut it.

### Dimension 4: Engagement Potential (0-25)

Would someone share, reply, or take action after reading this?

| Score Range | Description | Characteristics |
|-------------|-------------|-----------------|
| 0-5 | No engagement triggers | Reads like a textbook; no reason to share |
| 6-15 | Mildly shareable | Useful but not remarkable enough to share |
| 16-20 | Would share with a colleague | Contains a surprising insight or useful framework |
| 21-25 | Would share publicly and comment | Sparks debate, provides unique value, demands response |

**What to check:**
- Would someone share or repost this?
- Does the CTA invite genuine response (not generic "contact us")?
- Does it spark debate or strong agreement?
- Platform-native formatting (if for social)?
- Does it contain a "quotable moment" someone would screenshot?

---

## The 24 AI Writing Detection Patterns

These patterns indicate AI-generated content. Each pattern has a point penalty. Start at 100 and deduct for each pattern detected. Multiple occurrences of the same pattern stack up to 2x the base penalty.

### Scoring Scale

| Score | Rating | Action |
|-------|--------|--------|
| 90-100 | Human-sounding, clean | Ready for publication |
| 70-89 | Minor AI tells, quick fixes needed | Light editing pass |
| 50-69 | Obvious AI patterns, significant rewrite needed | Major revision |
| 0-49 | Reads like raw ChatGPT output | Full rewrite |

### Banned Vocabulary (instant -5 per occurrence)

Any occurrence of these words triggers an automatic 5-point deduction:

delve, tapestry, landscape (abstract use), leverage, multifaceted, nuanced, pivotal, realm, robust, seamless, testament, transformative, underscore (verb), utilize, whilst, keen, embark, comprehensive, intricate, commendable, meticulous, paramount, groundbreaking, innovative, cutting-edge, synergy, holistic, paradigm, ecosystem, Additionally, align with, crucial, enduring, enhance, fostering, garner, highlight (verb), interplay, intricacies, showcase, vibrant, valuable, profound, renowned, breathtaking, nestled, stunning

### Content Patterns (6 patterns)

**Pattern 1: Significance Inflation (-10)**

Puffing up importance with grandiose language.

Trigger phrases: "stands as", "is a testament", "pivotal moment", "underscores its importance", "reflects broader", "setting the stage for", "indelible mark", "deeply rooted"

- Before: "This initiative marked a pivotal moment in the evolution of supply chain management."
- After: "The company launched its first automated QC process in 2024."

**Pattern 2: Undue Notability Claims (-5)**

Listing achievements without context or evidence.

Trigger phrases: "Active social media presence", "leading expert", "has been featured in"

- Before: "His insights have been featured in Forbes, Inc, and Entrepreneur."
- After: "In a 2024 Forbes interview, he argued most sourcing budgets are wasted on the wrong suppliers."

**Pattern 3: Superficial -ing Analyses (-8)**

Tacking "-ing" phrases for fake depth.

Trigger phrases: "highlighting", "underscoring", "emphasizing", "ensuring", "reflecting", "symbolizing", "contributing to", "fostering", "showcasing"

- Before: "The platform grew 40% YoY, showcasing the team's commitment to innovation and highlighting the importance of supplier diversity."
- After: "The platform grew 40% YoY. Most of that came from a referral loop they built in Q2."

**Pattern 4: Promotional Language (-8)**

Trigger phrases: "boasts a", "vibrant", "rich" (figurative), "profound", "exemplifies", "commitment to", "natural beauty", "nestled", "in the heart of", "must-visit"

- Before: "The company boasts a vibrant team with a profound commitment to delivering groundbreaking sourcing solutions."
- After: "The company has 45 employees. Their sourcing platform processes 2,000 orders per month."

**Pattern 5: Vague Attributions (-8)**

No specific citations for factual claims.

Trigger phrases: "Industry reports", "Experts argue", "Some critics argue", "several sources"

- Before: "Experts believe AI will transform the sourcing landscape."
- After: "A 2024 McKinsey survey found 67% of procurement leaders plan to increase AI spend for supplier evaluation next year."

**Pattern 6: Formulaic "Challenges and Future" Sections (-10)**

Trigger phrases: "Despite its X, faces challenges...", "Despite these challenges, continues to Y", "Future Outlook"

- Before: "Despite these challenges, the company continues to thrive as a leader in the sourcing space."
- After: "Supplier churn hit 15% in Q3. They hired a dedicated account management team in October."

### Language and Grammar Patterns (6 patterns)

**Pattern 7: AI Vocabulary Clustering (-10)**

Multiple banned words appearing in the same paragraph.

- Before: "Additionally, this innovative approach showcases the intricate interplay between technology and sourcing, highlighting its crucial role in the evolving landscape."
- After: "The tool saves about 3 hours per week on supplier evaluation. That is it."

**Pattern 8: Copula Avoidance (-5)**

Using elaborate substitutes for simple "is/are/has."

Trigger phrases: "serves as", "stands as", "marks", "represents", "boasts", "features", "offers"

- Before: "The platform serves as a valuable resource for procurement teams."
- After: "The platform is a resource for procurement teams. 500 companies use it weekly."

**Pattern 9: Negative Parallelisms (-5)**

Trigger phrases: "Not only...but...", "It's not just about X, it's Y", "It's not merely X, it's Y"

- Before: "It's not just about finding suppliers; it's about building lasting partnerships."
- After: "Good suppliers deliver on time. That is how you build a partnership."

**Pattern 10: Rule of Three Overuse (-8)**

Forcing ideas into groups of three -- triple adjectives, triple nouns, triple parallel clauses.

- Before: "The platform offers speed, reliability, and transparency."
- After: "The platform is fast and reliable. Suppliers can see order status in real time."

**Pattern 11: Elegant Variation / Synonym Cycling (-5)**

Excessive synonym substitution to avoid repeating words.

- Before: "The CEO shared his vision. The business leader outlined the strategy. The company head detailed the plan."
- After: "The CEO shared his vision and outlined the strategy."

**Pattern 12: False Ranges (-5)**

"From X to Y" where X and Y are not on a meaningful scale.

- Before: "From supplier discovery to quality control, from logistics to payments, the sourcing landscape is shifting."
- After: "Supplier discovery, QC, and logistics are all changing. Here is what actually matters."

### Style Patterns (6 patterns)

**Pattern 13: Em Dash Overuse (-5)**

More than 1 em dash per 200 words. AI uses them for "punchy" sales writing.

**Pattern 14: Overuse of Boldface (-3)**

Mechanical bold emphasis on every key term rather than selective use.

**Pattern 15: Inline-Header Vertical Lists (-5)**

Lists where every item starts with a bolded header followed by a colon.

**Pattern 16: Title Case in Headings (-3)**

Capitalizing All Main Words In Every Heading instead of sentence case.

**Pattern 17: Emoji Decoration (-5)**

Emojis used on headings or bullet points (rocket, lightbulb, checkmark).

**Pattern 18: Curly Quotation Marks (-2)**

Using typographic curly quotes instead of straight quotes (minor tell).

### Communication Patterns (3 patterns)

**Pattern 19: Collaborative Artifacts (-10)**

Phrases that reveal AI assistant origin.

Trigger phrases: "I hope this helps", "Of course!", "Certainly!", "Would you like...", "let me know", "here is a..."

**Pattern 20: Knowledge-Cutoff Disclaimers (-10)**

Trigger phrases: "As of [date]", "While specific details are limited", "based on available information"

**Pattern 21: Sycophantic Tone (-8)**

Trigger phrases: "Great question!", "You're absolutely right!", "That's an excellent point!"

### Filler and Hedging Patterns (3 patterns)

**Pattern 22: Filler Phrases (-5 each)**

Replace with shorter alternatives:
- "In order to" --> "To"
- "Due to the fact that" --> "Because"
- "At this point in time" --> "Now"
- "It is important to note that" --> (just state the thing)
- "In today's digital landscape" --> (delete entirely)

**Pattern 23: Excessive Hedging (-8)**

Trigger phrases: "could potentially possibly", "might have some effect", "it could be argued that"

- Before: "It could potentially be argued that this approach might have some positive impact on supplier quality."
- After: "This approach improves supplier quality. Here is the data."

**Pattern 24: Generic Positive Conclusions (-10)**

Trigger phrases: "The future looks bright", "Exciting times lie ahead", "continues their journey toward excellence"

- Before: "The future looks bright for AI in sourcing. Exciting times lie ahead."
- After: "They plan to double their AI procurement budget next quarter. We will see if it pays off."

---

## Recursive Improvement Loop Protocol

When content scores below 90/100 across the expert panel, it enters a recursive improvement loop. Maximum 3 rounds.

### Loop Rules

1. **Target: 90/100 aggregate. Non-negotiable. Max 3 rounds.**
2. Each round: score all dimensions, identify top 3 weaknesses, revise, re-score
3. AI Writing Detector (humanizer) score is weighted 1.5x in the aggregate
4. Scores must be honest -- no padding to reach 90
5. After 3 rounds, if still below 90: return best version with honest score and note on what is holding it back
6. Show ALL rounds in output -- the iteration trail is part of the value

### Round Output Format

```
## Round [N] -- Score: [AVG]/100

| Expert | Score | Key Feedback |
|--------|-------|--------------|
| [Name] | [0-100] | [One-line rationale] |
| AI Writing Detector | [0-100] (1.5x weight) | [One-line rationale] |
| ... | ... | ... |

Aggregate: [weighted average]
Top 3 weaknesses: [ranked]
Changes made: [specific edits addressing each weakness]
```

### Expert Panel Assembly

For each piece of content, auto-assemble 7-10 experts:

1. **Content-type experts** -- Matching the format (blog, email, landing page, etc.)
2. **Domain/offer experts** -- Matching the industry (add 1-3 based on content topic)
3. **AI Writing Detector** -- Always included, weighted 1.5x. Non-negotiable.
4. **Brand Voice Match** -- Always included. Checks alignment with brand voice.
5. **Cap at 10 experts** -- Merge overlapping roles if over 10

**Domain expert examples for B2B sourcing:**
- Supply Chain Procurement Expert
- International Trade Compliance Expert
- Manufacturing Quality Expert
- B2B Content Marketing Expert

### Variant Comparison Mode

When scoring multiple content variants (A/B/C):
1. Score each variant independently through the full panel
2. Rank variants by aggregate score after scoring
3. If top variant is below 90, iterate on the best one only (do not iterate all variants)

---

## Content Quality Gates

### Gate 1: Pre-Draft Gate

Before writing, verify:
- [ ] Target audience clearly defined
- [ ] Primary keyword and intent identified
- [ ] Content type selected (blog, comparison, guide, etc.)
- [ ] Competitive content reviewed (what exists, what gaps remain)
- [ ] Unique angle or data identified (what makes this different)

### Gate 2: First Draft Gate

After first draft, check:
- [ ] Hook power assessment (does the opening grab attention?)
- [ ] AI writing pattern scan (run through 24-pattern checklist)
- [ ] Value density check (does every paragraph add something new?)
- [ ] Factual accuracy verification (all claims sourced?)
- [ ] Brand voice alignment (matches established tone?)

### Gate 3: Expert Panel Gate

Score through full expert panel. Minimum thresholds:
- [ ] Aggregate score >= 90/100
- [ ] No single dimension below 15/25
- [ ] AI Writing Detector score >= 80/100
- [ ] Zero banned vocabulary occurrences
- [ ] Zero Pattern 19-21 occurrences (collaborative artifacts, disclaimers, sycophancy)

### Gate 4: Publication Gate

Final checks before publish:
- [ ] All links verified and working
- [ ] Images have alt text and are optimized
- [ ] Schema markup validates in Rich Results Test
- [ ] Meta title and description optimized
- [ ] Internal links to related content included (3-5 per 1000 words)
- [ ] Publication and author metadata present

---

## What Good Human Writing Looks Like

Reference characteristics to aim for:

- **Opinions, not just reporting** -- Take a position and defend it
- **Varied sentence rhythm** -- Mix short punches with longer explanatory sentences
- **Specific details over vague claims** -- Names, dates, numbers, places
- **Simple verbs** -- "is", "has", "does" instead of "serves as", "represents"
- **Acknowledgment of uncertainty** -- "This worked for us, but..." instead of universal claims
- **First-person perspective** -- When appropriate, use "I" and "we"
- **Humor, edge, or personality** -- Something that could not have been written by anyone else
- **Concrete examples** -- With specific companies, products, numbers, and outcomes

### The Specificity Test

For each claim in the content, ask: "Could I make this more specific?"

- Vague: "Many companies struggle with supplier quality."
- Specific: "In our 2024 survey of 200 DTC brands, 68% reported at least one quality-related order rejection in the past year."

- Vague: "Communication is important when working with overseas suppliers."
- Specific: "We require suppliers to respond to messages within 4 hours during their business hours. The 3 factories that consistently met this SLA had 40% fewer order issues than those that did not."

### The Deletion Test

Read each paragraph and ask: "If I deleted this, would the reader lose something they need?" If no, delete it. Apply this aggressively to introductions, transitions, and conclusions -- these are where filler accumulates.

---

## Feedback-to-Source Protocol

When the expert panel scores content that came from another skill or process, generate a Source Improvement Brief:

```
## Feedback for [Source Skill/Process]

### What scored low
- [Pattern]: [Specific example from this content]

### Suggested improvements
- [Concrete change to the source process]

### Patterns to add
- [Any recurring weakness that should become a rule]
```

This creates a feedback loop where content quality insights flow back to improve the processes that generate content.

---

## Pattern Memory Protocol

### On Rejection (User Overrides Panel or Rejects 90+ Content)

1. Ask why (or infer from context)
2. Record a new pattern:

```
## [Pattern Name]
- Type: rejection | preference | override
- Content types: [which types this applies to]
- Rule: [What to always/never do]
- Example: [The specific instance that triggered this]
- Date: [YYYY-MM-DD]
- Point dock: [-N points when detected]
```

3. Apply pattern in all future scoring runs -- known-bad patterns are penalized before individual expert scoring begins

This means the panel gets smarter over time, learning from each approval and rejection.
