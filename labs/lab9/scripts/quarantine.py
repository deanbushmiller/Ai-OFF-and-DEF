"""RECOVER - contain the artifact and record what you learned.

    python quarantine.py <artifact.pt>

Three things happen, in this order:

  1. the file is MOVED to quarantine/ - out of the build path, not deleted.
     You cannot investigate a file you destroyed, and you may need it for a
     supplier conversation.
  2. its SHA-256 goes on blocklist.json with the date and the reason, so the
     gate refuses it next time without running a scanner at all
  3. the sandbox log is copied in beside it, because the evidence and the
     artifact belong together

What this is not: a real quarantine writes to a ticket, notifies the owning
team, and revokes the artifact wherever it was already pulled. Here it is a
directory and a JSON file. The shape is right; the scale is not.
"""
import datetime
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
QUARANTINE = os.path.join(HERE, "quarantine")
BLOCKLIST = os.path.join(HERE, "blocklist.json")
LOG = os.path.join(HERE, "sandbox-log.jsonl")
WIDTH = 64


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reason_from_log():
    """Read the sandbox's own findings rather than asking the student to retype them."""
    if not os.path.exists(LOG):
        return "blocked at the gate", []
    events = []
    for line in open(LOG, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("verdict") in ("EXECUTED", "BLOCKED"):
            events.append(rec["event"] + " " + rec["detail"][:80])
    if not events:
        return "blocked at the gate", []
    return events[0].split(" ")[0] + " on load", events


def main():
    if len(sys.argv) != 2:
        print("usage: python quarantine.py <artifact.pt>")
        return 64
    path = sys.argv[1]
    if not os.path.exists(path):
        print("No such file: " + path)
        return 66

    name = os.path.basename(path)
    digest = sha256(path)
    when = datetime.date.today().isoformat()
    reason, events = reason_from_log()

    os.makedirs(QUARANTINE, exist_ok=True)
    dest = os.path.join(QUARANTINE, name)
    shutil.move(path, dest)

    if os.path.exists(LOG):
        shutil.copy(LOG, os.path.join(QUARANTINE, name + ".sandbox-log.jsonl"))

    book = {"blocked": {}}
    if os.path.exists(BLOCKLIST):
        try:
            book = json.loads(open(BLOCKLIST, encoding="utf-8").read())
        except ValueError:
            pass
    book.setdefault("blocked", {})[digest] = {
        "name": name, "when": when, "reason": reason,
        "evidence": events[:4],
    }
    with open(BLOCKLIST, "w", encoding="utf-8") as fh:
        json.dump(book, fh, indent=2)
        fh.write("\n")

    print("=" * WIDTH)
    print(" QUARANTINED  " + name)
    print("=" * WIDTH)
    print()
    print("  moved to    quarantine/" + name)
    print("  sha256      " + digest)
    print("  reason      " + reason)
    if events:
        print("  evidence    " + events[0])
        for extra in events[1:3]:
            print("              " + extra)
    print()
    print("  " + str(len(book["blocked"])) + " artifact(s) now on the block list.")
    print()
    print("  The gate will refuse this hash from now on, without scanning.")
    print("=" * WIDTH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
