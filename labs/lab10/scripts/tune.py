"""RECOVER, second half - tune the validator with what you just learned.

    python tune.py --add invisible-text

You purged the poisoned chunks and the canary answers correctly again. The index
is clean.

Clean, and exactly as easy to poison as it was an hour ago.

So this step does what an attacker does the next morning: it re-issues the same
payload as a NEW document with a different filename, and asks the validator
again. Watch which rule catches the re-upload before you add yours, and which
catches it after. The verdict is the same both times. The authority behind it is
not, and that is the whole point of this step.

Rules 1, 2 and 3 came with the lab. They are somebody else's judgement about what
a poisoned document looks like - well-founded, measured, and written before your
incident happened. The rule you add here is the one your own detector produced,
on your own corpus, from the document that actually got through. It is the only
one of the four that knows anything about you.

Expert mode makes the same edit with `nano rules.json`.
"""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys

LAB = pathlib.Path("/labs/lab10")
RULES = LAB / "rules.json"
SOURCE_PDF = LAB / "poisoned_handbook.pdf"
REUPLOAD = LAB / "q3-planning-notes.pdf"
WIDTH = 68


def validate(path):
    proc = subprocess.run([sys.executable, str(LAB / "validate.py"), str(path)],
                          capture_output=True, text=True)
    out = proc.stdout or ""
    rules_fired = [l.strip() for l in out.split("\n")
                   if l.strip().startswith(("RULE", "YOUR RULE"))]
    verdict = "REFUSED" if proc.returncode else "PASS"
    return verdict, rules_fired


def main():
    ap = argparse.ArgumentParser(description="Add an indicator to your own rules.")
    ap.add_argument("--add", required=True, metavar="INDICATOR",
                    help="the indicator to refuse on sight, e.g. invisible-text")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z][a-z0-9-]{1,40}", args.add):
        print("That does not look like an indicator name: " + args.add)
        print("Try something like: invisible-text")
        return 64

    if not SOURCE_PDF.exists():
        print("Could not find poisoned_handbook.pdf to work from.")
        print("Run:  python make_poison.py")
        return 66

    rules = json.loads(RULES.read_text(encoding="utf-8"))

    print("=" * WIDTH)
    print(" TUNE THE VALIDATOR")
    print("=" * WIDTH)
    print()

    shutil.copy(SOURCE_PDF, REUPLOAD)
    print("  The same payload, re-issued under a name nobody would question:")
    print("    " + REUPLOAD.name)
    print("    identical content, new filename, and it has never been seen")
    print("    by this pipeline before.")
    print()

    verdict, fired = validate(REUPLOAD)
    print("  BEFORE you add your rule:")
    print("    " + verdict)
    for f in fired:
        print("      " + f)
    print()

    if args.add in rules.get("blocked_indicators", []):
        print("  " + args.add + " is already in rules.json. Nothing to add.")
        return 0

    rules.setdefault("blocked_indicators", []).append(args.add)
    RULES.write_text(json.dumps(rules, indent=2) + "\n", encoding="utf-8")
    print("  Added to rules.json blocked_indicators:")
    print("    " + args.add)
    print("    (the indicator your own detector produced, not one you were given)")
    print()

    verdict, fired = validate(REUPLOAD)
    print("  AFTER:")
    print("    " + verdict)
    for f in fired:
        print("      " + f)
    print()
    print("  Same verdict. Different authority.")
    print()
    print("    rules 1-3        somebody else's judgement, written before your")
    print("                     incident, and right about this one")
    print("    the canary       caught it only AFTER it was already answering")
    print("                     your users' questions")
    print("    your rule        catches it at the door, and it exists because")
    print("                     your own detector produced it")
    print()
    print("  You need all three. Only one of them is yours.")
    print()
    print("  Validate, detect, purge, tune. The loop is closed.")
    print("=" * WIDTH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
