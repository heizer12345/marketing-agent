"""One-time setup script to get Google Ads OAuth2 refresh token.

Run this once: python setup_google_ads_auth.py
It will open your browser, you log in, and it saves the refresh token to .env
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

OAUTH_CLIENT_FILE = "credentials/client_secret_349420254291-hns01gj0di72viag0vf79ei3ohlobkjb.apps.googleusercontent.com.json"

SCOPES = ["https://www.googleapis.com/auth/adwords"]


def main():
    print("=" * 60)
    print("Google Ads OAuth2 Setup")
    print("=" * 60)
    print()
    print("This will open your browser to authorize access to Google Ads.")
    print("Log in with the Google account that has access to your Ads account.")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_FILE, scopes=SCOPES)
    credentials = flow.run_local_server(port=8080)

    print()
    print("=" * 60)
    print("SUCCESS! Add these to your .env file:")
    print("=" * 60)
    print()

    # Read the client file to get client_id and client_secret
    with open(OAUTH_CLIENT_FILE) as f:
        client_data = json.load(f)
        # Handle both "installed" and "web" client types
        client_info = client_data.get("installed", client_data.get("web", {}))

    print(f"GOOGLE_ADS_CLIENT_ID={client_info['client_id']}")
    print(f"GOOGLE_ADS_CLIENT_SECRET={client_info['client_secret']}")
    print(f"GOOGLE_ADS_REFRESH_TOKEN={credentials.refresh_token}")
    print()
    print("Copy these lines into your .env file.")
    print()

    # Auto-append to .env if it exists
    try:
        with open(".env", "a") as f:
            f.write(f"\n# Google Ads OAuth2 (auto-generated)\n")
            f.write(f"GOOGLE_ADS_CLIENT_ID={client_info['client_id']}\n")
            f.write(f"GOOGLE_ADS_CLIENT_SECRET={client_info['client_secret']}\n")
            f.write(f"GOOGLE_ADS_REFRESH_TOKEN={credentials.refresh_token}\n")
        print("Auto-saved to .env file!")
    except Exception:
        print("Could not auto-save to .env. Please copy manually.")


if __name__ == "__main__":
    main()
