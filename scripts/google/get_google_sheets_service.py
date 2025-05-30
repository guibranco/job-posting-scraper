# pylint: disable=broad-exception-caught
# pylint: disable=broad-exception-raised
# type: ignore

# Standard imports
import base64
import os
import pickle
from typing import Any

# Third party imports
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Local imports
from scripts.google.create_oauth_json import create_oauth_json
from utils.handle_exceptions import handle_exceptions
import fickling

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


@handle_exceptions(raise_on_error=True)
def get_google_sheets_service():
    """Initialize Google Sheets API client using OAuth"""
    env = os.getenv("ENV", "")
    is_local = env.lower() == "local"

    creds: Credentials | None = None

    # For GitHub Actions, try to use token from environment variable
    token_pickle_base64 = os.getenv("GOOGLE_TOKEN_PICKLE")
    if not is_local and token_pickle_base64:
        try:
            create_oauth_json()
            print("Created google-oauth.json from environment variable")

            token_pickle = base64.b64decode(token_pickle_base64)
            creds = pickle.loads(token_pickle)
            print("Loaded token from GOOGLE_TOKEN_PICKLE environment variable")

        except Exception as e:
            print(f"Failed to load token from environment: {e}")

    # For local development, use token.pickle file
    elif is_local and os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = fickling.load(token)
            print("Loaded token from token.pickle file")

    # If token does not exist or is invalid, get new one
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This will only work in local environment
            if is_local:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "google-oauth.json",
                    SCOPES,
                )
                creds = flow.run_local_server(port=0)

                # Save token locally
                with open("token.pickle", "wb") as token:
                    pickle.dump(creds, token)
            else:
                raise Exception(
                    "Cannot authenticate with Google in GitHub Actions without GOOGLE_TOKEN_PICKLE"
                )

    service: Any = build("sheets", "v4", credentials=creds)
    return service
