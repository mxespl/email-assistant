# Email Assistant

A read-only AI assistant for a personal Gmail inbox. Every morning it reads new emails, uses Claude to categorize and summarize them, flags what's urgent, extracts deadlines and requested actions, and writes a daily overview you can read in a minute.

## Overview

Inboxes mix important messages (university, bills, official letters) with newsletters and promotions, often in several languages. This project turns unread emails into one short report:

- what is urgent,
- which deadlines are coming up,
- what you've been asked to do.

It never writes, sends, or deletes anything in Gmail.

## Features

- **Categorization:** University, Work & Jobs, Finance & Bills, Official & Admin, Personal, Shopping & Orders, Newsletter & Promo, Spam, Other
- **Summaries:** 1–2 sentences per email, always in English, whatever the email's language
- **Urgency:** High / Medium / Low, with a short reason
- **Deadlines and actions:** relative dates ("next Friday", "bis Ende des Monats") are converted to real dates, counted from the email's sent date
- **Daily overview** as a clean web page (`daily_overview.html`) and as Markdown (`daily_overview.md`): urgent first, deadlines sorted by date, to-do list, count per category
- **Task tracking:** mark tasks as done with `done.py`; they disappear from the next report
- **No double work:** emails that were already analyzed are skipped, so Claude isn't called (or paid) twice
- **Scheduled runs:** Windows Task Scheduler builds the report every morning
- **Safe failure:** if the Gmail login has expired, the report is still written, with a warning banner on top

## Tech stack

- Python (developed and tested with 3.14)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python), model `claude-haiku-5-5`
- Gmail API with OAuth 2.0 (scope `gmail.readonly`)
- Windows Task Scheduler (for automatic runs)

## How it works

```
Gmail (unread, Primary tab)
   │  gmail_tools.py: fetch emails, decode bodies, normalize dates
   ▼
Claude (claude-haiku-5-5)
   │  analyze.py: fill in a fixed JSON form per email
   ▼
memory.json (the "notebook")
   │  daily.py: store results, skip known emails, track done tasks
   ▼
daily_overview.html + daily_overview.md (the report)
```

Each email is analyzed into this JSON shape:

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

## Prerequisites

- Python 3 and a code editor (VS Code recommended)
- An Anthropic API key with credit ([console.anthropic.com](https://console.anthropic.com)). A Claude.ai subscription does not include API credit.
- A Google account and a Google Cloud project (free, no credit card needed)
- Windows, for the `.bat` launcher and Task Scheduler. The Python scripts themselves are not Windows-specific.

## Installation

### 1. Create a virtual environment and install dependencies

```powershell
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install anthropic python-dotenv google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

If PowerShell says *"running scripts is disabled on this system"*, run this once, then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. Add your Anthropic API key

Create a file named `.env` in the project folder:

```
ANTHROPIC_API_KEY=sk-ant-...
```

No spaces around `=`, no quotes. The `anthropic` library reads this variable automatically.

### 3. Set up Gmail API access

In the [Google Cloud Console](https://console.cloud.google.com):

1. Create a project and enable the **Gmail API**.
2. **Google Auth Platform → Get started:** set an app name and support email, and choose Audience **External**.
3. **Audience → Test users:** add your own Gmail address.
4. **Clients → Create client:** choose type **Desktop app**, then **Download JSON**.
5. Rename the file to `credentials.json` and put it in the project folder.

### 4. Log in to Gmail once

```powershell
python gmail_tools.py
```

A browser opens. Choose your account. You'll see *"Google hasn't verified this app"*, which is expected for a personal app, so click **Continue** and allow read access. This creates `token.json`, and the terminal prints your newest unread emails.

### 5. Check the Claude connection (optional)

```powershell
python hello.py
```

## Usage

| Command | What it does |
|---|---|
| `python daily.py` | Fetch and analyze new emails, then write `daily_overview.html` and `daily_overview.md` |
| `python done.py` | List open tasks and mark finished ones (e.g. `1,3`) |
| `python analyze.py` | Print the analysis of the 5 newest unread emails (nothing saved) |
| `python gmail_tools.py` | Test Gmail access, or log in again |

Open the report by double-clicking `daily_overview.html` (it opens in your browser and follows the system's light/dark mode). The same report is also written as `daily_overview.md`. Deadlines and to-dos share one numbering, the same as in `done.py`, which also refreshes both files.

### Run it automatically every morning (Windows)

`run_daily.bat` runs `daily.py` with the venv's Python and appends all output to `run_log.txt`. Schedule it in **Task Scheduler → Create Task**:

- **Trigger:** Daily, e.g. 07:00
- **Action:** Start a program, `run_daily.bat`, with **Start in** set to the project folder's full path
- **Conditions:** untick "Start the task only if the computer is on AC power"
- **Settings:** tick "Run task as soon as possible after a scheduled start is missed"

To test it, right-click the task → **Run**. **Last Run Result** should be `0x0`.

### Daily routine

- Open `daily_overview.html` and check that the date in the header is today.
- If the date is old, read the bottom of `run_log.txt`.
- If the report shows a **"Gmail login expired"** banner, run `python gmail_tools.py`, log in, then run `python daily.py`.

## Configuration

| Setting | Where | Default |
|---|---|---|
| Which emails are fetched (Gmail search syntax) | `q=` in `gmail_tools.py` | `is:unread category:primary` |
| Emails per daily run | `update_memory(max_results=...)` in `daily.py` | `10` |
| Categories | `CATEGORIES` in `analyze.py` | see Features |
| Urgency rules and output format | `SYSTEM_PROMPT` in `analyze.py` | |
| Days an info-only urgent email stays in the report | `KEEP_INFO_DAYS` in `daily.py` | `3` |
| Claude model | `model=` in `analyze.py` | `claude-haiku-5-5` |

Each email costs one Claude call. Fetching from Gmail is free. After changing `SCOPES` in `gmail_tools.py`, delete `token.json` and log in again.

## Project structure

```
email-assistant/
├── gmail_tools.py     # Gmail login, fetching, body decoding, date formatting
├── analyze.py         # Claude analysis per email (JSON form)
├── daily.py           # Main script: notebook + daily overview (HTML + Markdown)
├── done.py            # Mark tasks as done
├── run_daily.bat      # Launcher for Task Scheduler
├── hello.py           # Claude API connection test
├── read_emails.py     # Early version: list unread emails (kept for reference)
├── summarize.py       # Early version: plain-text summaries (kept for reference)
└── docs/
    └── build-log.md   # Detailed step-by-step build notes
```

Created at runtime and excluded from Git (`.gitignore`):

| File | Contains |
|---|---|
| `.env` | Anthropic API key |
| `credentials.json` | Google OAuth client |
| `token.json` | Gmail access token |
| `memory.json` | Analyzed emails and done tasks |
| `daily_overview.html` / `daily_overview.md` | The daily report (web page / Markdown) |
| `run_log.txt` | Output of scheduled runs |

## Privacy and security

- Gmail access is read-only (`gmail.readonly`).
- Email content (sender, date, subject, and the first 4,000 characters of the body) is sent to the Anthropic API for analysis.
- Never commit or share `.env`, `credentials.json`, `token.json`, or the generated files above. If an API key leaks, delete it in the Anthropic console and create a new one.

## Known limitations

- **Weekly re-login.** While the Google app is in **Testing** mode, Google expires the login after 7 days. Publishing the app removes this, but Google requires a homepage URL and a privacy policy URL first. Until then, re-run `python gmail_tools.py` when the warning banner appears.
- The laptop must be on (or asleep, with wake enabled) for the scheduled run. Missed runs start when the laptop is switched on.
- Only the newest unread emails are fetched (10 per daily run). Older unread emails are picked up as newer ones are read.
- HTML-only emails (no plain-text part) are analyzed from Gmail's short snippet.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Activate the venv: `venv\Scripts\activate` |
| Claude authentication error | Check `.env` (no spaces or quotes). The key may have expired: create a new one. |
| `FileNotFoundError: credentials.json` | Put the downloaded file in the project folder and rename it to `credentials.json` |
| Google: *"Access blocked"* | Add your email under **Audience → Test users** |
| `invalid_grant` / login-expired banner | `python gmail_tools.py` and log in again |
| Email shows "(could not analyze)" | Claude returned invalid JSON for that email. Run again. |
| Report date isn't today | Check the bottom of `run_log.txt` and Task Scheduler's **Last Run Result** |
| `UnicodeEncodeError` in `run_log.txt` | `set PYTHONUTF8=1` is missing from `run_daily.bat` |
| Marked the wrong task as done | Remove its key from the `"done"` list in `memory.json` |
| Start over | Delete `memory.json`. The next run re-analyzes everything, which uses credit. |

More cases, and the reasoning behind each fix, are in [docs/build-log.md](docs/build-log.md#troubleshooting).

## Roadmap

- [x] Categorize, summarize, flag urgency, extract deadlines and actions
- [x] Daily overview with task tracking
- [x] Scheduled daily runs
- [x] Daily overview as a web page
- [ ] Open the page automatically every morning
- [ ] Keyword filters (e.g. a single sender)
- [ ] Custom topics (e.g. food, jobs, coupons)
- [ ] Publish the Google app to remove the weekly re-login
- [ ] Chat-style agent ("show me this week's job emails")

## Further reading

[docs/build-log.md](docs/build-log.md) covers how this was built, phase by phase:

- concepts (OAuth, scopes, JSON output, time zones),
- every setup step in detail,
- full code walkthroughs,
- bugs that came up and how they were fixed,
- design decisions, such as why draft replies were dropped.