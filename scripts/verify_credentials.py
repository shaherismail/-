"""
verify_credentials.py – Automatically checks the validity of all API keys
and tokens stored in the .env file.
"""

import os
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
# Load .env manually to avoid dependency issues
def load_env_manual():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v

load_env_manual()

def verify_youtube_api():
    key = os.getenv("YOUTUBE_API_KEY")
    if not key or "YOUR_" in key:
        return "❌ Missing"
    try:
        youtube = build("youtube", "v3", developerKey=key)
        youtube.search().list(q="test", part="id", maxResults=1).execute()
        return "✅ Working"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def verify_youtube_oauth():
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    
    if not client_id or not client_secret: return "❌ Missing Client ID/Secret"
    if not refresh_token: return "⏳ Refresh Token Missing (Upload will fail)"
    
    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
        )
        youtube = build("youtube", "v3", credentials=creds)
        youtube.channels().list(mine=True, part="id").execute()
        return "✅ Working (Ready for upload)"
    except Exception as e:
        return f"❌ OAuth Error: {str(e)}"

def verify_pexels():
    key = os.getenv("PEXELS_API_KEY")
    if not key or "YOUR_" in key:
        return "❌ Missing"
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/curated?per_page=1",
            headers={"Authorization": key},
            timeout=10
        )
        if resp.status_code == 200: return "✅ Working"
        return f"❌ Error: {resp.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def verify_instagram():
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    if not token or not account_id or "YOUR_" in token:
        return "❌ Missing Token or Account ID"
    try:
        url = f"https://graph.facebook.com/v19.0/{account_id}"
        resp = requests.get(url, params={"access_token": token, "fields": "name"}, timeout=10)
        if resp.status_code == 200: return f"✅ Working (Account: {resp.json().get('name')})"
        return f"❌ Error: {resp.json().get('error', {}).get('message')}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def main():
    print("=" * 60)
    print("🔍 API Credential Verification")
    print("=" * 60)
    print(f"YouTube Search API:   {verify_youtube_api()}")
    print(f"YouTube Upload OAuth: {verify_youtube_oauth()}")
    print(f"Pexels API:           {verify_pexels()}")
    print(f"Instagram Graph API:  {verify_instagram()}")
    print("=" * 60)
    print("\nTikTok Verification: Manual (requires approved app)")

if __name__ == "__main__":
    main()
