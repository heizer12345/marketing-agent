"""Shared Google service-account helpers for GA4 and Search Console."""

from __future__ import annotations

from google.oauth2 import service_account

import config

GA4_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def get_service_account_credentials(scopes: list[str]):
    """Load service account credentials from the resolved config path."""
    path = config.google_credentials_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Google credentials file not found: {path}. "
            "Set GOOGLE_APPLICATION_CREDENTIALS in .env or add "
            "credentials/service-account-key.json."
        )
    return service_account.Credentials.from_service_account_file(str(path), scopes=scopes)
