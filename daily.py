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