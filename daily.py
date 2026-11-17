import html
import json
import os
from collections import Counter
from datetime import date, datetime
from gmail_tools import get_unread_emails, GmailLoginExpired
from analyze import analyze_email  # reuse the Phase 4 "form filler"

MEMORY_FILE = "memory.json"
REPORT_FILE = "daily_overview.md"
HTML_FILE = "daily_overview.html"  # the same report as a web page, opened in the browser
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


# ---------- The web page (daily_overview.html) ----------

CSS = """
:root { --bg:#f8f9fa; --surface:#fff; --text:#202124; --muted:#5f6368; --line:#dadce0;
        --blue:#1a73e8; --blue-bg:#e8f0fe; --red:#d93025; --red-bg:#fce8e6;
        --amber:#b06000; --amber-bg:#fef7e0; --green:#188038; --green-bg:#e6f4ea;
        --shadow:0 1px 2px rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15); }
@media (prefers-color-scheme: dark) {
  :root { --bg:#202124; --surface:#2d2e31; --text:#e8eaed; --muted:#9aa0a6; --line:#3c4043;
          --blue:#8ab4f8; --blue-bg:#1e2a3d; --red:#f28b82; --red-bg:#3c2523;
          --amber:#fdd663; --amber-bg:#3a3424; --green:#81c995; --green-bg:#1f3326;
          --shadow:0 1px 2px rgba(0,0,0,.6), 0 1px 3px 1px rgba(0,0,0,.3); }
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text);
       font:14px/20px "Google Sans", Roboto, "Segoe UI", Arial, sans-serif; }
header { background:var(--surface); border-bottom:1px solid var(--line); }
header div { max-width:880px; margin:0 auto; padding:16px 24px; display:flex;
             justify-content:space-between; align-items:baseline; }
header h1 { font-size:22px; font-weight:400; margin:0; }
header span { color:var(--muted); }
main { max-width:880px; margin:0 auto; padding:24px; }
h2 { font-size:16px; font-weight:500; margin:32px 0 12px; display:flex; align-items:center; gap:8px; }
.count { font-size:12px; font-weight:500; color:var(--muted); background:var(--line);
         border-radius:10px; padding:0 8px; line-height:20px; }
.stats { display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; }
.stat { background:var(--surface); border-radius:8px; box-shadow:var(--shadow); padding:16px; }
.stat b { display:block; font-size:32px; font-weight:400; line-height:40px; }
.stat span { color:var(--muted); font-size:13px; }
.stat.red b { color:var(--red); } .stat.blue b { color:var(--blue); }
.list { background:var(--surface); border-radius:8px; box-shadow:var(--shadow); overflow:hidden; }
.row { display:flex; gap:16px; align-items:flex-start; padding:14px 16px; border-top:1px solid var(--line); }
.row:first-child { border-top:0; }
.row:hover { background:var(--bg); }
.main { flex:1; min-width:0; }
.from, .meta { color:var(--muted); font-size:13px; }
.main p { margin:4px 0 0; }
.num { color:var(--muted); font-weight:500; min-width:20px; text-align:right; flex:none; }
.date { font-weight:500; min-width:92px; flex:none; }
.label { font-size:12px; font-weight:500; padding:2px 8px; border-radius:4px; white-space:nowrap; flex:none;
         background:var(--blue-bg); color:var(--blue); }
.label.today, .label.overdue { background:var(--red-bg); color:var(--red); }
.label.soon { background:var(--amber-bg); color:var(--amber); }
.chips { display:flex; flex-wrap:wrap; gap:8px; }
.chip { border:1px solid var(--line); border-radius:8px; padding:6px 12px; font-size:13px;
        background:var(--surface); }
.chip b { font-weight:500; margin-left:6px; color:var(--muted); }
.empty { background:var(--surface); border-radius:8px; box-shadow:var(--shadow);
         padding:16px; color:var(--muted); }
.warning { background:var(--red-bg); color:var(--red); border-radius:8px; padding:12px 16px; margin-bottom:16px; }
.warning small { display:block; color:var(--text); margin-top:4px; }
footer { color:var(--muted); font-size:12px; margin-top:40px; }
.email { padding:16px; border-top:1px solid var(--line); }
.email:first-child { border-top:0; }
.title-row { display:flex; justify-content:space-between; gap:12px; align-items:baseline; }
.title { font-size:16px; font-weight:500; line-height:22px; }
.sender { color:var(--muted); font-size:13px; margin-top:2px; }
.summary { margin:8px 0 0; line-height:22px; }
.why { background:var(--bg); border-radius:6px; padding:8px 12px; margin-top:10px;
       color:var(--muted); font-size:13px; }
code { font-family:"Roboto Mono", Consolas, monospace; background:var(--line); padding:1px 6px; border-radius:4px; }
@media (max-width:640px) { .stats { grid-template-columns:repeat(2, 1fr); } }
"""


def _e(text):
    """Escape text so characters like < or & in an email subject can't break the page."""
    return html.escape(str(text))


def _label(due, today):
    """A coloured label for a due date: red = today/overdue, amber = within 3 days."""
    days = (due - today).days
    kind = "overdue" if days < 0 else "today" if days == 0 else "soon" if days <= 3 else ""
    return f'<span class="label {kind}">{_e(_when(due, today).replace("⚠️ ", ""))}</span>'


def _section(title, count):
    return f"<h2>{_e(title)}<span class='count'>{count}</span></h2>"


def build_html(memory, warning=None):
    """Turn the notebook into a clean web page (same content as the .md report)."""
    today = date.today()
    items = open_items(memory)
    open_email_ids = {item["email_id"] for item in items}
    groups = {level: [e for email_id, e in memory["emails"].items()
                      if e.get("urgency") == level
                      and _still_relevant(email_id, e, open_email_ids, today)]
              for level in ("High", "Medium")}
    numbered = list(enumerate(items, start=1))
    deadlines = [(n, it) for n, it in numbered if it["kind"] == "deadline"]
    todos = [(n, it) for n, it in numbered if it["kind"] == "action"]

    parts = []
    if warning:
        parts.append(f"<div class='warning'><b>Gmail login expired.</b> {_e(warning)}"
                     "<small>The overview below only shows what was already in the notebook.</small></div>")

    # At a glance
    parts.append("<div class='stats'>"
                 f"<div class='stat red'><b>{len(groups['High'])}</b><span>Urgent</span></div>"
                 f"<div class='stat blue'><b>{len(deadlines)}</b><span>Open deadlines</span></div>"
                 f"<div class='stat'><b>{len(todos)}</b><span>To-dos</span></div>"
                 f"<div class='stat'><b>{len(memory['emails'])}</b><span>Emails analyzed</span></div>"
                 "</div>")

    # Urgent + needs attention (goal 3): subject as title, Claude's summary below, reason in a grey box
    for level, title, label, css, empty in [("High", "Urgent", "Urgent", "today", "Nothing urgent."),
                                            ("Medium", "Needs attention soon", "Soon", "soon", "Nothing here.")]:
        parts.append(_section(title, len(groups[level])))
        if not groups[level]:
            parts.append(f"<div class='empty'>{empty}</div>")
            continue
        parts.append("<div class='list'>")
        for e in groups[level]:
            parts.append("<div class='email'>"
                         f"<div class='title-row'><div class='title'>{_e(e['subject'])}</div>"
                         f"<span class='label {css}'>{label}</span></div>"
                         f"<div class='sender'>{_e(e['from'])}</div>"
                         f"<p class='summary'>{_e(e['summary'])}</p>"
                         f"<div class='why'>Why: {_e(e['urgency_reason'])}</div>"
                         "</div>")
        parts.append("</div>")

    # Deadlines (goal 4)
    parts.append(_section("Deadlines", len(deadlines)))
    if not deadlines:
        parts.append("<div class='empty'>No open deadlines.</div>")
    else:
        parts.append("<div class='list'>")
        for n, it in deadlines:
            parts.append(f"<div class='row'><span class='num'>{n}</span>"
                         f"<span class='date'>{it['due'].strftime('%a, %d %b')}</span>"
                         f"<div class='main'>{_e(it['text'])}<div class='meta'>{_e(it['subject'])}</div></div>"
                         f"{_label(it['due'], today)}</div>")
        parts.append("</div>")

    # To-do (goal 4)
    parts.append(_section("To-do", len(todos)))
    if not todos:
        parts.append("<div class='empty'>Nothing to do.</div>")
    else:
        parts.append("<div class='list'>")
        for n, it in todos:
            parts.append(f"<div class='row'><span class='num'>{n}</span>"
                         f"<div class='main'>{_e(it['text'])}<div class='meta'>{_e(it['subject'])}</div></div></div>")
        parts.append("</div>")

    # Categories (goal 1)
    counts = Counter(e.get("category", "Other") for e in memory["emails"].values())
    parts.append(_section("By category", len(counts)))
    parts.append("<div class='chips'>")
    parts.extend(f"<span class='chip'>{_e(category)}<b>{n}</b></span>" for category, n in counts.most_common())
    parts.append("</div>")

    parts.append("<footer>Finished something? Run <code>python done.py</code> and type its number. "
                 f"Updated {datetime.now().strftime('%d %b %Y, %H:%M')}.</footer>")

    return ("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>Daily overview · {today.strftime('%d %b')}</title><style>{CSS}</style></head>"
            f"<body><header><div><h1>Daily overview</h1><span>{today.strftime('%A, %d %B %Y')}</span></div></header>"
            f"<main>{''.join(parts)}</main></body></html>")


def write_report(memory, warning=None):
    """Save the overview twice: as Markdown and as a web page."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(build_report(memory, warning))
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(build_html(memory, warning))
    print(f"Daily overview saved to {REPORT_FILE} and {HTML_FILE}")


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