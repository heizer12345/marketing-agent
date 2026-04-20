"""Web reference fetcher — fetch documentation URLs and extract content for recommendations.

Used by the recommendation engine to pull Google support articles, Meta docs, etc.
and include relevant excerpts + links in recommendations.
"""

import json
import re
from html.parser import HTMLParser
import httpx
from agents import function_tool


class _TextExtractor(HTMLParser):
    """Simple HTML to text converter."""

    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer", "header"):
            self.skip = True
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header"):
            self.skip = False
        if tag in ("p", "div", "h1", "h2", "h3", "h4", "li", "br"):
            self.text.append("\n")
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if hasattr(self, "_in_title") and self._in_title:
            self.title += data.strip()
        if not self.skip:
            self.text.append(data)


@function_tool
def fetch_reference_content(url: str, extract_query: str = "") -> str:
    """Fetch a documentation URL and extract key content for use in recommendations.
    Returns the page title, a content summary, and the URL for linking.

    Use this to pull Google support articles, Meta docs, best practice guides, etc.
    The summary helps you contextualize the recommendation; the URL goes in the reference section.

    Args:
        url: Full URL to fetch (e.g., 'https://support.google.com/analytics/answer/7667196')
        extract_query: Optional query to focus extraction on (e.g., 'data retention settings')
    """
    try:
        resp = httpx.get(
            url,
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 SourcyBot/1.0"},
        )

        if resp.status_code != 200:
            return json.dumps({
                "url": url,
                "fetched": False,
                "error": f"HTTP {resp.status_code}",
            })

        # Parse HTML to extract text
        extractor = _TextExtractor()
        extractor.feed(resp.text)

        raw_text = "".join(extractor.text)
        # Clean up whitespace
        raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)
        raw_text = re.sub(r" {2,}", " ", raw_text)
        raw_text = raw_text.strip()

        # If extract_query provided, try to find the most relevant section
        summary = raw_text[:3000]
        if extract_query:
            query_lower = extract_query.lower()
            lines = raw_text.split("\n")
            # Find the paragraph containing the query terms
            relevant = []
            for i, line in enumerate(lines):
                if query_lower in line.lower() or any(w in line.lower() for w in query_lower.split()):
                    # Include context: 2 lines before and 5 after
                    start = max(0, i - 2)
                    end = min(len(lines), i + 6)
                    relevant.extend(lines[start:end])
                    if len(relevant) > 30:
                        break
            if relevant:
                summary = "\n".join(relevant)[:3000]

        return json.dumps({
            "url": url,
            "fetched": True,
            "title": extractor.title or "(no title)",
            "summary": summary,
            "content_length": len(raw_text),
        })
    except Exception as e:
        return json.dumps({
            "url": url,
            "fetched": False,
            "error": str(e),
        })
