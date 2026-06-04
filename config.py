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

# On Railway/cloud: store full JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON env var.
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
