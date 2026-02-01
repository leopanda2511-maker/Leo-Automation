from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config.settings import settings
from typing import Optional, Dict, Any
import json


SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]


def get_oauth_flow() -> Flow:
    """Create OAuth flow for YouTube authorization"""
    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.oauth_redirect_uri]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=settings.oauth_redirect_uri
    )
    return flow


def get_authorization_url(user_id: str = None) -> tuple[str, str]:
    """Get authorization URL for OAuth flow"""
    flow = get_oauth_flow()
    # Encode user_id in state if provided
    state = user_id if user_id else None
    authorization_url, flow_state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=state
    )
    return authorization_url, flow_state or state


def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """Exchange authorization code for tokens"""
    flow = get_oauth_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None
    }


def get_credentials_from_token(token_data: Dict[str, Any]) -> Credentials:
    """Create Credentials object from stored token data"""
    return Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id", settings.google_client_id),
        client_secret=token_data.get("client_secret", settings.google_client_secret),
        scopes=token_data.get("scopes", SCOPES)
    )


def refresh_credentials(credentials: Credentials) -> Credentials:
    """Refresh expired credentials"""
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return credentials
