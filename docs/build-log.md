# Build log

> Detailed, step-by-step notes written while building this project (phases 1–6): concepts, every setup step, code walkthroughs, bugs hit and how they were fixed. For a quick start, see the main [README](../README.md).


A **read-only** AI assistant for my personal Gmail. It categorizes emails, summarizes the important ones, flags what's urgent, pulls out deadlines and requested actions, and builds a daily overview.

**Goals**
1. Automatically categorize incoming emails.
2. Generate concise summaries of important messages.
3. Identify potentially urgent communications.
4. Extract deadlines, dates and requested actions.
5. Generate a daily overview of important emails and outstanding tasks.

**Ground rules**
- **Read-only.** The assistant never writes, sends, or deletes anything in Gmail. Scope stays `gmail.readonly`.
- Gmail access goes through the Gmail API + OAuth (log in to Google once; the script never sees my password).
- Secret files (`.env`, `credentials.json`, `token.json`) must never be uploaded to GitHub, screenshotted, or pasted into a chat.

**Tech stack:** Python 3.14 · VS Code · Anthropic SDK · Gmail API

---

## Roadmap

> 🎉 **Version 1 finished on Nov 16, 2026:** all 5 goals work, and the report is built automatically every morning.

| Phase | Name | What it does | Goals | Status |
|---|---|---|---|---|
| 1 | Hello Claude | Python can call the Claude API | – | ✅ Done (Nov 12, 2026) |
| 2 | Read emails | Fetch unread emails via the Gmail API | – | ✅ Done (Nov 15, 2026) |
| 3 | Summarize | Email in → summary out | 2 | ✅ Done (Nov 15, 2026) |
| 4 | Smart analysis | Per email, Claude returns **structured data (JSON)**: category, urgency (High/Medium/Low + why), deadlines & dates, requested actions | 1, 3, 4 | ✅ Done (Nov 16, 2026) |
| 5 | Daily overview | One digest: 🔴 urgent first, 📅 deadlines sorted by date, ✅ to-do list. Saved as a file. Plus a small "memory" file so tasks stay until marked done and emails aren't processed twice | 5 | ✅ Done (Nov 16, 2026) |
| 6 | Run automatically | Windows Task Scheduler runs it every morning (e.g. 7:00) | all | ✅ Done (Nov 16, 2026) |
| 7 | Later (optional) | Upload to GitHub, keyword filter, topics (food, jobs, coupons…), email count setting, chat-style agent | extras | ⏳ Next: GitHub |

### Decision log
- **Nov 16, 2026: dropped draft replies.** The original Phase 4 would have saved reply drafts in Gmail. Dropped because (a) most inbox emails don't need a reply, so drafts would pile up, (b) running hourly would re-draft the same unread email again and again, and (c) it needs the `gmail.compose` scope, which technically also allows sending. The goals above are all read-only, which is simpler and safer. `SCOPES` was reverted to `gmail.readonly` and `token.json` regenerated.

---

## Folder structure (current)

```
email-assistant/
├── venv/              ← Python "room" just for this project (don't edit)
├── .env               ← Claude API key (SECRET)
├── .gitignore         ← list of files that must never go into Git/GitHub
├── credentials.json   ← the app's "ID card" at Google (SECRET)
├── token.json         ← Gmail key card, created automatically after login (SECRET)
├── hello.py           ← Phase 1
├── read_emails.py     ← Phase 2 (kept as an archive)
├── gmail_tools.py     ← Gmail "toolbox" reused by other scripts (Phase 3, updated in Phase 4)
├── summarize.py       ← Phase 3: Gmail + Claude → summaries (kept as an archive)
├── analyze.py         ← Phase 4: category, urgency, deadlines, actions (JSON)
├── daily.py           ← Phase 5: notebook + daily overview  ← RUN THIS DAILY
├── done.py            ← Phase 5: mark tasks as done
├── run_daily.bat      ← Phase 6: "one-click button" the scheduler presses
├── run_log.txt        ← Phase 6: "black box" log of every automatic run (PERSONAL DATA)
├── memory.json        ← the "notebook", created automatically (PERSONAL DATA)
├── daily_overview.md  ← the daily report, created automatically (PERSONAL DATA)
├── README.md          ← main README
└── docs/build-log.md  ← this file
```

---

## Daily routine (version 1)

| When | What |
|---|---|
| Every morning | Open `daily_overview.md` (right-click → **Open Preview**). Check the **date in the title** is today. |
| Finished a task | `python done.py` → type its number(s) |
| Report shows a ⚠️ banner | Gmail login expired (about once a week, see Phase 6). Run `python gmail_tools.py`, log in, then `python daily.py`. |
| Report date is NOT today | Open `run_log.txt`, scroll to the bottom, read the error. |
| Want it right now | `python daily.py` (or double-click `run_daily.bat`) |

## Every time you start working again

1. Open VS Code → File → Open Folder → `email-assistant`
2. Terminal → New Terminal
3. `venv\Scripts\activate`. Make sure **(venv)** shows up.

---

## Phase 1 — Hello Claude ✅

**Goal:** a Python script sends a message to Claude and prints the answer in the terminal.

**Result:** `python hello.py` → Claude answers. Works.

**Analogy:** API key = access card · `anthropic` library = phone · `hello.py` = you calling Claude.

### Steps

**1. Install Python**
- Download from python.org (got version 3.14).
- Must tick **"Add Python to environment variables"** (PATH).
- Check in PowerShell: `python --version`
- Note: if you open the installer again and see "Modify Setup", Python is already installed.

**2. Install VS Code**: from code.visualstudio.com

**3. Install the "Python" extension** (by Microsoft) in VS Code → `Ctrl+Shift+X` → search "Python" → Install

**4. Create the project folder**
- Folder: any folder you like, e.g. `Documents\Projects\email-assistant`
- Open it in VS Code: File → Open Folder → pick the folder → "Yes, I trust the authors"

**5. Create & activate the venv** (in the VS Code terminal: Terminal → New Terminal)
```
python -m venv venv
venv\Scripts\activate
```
It worked if **(venv)** appears at the start of the terminal line.

If you get *"running scripts is disabled on this system"*: Windows blocks scripts by default. Run this once:
```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
→ type `Y` → run `venv\Scripts\activate` again.

**6. Install libraries**
```
pip install anthropic python-dotenv
```
- `anthropic`: talks to Claude
- `python-dotenv`: reads the API key from the `.env` file

**7. Get an API key** at console.anthropic.com
- Add credit under Billing ($5 is plenty for learning). A Claude.ai subscription is **separate** from the API.
- Click **Get API key** → choose **"Somewhere else"** (the API key option).
- Enter a name, check the **Expires** date, leave Linked account & Scope as default → **Create key**.
- **Copy the key** right away. It's only shown once.
- ⚠️ **Lesson learned:** the first key ended up fully visible in a screenshot, so it was **deleted** on the API Keys page and a new one was created. If a key leaks, don't keep using it: delete it and replace it.
- 📅 Keys expire. If a script suddenly throws an authentication error, first check whether the key has expired → create a new key → update `.env`.

**8. Save the key in `.env`**
```
ANTHROPIC_API_KEY=sk-ant-xxxxx
```
No spaces around `=`, no quotes. The variable name must be exactly `ANTHROPIC_API_KEY`, because the `anthropic` library looks for that name automatically.

**9. Create `hello.py`**
```python
from dotenv import load_dotenv
import anthropic

load_dotenv()                      # read the API key from .env
client = anthropic.Anthropic()     # the "phone" we use to call Claude

message = client.messages.create(
    model="claude-haiku-5-5",      # cheapest & fastest model, great for learning
    max_tokens=500,                # max length of the answer
    messages=[
        {"role": "user", "content": "Hi Claude! Explain in one sentence what you are."}
    ],
)

# Skip the "scratch paper" (thinking), keep only the final answer (text)
print("".join(block.text for block in message.content if block.type == "text"))
```

> Updated in Phase 3: originally this was `print(message.content[0].text)`, which crashes when Claude "thinks" first (see Phase 3, step 4).

| Line | Meaning |
|---|---|
| `load_dotenv()` | Open the `.env` safe and take out the API key |
| `anthropic.Anthropic()` | Grab the "phone" (the key is used automatically) |
| `messages.create(...)` | Call Claude |
| `model` | Which model. Haiku = cheapest & fastest |
| `max_tokens` | Max length of the answer |
| `messages` | What we say to Claude (`role: "user"` = from us) |
| `print(...)` | Show Claude's answer in the terminal (text blocks only) |

**10. Run it**
```
python hello.py
```
✅ Claude answers → Phase 1 done.

---

## Phase 2 — Read emails ✅

**Goal:** a Python script fetches unread emails from Gmail and shows the sender, subject, and snippet.

**Result:** `python read_emails.py` → 5 unread emails show up in the terminal. Works.

### Concept: OAuth (the hotel analogy)

- **Without OAuth:** giving your Google password to an app = handing over your real house key. The app can do anything, and if it leaks, your password leaks too.
- **With OAuth:** you log in directly on Google's page → click **Allow** → Google gives the app a **hotel key card** (a token).
  - **Limited**: it only opens the doors you allowed. These limits are called **scopes**. Here: `gmail.readonly` = read only.
  - **Revocable** any time in your Google account settings (Security → Third-party access).
  - **The script never sees your password.**

| Term / File | Analogy |
|---|---|
| Google Cloud Console | Immigration office, where you register the app |
| Gmail API (Enable) | Opening the "Gmail door" for the project |
| OAuth consent screen | The front desk asking "may this app have access?" |
| Test user | Guest list of a private club. Anyone not on the list gets turned away. |
| `credentials.json` | The app's ID card, so Google knows "this is the email-assistant app" |
| `token.json` | The key card you get after clicking Allow |
| Scope | Which doors that key card can open |

### Steps

**1. Create a Google Cloud project**
- console.cloud.google.com → log in with personal Gmail → accept Terms of Service
- Project dropdown at the top → **New Project** → name `email-assistant` → **Create**
- Make sure **email-assistant** is selected in the top dropdown
- Free, no credit card needed. If offered a "Start free trial", skip it.

**2. Enable the Gmail API**
- Top search bar → **Gmail API** → **Enable**

**3. Set up the OAuth consent screen**
- Search **OAuth consent screen** → opens **Google Auth Platform** → **Get started**
- App name: `email-assistant` · User support email: your own → Next
- Audience: **External** (personal Gmail must be External; Internal is only for Google Workspace) → Next
- Contact info: your own email → Next → accept the policy → **Create**

**4. Add yourself as a test user**
- Google Auth Platform → **Audience** → **Test users** → **+ Add users** → your own Gmail → **Save**
- If you skip this, login fails with *"access blocked"*.

**5. Create the OAuth client & download `credentials.json`**
- Google Auth Platform → **Clients** → **+ Create client**
- Application type: **Desktop app** (the script runs on a laptop, not a website)
- Name: `email-assistant-desktop`
- Checkbox **"Use this client for an AI-powered agent"**: **left unticked**. That option is for agents going through MCP tools; our script talks to the Gmail API directly. Ticking it or not doesn't add permissions either.
- **Create** → **Download JSON** → rename it to **`credentials.json`** → move it into the `email-assistant` folder

**6. Install the Google libraries**
```
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
- `google-api-python-client`: the "phone" to Gmail
- `google-auth-oauthlib`: handles the login & "Allow" flow
- `google-auth-httplib2`: the internet connection (behind the scenes)

**7. Create `read_emails.py`**
```python
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
```

| Part | Meaning |
|---|---|
| `SCOPES` | Doors we ask for: `gmail.readonly` = read only |
| `get_gmail_service()` | Front-desk business: reuse the old token → renew it if expired → if there's none, open the browser to ask permission → save `token.json` |
| `messages().list(q="is:unread in:inbox", maxResults=5)` | Find 5 unread emails in the inbox (the query works just like Gmail's search bar) |
| `messages().get(format="metadata")` | Get each email's details: sender, subject, snippet |
| `print(...)` | Show them in the terminal |

Because the scope is **readonly**, emails are **not** marked as "read".

**8. Run it & grant permission**
```
python read_emails.py
```
- Browser opens → pick the Gmail account (the one registered as a test user)
- The **"Google hasn't verified this app"** screen is normal (it's your own app) → **Continue**
- Permission screen "Read your email..." → tick the checkbox if there is one → **Continue**
- *"The authentication flow has completed"* → close the tab
- The terminal shows the unread emails, and `token.json` appears in the folder
- Later runs don't open the browser anymore.

**9. Create `.gitignore`**
```
# Secrets - NEVER upload
.env
credentials.json
token.json

# Python folders
venv/
__pycache__/
```
(Phase 5 added `memory.json` and `daily_overview.md` under the secrets, see Phase 5.)
- **Git** = a "save point" system for the project, like checkpoints in a game. Can be uploaded to GitHub.
- **`.gitignore`** = the "don't photograph this" list. Git automatically skips everything listed here. It's not just a reminder: Git actually reads and obeys it.
- Git isn't in use yet, but this file kicks in automatically as soon as it is.

---

## Phase 3 — Summarize ✅

**Goal:** fetch full unread emails, send them to Claude, and get a short summary + category + "needs reply?" for each.

**Result:** `python summarize.py` → each unread email gets an English summary, a category, and a "needs reply" verdict. Works.

**Why:** Phase 2 only fetched a *snippet* (about one sentence), which is too little to summarize. So we fetch the full body and hand it to Claude.

### Steps

**1. Create the Gmail "toolbox": `gmail_tools.py`**

Instead of rewriting the Gmail login code in every script, it lives in one file. Other scripts (summarize, drafts, etc.) just "borrow a tool" from it. `read_emails.py` stays as a Phase 2 archive.

```python
import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    """Log in to Gmail (exactly the same as Phase 2)."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
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


def get_unread_emails(max_results=5):
    """Get full unread emails: id, sender, subject, body."""
    service = get_gmail_service()
    results = service.users().messages().list(
        userId="me", q="is:unread in:inbox", maxResults=max_results
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
```

| Part | Meaning |
|---|---|
| `_decode` | Gmail sends the body as "code" (base64), like a sealed envelope. This opens the seal. |
| `_extract_body` | An email is a **nested package**: plain-text version, HTML version (colors/images), attachments. This opens box after box until it finds the plain text. If there is none (HTML-only newsletters), the snippet is used instead. |
| `get_unread_emails` | Returns a tidy **list of emails** instead of printing, so it's easy to hand to Claude. |
| `if __name__ == "__main__"` | Test section. Only runs when you run this file directly, not when another script borrows from it. |

**2. Test the toolbox**
```
python gmail_tools.py
```
- No browser this time: `token.json` from Phase 2 is reused.
- The **Body** is now longer than the Phase 2 snippet (up to the first 300 characters).
- Normal: some bodies look messy or full of links (newsletters/promos), and some are just one sentence (HTML-only emails → snippet fallback).

**3. Create `summarize.py`: Gmail + Claude**
```python
from dotenv import load_dotenv
import anthropic
from gmail_tools import get_unread_emails  # borrow a tool from the toolbox

load_dotenv()
client = anthropic.Anthropic()

# Claude's "briefing": what the job is & what the report looks like
SYSTEM_PROMPT = """You are a personal email assistant. Your job is to summarize one email.
Always answer in English, briefly, using exactly this format:

Summary: <1-2 sentences with the core of the email>
Category: <Important / Info / Promo / Spam>
Needs reply: <Yes / No> - <short reason>"""


def summarize_email(email):
    """Send one email to Claude and get its summary back."""
    content = (
        f"From: {email['from']}\n"
        f"Subject: {email['subject']}\n\n"
        f"{email['body'][:4000]}"  # cut very long emails to save credit
    )
    message = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=1024,  # extra room: thinking also uses tokens
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    # Skip the "scratch paper" (thinking), keep only the final answer (text)
    return "".join(block.text for block in message.content if block.type == "text")


def main():
    emails = get_unread_emails(max_results=5)
    if not emails:
        print("No unread emails. Inbox zero!")
        return

    for i, email in enumerate(emails, start=1):
        print(f"[{i}] {email['subject']}")
        print(f"    From: {email['from']}")
        print(summarize_email(email))
        print("-" * 50)


if __name__ == "__main__":
    main()
```

| Part | Meaning |
|---|---|
| `from gmail_tools import ...` | Borrow a function from the toolbox. No need to rewrite the Gmail login. |
| `SYSTEM_PROMPT` | A **briefing for an intern** before work: "here's your job, here's the report format." The clearer the briefing, the tidier the output. |
| `system=SYSTEM_PROMPT` | The briefing goes through the separate `system` channel, so Claude knows what's instruction and what's material. |
| "Always answer in English" | The inbox can contain emails in several languages (e.g. German); summaries always come out in English. |
| `[:4000]` | Very long emails (e.g. newsletters) are cut to the first 4,000 characters to save credit. |
| `max_tokens=1024` | Room for both Claude's thinking and the answer. Thinking uses tokens too, so 300 was too tight. |
| `"".join(... if block.type == "text")` | Keep only the final answer (see step 4). |

Note: this script sends email contents to the Claude API to be summarized. That's how it works, but good to be aware of.

**4. Run it**
```
python summarize.py
```
Output per email:
```
[1] <subject>
    From: <sender>
Summary: ...
Category: Important / Info / Promo / Spam
Needs reply: Yes / No - <reason>
--------------------------------------------------
```

🐛 **Bug hit on the first run:** `AttributeError: 'ThinkingBlock' object has no attribute 'text'`
- **Why:** Claude's reply is a **package that can hold several blocks**: sometimes a **scratch paper** (`ThinkingBlock`, Claude thinking first) and then the **final answer** (`TextBlock`). The original code took `content[0].text`, assuming the first block is always the answer. For a German newsletter, Claude thought first → block #1 was the scratch paper → crash. `hello.py` didn't crash because its question was too simple to need thinking.
- **Fix:** loop over all blocks and keep only the `text` ones, and raise `max_tokens` so thinking doesn't eat the whole budget. Applied to both `summarize.py` and `hello.py`.
- **Rule from now on:** never use `message.content[0].text`. Always filter by `block.type == "text"`.

### Tweaks after Phase 3

**Which emails get fetched?** The `q` filter in `gmail_tools.py` works exactly like Gmail's search bar.
- `is:unread in:inbox` = unread emails from **all tabs** (Primary, Promotions, Social, Updates, Forums). Not archived, Spam, or Trash.
- Gmail returns the **newest first**, so `max_results=5` = the 5 newest unread emails.
- Recommended: **Primary only**, so promos/newsletters don't waste credit:
```python
        userId="me", q="is:unread category:primary", maxResults=max_results
```

| Filter | Result |
|---|---|
| `is:unread category:primary` | Unread from the Primary tab only |
| `is:unread in:inbox -category:promotions -category:social` | All tabs **except** Promotions & Social |
| `is:unread newer_than:1d` | Unread from the last 24 hours |
| `is:unread from:example-university.de` | Unread from one sender domain only (e.g. your university) |

**How many emails?** Set in `summarize.py`, not `gmail_tools.py` (there it's only the default):
```python
    emails = get_unread_emails(max_results=5)
```
- Each email = **one call to Claude**, so cost grows roughly in proportion. 5 emails = 5 calls, 20 emails = 20 calls.
- Fetching from Gmail is **free**. Only the Claude part uses credit. Check exact cost at console.anthropic.com → **Usage**.

---

## Phase 4 — Smart analysis ✅

**Goal:** instead of a free-text summary, Claude fills in a fixed **form (JSON)** for every email: category, summary, urgency + reason, deadlines, requested actions. Covers goals 1, 3 and 4.

**Result:** `python analyze.py` → each unread Primary email gets a category, 🔴/🟡/🟢 urgency, summary, deadlines with real dates, and actions. Works.

### Concept: JSON = a form instead of an essay

Phase 3's output was like a **free essay**: nice for humans, but code can't sort or filter an essay. Now Claude fills in the **same form with fixed boxes** for every email:

```json
{
  "category": "University",
  "summary": "Exam registration closes Friday.",
  "urgency": "High",
  "urgency_reason": "Deadline in 3 days",
  "deadlines": [{"date": "2026-11-20", "what": "Exam registration"}],
  "actions": ["Register for the exam in the portal"]
}
```
(This is just an example of what Claude produces. It isn't pasted anywhere.)

Because every email uses the same form, code can later say "give me everything with urgency High" or "sort all deadlines by date". That's what Phase 5 needs.

### Steps

**1. Create `analyze.py`**
```python
import json
from datetime import date
from dotenv import load_dotenv
import anthropic
from gmail_tools import get_unread_emails

load_dotenv()
client = anthropic.Anthropic()

# Goal 1: the categories Claude can choose from (edit freely)
CATEGORIES = [
    "University", "Work & Jobs", "Finance & Bills", "Official & Admin",
    "Personal", "Shopping & Orders", "Newsletter & Promo", "Spam", "Other",
]

# The "form" Claude must fill in for every email
SYSTEM_PROMPT = f"""You are a personal email assistant. Analyze ONE email and fill in a form.
Today's date is {date.today().isoformat()}.

Reply with ONLY valid JSON, no extra text, in exactly this shape:
{{
  "category": one of {CATEGORIES},
  "summary": "1-2 sentences with the core of the email",
  "urgency": "High" | "Medium" | "Low",
  "urgency_reason": "short reason",
  "deadlines": [{{"date": "YYYY-MM-DD", "what": "what is due"}}],
  "actions": ["things the reader is asked to do"]
}}

Rules:
- High = needs attention within about 48 hours, or serious consequences if missed.
- Medium = needs action, but not within 48 hours.
- Low = no action needed (info, promos, newsletters).
- Convert relative dates ("next Friday", "bis Ende des Monats") to YYYY-MM-DD,
  counting from the email's Date.
- Only list actions the email explicitly asks for. Don't invent suggestions.
- Combine steps of the same task into one action (max 3 actions).
- Promos and newsletters get NO actions and NO deadlines: use empty lists [].
- If there are no deadlines or actions, use empty lists [].
- Always write in English, whatever language the email is in."""


def _parse_json(text):
    """Turn Claude's answer into a Python dictionary."""
    text = text.strip()
    if text.startswith("```"):  # sometimes Claude wraps JSON in ```json ... ```
        text = text.strip("`").removeprefix("json").strip()
    return json.loads(text)


def analyze_email(email):
    """Send one email to Claude and get the filled-in form back."""
    content = (
        f"From: {email['from']}\n"
        f"Date: {email.get('date', 'unknown')}\n"
        f"Subject: {email['subject']}\n\n"
        f"{email['body'][:4000]}"
    )
    message = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    try:
        return _parse_json(text)
    except json.JSONDecodeError:
        # Claude didn't return a clean form: don't crash, mark it instead
        return {"category": "Other", "summary": "(could not analyze)",
                "urgency": "Low", "urgency_reason": "-", "deadlines": [], "actions": []}


URGENCY_ICON = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}


def main():
    emails = get_unread_emails(max_results=5)
    if not emails:
        print("No unread emails. Inbox zero!")
        return

    for i, email in enumerate(emails, start=1):
        result = analyze_email(email)
        icon = URGENCY_ICON.get(result["urgency"], "⚪")
        print(f"[{i}] {email['subject']}")
        print(f"    From     : {email['from']}")
        print(f"    Date     : {email['date']}")
        print(f"    Category : {result['category']}")
        print(f"    Urgency  : {icon} {result['urgency']} - {result['urgency_reason']}")
        print(f"    Summary  : {result['summary']}")
        for d in result["deadlines"]:
            print(f"    Deadline : {d['date']} - {d['what']}")
        for action in result["actions"]:
            print(f"    Action   : {action}")
        print("-" * 50)


if __name__ == "__main__":
    main()
```

| Part | Meaning |
|---|---|
| `CATEGORIES` | The categories Claude may choose from (goal 1). Edit freely. |
| `SYSTEM_PROMPT` | The form + the rules for filling it in. Includes **today's date** so "next Friday" becomes a real date (goal 4). Clear High/Medium/Low rules so Claude doesn't guess (goal 3). |
| `{{` and `}}` | Inside an f-string, `{` means "insert a variable". Double braces mean "a literal brace", needed for the JSON shape. |
| `_parse_json` | Turns Claude's JSON text into Python data. Removes a ```` ```json ```` wrapper if Claude adds one. |
| `try / except` | If Claude fills the form in badly once, the script **doesn't crash**: it marks that email "(could not analyze)". |
| `URGENCY_ICON` | 🔴 High · 🟡 Medium · 🟢 Low |

**2. Run it:** `python analyze.py`

**3. Pass the email's sent date to Claude** (in `gmail_tools.py`, `get_unread_emails`)
```python
            "date": headers.get("Date", "unknown"),
```
- Why: an email from Nov 10 saying "bis nächsten Freitag" means **Nov 14**, not the Friday after today. Without the sent date, Claude can only guess.
- `analyze.py` already had `Date: {email.get('date', 'unknown')}`, so it needed no change (it just said "unknown" before).
- Added `print(f"    Date     : {email['date']}")` to `main()` so the date is visible too.

**4. Tighten the rules + Primary only**
- First run showed promos getting "optional" actions and deadlines (e.g. "discount ends Nov 26"). Fixed with the rules: *only explicit actions*, *combine steps (max 3)*, *promos get NO actions and NO deadlines*, and *count dates from the email's Date*.
- ⚠️ Lesson: new rules must go **inside** the `"""..."""` of `SYSTEM_PROMPT`. Anything outside it, Claude never sees.
- Switched the filter to `q="is:unread category:primary"`, so promo-tab emails (food delivery, online courses, shops…) aren't fetched anymore.

**5. One clean date format, in local time** (in `gmail_tools.py`)

Raw date stamps look different per sender, because each sender's mail server writes its own "postmark":

| Raw text | Meaning |
|---|---|
| `+0000` | Offset from world standard time (UTC): **0 hours**, i.e. the time is written in UTC |
| `+0100` | German winter time (CET = UTC+1) |
| `+0200` | German summer time (CEST = UTC+2, from late March) |
| `GMT` | Practically **the same as UTC** |
| `(UTC)` / `(GMT)` | Just a comment in brackets, changes nothing |

Example: `17:58:00 +0000 (UTC)` = **18:58** in Germany (winter). `13:46:19 GMT` = **14:46** in Germany.

Fix: convert everything to the **laptop's local time**, which also handles winter/summer time automatically (and follows the laptop if it's in another time zone).

```python
from email.utils import parsedate_to_datetime   # at the top, under "import base64"


def _format_date(raw):
    """Turn any email date stamp into one clean format, in your local time."""
    if not raw:
        return "unknown"
    try:
        dt = parsedate_to_datetime(raw).astimezone()  # convert to your laptop's time zone
        return dt.strftime("%a, %d %b %Y %H:%M")
    except (TypeError, ValueError):
        return raw  # weird format: just show it as-is
```
And in `get_unread_emails`:
```python
            "date": _format_date(headers.get("Date", "")),
```
Result: `Date     : Mon, 16 Nov 2026 18:58`. `parsedate_to_datetime` is built into Python, no `pip install` needed.

### Notes from testing
- **Number of actions varies per email** (0, 1, or more). That's by design: it follows how many things the email actually asks for.
- **Google "Security alert" → 🔴 High** about the app "email-assistant": that's from logging in again ourselves, so it's safe. Good sign though: if you *didn't* recognize the app, it would be a real alarm.
- **Job alert emails → Work & Jobs, 🟢 Low**: correct, alerts aren't requests.

### Final `gmail_tools.py` (after Phase 4)
```python
import os
import base64
from email.utils import parsedate_to_datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    """Log in to Gmail (exactly the same as Phase 2)."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
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


def get_unread_emails(max_results=5):
    """Get full unread emails: id, sender, date, subject, body."""
    service = get_gmail_service()
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
```


---

## Phase 5 — Daily overview ✅

**Goal (5):** one readable daily report: 🔴 urgent first, 📅 deadlines nearest first, ✅ to-do list, 🗂️ category overview. Plus a "notebook" so tasks survive until marked done and no email gets analyzed twice.

**Result:** `python daily.py` → analyzes only new emails → writes `daily_overview.md`. `python done.py` → tick off finished tasks. Works.

### Daily use
```
python daily.py      # fetch + analyze new emails + write the report
python done.py       # mark finished tasks (type their numbers, e.g. 1,3)
```
Open the report: right-click `daily_overview.md` → **Open Preview**.

### Concepts

| Thing | Analogy |
|---|---|
| `memory.json` | **Notebook / archive.** Every analyzed email, stored under its Gmail ID. Complete, but not nice to read. |
| Gmail message ID | **Tracking number** of a parcel. Unique per email, used as the notebook's page name. |
| Skipping known IDs | A courier checking "did I already scan this parcel?" Already in the notebook → no call to Claude → no credit used. |
| `daily_overview.md` | **Morning paper** made from the archive: front page = urgent, then deadlines, then to-do. |
| Task key (e.g. `19a8f…:action:0`) | A unique **sticker** per task: email ID + task type + position. Marking done = putting that sticker on the "done" list. |

### Steps

**1. Save results in a notebook (`memory.json`)**
- `load_memory` / `save_memory` open and close the notebook (an empty one is created if it doesn't exist).
- `**result` = "pour every field of Claude's form in here" (category, summary, urgency, deadlines, actions).
- `ensure_ascii=False` keeps ü, ö, ß and emoji readable; `indent=2` keeps the file tidy.
- `memory.json` holds summaries of personal emails → added to `.gitignore`.

**2. Look inside the notebook**: `python daily.py` → `memory.json` appears in the sidebar.

**3. Skip emails that are already in the notebook**
- `if email["id"] in memory["emails"]: continue` → no second call to Claude.
- Fetching from Gmail still runs (free). Only the Claude part is skipped.
- ❓ *Why doesn't it analyze "the next 10"?* It always fetches the **10 newest unread** emails, like taking the top 10 letters off a pile. If the pile hasn't changed, it's the same 10 → all skipped. Older emails get analyzed when a new email arrives, when you read emails in Gmail (they leave "unread"), or when `max_results` is raised.
- ❓ *Why 10 here but 5 in `analyze.py`?* Each file sets its own `max_results`. `daily.py` uses 10 so the daily report covers more. Thanks to skipping, the daily cost stays small.

**4. Build the daily report (`daily_overview.md`)**

| Section | Content | Goal |
|---|---|---|
| 🔴 Urgent | High emails + summary + why urgent | 3 |
| 🟡 Needs attention soon | Medium emails | 3 |
| 📅 Deadlines | Nearest first, with "TODAY", "tomorrow", "in 4 days", "⚠️ overdue" | 4 |
| ✅ To-do | Every requested action | 4 |
| 🗂️ By category | Count per category (all emails in the notebook) | 1 |

- `open_items` collects every deadline + action that isn't done, deadlines sorted by date. `YYYY-MM-DD` sorts easily, which is why Claude was asked for that format in Phase 4.
- `_when` turns a date into words.
- Badly filled dates are skipped instead of crashing.
- `daily_overview.md` is also personal data → added to `.gitignore`.

**5. Mark tasks as done (`done.py`)**
- Deadlines and to-dos share **one numbering**, the same in the report and in `done.py`.
- Typed numbers get a "done" sticker in `memory["done"]`, and the report is rewritten right away.
- Invalid input (letters, numbers out of range) is ignored with a message, not a crash.
- Rules so the report doesn't pile up forever:
  - An urgent/medium email whose tasks are **all done** leaves the Urgent/Medium sections.
  - An urgent/medium email that **never had tasks** (info only) stays for `KEEP_INFO_DAYS` = 3 days.

### `.gitignore` after Phase 5
```
# Secrets - NEVER upload
.env
credentials.json
token.json

# Personal data generated by the assistant
memory.json
daily_overview.md
run_log.txt

# Python folders
venv/
__pycache__/
```

### `daily.py`
```python
import json
import os
from collections import Counter
from datetime import date
from gmail_tools import get_unread_emails
from analyze import analyze_email  # reuse the Phase 4 "form filler"

MEMORY_FILE = "memory.json"
REPORT_FILE = "daily_overview.md"
KEEP_INFO_DAYS = 3  # urgent/medium emails WITHOUT tasks stay in the report this many days


# ---------- The notebook (memory.json) ----------

def load_memory():
    """Open the notebook. If it doesn't exist yet, start an empty one."""
    if not os.path.exists(MEMORY_FILE):
        return {"emails": {}, "done": []}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
    memory.setdefault("done", [])  # older notebooks don't have a "done" list yet
    return memory


def save_memory(memory):
    """Write the notebook back to the file."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def update_memory(max_results=10):
    """Fetch unread emails, analyze only NEW ones, and write them in the notebook."""
    memory = load_memory()
    emails = get_unread_emails(max_results=max_results)

    new_count = 0
    for email in emails:
        # Already in the notebook? Skip it, no need to call Claude again
        if email["id"] in memory["emails"]:
            print(f"Skipped (already analyzed): {email['subject']}")
            continue

        result = analyze_email(email)
        memory["emails"][email["id"]] = {   # the email's ID = its "tracking number"
            "from": email["from"],
            "date": email["date"],
            "subject": email["subject"],
            "analyzed_on": date.today().isoformat(),
            **result,  # category, summary, urgency, deadlines, actions
        }
        new_count += 1
        print(f"Analyzed: {email['subject']}")

    save_memory(memory)
    print(f"\n{new_count} new email(s) analyzed. Notebook holds {len(memory['emails'])} emails.")
    return memory


# ---------- Open tasks (deadlines + actions that aren't done yet) ----------

def open_items(memory):
    """Every deadline and action NOT marked done, with one shared numbering.
    Deadlines come first (nearest first), then actions."""
    done = set(memory.get("done", []))
    deadlines, actions = [], []

    for email_id, e in memory["emails"].items():
        for i, d in enumerate(e.get("deadlines", [])):
            key = f"{email_id}:deadline:{i}"  # unique "sticker" for this one task
            if key in done:
                continue
            try:
                due = date.fromisoformat(d["date"])
            except (KeyError, TypeError, ValueError):
                continue  # skip dates Claude couldn't fill in properly
            deadlines.append({"key": key, "kind": "deadline", "text": d.get("what", ""),
                              "due": due, "subject": e["subject"], "email_id": email_id})

        for i, action in enumerate(e.get("actions", [])):
            key = f"{email_id}:action:{i}"
            if key in done:
                continue
            actions.append({"key": key, "kind": "action", "text": action,
                            "due": None, "subject": e["subject"], "email_id": email_id})

    deadlines.sort(key=lambda item: item["due"])
    return deadlines + actions


def _still_relevant(email_id, e, open_email_ids, today):
    """Should this urgent/medium email still show up in the report?"""
    if email_id in open_email_ids:
        return True   # it still has open tasks
    if e.get("actions") or e.get("deadlines"):
        return False  # it had tasks, and all of them are done
    try:
        analyzed = date.fromisoformat(e.get("analyzed_on", ""))
    except ValueError:
        return True
    return (today - analyzed).days <= KEEP_INFO_DAYS  # no tasks: show it for a few days


# ---------- The morning paper (daily_overview.md) ----------

def _when(due, today):
    """Turn a due date into words: 'TODAY', 'in 3 days', 'overdue by 2 days'."""
    days = (due - today).days
    if days < 0:
        return f"⚠️ overdue by {-days} day(s)"
    if days == 0:
        return "TODAY"
    if days == 1:
        return "tomorrow"
    return f"in {days} days"


def build_report(memory):
    """Turn the notebook into a readable daily overview."""
    today = date.today()
    items = open_items(memory)
    open_email_ids = {item["email_id"] for item in items}
    lines = [f"# 📬 Daily overview: {today.strftime('%a, %d %b %Y')}", ""]

    # 1 + 2. Urgent first, then medium (goal 3)
    for level, title, empty in [("High", "🔴 Urgent", "Nothing urgent. 🎉"),
                                ("Medium", "🟡 Needs attention soon", "Nothing here.")]:
        group = [e for email_id, e in memory["emails"].items()
                 if e.get("urgency") == level
                 and _still_relevant(email_id, e, open_email_ids, today)]
        lines.append(f"## {title} ({len(group)})")
        if not group:
            lines.append(empty)
        for e in group:
            lines.append(f"- **{e['subject']}** ({e['from']})")
            lines.append(f"  - {e['summary']}")
            if level == "High":
                lines.append(f"  - Why urgent: {e['urgency_reason']}")
        lines.append("")

    # 3. Deadlines, nearest first (goal 4). Numbers match `python done.py`.
    numbered = list(enumerate(items, start=1))
    deadline_lines = [f"{n}. **{it['due'].strftime('%a, %d %b')}** ({_when(it['due'], today)}): "
                      f"{it['text']} · _{it['subject']}_"
                      for n, it in numbered if it["kind"] == "deadline"]
    lines.append(f"## 📅 Deadlines ({len(deadline_lines)})")
    lines.extend(deadline_lines or ["No open deadlines."])
    lines.append("")

    # 4. To-do list (goal 4)
    todo_lines = [f"{n}. {it['text']} · _{it['subject']}_"
                  for n, it in numbered if it["kind"] == "action"]
    lines.append(f"## ✅ To-do ({len(todo_lines)})")
    lines.extend(todo_lines or ["Nothing to do. 🎉"])
    lines.append("")
    lines.append("_Finished something? Run `python done.py` and type its number._")
    lines.append("")

    # 5. Overview by category (goal 1)
    counts = Counter(e.get("category", "Other") for e in memory["emails"].values())
    lines.append("## 🗂️ By category (all emails in the notebook)")
    for category, n in counts.most_common():
        lines.append(f"- {category}: {n}")

    return "\n".join(lines)


def write_report(memory):
    """Save the overview to a file."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(build_report(memory))
    print(f"Daily overview saved to {REPORT_FILE}")


if __name__ == "__main__":
    memory = update_memory()
    write_report(memory)
```

### `done.py`
```python
from daily import load_memory, save_memory, open_items, write_report


def main():
    memory = load_memory()
    items = open_items(memory)

    if not items:
        print("No open tasks. 🎉")
        return

    # Show every open task with its number (same numbers as the report)
    for n, item in enumerate(items, start=1):
        if item["kind"] == "deadline":
            label = f"📅 {item['due'].strftime('%a, %d %b')}: {item['text']}"
        else:
            label = f"✅ {item['text']}"
        print(f"[{n}] {label}  ({item['subject']})")

    answer = input("\nWhich numbers are done? (e.g. 1,3 or Enter to cancel): ").strip()
    if not answer:
        print("Nothing changed.")
        return

    # Read the numbers the user typed, ignore anything that isn't a valid number
    chosen = set()
    for part in answer.split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(items):
            chosen.add(int(part))
        else:
            print(f"Ignored '{part}' (not a valid number)")

    for n in sorted(chosen):
        memory["done"].append(items[n - 1]["key"])  # put a "done" sticker on it
        print(f"Marked done: {items[n - 1]['text']}")

    save_memory(memory)
    write_report(memory)  # refresh the report so done tasks disappear


if __name__ == "__main__":
    main()
```


---

## Phase 6 — Run automatically ✅

**Goal:** the daily overview is built automatically every morning, without typing anything.

**Result:** Windows Task Scheduler runs `run_daily.bat` every day at 07:00 → `daily_overview.md` is ready. If the Gmail login has expired, the report still gets written, with a ⚠️ banner on top. Works.

### Concepts

| Thing | Analogy |
|---|---|
| Task Scheduler | An **alarm clock**. It can only "press one button", it can't open VS Code, activate the venv, and type commands. |
| `run_daily.bat` | The **one-click button** that does all of that in one go. |
| `run_log.txt` | The **black box / CCTV**. Technical record of every run: when, what was analyzed or skipped, errors. Not for daily reading, only when something's wrong. |
| `daily_overview.md` | The **morning paper** you actually read. |

### Steps

**1. Create `run_daily.bat`**
```bat
@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
echo ===== %date% %time% ===== >> run_log.txt
"venv\Scripts\python.exe" daily.py >> run_log.txt 2>&1
```

| Line | Meaning |
|---|---|
| `@echo off` | Don't print every command on screen |
| `cd /d "%~dp0"` | Go to the folder this `.bat` file is in (the project folder) |
| `set PYTHONUTF8=1` | Emoji like 🔴 📅 🎉 won't crash when output is written to a file (Windows default encoding issue) |
| `echo ===== %date% %time% =====` | Stamp the date and time in the log |
| `"venv\Scripts\python.exe" daily.py` | Run `daily.py` with the **venv's Python** directly, so no `activate` needed |
| `>> run_log.txt 2>&1` | Append all output, **including errors**, to `run_log.txt` |

- Test: double-click `run_daily.bat` in File Explorer → a black window flashes → `run_log.txt` appears.
- `run_log.txt` added to `.gitignore` (it contains email subjects). It grows every day; delete it any time, it's recreated.

**2. Schedule it in Task Scheduler**
- Start → **Task Scheduler** → right panel **Create Task...** (not "Create Basic Task", fewer options)
- **General:** Name `Email Assistant Daily` · "Run only when user is logged on"
- **Triggers:** New → **Daily** · start tomorrow **07:00:00** · recur every `1` days · Enabled
- **Actions:** New → **Start a program** · Program/script: Browse → `run_daily.bat` · **Start in:** the full path of your project folder, e.g. `C:\Users\<your-name>\Documents\Projects\email-assistant` (no quotes)
- **Conditions:** ❌ untick "Start the task only if the computer is on AC power" (laptop on battery) · optional ✅ "Wake the computer to run this task"
- **Settings:** ✅ "Run task as soon as possible after a scheduled start is missed" (laptop was off at 7:00 → runs when it's switched on)
- OK

**3. Test the alarm now**
- Task Scheduler Library → right-click **Email Assistant Daily** → **Run** → Refresh
- **Last Run Result** `The operation completed successfully. (0x0)` = ✅. `(0x1)` or other = error → check `run_log.txt`.
- `run_log.txt` gets a new block with the current time.

**4. The Google login trap + Plan B**

⚠️ **Problem:** the app's Google publishing status is **"Testing"**. In that mode, Google lets the refresh token (the key card in `token.json`) expire **7 days** after login. After that, the 7:00 run would fail silently with `invalid_grant`.

- **Real fix = publish the app ("In production")**: tokens then don't expire. But Google requires a **homepage URL + privacy policy URL** first ("Publish app" stays greyed out). Decided **not** to do that for now.
- **Plan B (chosen): stay in Testing, but make it safe.**
  - `gmail_tools.py`: if Google refuses to renew the key card, it's detected instead of crashing. New setting **`allow_login`**:
    - `allow_login=True` (manual runs like `python gmail_tools.py`) → opens the browser to log in again. **No need to delete `token.json` by hand anymore.**
    - `allow_login=False` (used by `daily.py`) → never opens a browser (nobody is there at 7:00 to click it, it would hang forever) → raises `GmailLoginExpired`.
  - `daily.py`: on `GmailLoginExpired` it **still writes the report** from the notebook, with a ⚠️ banner on top saying how to fix it.
  - Weekly routine: banner appears → VS Code → activate venv → `python gmail_tools.py` → log in → `python daily.py`. About 30 seconds.
  - Tested by renaming `token.json` → `token_backup.json`, running `run_daily.bat`, checking the banner, renaming it back.
- Other things that also kill the token (rare): not used for 6 months, revoking access yourself, changing the Google account password. Fix is the same: `python gmail_tools.py`.
- Sources: [Google Developer forums](https://discuss.google.dev/t/oauth2-refresh-token-expiration-and-youtube-api-v3/160874) · [Google Ads API forum](https://groups.google.com/g/adwords-api/c/QTdeilIh_QY/m/eOHg0Q9CAgAJ) · [Unified.to](https://unified.to/blog/why_google_oauth_returns)

### Final `gmail_tools.py` (after Phase 6)
```python
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
```

### Final `daily.py` (after Phase 6)
```python
import json
import os
from collections import Counter
from datetime import date
from gmail_tools import get_unread_emails, GmailLoginExpired
from analyze import analyze_email  # reuse the Phase 4 "form filler"

MEMORY_FILE = "memory.json"
REPORT_FILE = "daily_overview.md"
KEEP_INFO_DAYS = 3  # urgent/medium emails WITHOUT tasks stay in the report this many days


# ---------- The notebook (memory.json) ----------

def load_memory():
    """Open the notebook. If it doesn't exist yet, start an empty one."""
    if not os.path.exists(MEMORY_FILE):
        return {"emails": {}, "done": []}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
    memory.setdefault("done", [])  # older notebooks don't have a "done" list yet
    return memory


def save_memory(memory):
    """Write the notebook back to the file."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def update_memory(max_results=10):
    """Fetch unread emails, analyze only NEW ones, and write them in the notebook."""
    memory = load_memory()
    # Never open a browser here: this may run automatically with nobody watching
    emails = get_unread_emails(max_results=max_results, allow_login=False)

    new_count = 0
    for email in emails:
        # Already in the notebook? Skip it, no need to call Claude again
        if email["id"] in memory["emails"]:
            print(f"Skipped (already analyzed): {email['subject']}")
            continue

        result = analyze_email(email)
        memory["emails"][email["id"]] = {   # the email's ID = its "tracking number"
            "from": email["from"],
            "date": email["date"],
            "subject": email["subject"],
            "analyzed_on": date.today().isoformat(),
            **result,  # category, summary, urgency, deadlines, actions
        }
        new_count += 1
        print(f"Analyzed: {email['subject']}")

    save_memory(memory)
    print(f"\n{new_count} new email(s) analyzed. Notebook holds {len(memory['emails'])} emails.")
    return memory


# ---------- Open tasks (deadlines + actions that aren't done yet) ----------

def open_items(memory):
    """Every deadline and action NOT marked done, with one shared numbering.
    Deadlines come first (nearest first), then actions."""
    done = set(memory.get("done", []))
    deadlines, actions = [], []

    for email_id, e in memory["emails"].items():
        for i, d in enumerate(e.get("deadlines", [])):
            key = f"{email_id}:deadline:{i}"  # unique "sticker" for this one task
            if key in done:
                continue
            try:
                due = date.fromisoformat(d["date"])
            except (KeyError, TypeError, ValueError):
                continue  # skip dates Claude couldn't fill in properly
            deadlines.append({"key": key, "kind": "deadline", "text": d.get("what", ""),
                              "due": due, "subject": e["subject"], "email_id": email_id})

        for i, action in enumerate(e.get("actions", [])):
            key = f"{email_id}:action:{i}"
            if key in done:
                continue
            actions.append({"key": key, "kind": "action", "text": action,
                            "due": None, "subject": e["subject"], "email_id": email_id})

    deadlines.sort(key=lambda item: item["due"])
    return deadlines + actions


def _still_relevant(email_id, e, open_email_ids, today):
    """Should this urgent/medium email still show up in the report?"""
    if email_id in open_email_ids:
        return True   # it still has open tasks
    if e.get("actions") or e.get("deadlines"):
        return False  # it had tasks, and all of them are done
    try:
        analyzed = date.fromisoformat(e.get("analyzed_on", ""))
    except ValueError:
        return True
    return (today - analyzed).days <= KEEP_INFO_DAYS  # no tasks: show it for a few days


# ---------- The morning paper (daily_overview.md) ----------

def _when(due, today):
    """Turn a due date into words: 'TODAY', 'in 3 days', 'overdue by 2 days'."""
    days = (due - today).days
    if days < 0:
        return f"⚠️ overdue by {-days} day(s)"
    if days == 0:
        return "TODAY"
    if days == 1:
        return "tomorrow"
    return f"in {days} days"


def build_report(memory, warning=None):
    """Turn the notebook into a readable daily overview."""
    today = date.today()
    items = open_items(memory)
    open_email_ids = {item["email_id"] for item in items}
    lines = [f"# 📬 Daily overview: {today.strftime('%a, %d %b %Y')}", ""]

    # 0. Big warning banner if something went wrong (e.g. Gmail login expired)
    if warning:
        lines.append(f"> ⚠️ **{warning}**")
        lines.append("> _The report below only shows what was already in the notebook._")
        lines.append("")

    # 1 + 2. Urgent first, then medium (goal 3)
    for level, title, empty in [("High", "🔴 Urgent", "Nothing urgent. 🎉"),
                                ("Medium", "🟡 Needs attention soon", "Nothing here.")]:
        group = [e for email_id, e in memory["emails"].items()
                 if e.get("urgency") == level
                 and _still_relevant(email_id, e, open_email_ids, today)]
        lines.append(f"## {title} ({len(group)})")
        if not group:
            lines.append(empty)
        for e in group:
            lines.append(f"- **{e['subject']}** ({e['from']})")
            lines.append(f"  - {e['summary']}")
            if level == "High":
                lines.append(f"  - Why urgent: {e['urgency_reason']}")
        lines.append("")

    # 3. Deadlines, nearest first (goal 4). Numbers match `python done.py`.
    numbered = list(enumerate(items, start=1))
    deadline_lines = [f"{n}. **{it['due'].strftime('%a, %d %b')}** ({_when(it['due'], today)}): "
                      f"{it['text']} · _{it['subject']}_"
                      for n, it in numbered if it["kind"] == "deadline"]
    lines.append(f"## 📅 Deadlines ({len(deadline_lines)})")
    lines.extend(deadline_lines or ["No open deadlines."])
    lines.append("")

    # 4. To-do list (goal 4)
    todo_lines = [f"{n}. {it['text']} · _{it['subject']}_"
                  for n, it in numbered if it["kind"] == "action"]
    lines.append(f"## ✅ To-do ({len(todo_lines)})")
    lines.extend(todo_lines or ["Nothing to do. 🎉"])
    lines.append("")
    lines.append("_Finished something? Run `python done.py` and type its number._")
    lines.append("")

    # 5. Overview by category (goal 1)
    counts = Counter(e.get("category", "Other") for e in memory["emails"].values())
    lines.append("## 🗂️ By category (all emails in the notebook)")
    for category, n in counts.most_common():
        lines.append(f"- {category}: {n}")

    return "\n".join(lines)


def write_report(memory, warning=None):
    """Save the overview to a file."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(build_report(memory, warning))
    print(f"Daily overview saved to {REPORT_FILE}")


if __name__ == "__main__":
    warning = None
    try:
        memory = update_memory()
    except GmailLoginExpired:
        # Key card missing or dead (Google Testing mode = 7 days).
        # Don't fail silently: still write the report, with a big warning on top.
        warning = ("Gmail login expired. In the project folder (venv active) run "
                   "`python gmail_tools.py` and log in, then `python daily.py`.")
        memory = load_memory()

    if warning:
        print(f"WARNING: {warning}")
    write_report(memory, warning)
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `running scripts is disabled` when activating the venv | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` → type Y |
| `python` not recognized / opens the Microsoft Store | Python installer → Modify → tick "Add Python to environment variables" → close & open a new terminal |
| Yellow: "A new release of pip is available" | Not an error, ignore it |
| `ModuleNotFoundError: No module named '...'` | venv isn't active → `venv\Scripts\activate`. If it persists, `pip install` that library again. |
| Authentication error / invalid API key (Claude) | Check `.env` (no spaces/quotes) or the key has expired → create a new key |
| Key accidentally shared / screenshotted | Delete the key in the console → create a new one → update `.env` |
| `FileNotFoundError: credentials.json` | File isn't in the project folder, or it wasn't renamed (still `client_secret_...json`) |
| Google: *"Access blocked"* / *"has not completed the Google verification process"* | Your email isn't listed under **Audience → Test users** |
| Google: *"invalid_grant"* / *"Token has been expired or revoked"* | Run `python gmail_tools.py` and log in again (it now detects the dead token itself). Happens about every 7 days in Testing mode. |
| **Changing `SCOPES`** (adding or removing a permission) | **You must delete `token.json`** first and log in again. The old token keeps the old permissions. |
| `AttributeError: 'ThinkingBlock' object has no attribute 'text'` | Claude thought before answering. Use `"".join(b.text for b in message.content if b.type == "text")` instead of `content[0].text`, and give `max_tokens` enough room (e.g. 1024). |
| Claude's answer is empty or cut off | `max_tokens` too low: thinking used up the budget. Raise it. |
| Email shows "(could not analyze)" | Claude didn't return clean JSON for that one email. Usually rare; run again. If it happens often, check `SYSTEM_PROMPT` still says "Reply with ONLY valid JSON". |
| New prompt rules seem ignored | They're probably outside the `"""..."""` of `SYSTEM_PROMPT`. Move them inside. |
| `IndentationError` | A `def` or line has the wrong number of spaces. Top-level `def`s start at the far left; lines inside use 4 spaces. |
| "No unread emails. Inbox zero!" with `category:primary` | Not an error: the Primary tab simply has no unread emails right now. |
| Want to start the notebook over | Delete `memory.json` (and `daily_overview.md`). Next `python daily.py` re-analyzes everything (uses credit). |
| Marked the wrong task as done | Open `memory.json`, find the `"done"` list at the bottom, delete that key line (watch the commas), save. |
| Task numbers changed | Numbers are recalculated every run (done tasks disappear, new ones appear). Always check the latest report or `done.py` list before typing a number. |
| ⚠️ banner "Gmail login expired" in the report | Normal about once a week (Testing mode). `python gmail_tools.py` → log in → `python daily.py`. |
| Report date isn't today | The automatic run failed or didn't happen. Check the bottom of `run_log.txt`, and Task Scheduler → **Last Run Result**. |
| Task Scheduler: Last Run Result `0x1` | The script crashed. Read the bottom of `run_log.txt`. |
| Task didn't run at 07:00 | Laptop was off/asleep. With "Run task as soon as possible after a scheduled start is missed", it runs when the laptop starts. Also check "AC power only" is unticked. |
| `UnicodeEncodeError` in `run_log.txt` | `set PYTHONUTF8=1` is missing from `run_daily.bat`. |
| Dates show in UTC (`+0000`, `GMT`) | Use `_format_date` in `gmail_tools.py` to convert to local time. Check Windows time zone is Europe/Berlin. |
| Screenshots of the terminal | They contain personal emails, so blur sensitive parts first |
