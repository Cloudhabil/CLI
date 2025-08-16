import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from kb import add_entry


class GmailClient:
    def __init__(self, creds: Credentials, dry_run: bool = True):
        self.creds = creds
        self.dry_run = dry_run
        self.service = build("gmail", "v1", credentials=creds)

    def send_email(self, sender: str, to: str, subject: str, body: str):
        msg = EmailMessage()
        msg["To"] = to
        msg["From"] = sender
        msg["Subject"] = subject
        msg.set_content(body)
        encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        if not self.dry_run:
            self.service.users().messages().send(userId="me", body={"raw": encoded}).execute()
        add_entry(kind="gmail_send", to=to, subject=subject, dry_run=self.dry_run)

    def list_recent(self, max_results: int = 5):
        msgs = self.service.users().messages().list(userId="me", maxResults=max_results).execute().get("messages", [])
        add_entry(kind="gmail_list", count=len(msgs))
        return msgs
