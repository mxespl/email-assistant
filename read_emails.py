import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Izin yang diminta: CUMA BACA email (nggak bisa hapus/kirim)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    creds = None
    # Udah pernah login? Pakai kartu akses (token.json) yang lama
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Kartu akses kadaluarsa -> perpanjang otomatis
            creds.refresh(Request())
        else:
            # Belum pernah login -> buka browser, minta izin ke lo
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Simpen kartu akses biar nggak perlu login lagi
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def main():
    service = get_gmail_service()

    # Cari 5 email unread di inbox
    results = service.users().messages().list(
        userId="me", q="is:unread in:inbox", maxResults=5
    ).execute()
    messages = results.get("messages", [])

    if not messages:
        print("Nggak ada email unread. Inbox zero!")
        return

    # Ambil pengirim, subjek, dan cuplikan tiap email
    for msg in messages:
        detail = service.users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["From", "Subject"],
        ).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        print("Dari   :", headers.get("From", "-"))
        print("Subjek :", headers.get("Subject", "(tanpa subjek)"))
        print("Cuplik :", detail.get("snippet", ""))
        print("-" * 50)


if __name__ == "__main__":
    main()