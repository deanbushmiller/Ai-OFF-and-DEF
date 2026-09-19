"""RECOVER, second half - tune the control with what you just learned.

    python tune.py --add socket.create_connection

You quarantined the beacon artifact and its SHA-256 is on the block list. The
gate will refuse that exact file forever, for free, without scanning.

Forever, and only that exact file.

So this step does what an adversary does the next morning: it takes the
quarantined artifact and changes one byte that has no effect on the payload.
Same behaviour, new hash, and your block list has never seen it.

Watch which line of the gate catches the re-upload before you add the rule,
and which line catches it after. The verdict is the same both times. The
authority behind it is not, and that is the whole point of this step:
picklescan has had 58 published CVEs since February 2025, every one a way
past its own denylist. It is patched today. The fifty-ninth is written and
not yet published. A control you own does not depend on that.

Expert mode makes the same edit with `nano rules.json`.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "rules.json")
QUARANTINE = os.path.join(HERE, "quarantine")
WIDTH = 64
SOURCES = (os.path.join(QUARANTINE, "bert_tiny_beacon.pt"),
           os.path.join(HERE, "bert_tiny_beacon.pt"))
REUPLOAD = os.path.join(HERE, "bert_tiny_beacon_reupload.pt")


def make_reupload():
    """Same artifact, one meaningless byte different, therefore a new hash.

    The byte goes in the ZIP archive comment - a field no loader reads and no
    payload depends on. Nothing about the behaviour changes.
    """
    src = next((p for p in SOURCES if os.path.exists(p)), None)
    if src is None:
        return None
    shutil.copy(src, REUPLOAD)
    with zipfile.ZipFile(REUPLOAD, "a") as archive:
        archive.comment = b"reuploaded-under-a-new-name"
    return REUPLOAD


def gate(path):
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "gate.py"), path],
        capture_output=True, text=True, timeout=180,
    )
    out = proc.stdout or ""
    return next((l.strip() for l in out.split("\n") if "BLOCKED" in l or "ALLOWED" in l),
                "(no verdict line)")


def main():
    ap = argparse.ArgumentParser(description="Add an indicator to the gate's own rules.")
    ap.add_argument("--add", required=True, metavar="GLOBAL",
                    help="the global to refuse on sight, e.g. socket.create_connection")
    args = ap.parse_args()

    if not re.fullmatch(r"[A-Za-z_][\w.]{0,80}", args.add):
        print("That does not look like a module.attribute name: " + args.add)
        return 64

    rules = json.loads(open(RULES, encoding="utf-8").read())

    print("=" * WIDTH)
    print(" TUNE THE GATE")
    print("=" * WIDTH)
    print()

    variant = make_reupload()
    if variant is None:
        print("  Could not find bert_tiny_beacon.pt to work from.")
        print("  Run:  python make_model.py --all")
        return 66

    print("  Made a re-upload of the quarantined artifact:")
    print("    " + os.path.basename(variant))
    print("    identical payload, one byte of archive comment different,")
    print("    so its hash is new and the block list has never seen it.")
    print()
    print("  BEFORE you add the rule:")
    print("    " + gate(variant))
    print()

    if args.add in rules.get("blocked_globals", []):
        print("  " + args.add + " is already in rules.json. Nothing to add.")
        return 0

    rules.setdefault("blocked_globals", []).append(args.add)
    with open(RULES, "w", encoding="utf-8") as fh:
        json.dump(rules, fh, indent=2)
        fh.write("\n")

    print("  Added to rules.json blocked_globals:")
    print("    " + args.add)
    print("  (the indicator your own sandbox produced, not one you were given)")
    print()
    print("  AFTER:")
    print("    " + gate(variant))
    print()
    print("  Same verdict. Different authority.")
    print()
    print("    the block list  caught the file you had already seen")
    print("    your rule       catches the behaviour, including tomorrow's copy")
    print("    the scanner     catches what its vendor knew about when it shipped")
    print()
    print("  You need all three. Only one of them is yours.")
    print()
    print("  Detect, contain, tune. The loop is closed.")
    print("=" * WIDTH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
