"""Expert-mode self-check.

    python check.py

Beginner mode asserts as it goes and cannot finish in a wrong state. Expert
mode has no rails: you ran the pieces in your own order and edited rules.json
by hand. This says whether the defence actually holds together.

It checks the recorded evidence, not what scrolled past on screen.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "rules.json")
BLOCKLIST = os.path.join(HERE, "blocklist.json")
QUARANTINE = os.path.join(HERE, "quarantine")
LOG = os.path.join(HERE, "sandbox-log.jsonl")

OK, BAD = "  PASS  ", "  FAIL  "
problems = []


def check(label, cond, hint):
    print((OK if cond else BAD) + label)
    if not cond:
        problems.append(hint)


def read_json(path, default):
    try:
        return json.loads(open(path, encoding="utf-8").read())
    except (OSError, ValueError):
        return default


def main():
    print("=" * 68)
    print(" LAB 9 SELF-CHECK")
    print("=" * 68)
    print()

    rules = read_json(RULES, {})
    book = read_json(BLOCKLIST, {}).get("blocked", {})

    quarantined = []
    if os.path.isdir(QUARANTINE):
        quarantined = [f for f in os.listdir(QUARANTINE) if f.endswith(".pt")]

    events = []
    if os.path.exists(LOG):
        for line in open(LOG, encoding="utf-8"):
            line = line.strip()
            if line:
                events.append(json.loads(line))

    check("the sandbox ran and wrote a log",
          bool(events),
          "run: python sandboxed_load.py bert_tiny_corrupt.pt")

    check("the sandbox caught a payload acting on load",
          any(e.get("verdict") in ("EXECUTED", "BLOCKED") for e in events),
          "run the sandbox against bert_tiny_corrupt.pt or bert_tiny_beacon.pt, not the clean file")

    check("an artifact is in quarantine/",
          bool(quarantined),
          "run: python quarantine.py bert_tiny_beacon.pt")

    check("its hash is on the block list",
          bool(book),
          "quarantine.py records the hash - check blocklist.json exists")

    check("the block list entry carries its evidence",
          any(entry.get("evidence") for entry in book.values()),
          "quarantine the file AFTER sandboxing it, so there is a log to record")

    check("the gate fails closed on an unreadable artifact",
          rules.get("on_scanner_error") == "block",
          'set "on_scanner_error": "block" in rules.json')

    check("you added an indicator of your own to rules.json",
          "socket.create_connection" in rules.get("blocked_globals", []),
          'add "socket.create_connection" to blocked_globals in rules.json')

    print()
    if problems:
        print(" NOT DONE YET. " + str(len(problems)) + " thing(s) to finish:")
        print()
        for hint in problems:
            print("   - " + hint)
        print()
        print("=" * 68)
        return 1

    print(" ALL CHECKS PASS.")
    print()
    print(" You have the four pieces of evidence the lab asks for:")
    print("   the gate's verdicts, the sandbox log, the quarantine record,")
    print("   and a rule you wrote yourself.")
    print()
    print(" Paste the block list entry and the sandbox finding into the class")
    print(" chat. The pair is the proof.")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())
