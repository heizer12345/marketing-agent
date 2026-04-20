# Analytics Knowledge Base for Sourcy Global

## GA4 Metric Interpretation for B2B

### Key Metrics and Benchmarks (B2B SaaS / Marketplace)
- **Engagement Rate**: 55-70% is healthy for B2B; below 45% signals content-audience mismatch
- **Average Engagement Time**: 1:30-3:00 min for blog content; 2:00-5:00 min for product/category pages
- **Sessions per User**: 1.5-3.0 for B2B (buyers research across multiple sessions before converting)
- **Conversion Rate (session-based)**: 1-3% for lead gen forms; 0.5-1.5% for RFQ submissions; 5-15% for email signups
- **Pages per Session**: 2.5-4.0 is healthy; below 2.0 suggests poor internal linking or irrelevant traffic
- **New vs Returning Users**: Healthy B2B mix is 60-70% new / 30-40% returning; high returning % indicates brand strength

### Bounce Rate vs Engagement Rate in GA4
- GA4 does NOT use traditional bounce rate; it uses "Engagement Rate" (inverse of bounce)
- An "engaged session" = lasted >10 seconds, OR had a conversion event, OR had 2+ page views
- Bounce rate in GA4 = % of sessions that were NOT engaged (opposite of engagement rate)
- Blog posts: 60-70% engagement rate normal (some users read and leave satisfied)
- Landing pages: aim for 70%+ engagement rate
- Category/listing pages: 65-80% engagement rate expected (users browse, filter, click suppliers)
- If engagement rate is below 40% on any page type, investigate: wrong traffic source, slow load, content mismatch

### Red Flag Patterns
- High traffic + low engagement = SEO attracting wrong audience or clickbait titles
- High engagement + low conversion = content is good but CTA/UX/form is the problem
- Sudden drop in engagement rate = technical issue (broken page, slow load, JS error)
- Returning users with zero conversions = nurture content is failing or conversion friction is too high
- Single-page sessions with high time-on-page = user found answer without exploring further (okay for blog, bad for product pages)

## Traffic Pattern Analysis

### Daily and Weekly Patterns (B2B Norms)
- B2B traffic peaks: Tuesday-Thursday, 9am-12pm and 2pm-5pm local time
- Monday is typically lower (planning/meetings); Friday drops 15-25% vs midweek
- Weekend traffic drops 40-60% for B2B; if weekends are strong, you have consumer traffic mixed in
- If traffic doesn't follow B2B patterns, the audience targeting or content may be attracting wrong segments

### Seasonal Patterns for Sourcing
- Q1 (Jan-Mar): Spike in sourcing activity as annual budgets are allocated; highest intent period
- Q2 (Apr-Jun): Steady sourcing; pre-production for Q4 consumer goods
- Q3 (Jul-Sep): Moderate; some slowdown in Aug (summer in US/EU, holidays in SEA)
- Q4 (Oct-Dec): Mixed; US/EU slows for holidays but some markets push Q1 procurement
- Trade show seasons create temporary spikes: Canton Fair (April/October), ASEAN trade events
- Ramadan (Indonesia): B2B activity dips 20-30% during the month; plan campaigns around it

### Anomaly Detection
- Traffic drop >15% WoW without a known cause = investigate immediately (indexing issue, tracking break, site outage)
- Traffic spike >30% from a single source = check for bot traffic or viral content (verify with engagement metrics)
- If direct traffic suddenly spikes, check: tracking code issues, redirects stripping UTM parameters, dark social sharing

## Conversion Tracking for B2B Lead Gen

### Conversion Hierarchy (Priority Order for Sourcy)
1. **Primary Conversions** (high value, feed into bidding):
   - RFQ form submission (assign value: $50-100 based on close rate)
   - Supplier contact initiated (assign value: $30-50)
   - Demo/consultation booked (assign value: $75-150)
2. **Secondary Conversions** (micro-conversions, track but don't optimize ads to):
   - Account creation (assign value: $10-20)
   - Email newsletter signup (assign value: $3-5)
   - Resource download / whitepaper (assign value: $5-10)
3. **Engagement Events** (behavioral signals, no monetary value):
   - Supplier profile viewed (threshold: 3+ profiles in one session)
   - Search/filter used on platform
   - Pricing page visited
   - Scroll depth >75% on key pages

### Conversion Value Assignment Method
- Calculate: (Average Deal Value) x (Close Rate from Lead Type) = Conversion Value
- Example: If average sourcing deal = $10,000 and RFQ-to-close rate = 2%, then RFQ value = $200
- Revisit values quarterly as close rates and deal sizes change
- Import offline conversions from CRM (Hubspot, Salesforce) back into GA4 and Google Ads weekly

### Multi-Touch Conversion Paths (B2B Reality)
- Average B2B sourcing buyer: 6-12 touchpoints across 2-6 weeks before converting
- Typical path: Organic search (blog) -> Direct (return visit) -> Paid search (category) -> Organic (supplier page) -> Conversion
- First-touch credit should go to awareness channels (SEO blog, display, social)
- Last-touch credit overvalues branded search and direct traffic

## Attribution Models

### GA4 Attribution Options
- **Data-Driven Attribution (DDA)**: Default in GA4; uses machine learning to assign credit based on actual conversion paths. Best choice when you have 300+ conversions/month
- **Last Click**: Gives all credit to the final touchpoint. Overvalues bottom-funnel channels (branded search, direct). Use only for simple reporting
- **First Click**: Gives all credit to the first touchpoint. Useful for understanding which channels drive awareness. Not available as default in GA4 but can be analyzed via path exploration

### Practical Attribution Approach for Sourcy
- Use DDA as default reporting model (GA4 already does this)
- Run monthly comparison: DDA vs Last Click to identify undervalued awareness channels
- If organic blog traffic shows low conversions in last-click but high in DDA, it's an awareness driver worth investing in
- Paid search will always look better in last-click; don't let it cannibalize organic budget
- For budget allocation decisions, weight DDA 70% / First Click 30% to balance acquisition and conversion

### Cross-Channel Analysis Framework
- Map each channel's role: Awareness (first touch), Consideration (middle touch), Conversion (last touch)
- Organic Search: Typically strong in awareness (blog) and conversion (product pages)
- Paid Search: Strongest in conversion; moderate in awareness (for non-brand)
- Social (LinkedIn, Facebook): Awareness and consideration; rarely last-touch for B2B
- Email: Consideration and conversion; nurtures existing leads
- Direct: Often mislabeled; includes dark social, bookmark returns, and broken tracking
- Referral: Varies; trade publication referrals are high-value awareness signals

### Channel Performance Red Flags
- Paid search CPA rising >20% MoM with stable budget = competition increasing or ad fatigue
- Organic traffic flat while paid traffic grows = over-reliance on ads; invest in SEO
- Email open rates dropping below 15% = list fatigue; segment and clean
- Social engagement dropping while follower count grows = content quality issue
- Referral traffic from unknown domains = potential spam; verify in GA4 before acting on it

## GA4 Configuration Essentials for Sourcy

### Must-Have Custom Events
- `supplier_profile_view`: When a user views a supplier detail page
- `rfq_started`: When a user begins an RFQ form
- `rfq_completed`: When an RFQ is successfully submitted
- `search_performed`: When a user searches for suppliers/products (capture search term)
- `filter_applied`: When a user applies category/country/certification filters
- `contact_supplier`: When a user initiates direct supplier contact

### Audience Segments to Build
- High-intent visitors: Viewed 3+ supplier profiles in one session
- RFQ abandoners: Started but didn't complete RFQ (retarget aggressively)
- Category researchers: Visited 2+ category pages without converting (serve deeper content)
- Returning non-converters: 3+ sessions, zero conversions (test different CTAs)
- Converters by country: Separate audiences for each Sourcy market for localized remarketing

---

## GA4 Manual Settings Guide (Settings That CANNOT Be Changed Via API)

The following settings must be configured by the marketing team directly in the GA4 web interface.
When recommending these changes, always provide the exact navigation path and reference link.

### Data Retention
- **Location**: GA4 Admin > Property > Data Settings > Data Retention
- **Recommended**: Set to 14 months (maximum for free GA4; default is only 2 months)
- **Why**: Longer retention enables better trend analysis and year-over-year comparison
- **Reference**: https://support.google.com/analytics/answer/7667196

### Geographic Data Filters
- **Location**: GA4 Admin > Data Settings > Data Filters
- **For Sourcy**: Create a filter to flag or exclude non-target country traffic
- **Important**: Test in "Testing" state first — data filters are permanent once applied
- **Steps**: Admin > Data Filters > Create Filter > Developer traffic / Internal traffic
- **Note**: GA4 supports up to 10 data filters per property
- **Reference**: https://support.google.com/analytics/answer/10108813

### Attribution Settings
- **Location**: GA4 Admin > Attribution Settings
- **Recommended**: Data-driven attribution (default for 2025+)
- **Lookback window**: 90 days for acquisition events, 30 days for other conversions
- **Review**: Check monthly to ensure the model has enough conversion data (400+ for specific events)
- **Reference**: https://support.google.com/analytics/answer/10597962

### Cross-Domain Tracking
- **Location**: GA4 Admin > Data Streams > Web > Configure tag settings > Configure your domains
- **For Sourcy**: Required if sourcy.ai has subdomains (app.sourcy.ai, api.sourcy.ai) used in user journeys
- **Reference**: https://support.google.com/analytics/answer/10071811

### Referral Exclusion List
- **Location**: GA4 Admin > Data Streams > Web > Configure tag settings > List unwanted referrals
- **For Sourcy**: Exclude payment processors (Stripe, PayPal), SSO providers, and internal domains
- **Why**: Prevents false referral traffic from distorting source attribution
- **Reference**: https://support.google.com/analytics/answer/10327750

### Conversion Event Setup (Key Events)
- **Location**: GA4 Admin > Events > Mark as key event
- **For Sourcy**: Ensure these events are marked as key events:
  - `sourcing_request_submitted` (primary conversion)
  - `contact_supplier` (secondary conversion)
  - `sign_up` (lead capture)
- **API**: Can read conversion events via GA4 Admin API, but modifications are limited
- **Reference**: https://support.google.com/analytics/answer/9267568

### Google Ads Country Exclusion (When API is Available)
- **In Google Ads UI**: Campaign > Settings > Locations > Excluded locations
- **Steps**: Click "Excluded" tab > Search for country > Add as exclusion
- **Note**: Maximum 122 country-level exclusions per campaign
- **Reference**: https://support.google.com/google-ads/answer/1722038
- **Also see**: https://support.google.com/google-ads/answer/1722043 (location targeting options)

---

## Historical Comparison Benchmarks

### What Constitutes a Significant Change (investigate these)
- **Traffic**: >15% WoW change without a known campaign change = investigate
- **Bounce rate**: >5 percentage point change week-over-week = investigate
- **CTR (organic)**: >20% relative change on a top-20 keyword = investigate
- **Position**: >3 position drop on a keyword with >500 impressions/month = alert
- **Conversions**: Any drop to 0 across all channels = URGENT tracking check
- **Session duration**: >30% decrease on a specific channel = quality issue
- **New users ratio**: Sudden spike in new users with high bounce = possible bot traffic

### Seasonal Patterns for B2B Sourcing (Sourcy-specific)
- **Q1 (Jan-Mar)**: High activity — new year budgets allocated, sourcing planning season
- **Q2 (Apr-Jun)**: Moderate — execution phase, trade show season (Canton Fair in Apr/May)
- **Q3 (Jul-Sep)**: Slower — summer lull in Western markets, but SEA remains active
- **Q4 (Oct-Dec)**: Variable — holiday sourcing rush (Sep-Oct peak for Q1 delivery), then year-end slowdown
- **Chinese New Year**: Major disruption to supplier availability (Jan/Feb) — expect inquiry spikes before, dip during
- **Ramadan**: Impacts Indonesia, Malaysia — adjust ad schedules and messaging

### Period-Over-Period Comparison Rules
When analyzing trends, always check:
1. **Current vs previous period** (e.g., last 7 days vs prior 7 days)
2. **Rolling 30-day average** as a baseline
3. **Before vs after** specific campaign or website changes
4. **Same period last year** (if 12+ months of data available)
5. **Weekday vs weekend** patterns (B2B traffic typically drops on weekends)
