import csv
import os
import time
from integrations.gmail_client import send_email
from kb import add_entry

RATE = int(os.environ.get('PROSPECT_RATE_LIMIT_PER_MIN', '12'))
DRY_RUN = os.environ.get('PROSPECT_DRY_RUN', 'true').lower() == 'true'
SENDER_NAME = os.environ.get('PROSPECT_SENDER_NAME', '')
SENDER_EMAIL = os.environ.get('PROSPECT_SENDER_EMAIL', '')


def main():
    with open('leads.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            to = row['email']
            subject = row.get('subject', 'Hello')
            body = row.get('body', '')
            send_email(to, subject, body, dry_run=DRY_RUN)
            add_entry('prospect', to, subject)
            time.sleep(60 / RATE)

if __name__ == '__main__':
    main()
