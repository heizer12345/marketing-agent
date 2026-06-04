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
    ga4 = config.ping_ga4()
    gsc = config.ping_search_console()
    ga4_line = "OK" if ga4["ok"] else f"FAILED — {ga4['detail']}"
    gsc_line = "OK" if gsc["ok"] else f"FAILED — {gsc['detail']}"
    if ga4.get("sessions_7d"):
        ga4_line += f" ({ga4['sessions_7d']} sessions, 7d)"
    print(f"  GA4:            {ga4_line}")
    print(f"  Search Console: {gsc_line}")
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
