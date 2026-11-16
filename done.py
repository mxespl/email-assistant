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