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