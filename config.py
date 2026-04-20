import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Base paths ---
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
SPECS_DIR = BASE_DIR / "specs"
SKILLS_DIR = BASE_DIR / "skills"
OUTPUT_DIR = BASE_DIR / "public" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Content Engine output ---
CONTENT_OUTPUT_DIR = BASE_DIR / "public" / "content"
for _subdir in ("blogs", "audits", "briefs", "landing-pages"):
    (CONTENT_OUTPUT_DIR / _subdir).mkdir(parents=True, exist_ok=True)

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- Google Cloud / Auth ---
# On Railway/cloud: store full JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON env var
if _cred_json := os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
    _cred_path = Path("/tmp/google_creds.json")
    _cred_path.write_text(_cred_json)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_cred_path)

GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(BASE_DIR / "credentials" / "service-account-key.json")
)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

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
        return path.read_text()
    return ""
