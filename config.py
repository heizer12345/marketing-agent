import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Public marketing site (briefing links, page references) ---
PUBLIC_SITE_URL = os.getenv("PUBLIC_SITE_URL", "https://www.sourcy.ai").rstrip("/")

# --- Base paths ---
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
SPECS_DIR = BASE_DIR / "specs"
SKILLS_DIR = BASE_DIR / "skills"
CREDENTIALS_DIR = BASE_DIR / "credentials"
OUTPUT_DIR = BASE_DIR / "public" / "reports"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Content Engine output ---
CONTENT_OUTPUT_DIR = BASE_DIR / "public" / "content"
for _subdir in ("blogs", "audits", "briefs", "landing-pages", "calendars"):
    (CONTENT_OUTPUT_DIR / _subdir).mkdir(parents=True, exist_ok=True)

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- Google Cloud / Auth ---
_DEFAULT_GOOGLE_CREDENTIALS_PATH = CREDENTIALS_DIR / "service-account-key.json"
_INLINE_GOOGLE_CREDENTIALS_PATH = CREDENTIALS_DIR / "service-account-key.inline.json"
_INLINE_GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", "").strip()
_GOOGLE_CREDENTIALS_ENV_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

# On cloud hosts: store full JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON env var.
# For local dev, we persist the inline JSON into the repo-local credentials dir so
# the same path works on Windows and future restarts do not depend on /tmp.
def _resolve_credentials_path(path: str | Path) -> Path:
    """Always resolve to an absolute path under BASE_DIR when relative."""
    p = Path(path)
    if not p.is_absolute():
        p = BASE_DIR / p
    return p.resolve()


if _INLINE_GOOGLE_CREDENTIALS_JSON:
    _INLINE_GOOGLE_CREDENTIALS_PATH.write_text(_INLINE_GOOGLE_CREDENTIALS_JSON, encoding="utf-8")
    GOOGLE_APPLICATION_CREDENTIALS = str(_resolve_credentials_path(_INLINE_GOOGLE_CREDENTIALS_PATH))
elif _GOOGLE_CREDENTIALS_ENV_PATH:
    GOOGLE_APPLICATION_CREDENTIALS = str(_resolve_credentials_path(_GOOGLE_CREDENTIALS_ENV_PATH))
else:
    GOOGLE_APPLICATION_CREDENTIALS = str(_resolve_credentials_path(_DEFAULT_GOOGLE_CREDENTIALS_PATH))

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS


def google_credentials_path() -> Path:
    return Path(GOOGLE_APPLICATION_CREDENTIALS)

# --- Google Ads (OAuth2) ---
GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
GOOGLE_ADS_CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
GOOGLE_ADS_CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")
GOOGLE_ADS_REFRESH_TOKEN = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "")
GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "")
GOOGLE_ADS_LOGIN_CUSTOMER_ID = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")

# --- Google Analytics GA4 ---
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "")

# --- Google Search Console ---
SEARCH_CONSOLE_SITE_URL = os.getenv("SEARCH_CONSOLE_SITE_URL", "")

# --- SEMrush ---
SEMRUSH_API_KEY = os.getenv("SEMRUSH_API_KEY", "")

# --- GEO/AEO Visibility APIs (optional) ---
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

# --- Meta Ads (Facebook Business) ---
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID", "").replace("-", "")
META_APP_ID = os.getenv("META_APP_ID", "")
META_APP_SECRET = os.getenv("META_APP_SECRET", "")

# --- Instagram (via Meta Graph API) ---
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")

# --- PostHog Analytics ---
POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY", "")
POSTHOG_PROJECT_ID = os.getenv("POSTHOG_PROJECT_ID", "")
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.posthog.com")


def has_google_credentials() -> bool:
    """Return True when GA4/Search Console credentials file exists."""
    return google_credentials_path().is_file()


def ping_ga4() -> dict:
    """Lightweight live check — returns {ok, detail, sessions?}."""
    if not has_ga4_configured():
        return {"ok": False, "detail": "GA4_PROPERTY_ID or credentials missing"}
    try:
        from datetime import datetime, timedelta
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
        from tools.google_credentials import get_service_account_credentials, GA4_SCOPES

        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        client = BetaAnalyticsDataClient(
            credentials=get_service_account_credentials(GA4_SCOPES)
        )
        resp = client.run_report(
            RunReportRequest(
                property=f"properties/{GA4_PROPERTY_ID}",
                metrics=[Metric(name="sessions")],
                date_ranges=[DateRange(start_date=start, end_date=end)],
            )
        )
        sessions = resp.rows[0].metric_values[0].value if resp.rows else "0"
        return {"ok": True, "detail": f"property {GA4_PROPERTY_ID}", "sessions_7d": sessions}
    except Exception as ex:
        return {"ok": False, "detail": str(ex)[:200]}


def ping_search_console() -> dict:
    """Lightweight live check — returns {ok, detail}."""
    if not has_search_console_configured():
        return {"ok": False, "detail": "SEARCH_CONSOLE_SITE_URL or credentials missing"}
    try:
        from tools.search_console import _query_search_analytics

        rows = _query_search_analytics(["query"], "last_7_days", row_limit=1)
        if rows and "error" in rows[0]:
            return {"ok": False, "detail": rows[0]["error"][:200]}
        return {"ok": True, "detail": SEARCH_CONSOLE_SITE_URL}
    except Exception as ex:
        return {"ok": False, "detail": str(ex)[:200]}


def has_ga4_configured() -> bool:
    return bool(GA4_PROPERTY_ID) and has_google_credentials()


def has_search_console_configured() -> bool:
    return bool(SEARCH_CONSOLE_SITE_URL) and has_google_credentials()


def ping_google_ads() -> dict:
    if not GOOGLE_ADS_REFRESH_TOKEN:
        return {"ok": False, "detail": "GOOGLE_ADS_REFRESH_TOKEN missing"}
    try:
        from tools.google_ads import _run_query

        rows = _run_query(
            "SELECT metrics.impressions FROM customer WHERE segments.date DURING LAST_7_DAYS LIMIT 1"
        )
        if rows and isinstance(rows[0], dict) and rows[0].get("error"):
            return {"ok": False, "detail": rows[0]["error"][:200]}
        return {"ok": True, "detail": f"customer {GOOGLE_ADS_CUSTOMER_ID or '(unset)'}"}
    except Exception as ex:
        return {"ok": False, "detail": str(ex)[:200]}


def ping_meta_ads() -> dict:
    if not META_ACCESS_TOKEN or not META_AD_ACCOUNT_ID:
        return {"ok": False, "detail": "META_ACCESS_TOKEN or META_AD_ACCOUNT_ID missing"}
    try:
        from tools.meta_ads import _init_api

        acct = _init_api()
        if not acct:
            return {"ok": False, "detail": "Meta API init failed (check token / account id)"}
        info = acct.api_get(fields=["name", "account_status"])
        return {
            "ok": True,
            "detail": f"{info.get('name', 'account')} · status {info.get('account_status')}",
        }
    except Exception as ex:
        return {"ok": False, "detail": str(ex)[:200]}


def ping_instagram() -> dict:
    if not INSTAGRAM_BUSINESS_ACCOUNT_ID or not META_ACCESS_TOKEN:
        return {"ok": False, "detail": "INSTAGRAM_BUSINESS_ACCOUNT_ID or META_ACCESS_TOKEN missing"}
    try:
        import httpx

        url = f"https://graph.facebook.com/v21.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}"
        resp = httpx.get(
            url,
            params={
                "fields": "username,followers_count,media_count",
                "access_token": META_ACCESS_TOKEN,
            },
            timeout=30,
        )
        data = resp.json()
        if "error" in data:
            return {"ok": False, "detail": data["error"].get("message", str(data))[:200]}
        return {
            "ok": True,
            "detail": (
                f"@{data.get('username', '?')} · "
                f"{data.get('followers_count', 0)} followers · "
                f"{data.get('media_count', 0)} posts"
            ),
        }
    except Exception as ex:
        return {"ok": False, "detail": str(ex)[:200]}


def ping_posthog() -> dict:
    if not POSTHOG_API_KEY or not POSTHOG_PROJECT_ID:
        return {"ok": False, "detail": "POSTHOG_API_KEY or POSTHOG_PROJECT_ID missing"}
    try:
        from tools.posthog import _hogql_query

        result = _hogql_query(
            "SELECT count() AS events FROM events WHERE timestamp > now() - interval 7 day"
        )
        if not result or result.get("error"):
            return {"ok": False, "detail": (result or {}).get("error", "empty response")[:200]}
        events_7d = result.get("results", [[0]])[0][0]
        return {"ok": True, "detail": f"project {POSTHOG_PROJECT_ID}", "events_7d": str(events_7d)}
    except Exception as ex:
        return {"ok": False, "detail": str(ex)[:200]}


def ping_semrush() -> dict:
    if not SEMRUSH_API_KEY:
        return {"ok": False, "detail": "SEMRUSH_API_KEY missing"}
    try:
        import httpx

        resp = httpx.get(
            "https://api.semrush.com/",
            params={
                "type": "domain_ranks",
                "key": SEMRUSH_API_KEY,
                "domain": "sourcy.ai",
                "database": "us",
                "export_columns": "Dn,Rk",
            },
            timeout=30,
        )
        text = resp.text.strip()
        if text.startswith("ERROR"):
            return {"ok": False, "detail": text[:200]}
        return {"ok": True, "detail": "sourcy.ai domain ranks (US)"}
    except Exception as ex:
        return {"ok": False, "detail": str(ex)[:200]}


def ping_sourcy_db() -> dict:
    try:
        from tools.sourcy_activation import _api_get

        rows = _api_get("unified_activation_conversations", {"select": "id", "limit": 1})
        if not rows or (isinstance(rows[0], dict) and rows[0].get("error")):
            err = rows[0].get("error", "no data") if rows else "no response"
            return {"ok": False, "detail": str(err)[:200]}
        return {"ok": True, "detail": "api.sourcy.ai PostgREST"}
    except Exception as ex:
        return {"ok": False, "detail": str(ex)[:200]}


def ping_openai() -> dict:
    if not OPENAI_API_KEY:
        return {"ok": False, "detail": "OPENAI_API_KEY missing"}
    return {"ok": True, "detail": "key configured"}


def ping_all_integrations() -> dict[str, dict]:
    """Live API checks for Memory tab and diagnostics (parallel)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    checks = {
        "openai": ping_openai,
        "ga4": ping_ga4,
        "search_console": ping_search_console,
        "google_ads": ping_google_ads,
        "meta_ads": ping_meta_ads,
        "semrush": ping_semrush,
        "instagram": ping_instagram,
        "posthog": ping_posthog,
        "sourcy_db": ping_sourcy_db,
    }
    out: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=len(checks)) as pool:
        futures = {pool.submit(fn): key for key, fn in checks.items()}
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                out[key] = fut.result()
            except Exception as ex:
                out[key] = {"ok": False, "detail": str(ex)[:200]}
    return out


# --- Target Markets ---
def load_target_markets():
    path = CONFIG_DIR / "target_markets.json"
    with open(path) as f:
        return json.load(f)

TARGET_MARKETS = load_target_markets()
TARGET_COUNTRY_CODES = [c["code"] for c in TARGET_MARKETS["target_countries"]]
ACCEPTABLE_COUNTRY_CODES = [c["code"] for c in TARGET_MARKETS.get("acceptable_countries", [])]
ALL_VALID_CODES = TARGET_COUNTRY_CODES + ACCEPTABLE_COUNTRY_CODES
KPI_TARGETS = TARGET_MARKETS.get("kpi_targets", {})


# --- Competitors ---
def load_competitors():
    """Load competitor registry from config/competitors.json."""
    path = CONFIG_DIR / "competitors.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


COMPETITORS = load_competitors()

# --- Builder.io (blog / case-study CMS) ---
BUILDER_API_KEY = os.getenv("BUILDER_API_KEY", "")

# --- Sourcy PostgREST (trends / market data) ---
POSTGREST_URL = os.getenv("POSTGREST_URL", "https://api.sourcy.ai/db")
POSTGREST_JWT = os.getenv("POSTGREST_JWT", "")

# --- Website Overhaul ---
# Path to the Sourcy Next.js customer app (for source_mapper + page_rewriter)
CUSTOMER_APP_PATH = Path(
    os.getenv(
        "CUSTOMER_APP_PATH",
        str(BASE_DIR.parent / "Sourcy Activation Bot" / "sourcy-new-website-nextjs"),
    )
)

# Reviews output directory (proposed changes saved here for human approval)
REVIEWS_OUTPUT_DIR = BASE_DIR / "public" / "reviews"
REVIEWS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_competitors_by_tier(tier: str = "primary") -> list:
    """Get flat list of competitors filtered by tier."""
    results = []
    for category, entries in COMPETITORS.items():
        if isinstance(entries, list):
            results.extend([c for c in entries if c.get("tier") == tier])
    return results


def load_knowledge(filename: str) -> str:
    """Load a knowledge base MD file content."""
    path = KNOWLEDGE_DIR / filename
    if path.exists():
        # Explicit utf-8 — on Windows the default codec is cp1252 which chokes
        # on em dashes / curly quotes that appear throughout the knowledge MD files.
        return path.read_text(encoding="utf-8")
    return ""
