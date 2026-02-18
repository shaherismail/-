"""
generate_token.py – One-time local script to generate a YouTube OAuth2
refresh token. Run this ONCE on your local machine, then store the
refresh token as the YOUTUBE_REFRESH_TOKEN GitHub Secret.

Usage:
    pip install google-auth-oauthlib
    python scripts/generate_token.py

You will be prompted to open a browser URL and paste the authorization code.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# OAuth2 credentials provided by user
CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "333306232532-pdoi4kln06ja4c4rg6j711o2e7kf7qjr.apps.googleusercontent.com")
CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "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")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

CLIENT_CONFIG = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}


def main():
    flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    print("\n" + "=" * 60)
    print("STEP 1: Open this URL in your browser and log in:")
    print("=" * 60)
    print(f"\n{authorization_url}\n")
    print("=" * 60)
    
    code = input("STEP 2: Paste the authorization code here: ").strip()
    flow.fetch_token(code=code)
    creds = flow.credentials

    print("\n" + "=" * 60)
    print("SUCCESS! Copy the following refresh token into your")
    print("GitHub Secret named: YOUTUBE_REFRESH_TOKEN")
    print("=" * 60)
    print(f"\nRefresh Token:\n{creds.refresh_token}\n")

    # Also save to a local file for reference
    token_data = {
        "refresh_token": creds.refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    with open("youtube_token.json", "w") as f:
        json.dump(token_data, f, indent=2)
    print("Token also saved to: youtube_token.json")
    print("⚠️  Do NOT commit youtube_token.json to git!")


if __name__ == "__main__":
    main()
