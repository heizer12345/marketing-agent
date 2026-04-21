# Sourcy Marketing Benchmarks

**Use these canonical benchmarks in reports. NEVER invent benchmark numbers — always cite this file.**
These are B2B SaaS / marketplace industry benchmarks relevant to Sourcy's target markets (SEA + LatAm).
Last updated: 2026-04-21. Sources: HubSpot B2B Report 2025, WordStream Industry Benchmarks 2025, Databox SaaS Benchmarks, First Page Sage.

---

## Website Performance

| Metric | Good | OK | Needs Work | Source |
|---|---|---|---|---|
| Bounce Rate (all traffic) | < 50% | 50–65% | > 65% | Google Analytics benchmarks |
| Bounce Rate (paid traffic) | < 70% | 70–85% | > 85% | WordStream |
| Avg Session Duration | > 2:30 | 1:30–2:30 | < 1:30 | GA4 industry avg |
| Pages/Session | > 3.0 | 2.0–3.0 | < 2.0 | GA4 industry avg |
| Engagement Rate (GA4) | > 55% | 40–55% | < 40% | Google Analytics |
| New User Rate | 40–60% | 30–40% / 60–70% | < 30% or > 70% | GA4 benchmarks |

---

## Paid Acquisition (Google Ads — B2B SaaS)

| Metric | Good | OK | Needs Work | Source |
|---|---|---|---|---|
| Click-Through Rate (CTR) | > 5% | 2–5% | < 2% | WordStream B2B avg 2.55% |
| Cost per Click (CPC) | < $2 | $2–$5 | > $5 | WordStream SEA markets |
| Conversion Rate (CVR) | > 5% | 2–5% | < 2% | WordStream B2B avg 3.75% |
| Cost per Lead (CPL) | < $25 | $25–$60 | > $60 | HubSpot B2B 2025 |
| Quality Score | 7–10 | 5–7 | < 5 | Google Ads |
| Impression Share (top keywords) | > 60% | 30–60% | < 30% | Google Ads |

---

## Paid Acquisition (Meta Ads — B2B / Marketplace)

| Metric | Good | OK | Needs Work | Source |
|---|---|---|---|---|
| Click-Through Rate (CTR) | > 1.5% | 0.8–1.5% | < 0.8% | WordStream Meta B2B avg 1.11% |
| Cost per Click (CPC) | < $0.80 | $0.80–$2.00 | > $2.00 | WordStream SEA avg |
| Cost per Lead (CPL) | < $20 | $20–$50 | > $50 | Meta B2B Benchmarks 2025 |
| Frequency | < 2.5 | 2.5–3.5 | > 3.5 (creative fatigue) | Meta Business |
| Relevance Score / Quality Ranking | Above Average | Average | Below Average | Meta Ads Manager |
| Video 3-Second View Rate | > 30% | 15–30% | < 15% | Meta Creative Hub |

---

## SEO & Organic Search

| Metric | Good | OK | Needs Work | Source |
|---|---|---|---|---|
| Branded CTR (Search Console) | > 25% | 15–25% | < 15% | Google Search Console |
| Non-Branded CTR | > 3% | 1.5–3% | < 1.5% | First Page Sage 2025 |
| Position 1–3 Share (target keywords) | > 30% | 15–30% | < 15% | SEMrush |
| Domain Authority (Ahrefs DR) | > 40 | 25–40 | < 25 | Ahrefs |
| Organic Traffic Growth MoM | > 10% | 3–10% | < 3% | Industry avg |
| Blog Conversion Rate | > 2% | 0.5–2% | < 0.5% | HubSpot 2025 |
| Core Web Vitals (LCP) | < 2.5s | 2.5–4s | > 4s | Google PageSpeed |
| Core Web Vitals (CLS) | < 0.1 | 0.1–0.25 | > 0.25 | Google PageSpeed |

---

## Conversion & Funnel

| Metric | Good | OK | Needs Work | Source |
|---|---|---|---|---|
| Landing Page CVR (B2B) | > 5% | 2–5% | < 2% | Unbounce 2025 |
| Lead-to-SQL Rate | > 20% | 10–20% | < 10% | HubSpot B2B |
| Trial/Signup Activation Rate | > 40% | 20–40% | < 20% | Mixpanel SaaS avg |
| Visitor-to-Lead (overall) | > 2% | 0.5–2% | < 0.5% | HubSpot B2B 2025 |
| Email Open Rate (nurture) | > 25% | 15–25% | < 15% | Mailchimp B2B |
| Email CTR (nurture) | > 3.5% | 1.5–3.5% | < 1.5% | Campaign Monitor |

---

## Social Media (Instagram — B2B)

| Metric | Good | OK | Needs Work | Source |
|---|---|---|---|---|
| Engagement Rate (likes+comments/reach) | > 3% | 1–3% | < 1% | Hootsuite B2B 2025 |
| Reach Rate (followers) | > 20% | 10–20% | < 10% | Hootsuite |
| Reel Play Rate | > 25% | 10–25% | < 10% | Meta |
| Story Completion Rate | > 70% | 50–70% | < 50% | Later.com |
| Profile Visit → Follow Rate | > 5% | 2–5% | < 2% | Hootsuite |

---

## Sourcy-Specific Targets (internal)

| Metric | Target | Context |
|---|---|---|
| CPL (all paid) | < $25 | Based on LTV model |
| Target Market Sessions (9 countries) | > 80% of total | Non-target = waste |
| Paid Bounce Rate | < 70% | Above 85% = immediate fix needed |
| Organic Branded Share | < 30% of total organic | High branded = over-reliance on brand |
| Activation Rate (Sourcy DB signups → active) | > 35% | SaaS activation benchmark |
| Lead Response Time | < 4h | B2B conversion rate drops 80% after 5h |

---

## How to Use These Benchmarks in Reports

1. **KPI cards**: Use `benchmark` parameter with the relevant benchmark from this table.
   Example: `benchmark="Target <60% (B2B avg 65%)"` for bounce rate.

2. **Decision tables**: Use benchmarks to classify Observation as on-track/off-track.

3. **Never invent benchmarks** — if a benchmark is not in this file, say "No established benchmark — monitor trend direction instead."

4. **Sourcy context**: Always prefer the Sourcy-specific targets over industry averages where available.

5. **Acknowledge limitations**: These are B2B SaaS averages. Sourcy is a marketplace in SEA/LatAm — actual benchmarks may differ. Flag outliers.
