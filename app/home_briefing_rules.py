"""Prompt rules for Home tab JSON briefing — accuracy, citations, channel grouping."""

HOME_SNAPSHOT_OUTPUT_RULES = """
## Accuracy (no false alarms)
- **Zero ad spend is not automatically a problem.** If Google Ads or Meta spend is $0, state the fact only
  (e.g. "Google Ads spend $0 (7d)") unless the API shows active/enabled campaigns with budget that failed
  to deliver. Paused or intentionally off campaigns are normal — do NOT say "despite active budget" unless
  you cite a specific campaign name/ID that is ENABLED with budget > 0 and still spent $0.
- Never invent campaigns, posts, pages, or channel names. Pull names/IDs from tool results only.
- If a source has no data in the period, omit alerts for it — do not speculate.

## Citations (mandatory in every alert & recommendation)
Each `detail` object MUST include:
- `evidence`: 2–5 bullet lines (each starts with "- "). Each bullet = one metric + number + date range.
- `references`: array of specific objects cited, e.g.:
  - GA4: "Channel: Organic Search", "Page: /blogs/foo"
  - Search Console: "Query: private label sourcing", "Page: https://www.sourcy.ai/sourcing/moq"
  - Google Ads: "Campaign: [name] (ID 123456)", "Status: PAUSED"
  - Meta: "Campaign: [name]", "Ad set: [name]", "Ad: [name]", "Instagram post: [caption snippet or ID]"
  - Instagram organic: "@handle · post [date or permalink]"
- `pages`: full https://www.sourcy.ai/... URLs when page-level (GA4/GSC/landing pages).

## KPI cards
Each KPI must include:
- `label`, `value`, `delta_pct` (or null), `source`
- `context`: what the number measures (required), e.g.:
  - "Site-wide sessions · GA4 · last 7 days"
  - "Organic clicks · Search Console · sc-domain:sourcy.ai · all pages"
  - "Spend · Google Ads · account 102-851-7956 · all campaigns"
  - "Spend · Meta Ads · act_1064665587623888"

## Recommendations by channel
- Set `source` to exactly one of: `GA4`, `Search Console`, `Google Ads`, `Meta Ads`, `Instagram`, `PostHog`, `Sourcy DB`
- Group mentally: at least 1 recommendation each for connected ads + SEO + GA4 when data exists.
- Headlines must name the object: bad = "Replace boosted Meta post"; good = "Replace boosted post on @eugeneatsourcy (ad set X) with tracked campaign"

## Formatting
- Use bullet lines in `evidence`, `cause`, `suggestion` (prefix with "- ").
- `text` = short headline only; depth lives in `detail`.
"""

HOME_SNAPSHOT_JSON_SHAPE = """
{
  "kpis": [{"label": "Sessions (7d)", "value": "12,180", "delta_pct": -8.2, "source": "GA4", "context": "Site-wide · GA4 · last 7 days"}, ...],
  "insights": [{"text": "...", "severity": "important", "source": "GA4"}, ...],
  "top_movers": [{"text": "...", "kind": "keyword_up", "source": "Search Console"}, ...],
  "alerts": [{
    "text": "Short headline (max 120 chars)",
    "severity": "urgent",
    "source": "GA4",
    "detail": {
      "cause": "- Bullet cause\\n- Second line if needed",
      "evidence": "- Metric with number (7d vs prior 7d)\\n- Second metric",
      "references": ["Channel: Organic Search", "Page: https://www.sourcy.ai/onboard"],
      "pages": ["https://www.sourcy.ai/onboard"],
      "suggestion": "- Action bullet",
      "next_step": "- One concrete step today"
    }
  }, ...],
  "recommendations": [{
    "text": "Short action headline naming campaign/page/channel",
    "priority": "high",
    "source": "Meta Ads",
    "detail": { "cause": "...", "evidence": "...", "references": ["Campaign: ...", "Ad: ..."], "pages": ["..."], "suggestion": "...", "next_step": "..." }
  }, ...]
}
"""
