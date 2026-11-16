import os
import base64
from email.utils import parsedate_to_datetime
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailLoginExpired(Exception):
    """The Gmail key card (token.json) is missing or no longer works."""


def get_gmail_service(allow_login=True):
    """Log in to Gmail.
    allow_login=True  -> if the key card is dead, open the browser to log in again.
    allow_login=False -> don't open a browser (nobody is there to click it during an
                         automatic run); raise GmailLoginExpired instead."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())  # try to renew the key card
            except RefreshError:
                creds = None  # renewal refused: the key card is dead (e.g. 7-day Testing limit)

        if not creds or not creds.valid:
            if not allow_login:
                raise GmailLoginExpired("Gmail login expired or missing. Run: python gmail_tools.py")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _decode(data):
    """Open Gmail's 'sealed envelope' (base64) into plain text."""
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")


def _extract_body(payload):
    """Find the plain-text version of the email inside the 'nested package'."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _decode(payload["body"]["data"])
    for part in payload.get("parts", []):
        text = _extract_body(part)
        if text:
            return text
    return ""


def _format_date(raw):
    """Turn any email date stamp into one clean format, in your local time."""
    if not raw:
        return "unknown"
    try:
        dt = parsedate_to_datetime(raw).astimezone()  # convert to your laptop's time zone
        return dt.strftime("%a, %d %b %Y %H:%M")
    except (TypeError, ValueError):
        return raw  # weird format: just show it as-is


def get_unread_emails(max_results=5, allow_login=True):
    """Get full unread emails: id, sender, date, subject, body."""
    service = get_gmail_service(allow_login=allow_login)
    results = service.users().messages().list(
        userId="me", q="is:unread category:primary", maxResults=max_results
    ).execute()

    emails = []
    for msg in results.get("messages", []):
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        body = _extract_body(detail["payload"]) or detail.get("snippet", "")
        emails.append({
            "id": msg["id"],
            "from": headers.get("From", "-"),
            "date": _format_date(headers.get("Date", "")),
            "subject": headers.get("Subject", "(no subject)"),
            "body": body,
        })
    return emails


# Test: only runs when this file is run directly
if __name__ == "__main__":
    for email in get_unread_emails():
        print("From    :", email["from"])
        print("Subject :", email["subject"])
        print("Body    :", email["body"][:300])
        print("-" * 50)