import os

import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def authenticate_trakt():
    # Trakt API credentials
    CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
    CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("TRAKT_REDIRECT_URI")

    # API endpoints
    TRAKT_API_URL = "https://api.trakt.tv"
    TRAKT_AUTH_URL = f"{TRAKT_API_URL}/oauth/authorize"
    TRAKT_TOKEN_URL = f"{TRAKT_API_URL}/oauth/token"

    # Token file path
    token_file = "trakt_token.json"

    # Step 1: Direct user to authorization URL
    auth_url = f"{TRAKT_AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    print(f"Please visit this URL in your browser to authorize the application:\n{auth_url}")

    # Step 2: Get the authorization code from user
    auth_code = input("Enter the authorization code from the browser: ")

    # Step 3: Exchange the code for an access token
    data = {
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    response = requests.post(TRAKT_TOKEN_URL, json=data)
    if response.status_code == 200:
        token_data = response.json()

        # Calculate expiration time
        expires_at = time.time() + token_data["expires_in"]
        token_data["expires_at"] = expires_at

        # Save token data to file
        with open(token_file, 'w') as f:
            json.dump(token_data, f)

        print("Authentication successful! Token saved to trakt_token.json")
        return True
    else:
        print(f"Authentication failed: {response.text}")
        return False


if __name__ == "__main__":
    authenticate_trakt()
