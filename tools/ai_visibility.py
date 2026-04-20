"""GEO/AEO visibility tools — check Sourcy presence in AI-generated search results.

All tools gracefully degrade if API keys are not configured.
"""

import json
import re
import httpx
from agents import function_tool

import config

_TIMEOUT = 30


def _missing_key(name: str) -> str:
    return json.dumps({"error": f"{name} not configured. Add {name} to .env to enable this check.", "skipped": True})


# ─── Google AI Overview (via SerpApi) ───────────────────────────────────

@function_tool
def check_google_ai_overview(query: str) -> str:
    """Check if Sourcy appears in Google AI Overview for a search query.
    Uses SerpApi to fetch AI Overview results.

    Args:
        query: Search query to check (e.g., 'best B2B sourcing platforms')
    """
    if not config.SERPAPI_KEY:
        return _missing_key("SERPAPI_KEY")

    try:
        resp = httpx.get(
            "https://serpapi.com/search",
            params={
                "engine": "google",
                "q": query,
                "api_key": config.SERPAPI_KEY,
                "num": 10,
            },
            timeout=_TIMEOUT,
        )
        data = resp.json()

        ai_overview = data.get("ai_overview", {})
        ai_text = ""
        cited_domains = []

        if ai_overview:
            # Extract text blocks from AI overview
            text_blocks = ai_overview.get("text_blocks", [])
            for block in text_blocks:
                if isinstance(block, dict):
                    ai_text += block.get("snippet", block.get("text", "")) + " "
                elif isinstance(block, str):
                    ai_text += block + " "

            # Extract referenced sources
            references = ai_overview.get("references", ai_overview.get("sources", []))
            for ref in references:
                if isinstance(ref, dict):
                    domain = ref.get("domain", ref.get("link", ""))
                    cited_domains.append(domain)

        sourcy_mentioned = "sourcy" in ai_text.lower()
        competitor_mentions = {}
        for comp in config.get_competitors_by_tier("primary"):
            name_lower = comp["name"].lower().split("/")[0].strip()
            if name_lower in ai_text.lower() or comp["domain"] in ai_text.lower():
                competitor_mentions[comp["name"]] = True

        return json.dumps({
            "query": query,
            "ai_overview_present": bool(ai_overview),
            "sourcy_mentioned": sourcy_mentioned,
            "sourcy_domain_cited": any("sourcy" in d for d in cited_domains),
            "cited_domains": cited_domains[:20],
            "competitor_mentions": competitor_mentions,
            "ai_overview_snippet": ai_text[:500] if ai_text else "No AI Overview for this query",
        })
    except Exception as e:
        return json.dumps({"error": f"SerpApi error: {str(e)}", "query": query})


# ─── Perplexity Citation Check ──────────────────────────────────────────

@function_tool
def check_perplexity_citation(query: str) -> str:
    """Check if Sourcy is cited in Perplexity AI responses.

    Args:
        query: Search query to check (e.g., 'best AI sourcing platforms for B2B')
    """
    if not config.PERPLEXITY_API_KEY:
        return _missing_key("PERPLEXITY_API_KEY")

    try:
        resp = httpx.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {config.PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": query}],
            },
            timeout=_TIMEOUT,
        )
        data = resp.json()

        content = ""
        citations = []

        if "choices" in data:
            content = data["choices"][0].get("message", {}).get("content", "")
        if "citations" in data:
            citations = data["citations"]

        sourcy_cited = any("sourcy" in str(c).lower() for c in citations)
        sourcy_mentioned = "sourcy" in content.lower()

        competitor_mentions = {}
        for comp in config.get_competitors_by_tier("primary"):
            name_lower = comp["name"].lower().split("/")[0].strip()
            if name_lower in content.lower():
                competitor_mentions[comp["name"]] = True

        return json.dumps({
            "query": query,
            "sourcy_cited": sourcy_cited,
            "sourcy_mentioned_in_text": sourcy_mentioned,
            "citations": citations[:20],
            "competitor_mentions": competitor_mentions,
            "response_snippet": content[:500],
        })
    except Exception as e:
        return json.dumps({"error": f"Perplexity API error: {str(e)}", "query": query})


# ─── ChatGPT Mention Check ─────────────────────────────────────────────

@function_tool
def check_chatgpt_mention(query: str) -> str:
    """Check if Sourcy is mentioned in ChatGPT responses.
    Note: API results may differ from web ChatGPT.

    Args:
        query: Search query to check (e.g., 'what are the best B2B sourcing platforms?')
    """
    if not config.OPENAI_API_KEY:
        return _missing_key("OPENAI_API_KEY")

    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": query}],
                "max_tokens": 1000,
            },
            timeout=_TIMEOUT,
        )
        data = resp.json()

        content = ""
        if "choices" in data:
            content = data["choices"][0].get("message", {}).get("content", "")

        sourcy_mentioned = "sourcy" in content.lower()

        competitor_mentions = {}
        for comp in config.get_competitors_by_tier("primary"):
            name_lower = comp["name"].lower().split("/")[0].strip()
            if name_lower in content.lower():
                competitor_mentions[comp["name"]] = True

        return json.dumps({
            "query": query,
            "sourcy_mentioned": sourcy_mentioned,
            "competitor_mentions": competitor_mentions,
            "response_snippet": content[:500],
            "note": "ChatGPT API responses may differ from web chat results.",
        })
    except Exception as e:
        return json.dumps({"error": f"OpenAI API error: {str(e)}", "query": query})


# ─── Structured Data Analysis ───────────────────────────────────────────

@function_tool
def analyze_structured_data(url: str) -> str:
    """Analyze structured data (JSON-LD, Schema.org) on a URL.
    Checks for FAQ, Organization, Product, BreadcrumbList schemas.

    Args:
        url: URL to analyze (e.g., 'https://www.sourcy.ai')
    """
    try:
        resp = httpx.get(url, timeout=_TIMEOUT, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 SourcyBot/1.0"})
        html = resp.text

        # Extract JSON-LD blocks
        json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(json_ld_pattern, html, re.DOTALL | re.IGNORECASE)

        schemas_found = []
        for match in matches:
            try:
                schema = json.loads(match.strip())
                if isinstance(schema, list):
                    for s in schema:
                        schemas_found.append(s.get("@type", "Unknown"))
                else:
                    schemas_found.append(schema.get("@type", "Unknown"))
            except json.JSONDecodeError:
                pass

        # Check for recommended schemas
        recommended = ["Organization", "WebSite", "Product", "FAQPage",
                       "BreadcrumbList", "Article", "HowTo"]
        present = [s for s in recommended if s in schemas_found]
        missing = [s for s in recommended if s not in schemas_found]

        # Check for meta tags relevant to SEO
        has_canonical = 'rel="canonical"' in html or "rel='canonical'" in html
        has_og_tags = 'property="og:' in html
        has_twitter_cards = 'name="twitter:' in html

        return json.dumps({
            "url": url,
            "schemas_found": schemas_found,
            "recommended_present": present,
            "recommended_missing": missing,
            "has_canonical": has_canonical,
            "has_og_tags": has_og_tags,
            "has_twitter_cards": has_twitter_cards,
            "score": f"{len(present)}/{len(recommended)}",
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to analyze {url}: {str(e)}"})


# ─── E-E-A-T Signal Analysis ───────────────────────────────────────────

@function_tool
def check_eeat_signals(url: str) -> str:
    """Analyze E-E-A-T (Experience, Expertise, Authority, Trust) signals on a page.

    Args:
        url: URL to analyze (e.g., 'https://www.sourcy.ai')
    """
    try:
        resp = httpx.get(url, timeout=_TIMEOUT, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 SourcyBot/1.0"})
        html = resp.text.lower()

        signals = {
            "experience": {
                "case_studies": "case stud" in html,
                "testimonials": "testimonial" in html or "customer review" in html,
                "customer_count": any(x in html for x in ["customers", "clients served"]),
            },
            "expertise": {
                "author_info": "author" in html and ("bio" in html or "about the author" in html),
                "credentials": any(x in html for x in ["certified", "years of experience", "expert"]),
                "detailed_content": len(html) > 5000,
            },
            "authority": {
                "about_page_linked": "/about" in html,
                "brand_mentions": "sourcy" in html,
                "press_mentions": any(x in html for x in ["featured in", "as seen in", "press"]),
                "social_proof": any(x in html for x in ["linkedin", "twitter", "crunchbase"]),
            },
            "trust": {
                "https": url.startswith("https"),
                "privacy_policy": "privacy" in html,
                "terms_of_service": "terms" in html,
                "contact_info": "contact" in html,
                "physical_address": "address" in html or "office" in html,
            },
        }

        # Calculate scores per category
        scores = {}
        total = 0
        max_total = 0
        for category, checks in signals.items():
            passed = sum(1 for v in checks.values() if v)
            possible = len(checks)
            scores[category] = {"passed": passed, "total": possible,
                                "score": round(passed / possible * 25)}
            total += scores[category]["score"]
            max_total += 25

        return json.dumps({
            "url": url,
            "eeat_score": total,
            "max_score": max_total,
            "breakdown": scores,
            "signals": signals,
            "recommendations": [
                f"Improve {cat}" for cat, s in scores.items() if s["score"] < 15
            ],
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to analyze {url}: {str(e)}"})
