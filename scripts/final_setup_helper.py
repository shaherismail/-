import os
import requests
import hashlib
import base64
import secrets

# YouTube Credentials
YT_CLIENT_ID = "333306232532-pdoi4kln06ja4c4rg6j711o2e7kf7qjr.apps.googleusercontent.com"
YT_CLIENT_SECRET = "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"
YT_AUTH_CODE = "4/0AfrIepAk1PUg64gJjASGftmBoJxeqSibaA8WWYfAV0IgLBkruzhj6GLuBtJYPaBdPhZS-w"
REDIRECT_URI = "http://localhost:8080"

# TikTok Credentials
TT_CLIENT_KEY = "awol3vl3mst4jc0o"

def get_yt_refresh_token():
    print("\n--- [1/2] YouTube: Exchanging Code for Refresh Token ---")
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": YT_AUTH_CODE,
        "client_id": YT_CLIENT_ID,
        "client_secret": YT_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    resp = requests.post(url, data=payload)
    if resp.status_code == 200:
        token = resp.json().get("refresh_token")
        print(f"✅ YouTube Refresh Token: {token}")
        return token
    else:
        print(f"❌ YouTube Error: {resp.text}")
        return None

def generate_tiktok_link():
    print("\n--- [2/2] TikTok: Generating Fixed Authorization Link ---")
    # Generate PKCE
    verifier = secrets.token_urlsafe(64)
    sha256_hash = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(sha256_hash).decode().replace("=", "")
    
    # TikTok Authorize URL
    url = (
        f"https://www.tiktok.com/v2/auth/authorize/?"
        f"client_key={TT_CLIENT_KEY}&"
        f"scope=video.upload,user.info.basic&"
        f"response_type=code&"
        f"redirect_uri={REDIRECT_URI}&"
        f"state=quran_shorts&"
        f"code_challenge={challenge}&"
        f"code_challenge_method=S256"
    )
    print("✅ Please click this link and copy the code after 'code=':")
    print(f"\n{url}\n")
    print(f"⚠️ IMPORTANT: Keep this 'Code Verifier' to exchange the code later:")
    print(f"Code Verifier: {verifier}")

if __name__ == "__main__":
    yt_token = get_yt_refresh_token()
    generate_tiktok_link()
