import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
SCOPES = os.environ.get('GOOGLE_SCOPES', '').split(',')
TOKEN_PATH = Path(os.environ.get('GOOGLE_TOKEN_PATH', 'data/google/token.json'))
CREDS_PATH = Path(os.environ.get('GOOGLE_CREDENTIALS_PATH', 'data/google/credentials.json'))


def ensure_token():
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                data = {
                    "installed": {
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                }
                CREDS_PATH.write_text(__import__('json').dumps(data))
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds

if __name__ == '__main__':
    ensure_token()
