import csv
import os
import time
from dotenv import load_dotenv
from pathlib import Path
from integrations.gmail_client import GmailClient
from integrations.google_oauth import ensure_token
from kb import add_entry

load_dotenv(".env.local")


def main():
    rate = int(os.environ.get("PROSPECT_RATE_LIMIT_PER_MIN", "12"))
    dry = os.environ.get("PROSPECT_DRY_RUN", "true").lower() == "true"
    token = ensure_token(os.environ["GOOGLE_CLIENT_ID"], os.environ["GOOGLE_CLIENT_SECRET"],
                         os.environ["GOOGLE_SCOPES"].split(","), Path(os.environ["GOOGLE_TOKEN_PATH"]))
    gmail = GmailClient(token, dry_run=dry)
    sender = os.environ["PROSPECT_SENDER_EMAIL"]
    with open("leads.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gmail.send_email(sender, row["email"], row["subject"], row["body"])
            add_entry(kind="prospect", to=row["email"])
            time.sleep(60 / rate)


if __name__ == "__main__":
    main()
