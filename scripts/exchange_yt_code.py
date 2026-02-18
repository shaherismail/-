import os
import requests
import json

# User provided credentials
CLIENT_ID = "333306232532-pdoi4kln06ja4c4rg6j711o2e7kf7qjr.apps.googleusercontent.com"
CLIENT_SECRET = "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"
AUTH_CODE = "4/0AfrIepAk1PUg64gJjASGftmBoJxeqSibaA8WWYfAV0IgLBkruzhj6GLuBtJYPaBdPhZS-w"
REDIRECT_URI = "http://localhost:8080" # This must match what was in the link

def exchange_code():
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": AUTH_CODE,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"SUCCESS_REFRESH_TOKEN: {data['refresh_token']}")
    else:
        print(f"FAILED: {response.text}")

if __name__ == "__main__":
    exchange_code()
