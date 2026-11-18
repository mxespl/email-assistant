import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Permission we ask for: READ-ONLY (can't delete or send)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    creds = None
    # Logged in before? Reuse the old key card (token.json)
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Key card expired -> renew it automatically
            creds.refresh(Request())
        else:
            # Never logged in -> open the browser and ask for permission
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the key card so we don't have to log in again
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def main():
    service = get_gmail_service()

    # Find 5 unread emails in the inbox
    results = service.users().messages().list(
        userId="me", q="is:unread in:inbox", maxResults=5
    ).execute()
    messages = results.get("messages", [])

    if not messages:
        print("No unread emails. Inbox zero!")
        return

    # Get sender, subject, and snippet of each email
    for msg in messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["From", "Subject"],
        ).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        print("From    :", headers.get("From", "-"))
        print("Subject :", headers.get("Subject", "(no subject)"))
        print("Snippet :", detail.get("snippet", ""))
        print("-" * 50)


if __name__ == "__main__":
    main()