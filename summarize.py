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