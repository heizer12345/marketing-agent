"""SEMrush API tools for keyword research and competitor analysis."""

import csv
import io
import json
import requests
from agents import function_tool

import config

BASE_URL = "https://api.semrush.com/"

COUNTRY_DB_MAP = {
    "us": "us", "US": "us",
    "br": "br", "BR": "br",
    "mx": "mx", "MX": "mx",
    "id": "id", "ID": "id",
    "ph": "ph", "PH": "ph",
    "th": "th", "TH": "th",
    "my": "my", "MY": "my",
    "sg": "sg", "SG": "sg",
    "vn": "vn", "VN": "vn",
}


def _parse_csv_response(text: str) -> list[dict]:
    """Parse SEMrush semicolon-delimited CSV response into list of dicts."""
    if not text or text.startswith("ERROR"):
        return [{"error": text.strip() if text else "Empty response"}]
    reader = csv.DictReader(io.StringIO(text.strip()), delimiter=";")
    return [dict(row) for row in reader]


def _call_api(params: dict) -> list[dict]:
    """Make a SEMrush API call with common error handling."""
    params["key"] = config.SEMRUSH_API_KEY
    if not params["key"]:
        return [{"error": "SEMrush API key not configured. Add SEMRUSH_API_KEY to .env"}]
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        if response.status_code != 200:
            return [{"error": f"HTTP {response.status_code}: {response.text[:200]}"}]
        return _parse_csv_response(response.text)
    except Exception as e:
        return [{"error": f"SEMrush API error: {str(e)}"}]


@function_tool
def semrush_domain_overview(domain: str, country_db: str = "us") -> str:
    """Get a quick overview of a domain: organic traffic, keywords, authority.
    Use this to size up competitors or check Sourcy's own domain stats.

    Args:
        domain: Domain to analyze (e.g., 'alibaba.com', 'sourcy.ai')
        country_db: Country database code (us, br, mx, id, ph, th, my, sg, vn)
    """
    db = COUNTRY_DB_MAP.get(country_db, country_db)
    data = _call_api({
        "type": "domain_rank",
        "domain": domain,
        "database": db,
        "export_columns": "Dn,Rk,Or,Ot,Oc,Ad,At,Ac",
    })

    if data and "error" in data[0]:
        return json.dumps({"error": data[0]["error"], "domain": domain, "database": db})

    row = data[0] if data else {}
    return json.dumps({
        "domain": domain,
        "database": db,
        "organic_keywords": row.get("Organic Keywords", row.get("Or", "0")),
        "organic_traffic": row.get("Organic Traffic", row.get("Ot", "0")),
        "organic_traffic_cost": row.get("Organic Cost", row.get("Oc", "0")),
        "paid_keywords": row.get("Adwords Keywords", row.get("Ad", "0")),
        "paid_traffic": row.get("Adwords Traffic", row.get("At", "0")),
        "paid_traffic_cost": row.get("Adwords Cost", row.get("Ac", "0")),
        "domain_rank": row.get("Rank", row.get("Rk", "N/A")),
    })


@function_tool
def semrush_competitor_keywords(domain: str, country_db: str = "us", limit: int = 30) -> str:
    """Get organic keywords a domain ranks for. Use to discover what keywords
    competitors like Alibaba, Global Sources rank for that Sourcy doesn't.

    Args:
        domain: Competitor domain (e.g., 'alibaba.com')
        country_db: Country database (us, br, mx, id, ph, th)
        limit: Max keywords to return (default 30)
    """
    db = COUNTRY_DB_MAP.get(country_db, country_db)
    data = _call_api({
        "type": "domain_organic",
        "domain": domain,
        "database": db,
        "display_limit": limit,
        "export_columns": "Ph,Po,Nq,Cp,Co,Tr,Tc",
    })

    if data and "error" in data[0]:
        return json.dumps({"error": data[0]["error"], "domain": domain, "database": db})

    keywords = []
    for row in data:
        keywords.append({
            "keyword": row.get("Keyword", row.get("Ph", "")),
            "position": row.get("Position", row.get("Po", "0")),
            "search_volume": row.get("Search Volume", row.get("Nq", "0")),
            "cpc": row.get("CPC", row.get("Cp", "0")),
            "competition": row.get("Competition", row.get("Co", "0")),
            "traffic_pct": row.get("Traffic (%)", row.get("Tr", "0")),
        })

    return json.dumps({
        "domain": domain,
        "database": db,
        "keywords_found": len(keywords),
        "keywords": keywords,
    })


@function_tool
def semrush_keyword_research(keyword: str, country_db: str = "us") -> str:
    """Research a specific keyword: search volume, difficulty, CPC, competition.
    Use to evaluate keyword opportunities before targeting them.

    Args:
        keyword: Keyword to research (e.g., 'sourcing agent indonesia')
        country_db: Country database (us, br, mx, id, ph, th)
    """
    db = COUNTRY_DB_MAP.get(country_db, country_db)
    data = _call_api({
        "type": "phrase_this",
        "phrase": keyword,
        "database": db,
        "export_columns": "Ph,Nq,Cp,Co,Nr,Td",
    })

    if data and "error" in data[0]:
        return json.dumps({"error": data[0]["error"], "keyword": keyword, "database": db})

    row = data[0] if data else {}
    return json.dumps({
        "keyword": keyword,
        "database": db,
        "search_volume": row.get("Search Volume", row.get("Nq", "0")),
        "cpc": row.get("CPC", row.get("Cp", "0")),
        "competition": row.get("Competition", row.get("Co", "0")),
        "results_count": row.get("Number of Results", row.get("Nr", "0")),
        "trend": row.get("Trends", row.get("Td", "")),
    })


@function_tool
def semrush_find_competitors(domain: str, country_db: str = "us", limit: int = 10) -> str:
    """Find domains that compete for the same organic keywords.
    Useful for discovering competitors you didn't know about.

    Args:
        domain: Your domain (e.g., 'sourcy.ai')
        country_db: Country database (us, br, mx, id, ph, th)
        limit: Max competitors to return
    """
    db = COUNTRY_DB_MAP.get(country_db, country_db)
    data = _call_api({
        "type": "domain_organic_organic",
        "domain": domain,
        "database": db,
        "display_limit": limit,
        "export_columns": "Dn,Cr,Np,Or,Ot,Oc,Ad",
    })

    if data and "error" in data[0]:
        return json.dumps({"error": data[0]["error"], "domain": domain, "database": db})

    competitors = []
    for row in data:
        competitors.append({
            "domain": row.get("Domain", row.get("Dn", "")),
            "competition_level": row.get("Competitor Relevance", row.get("Cr", "0")),
            "common_keywords": row.get("Common Keywords", row.get("Np", "0")),
            "organic_keywords": row.get("Organic Keywords", row.get("Or", "0")),
            "organic_traffic": row.get("Organic Traffic", row.get("Ot", "0")),
        })

    return json.dumps({
        "domain": domain,
        "database": db,
        "competitors_found": len(competitors),
        "competitors": competitors,
    })


@function_tool
def semrush_keyword_gap(domain: str, competitors: str, country_db: str = "us", limit: int = 100) -> str:
    """Find keywords that competitor domains rank for but the given domain does NOT.
    Critical for content gap analysis.

    Args:
        domain: Your domain (e.g., 'sourcy.ai')
        competitors: Comma-separated competitor domains, max 4 (e.g., 'alibaba.com,accio.com')
        country_db: Country database (us, br, mx, id, ph, th)
        limit: Max keywords to return (default 100, max 200)
    """
    db = COUNTRY_DB_MAP.get(country_db, country_db)
    comp_list = [c.strip() for c in competitors.split(",")][:4]

    # SEMrush domain_domains endpoint for keyword gap
    params = {
        "type": "domain_domains",
        "domains": "|".join([f"-|{domain}|or"] + [f"+|{c}|or" for c in comp_list]),
        "database": db,
        "display_limit": min(limit, 200),
        "export_columns": "Ph,Nq,Co,Cp,Kd",
        "display_sort": "nq_desc",
    }
    data = _call_api(params)

    if data and "error" in data[0]:
        return json.dumps({"error": data[0]["error"], "domain": domain})

    keywords = []
    for row in data:
        keywords.append({
            "keyword": row.get("Keyword", row.get("Ph", "")),
            "search_volume": row.get("Search Volume", row.get("Nq", "0")),
            "competition": row.get("Competition", row.get("Co", "0")),
            "cpc": row.get("CPC", row.get("Cp", "0")),
            "keyword_difficulty": row.get("Keyword Difficulty", row.get("Kd", "0")),
        })

    return json.dumps({
        "domain": domain,
        "competitors_checked": comp_list,
        "database": db,
        "gap_keywords_found": len(keywords),
        "keywords": keywords,
        "note": "These keywords are ranked by competitors but NOT by your domain.",
    })


@function_tool
def semrush_backlinks_overview(domain: str) -> str:
    """Get backlink profile overview for a domain — total backlinks, referring domains, authority.

    Args:
        domain: Domain to check (e.g., 'sourcy.ai')
    """
    data = _call_api({
        "type": "backlinks_overview",
        "target": domain,
        "target_type": "root_domain",
        "export_columns": "ascore,total,domains_num,urls_num,ips_num,follows_num,nofollows_num",
    })

    if data and "error" in data[0]:
        return json.dumps({"error": data[0]["error"], "domain": domain})

    row = data[0] if data else {}
    return json.dumps({
        "domain": domain,
        "authority_score": row.get("Authority Score", row.get("ascore", "N/A")),
        "total_backlinks": row.get("Total", row.get("total", "0")),
        "referring_domains": row.get("Domains", row.get("domains_num", "0")),
        "referring_urls": row.get("URLs", row.get("urls_num", "0")),
        "referring_ips": row.get("IPs", row.get("ips_num", "0")),
        "follow_links": row.get("Follow", row.get("follows_num", "0")),
        "nofollow_links": row.get("Nofollow", row.get("nofollows_num", "0")),
    })


@function_tool
def semrush_traffic_summary(domain: str) -> str:
    """Get traffic analytics summary for a domain (requires SEMrush Traffic Analytics add-on).
    Returns estimated visits, pages per visit, bounce rate, visit duration.

    Args:
        domain: Domain to check (e.g., 'alibaba.com')
    """
    # Traffic Analytics API — may not be available on all plans
    try:
        params = {
            "key": config.SEMRUSH_API_KEY,
            "targets": domain,
            "display_date": "",  # latest available
            "country": "",  # worldwide
            "export_columns": "target,visits,desktop_visits,mobile_visits,users,pages_per_visit,bounce_rate,avg_visit_duration",
        }
        if not config.SEMRUSH_API_KEY:
            return json.dumps({"error": "SEMrush API key not configured"})

        response = requests.get(
            "https://api.semrush.com/analytics/v1/",
            params=params,
            timeout=30,
        )
        if response.status_code != 200:
            return json.dumps({
                "error": f"Traffic Analytics may not be available on your plan. HTTP {response.status_code}",
                "domain": domain,
                "note": "Traffic Analytics requires a paid add-on in SEMrush Pro.",
            })
        data = _parse_csv_response(response.text)
        row = data[0] if data else {}
        return json.dumps({
            "domain": domain,
            "visits": row.get("visits", "N/A"),
            "desktop_visits": row.get("desktop_visits", "N/A"),
            "mobile_visits": row.get("mobile_visits", "N/A"),
            "users": row.get("users", "N/A"),
            "pages_per_visit": row.get("pages_per_visit", "N/A"),
            "bounce_rate": row.get("bounce_rate", "N/A"),
            "avg_visit_duration": row.get("avg_visit_duration", "N/A"),
        })
    except Exception as e:
        return json.dumps({"error": f"Traffic Analytics error: {str(e)}", "domain": domain})
