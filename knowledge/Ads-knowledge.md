# Google Ads Knowledge Base for Sourcy Global

## Campaign Structure Best Practices

### Account Hierarchy for Multi-Country B2B
- Separate campaigns per country (different budgets, bidding, languages, competition levels)
- Within each country campaign, separate ad groups by intent tier:
  - Brand campaigns (lowest CPC, highest conversion rate; protect brand terms)
  - Competitor campaigns (target competitor names; higher CPC, moderate conversion)
  - Category campaigns (product/industry keywords; medium CPC, high volume)
  - Long-tail campaigns (specific queries like "ISO certified textile supplier Indonesia"; lower CPC, high intent)
- Use campaign-level geographic targeting; never mix countries in one campaign
- Separate Search and Display/Performance Max; never combine network types

### Ad Group Structure
- 5-15 tightly themed keywords per ad group (single keyword theme ideal for high-spend groups)
- 3 responsive search ads per ad group minimum
- At least 2 sitelink extensions, 2 callout extensions, 1 structured snippet per campaign
- For Sourcy: pin primary value prop ("Compare Verified Suppliers") in headline position 1

## Bidding Strategies

### When to Use Each Strategy
- **Manual CPC**: Only during initial testing phase (first 2 weeks) when no conversion data exists
- **Maximize Clicks**: Learning phase for new campaigns; use with a max CPC cap to prevent overspending
- **Target CPA (tCPA)**: Once you have 30+ conversions in 30 days; set target at 10-20% above current CPA initially
- **Target ROAS (tROAS)**: Not typical for B2B lead gen; use only if revenue values are assigned to lead types
- **Maximize Conversions**: Good middle ground when conversion volume is 15-30/month; lets algorithm optimize
- **Maximize Conversion Value**: Use when different lead types have different values (RFQ > email signup)

### Bidding Strategy Transition Path
1. Start: Manual CPC or Maximize Clicks (2-4 weeks, gather data)
2. Mid: Maximize Conversions (once 15+ conversions/month)
3. Mature: Target CPA (once 30+ conversions/month and stable CPA)
- Never switch strategies during seasonal fluctuations or after major landing page changes
- Allow 2-week learning period after any bidding strategy change; don't panic-adjust

## Quality Score Components

### The Three Pillars (Each Rated: Below Average / Average / Above Average)
- **Expected CTR**: Predicted click-through rate based on keyword-ad relevance
  - Fix: Improve ad copy relevance, use keyword in headlines, test new angles
- **Ad Relevance**: How closely the ad matches the keyword intent
  - Fix: Tighten ad group themes, ensure keywords appear in ad headlines/descriptions
- **Landing Page Experience**: Quality and relevance of the landing page
  - Fix: Match landing page content to ad promise, improve page speed, mobile optimization

### Quality Score Impact on CPC
- QS 7+: You pay 15-30% less per click than competitors
- QS 5-6: You pay roughly market rate
- QS 3-4: You pay 25-50% more per click (fix urgently or pause)
- QS 1-2: Pause these keywords immediately; they drain budget
- B2B landing pages often score lower because of thin content; add supplier counts, category depth, trust signals

## B2B Google Ads Specifics

### Lead Generation Focus
- Primary conversion actions: RFQ submission, supplier contact form, demo request
- Secondary conversion actions: email signup, account creation, resource download
- Assign conversion values: RFQ = $50, Contact form = $20, Email signup = $5 (adjust based on close rates)
- Use offline conversion import: feed CRM data back into Google Ads to optimize for qualified leads, not just form fills
- Lead quality matters more than volume; track cost per qualified lead, not just cost per conversion

### B2B-Specific Ad Copy Patterns That Work
- Headline formulas: "Find Verified [Product] Suppliers" / "Compare [X]+ [Product] Manufacturers" / "Get Quotes in 48 Hours"
- Description: Include specific numbers (supplier count, country count, response time)
- CTAs: "Get Free Quotes", "Compare Suppliers Now", "Start Sourcing Today"
- Avoid: Generic "Learn More", "Click Here"; B2B buyers respond to specificity
- Use countdown timers for trade show seasons or limited promotions

### Audience Targeting for B2B
- In-market audiences: "Business Services", "Industrial & Manufacturing", "Import & Export"
- Custom intent audiences: Build from competitor URLs and industry search terms
- LinkedIn profile targeting (via Google Ads): Target by company size, industry, job title
- Remarketing lists: Segment by funnel stage (visited category page, started RFQ, completed RFQ)
- Exclude existing customers from acquisition campaigns

## Negative Keyword Management

### Essential Negative Keywords for Sourcy
- Job-related: "jobs", "careers", "salary", "hiring", "internship", "vacancy"
- Educational: "course", "degree", "certification program", "training"
- DIY/Consumer: "DIY", "homemade", "small quantity", "single unit", "retail"
- Free/Cheap: "free", "cheap" (context-dependent; "cheap manufacturer" might be valid intent)
- Irrelevant countries: Add countries Sourcy doesn't serve
- Competitor negative strategy: Exclude "login", "support", "complaints" for competitor campaigns

### Negative Keyword Review Process
- Review search terms report weekly for first 3 months, then bi-weekly
- Add negatives at ad group level for specificity, campaign level for broad exclusions
- Create a shared negative keyword list across campaigns for universal exclusions
- Flag search terms with >10 impressions and 0 clicks as potential negatives
- Watch for query drift: broad match keywords often match irrelevant queries over time

## Geographic and Language Targeting

### Country-Specific Settings
| Market | Language | Currency | Search Engine Notes |
|--------|----------|----------|-------------------|
| Indonesia | Bahasa Indonesia + English | IDR | Low CPC ($0.15-0.50 avg); high mobile % |
| Philippines | English + Filipino | PHP | Low CPC ($0.20-0.60 avg); English ads work |
| Thailand | Thai + English | THB | Moderate CPC ($0.30-0.80 avg); Thai language ads essential |
| Brazil | Portuguese (BR) | BRL | Moderate CPC ($0.25-0.70 avg); Portuguese mandatory |
| Mexico | Spanish (MX) | MXN | Moderate CPC ($0.20-0.60 avg); nearshoring terms expensive |
| US | English | USD | High CPC ($1.50-5.00 avg for sourcing); most competitive |

### Multi-Country Optimization
- US will consume budget fastest if not capped; set daily budgets per country campaign
- SEA markets offer lower CPC but longer conversion paths; adjust CPA targets accordingly
- Time-of-day bidding: target business hours in each country's timezone
- For US campaigns targeting buyers sourcing from other countries, use English ads with country-specific keywords

## Budget Allocation Framework

### Allocation by Market Maturity
- New market (0-3 months): 70% Search, 20% Display/Remarketing, 10% Brand
- Growing market (3-12 months): 60% Search, 25% Remarketing, 15% Brand
- Mature market (12+ months): 50% Search, 20% Remarketing, 15% Brand, 15% Expansion/Testing

### Allocation Across Countries (Starting Framework)
- Allocate based on: Market size x CPC efficiency x Conversion rate x Strategic priority
- US: 30-40% of total budget (highest CPC but highest deal values)
- Brazil: 15-20% (large market, moderate competition)
- Indonesia: 15-20% (large market, low CPC, high volume potential)
- Mexico: 10-15% (nearshoring trend creates opportunity)
- Philippines: 5-10% (smaller market, English-friendly)
- Thailand: 5-10% (moderate size, requires Thai language investment)
- Rebalance monthly based on cost per qualified lead, not just CPA

### Budget Efficiency Signals
- If a campaign consistently hits daily budget before 2pm local time, increase budget or tighten targeting
- If spend is <60% of daily budget, expand keywords or loosen match types
- Impression share <50% on high-converting keywords = budget or bid too low
- ROAS declining month-over-month = audience fatigue or increased competition; refresh creative

---

## Meta Ads Diagnostics Checklist

### Full Ad Chain Diagnostic (use for every Meta Ads issue)

#### 1. Targeting Layer
- **Symptom**: High spend in non-target countries (IN, DZ, VE, PK, NG)
- **Diagnosis**: Call `get_meta_adset_targeting` → check `geo_locations.countries` per ad set
- **Fix (Manual)**: Meta Ads Manager > Ad Set > Edit > Audience > Locations > Remove countries
- **Fix (API)**: Not yet available (requires write access)
- **Reference**: https://www.facebook.com/business/help/202297959811696

#### 2. Audience Layer
- **Symptom**: Low CTR (<0.5%), broad reach, low conversion rate
- **Diagnosis**: Call `get_meta_audience_overlap` → check if custom/lookalike audiences exist
- **Fix**: Create custom audience from website visitors (Meta Pixel); test lookalike audience
- **Reference**: https://www.facebook.com/business/help/717368264947302

#### 3. Interest/Keyword Layer
- **Symptom**: Irrelevant traffic, wrong user intent
- **Diagnosis**: Check `flexible_spec.interests` from targeting data
- **Fix**: Replace broad interests with B2B-specific interests (manufacturing, import/export, supply chain)

#### 4. Creative Layer
- **Symptom**: Low CTR, high frequency + declining CTR over time (creative fatigue)
- **Diagnosis**: Call `get_meta_ad_creatives` → review headlines, body, images
- **Common issues**: Generic stock photos, headline doesn't match Sourcy value props
- **Fix**: Refresh creative every 2-4 weeks; use product/platform screenshots; lead with speed ("quotes in 3 hours")
- **Reference**: https://www.facebook.com/business/help/1802417986679657

#### 5. Landing Page Layer
- **Symptom**: High bounce rate (>75%) on traffic from Meta Ads in GA4
- **Diagnosis**: Cross-reference Meta ad `link_url` with GA4 landing page bounce rates
- **Common issues**: Ad promises X, landing page shows Y; mobile load time >3s
- **Fix**: Align ad creative with landing page content; test specific landing pages per campaign

#### 6. Budget Layer
- **Symptom**: Non-target countries consuming >20% of budget
- **Diagnosis**: Call `get_meta_spend_by_country` → check `wasted_spend_non_target`
- **Fix**: Exclude non-target countries from ad sets; set per-country budget caps

### Meta Ads API Capabilities
| Action | API Available? | Notes |
|--------|---------------|-------|
| Read campaigns/ad sets/ads | ✅ Yes | Full read access with our token |
| Read targeting configuration | ✅ Yes | Countries, demographics, interests, audiences |
| Read performance by breakdown | ✅ Yes | Country, age, gender, device, platform |
| Read ad creatives + images | ✅ Yes | Headlines, body, image_url, CTAs |
| Modify targeting | ❌ Not yet | Requires write access approval |
| Pause/enable campaigns | ❌ Not yet | Requires write access approval |
| Create new ads | ❌ Not yet | Requires write access approval |

### Platform Reference Links
- Meta Ads Manager: https://business.facebook.com/adsmanager/manage/campaigns
- Meta Ad Set Editor: https://business.facebook.com/adsmanager/manage/adsets
- Meta Business Settings: https://business.facebook.com/settings/
- Meta Events Manager: https://business.facebook.com/events_manager2/
- Meta Pixel Setup: https://www.facebook.com/business/help/952192354843755

---

## Diagnostic Decision Trees (Root Cause Analysis)

### High Bounce Rate on Paid Traffic (>75%)
1. Check landing page load speed — if >3s on mobile = **speed issue**
2. Check ad creative headline vs landing page H1 — if mismatch = **message issue**
3. Check audience targeting breadth — if broad interests only, no custom audiences = **intent issue**
4. Check device breakdown — if mobile-heavy traffic hitting desktop-optimized page = **UX issue**
5. Check geo targeting — if non-target countries present = **targeting issue**
6. Check ad destination URL vs actual landing — if WhatsApp CTA but website landing = **routing issue**

### Declining CTR Over Time (>20% drop in 2 weeks)
1. Check frequency — if >3.0 = **creative fatigue** (refresh creative)
2. Check competitor ad activity via SEMrush — if new entrants = **competition pressure**
3. Check audience size vs impressions — if saturated = **audience exhaustion**
4. Check seasonal factors — Q3 slowdown in Western markets, holidays

### Zero Conversions Tracked
1. FIRST: Verify tracking is working (Meta Pixel, CAPI, GA4 events fire in debug mode)
2. If tracking works: Check funnel — are users reaching the conversion page at all?
3. If users reach page: Check form/CTA — is it visible? Does it work on mobile?
4. If form works: Check whether conversion is defined correctly in platform
5. If all above OK: It may be genuine low conversion — check offer relevance and traffic quality

### High CPC (>$2 for B2B sourcing)
1. Check Quality Score / Relevance Score — low score = ad/LP mismatch
2. Check competition — are competitors bidding aggressively?
3. Check keyword/interest breadth — too narrow = limited auction = high price
4. Check bid strategy — manual vs auto — is the algorithm over-bidding?

### Non-Target Country Traffic (>10% from outside target markets)
1. Check ad platform geo targeting settings — are exclusions set?
2. Check if "Advantage Audience" or "Audience Expansion" is enabled (auto-expands geo)
3. Check if location setting is "people IN location" vs "people INTERESTED IN location"
4. Check organic traffic separately — non-target may be organic, not paid
5. Reference: https://support.google.com/google-ads/answer/1722038
