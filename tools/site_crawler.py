"""Site crawler tools — lightweight page analysis for SEO/GEO/AEO audits.

Uses httpx + BeautifulSoup to fetch and parse web pages. No paid APIs required.
All tools return JSON strings matching the project's @function_tool pattern.
"""

import json
import re
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import httpx
from bs4 import BeautifulSoup
from agents import function_tool

_TIMEOUT = 15
_USER_AGENT = "Mozilla/5.0 (compatible; SourcyBot/1.0; +https://sourcy.ai)"
_HEADERS = {"User-Agent": _USER_AGENT}

# AI crawlers to check in robots.txt
AI_CRAWLERS = {
    "GPTBot": "OpenAI (ChatGPT, SearchGPT)",
    "OAI-SearchBot": "OpenAI SearchGPT",
    "ChatGPT-User": "ChatGPT browsing",
    "ClaudeBot": "Anthropic Claude",
    "anthropic-ai": "Anthropic (legacy)",
    "PerplexityBot": "Perplexity AI",
    "Google-Extended": "Google Gemini/AI Overview training",
    "Googlebot": "Google Search (blocks AI Overview too)",
    "Applebot-Extended": "Apple Intelligence",
    "Bytespider": "ByteDance/TikTok",
    "cohere-ai": "Cohere AI",
    "CCBot": "Common Crawl (used by many AI)",
    "FacebookBot": "Meta AI",
}


# ─── Page Crawler ──────────────────────────────────────────────────────

@function_tool
def crawl_page(url: str) -> str:
    """Crawl a single page and extract SEO-relevant elements.

    Returns structured data: title, meta tags, headers, links, images,
    schema markup, word count, and more.

    Args:
        url: Full URL to crawl (e.g., 'https://sourcy.ai/about')
    """
    try:
        resp = httpx.get(url, timeout=_TIMEOUT, follow_redirects=True, headers=_HEADERS)
        soup = BeautifulSoup(resp.text, "html.parser")

        # --- Title tag ---
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # --- Meta tags ---
        meta_desc = ""
        meta_robots = ""
        meta_viewport = ""
        for meta in soup.find_all("meta"):
            name = (meta.get("name") or meta.get("property") or "").lower()
            content = meta.get("content", "")
            if name == "description":
                meta_desc = content
            elif name == "robots":
                meta_robots = content
            elif name == "viewport":
                meta_viewport = content

        # --- Canonical ---
        canonical_tag = soup.find("link", rel="canonical")
        canonical = canonical_tag["href"] if canonical_tag and canonical_tag.get("href") else ""

        # --- Hreflang ---
        hreflang_tags = []
        for link in soup.find_all("link", rel="alternate"):
            if link.get("hreflang"):
                hreflang_tags.append({"lang": link["hreflang"], "href": link.get("href", "")})

        # --- Headers (H1-H6) ---
        headers = {}
        for level in range(1, 7):
            tag = f"h{level}"
            found = [h.get_text(strip=True) for h in soup.find_all(tag)]
            if found:
                headers[tag] = found

        # --- Body text and word count ---
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        body_text = soup.get_text(separator=" ", strip=True)
        words = body_text.split()
        word_count = len(words)

        # --- Internal vs external links ---
        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc.replace("www.", "")
        internal_links = []
        external_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            anchor = a.get_text(strip=True)[:100]
            absolute = urljoin(url, href)
            parsed_href = urlparse(absolute)
            if parsed_href.netloc.replace("www.", "") == base_domain:
                if len(internal_links) < 100:
                    internal_links.append({"href": absolute, "anchor": anchor})
            else:
                if parsed_href.scheme in ("http", "https") and len(external_links) < 50:
                    external_links.append({"href": absolute, "anchor": anchor})

        # --- Images ---
        images = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            alt = img.get("alt", "")
            if src and len(images) < 50:
                images.append({
                    "src": urljoin(url, src),
                    "alt": alt,
                    "has_alt": bool(alt.strip()),
                })
        images_without_alt = sum(1 for i in images if not i["has_alt"])

        # --- JSON-LD schemas ---
        json_ld_schemas = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    for item in data:
                        json_ld_schemas.append({
                            "@type": item.get("@type", "Unknown"),
                            "summary": {k: str(v)[:100] for k, v in item.items()
                                        if k in ("@type", "name", "description", "url")}
                        })
                elif isinstance(data, dict):
                    json_ld_schemas.append({
                        "@type": data.get("@type", "Unknown"),
                        "summary": {k: str(v)[:100] for k, v in data.items()
                                    if k in ("@type", "name", "description", "url")}
                    })
            except (json.JSONDecodeError, TypeError):
                pass

        # --- Open Graph tags ---
        og_tags = {}
        for meta in soup.find_all("meta", property=re.compile(r"^og:")):
            og_tags[meta["property"]] = meta.get("content", "")

        # --- Twitter Card tags ---
        twitter_tags = {}
        for meta in soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")}):
            twitter_tags[meta["name"]] = meta.get("content", "")

        # --- Redirect chain ---
        redirect_chain = []
        for r in resp.history:
            redirect_chain.append({"status": r.status_code, "url": str(r.url)})

        return json.dumps({
            "url": url,
            "final_url": str(resp.url),
            "status_code": resp.status_code,
            "redirect_chain": redirect_chain,
            "page_size_bytes": len(resp.content),
            "title": title,
            "title_length": len(title),
            "meta_description": meta_desc,
            "meta_description_length": len(meta_desc),
            "meta_robots": meta_robots,
            "meta_viewport": meta_viewport,
            "canonical": canonical,
            "hreflang": hreflang_tags,
            "headers": headers,
            "h1_count": len(headers.get("h1", [])),
            "word_count": word_count,
            "internal_links_count": len(internal_links),
            "internal_links": internal_links[:50],
            "external_links_count": len(external_links),
            "external_links": external_links[:20],
            "images_count": len(images),
            "images_without_alt": images_without_alt,
            "images": images[:20],
            "json_ld_schemas": json_ld_schemas,
            "og_tags": og_tags,
            "twitter_tags": twitter_tags,
            "body_text_preview": body_text[:2000],
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to crawl {url}: {str(e)}"})


# ─── Robots.txt Parser ─────────────────────────────────────────────────

@function_tool
def crawl_robots_txt(domain: str) -> str:
    """Fetch and parse robots.txt for a domain, with focus on AI crawler access.

    Args:
        domain: Domain to check (e.g., 'sourcy.ai' or 'https://sourcy.ai')
    """
    if not domain.startswith("http"):
        domain = f"https://{domain}"
    parsed = urlparse(domain)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        resp = httpx.get(robots_url, timeout=_TIMEOUT, follow_redirects=True, headers=_HEADERS)

        if resp.status_code == 404:
            return json.dumps({
                "url": robots_url,
                "exists": False,
                "ai_crawler_access": {name: "allowed (no robots.txt)" for name in AI_CRAWLERS},
                "note": "No robots.txt found — all crawlers allowed by default.",
            })

        content = resp.text
        lines = content.strip().split("\n")

        # Parse rules by user-agent
        rules = {}
        current_agents = []
        for line in lines:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if line.lower().startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                current_agents = [agent]
                if agent not in rules:
                    rules[agent] = {"disallow": [], "allow": [], "crawl_delay": None}
            elif line.lower().startswith("disallow:") and current_agents:
                path = line.split(":", 1)[1].strip()
                for agent in current_agents:
                    rules.setdefault(agent, {"disallow": [], "allow": [], "crawl_delay": None})
                    rules[agent]["disallow"].append(path)
            elif line.lower().startswith("allow:") and current_agents:
                path = line.split(":", 1)[1].strip()
                for agent in current_agents:
                    rules.setdefault(agent, {"disallow": [], "allow": [], "crawl_delay": None})
                    rules[agent]["allow"].append(path)
            elif line.lower().startswith("crawl-delay:") and current_agents:
                delay = line.split(":", 1)[1].strip()
                for agent in current_agents:
                    rules.setdefault(agent, {"disallow": [], "allow": [], "crawl_delay": None})
                    rules[agent]["crawl_delay"] = delay

        # Sitemaps referenced in robots.txt
        sitemaps = re.findall(r"Sitemap:\s*(\S+)", content, re.IGNORECASE)

        # Check AI crawler access
        ai_access = {}
        wildcard_rules = rules.get("*", {"disallow": [], "allow": []})
        wildcard_blocked = "/" in wildcard_rules["disallow"]

        for crawler_name, description in AI_CRAWLERS.items():
            if crawler_name in rules:
                agent_rules = rules[crawler_name]
                if "/" in agent_rules["disallow"]:
                    ai_access[crawler_name] = {
                        "status": "blocked",
                        "description": description,
                        "rule": f"User-agent: {crawler_name} / Disallow: /",
                    }
                elif agent_rules["disallow"]:
                    ai_access[crawler_name] = {
                        "status": "partially_blocked",
                        "description": description,
                        "blocked_paths": agent_rules["disallow"],
                    }
                else:
                    ai_access[crawler_name] = {
                        "status": "allowed",
                        "description": description,
                    }
            elif wildcard_blocked:
                ai_access[crawler_name] = {
                    "status": "blocked (via wildcard)",
                    "description": description,
                    "rule": "User-agent: * / Disallow: /",
                }
            else:
                ai_access[crawler_name] = {
                    "status": "allowed (no specific rule)",
                    "description": description,
                }

        blocked_count = sum(1 for v in ai_access.values()
                           if "blocked" in v["status"])

        return json.dumps({
            "url": robots_url,
            "exists": True,
            "sitemaps": sitemaps,
            "user_agents_defined": list(rules.keys()),
            "ai_crawler_access": ai_access,
            "ai_crawlers_blocked": blocked_count,
            "ai_crawlers_total": len(AI_CRAWLERS),
            "rules_summary": {
                agent: {
                    "disallow_count": len(r["disallow"]),
                    "allow_count": len(r["allow"]),
                    "crawl_delay": r["crawl_delay"],
                }
                for agent, r in rules.items()
            },
            "raw_content": content[:3000],
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch robots.txt for {domain}: {str(e)}"})


# ─── Sitemap Parser ────────────────────────────────────────────────────

@function_tool
def crawl_sitemap(domain: str) -> str:
    """Fetch and parse sitemap.xml for a domain.

    Handles sitemap index files and returns URL inventory.

    Args:
        domain: Domain to check (e.g., 'sourcy.ai' or 'https://sourcy.ai')
    """
    if not domain.startswith("http"):
        domain = f"https://{domain}"
    parsed = urlparse(domain)
    base = f"{parsed.scheme}://{parsed.netloc}"
    sitemap_url = f"{base}/sitemap.xml"

    try:
        resp = httpx.get(sitemap_url, timeout=_TIMEOUT, follow_redirects=True, headers=_HEADERS)

        if resp.status_code == 404:
            return json.dumps({
                "url": sitemap_url,
                "exists": False,
                "error": "No sitemap.xml found at root. Check robots.txt for alternate sitemap location.",
            })

        content = resp.text
        urls = []
        child_sitemaps = []

        try:
            root = ET.fromstring(content)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Check if sitemap index
            for sitemap in root.findall(".//sm:sitemap", ns):
                loc = sitemap.find("sm:loc", ns)
                if loc is not None and loc.text:
                    child_sitemaps.append(loc.text.strip())

            # Parse URLs from sitemap
            for url_elem in root.findall(".//sm:url", ns):
                loc = url_elem.find("sm:loc", ns)
                lastmod = url_elem.find("sm:lastmod", ns)
                changefreq = url_elem.find("sm:changefreq", ns)
                priority = url_elem.find("sm:priority", ns)
                if loc is not None and loc.text:
                    entry = {"url": loc.text.strip()}
                    if lastmod is not None and lastmod.text:
                        entry["lastmod"] = lastmod.text.strip()
                    if changefreq is not None and changefreq.text:
                        entry["changefreq"] = changefreq.text.strip()
                    if priority is not None and priority.text:
                        entry["priority"] = priority.text.strip()
                    urls.append(entry)
        except ET.ParseError:
            return json.dumps({
                "url": sitemap_url,
                "exists": True,
                "error": "Sitemap exists but has XML parsing errors.",
                "raw_preview": content[:1000],
            })

        # If it's an index, fetch child sitemaps (up to 5)
        if child_sitemaps and not urls:
            for child_url in child_sitemaps[:5]:
                try:
                    child_resp = httpx.get(child_url, timeout=_TIMEOUT,
                                           follow_redirects=True, headers=_HEADERS)
                    child_root = ET.fromstring(child_resp.text)
                    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                    for url_elem in child_root.findall(".//sm:url", ns):
                        loc = url_elem.find("sm:loc", ns)
                        lastmod = url_elem.find("sm:lastmod", ns)
                        if loc is not None and loc.text:
                            entry = {"url": loc.text.strip()}
                            if lastmod is not None and lastmod.text:
                                entry["lastmod"] = lastmod.text.strip()
                            urls.append(entry)
                except Exception:
                    continue

        # Classify URLs by path pattern
        path_patterns = {}
        for u in urls:
            path = urlparse(u["url"]).path
            segments = [s for s in path.split("/") if s]
            pattern = f"/{segments[0]}/" if segments else "/"
            path_patterns[pattern] = path_patterns.get(pattern, 0) + 1

        return json.dumps({
            "url": sitemap_url,
            "exists": True,
            "is_sitemap_index": bool(child_sitemaps),
            "child_sitemaps": child_sitemaps,
            "total_urls": len(urls),
            "url_path_patterns": dict(sorted(path_patterns.items(),
                                             key=lambda x: x[1], reverse=True)[:20]),
            "urls": urls[:500],
            "sample_urls": [u["url"] for u in urls[:20]],
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch sitemap for {domain}: {str(e)}"})


# ─── llms.txt Checker ──────────────────────────────────────────────────

@function_tool
def check_llms_txt(domain: str) -> str:
    """Check for llms.txt and llms-full.txt files on a domain.

    The llms.txt standard helps AI systems understand website content.

    Args:
        domain: Domain to check (e.g., 'sourcy.ai')
    """
    if not domain.startswith("http"):
        domain = f"https://{domain}"
    parsed = urlparse(domain)
    base = f"{parsed.scheme}://{parsed.netloc}"

    results = {}
    for filename in ["llms.txt", "llms-full.txt"]:
        file_url = f"{base}/{filename}"
        try:
            resp = httpx.get(file_url, timeout=_TIMEOUT, follow_redirects=True, headers=_HEADERS)
            if resp.status_code == 200 and resp.text.strip():
                content = resp.text
                # Basic validation — check for title line and link sections
                has_title = content.strip().split("\n")[0].startswith("#") if content.strip() else False
                has_links = bool(re.findall(r"https?://\S+", content))

                results[filename] = {
                    "exists": True,
                    "url": file_url,
                    "content_length": len(content),
                    "has_title": has_title,
                    "has_links": has_links,
                    "content_preview": content[:1500],
                }
            else:
                results[filename] = {"exists": False, "url": file_url, "status": resp.status_code}
        except Exception as e:
            results[filename] = {"exists": False, "url": file_url, "error": str(e)}

    has_any = any(r.get("exists") for r in results.values())

    return json.dumps({
        "domain": parsed.netloc,
        "has_llms_txt": has_any,
        "files": results,
        "recommendation": (
            "llms.txt found — review content for completeness."
            if has_any
            else "No llms.txt found. Consider creating one to help AI systems understand your site. "
                 "Format: # Title\\n> Description\\n## Section\\n- [Link name](url): description"
        ),
    })


# ─── AI Crawler Access Matrix ─────────────────────────────────────────

@function_tool
def check_ai_crawler_access(domain: str) -> str:
    """Combined analysis of AI crawler access via robots.txt and HTTP headers.

    Produces a per-crawler access matrix and recommendations.

    Args:
        domain: Domain to check (e.g., 'sourcy.ai')
    """
    if not domain.startswith("http"):
        domain = f"https://{domain}"
    parsed = urlparse(domain)
    base = f"{parsed.scheme}://{parsed.netloc}"

    # 1. Check robots.txt
    robots_result = json.loads(crawl_robots_txt.__wrapped__(domain))

    # 2. Check HTTP headers on homepage
    headers_info = {}
    try:
        resp = httpx.get(base, timeout=_TIMEOUT, follow_redirects=True, headers=_HEADERS)
        x_robots = resp.headers.get("x-robots-tag", "")
        headers_info = {
            "x_robots_tag": x_robots,
            "has_noai_header": "noai" in x_robots.lower() if x_robots else False,
            "has_noimageai_header": "noimageai" in x_robots.lower() if x_robots else False,
        }
    except Exception as e:
        headers_info = {"error": str(e)}

    # 3. Check llms.txt
    llms_result = json.loads(check_llms_txt.__wrapped__(domain))

    # 4. Build access matrix
    access_matrix = {}
    robots_access = robots_result.get("ai_crawler_access", {})
    for crawler, info in robots_access.items():
        status = info.get("status", "unknown")
        access_matrix[crawler] = {
            "description": info.get("description", AI_CRAWLERS.get(crawler, "")),
            "robots_txt": status,
            "http_headers": "blocked" if headers_info.get("has_noai_header") else "allowed",
            "overall": "blocked" if "blocked" in status or headers_info.get("has_noai_header") else "allowed",
        }

    blocked = [k for k, v in access_matrix.items() if v["overall"] == "blocked"]
    allowed = [k for k, v in access_matrix.items() if v["overall"] == "allowed"]

    recommendations = []
    if not robots_result.get("exists"):
        recommendations.append("Create a robots.txt file to control crawler access.")
    if len(blocked) == 0:
        recommendations.append("All AI crawlers are currently allowed. Consider if you want to block any for content protection.")
    if len(blocked) == len(AI_CRAWLERS):
        recommendations.append("WARNING: All AI crawlers are blocked. Your content will NOT appear in AI search results (ChatGPT, Perplexity, Google AI Overviews).")
    if "GPTBot" in blocked and "ClaudeBot" not in blocked:
        recommendations.append("GPTBot is blocked but ClaudeBot is not — inconsistent AI crawler policy.")
    if not llms_result.get("has_llms_txt"):
        recommendations.append("No llms.txt found — consider adding one to help AI systems understand your site structure.")

    return json.dumps({
        "domain": parsed.netloc,
        "access_matrix": access_matrix,
        "summary": {
            "total_ai_crawlers": len(AI_CRAWLERS),
            "blocked": len(blocked),
            "allowed": len(allowed),
            "blocked_names": blocked,
            "allowed_names": allowed,
        },
        "robots_txt_exists": robots_result.get("exists", False),
        "llms_txt_exists": llms_result.get("has_llms_txt", False),
        "http_headers": headers_info,
        "recommendations": recommendations,
    })


# ─── PageSpeed Insights (Free, No API Key) ────────────────────────────

# ─── Page Inventory ───────────────────────────────────────────────────────────

@function_tool
def get_page_inventory(
    domain: str = "sourcy.ai",
    category_filter: str = "",
    max_urls: int = 500,
) -> str:
    """Get a categorised page inventory from sourcy.ai's sitemap.

    Wraps crawl_sitemap and classifies each URL by content type:
    blogs, case-studies, trends, static-pages, other.

    Args:
        domain: Domain to inventory (default: 'sourcy.ai')
        category_filter: Filter to one category — 'blogs', 'case-studies',
                         'trends', 'static' or '' for all (default: all)
        max_urls: Maximum URLs to return per category (default 500)
    """
    sitemap_result = json.loads(crawl_sitemap.__wrapped__(domain))

    if "error" in sitemap_result:
        return json.dumps(sitemap_result)

    all_urls = sitemap_result.get("urls", [])

    def _classify(url_str: str) -> str:
        path = urlparse(url_str).path.lower().rstrip("/")
        segments = [s for s in path.split("/") if s]
        if not segments:
            return "static"
        # Skip lang prefixes like /en/, /pt/, etc.
        first = segments[0] if len(segments[0]) > 2 else (segments[1] if len(segments) > 1 else "")
        if first.startswith("blog"):
            return "blogs"
        if first in ("case-studies", "case_studies"):
            return "case-studies"
        if first == "trends":
            return "trends"
        if first in ("sourcing-bags-luggages", "sourcing-hub", "sourcing-playbook-newsletter",
                     "sourcing-results", "sourcing-form", "sourcing"):
            return "sourcing"
        return "static"

    categorised: dict[str, list] = {
        "blogs": [],
        "case-studies": [],
        "trends": [],
        "sourcing": [],
        "static": [],
    }

    for entry in all_urls:
        url_str = entry.get("url", "")
        cat = _classify(url_str)
        if cat in categorised:
            categorised[cat].append({
                "url": url_str,
                "category": cat,
                "lastmod": entry.get("lastmod", ""),
            })

    # Apply category filter
    if category_filter:
        cf = category_filter.lower()
        filtered = {cf: categorised.get(cf, [])}
    else:
        filtered = categorised

    # Apply max_urls per category
    result_categories = {}
    total = 0
    for cat, entries in filtered.items():
        trimmed = entries[:max_urls]
        result_categories[cat] = trimmed
        total += len(trimmed)

    counts = {cat: len(entries) for cat, entries in result_categories.items()}

    return json.dumps({
        "domain": domain,
        "total_sitemap_urls": sitemap_result.get("total_urls", 0),
        "returned_urls": total,
        "category_counts": counts,
        "categories": result_categories,
        "sitemap_url": sitemap_result.get("url", ""),
        "note": (
            f"Showing up to {max_urls} URLs per category. "
            "Use page_prioritizer for traffic-weighted ranking."
        ),
    })


@function_tool
def check_page_speed(url: str) -> str:
    """Check Core Web Vitals and Lighthouse scores via Google PageSpeed Insights API.

    This is free and requires no API key.

    Args:
        url: URL to test (e.g., 'https://sourcy.ai')
    """
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    results = {}
    for strategy in ["mobile", "desktop"]:
        try:
            resp = httpx.get(
                api_url,
                params={"url": url, "strategy": strategy, "category": ["performance", "seo", "accessibility"]},
                timeout=60,
            )
            data = resp.json()

            lighthouse = data.get("lighthouseResult", {})
            categories = lighthouse.get("categories", {})
            audits = lighthouse.get("audits", {})

            # Core Web Vitals
            cwv = {}
            for metric_key, metric_name in [
                ("largest-contentful-paint", "LCP"),
                ("cumulative-layout-shift", "CLS"),
                ("interaction-to-next-paint", "INP"),
                ("total-blocking-time", "TBT"),
                ("first-contentful-paint", "FCP"),
                ("speed-index", "Speed Index"),
            ]:
                audit = audits.get(metric_key, {})
                if audit:
                    cwv[metric_name] = {
                        "value": audit.get("displayValue", ""),
                        "score": audit.get("score"),
                        "numeric_value": audit.get("numericValue"),
                    }

            # Lighthouse category scores
            scores = {}
            for cat_key in ["performance", "seo", "accessibility"]:
                cat = categories.get(cat_key, {})
                if cat:
                    scores[cat_key] = round((cat.get("score", 0) or 0) * 100)

            results[strategy] = {
                "scores": scores,
                "core_web_vitals": cwv,
            }
        except Exception as e:
            results[strategy] = {"error": str(e)}

    # Determine overall CWV status
    mobile = results.get("mobile", {})
    cwv_status = "unknown"
    if "core_web_vitals" in mobile:
        cwv = mobile["core_web_vitals"]
        lcp_val = cwv.get("LCP", {}).get("numeric_value", 0)
        cls_val = cwv.get("CLS", {}).get("numeric_value", 0)
        lcp_good = lcp_val <= 2500 if lcp_val else True
        cls_good = cls_val <= 0.1 if cls_val else True
        if lcp_good and cls_good:
            cwv_status = "good"
        elif not lcp_good and not cls_good:
            cwv_status = "poor"
        else:
            cwv_status = "needs_improvement"

    return json.dumps({
        "url": url,
        "mobile": results.get("mobile", {}),
        "desktop": results.get("desktop", {}),
        "cwv_status": cwv_status,
        "cwv_thresholds": {
            "LCP": "≤2.5s good, ≤4s needs work, >4s poor",
            "CLS": "≤0.1 good, ≤0.25 needs work, >0.25 poor",
            "INP": "≤200ms good, ≤500ms needs work, >500ms poor",
        },
    })
