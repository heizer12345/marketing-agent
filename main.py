"""Marketing Agent v2 — Entry Point."""

import os
import config


def main():
    import uvicorn
    from app.server import app

    target = ", ".join(f"{c['name']}" for c in config.TARGET_MARKETS["target_countries"])

    print("\n" + "=" * 60)
    print("  Sourcy Marketing Analyst v2")
    print("  http://localhost:8000")
    print("=" * 60)
    print(f"  GA4:            {'OK' if config.GA4_PROPERTY_ID else 'Not configured'}")
    print(f"  Search Console: {'OK' if config.SEARCH_CONSOLE_SITE_URL else 'Not configured'}")
    print(f"  Google Ads:     {'OK' if config.GOOGLE_ADS_REFRESH_TOKEN else 'Pending (run setup_google_ads_auth.py)'}")
    print(f"  Meta Ads:       {'OK' if config.META_ACCESS_TOKEN else 'Not configured'}")
    print(f"  Instagram:      {'OK' if getattr(config, 'INSTAGRAM_BUSINESS_ACCOUNT_ID', '') else 'Not configured'}")
    print(f"  PostHog:        {'OK' if getattr(config, 'POSTHOG_API_KEY', '') else 'Not configured'}")
    print(f"  SEMrush:        {'Disabled' if not config.SEMRUSH_API_KEY else 'OK'}")
    print(f"  Target Markets: {target}")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))


if __name__ == "__main__":
    main()
