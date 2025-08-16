import base64
import os
from email.message import EmailMessage
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from kb import add_entry
from .google_oauth import ensure_token

SCOPES = os.environ.get('GOOGLE_SCOPES', '').split(',')
TOKEN_PATH = os.environ.get('GOOGLE_TOKEN_PATH', 'data/google/token.json')


def _service():
    creds = ensure_token()
    return build('gmail', 'v1', credentials=creds)


def send_email(to: str, subject: str, body: str, dry_run: bool = True):
    service = _service()
    msg = EmailMessage()
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)
    encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    if not dry_run:
        service.users().messages().send(userId='me', body={'raw': encoded}).execute()
    add_entry('gmail_send', to, subject)


def list_recent(max_results: int = 5):
    service = _service()
    res = service.users().messages().list(userId='me', maxResults=max_results).execute()
    msgs = res.get('messages', [])
    add_entry('gmail_list', 'me', str(len(msgs)))
    return msgs
