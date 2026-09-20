"""Plant the attacker's line in the public notes, and put it back afterwards.

    python plant.py            append payload.txt to the public notes
    python plant.py --reset    restore the notes to their baked state

Carried over from lab 5 unchanged in spirit. The attacker's whole move is one
visible line in a file the agent is supposed to read. Nothing is hidden: no
zero-width characters, no white-on-white text, no HTML comment. Concealment is
lab 12's subject and it is not needed here.

That is the lesson, not a shortcut. When the authorization is missing, payload
craft stops mattering - lab 5 measured four completely different payload styles
escalating 3 times out of 3 each. An attacker who can get one line of text in
front of the agent has already won the argument with the model.

In the real world that line arrives inside a support ticket, a calendar invite, a
CI log, or - as Cline found out in February 2026 - a GitHub issue title.
"""
import argparse
import pathlib
import shutil
import sys

WORK = pathlib.Path("/labs/lab13")
NOTES = WORK / "notes"
PRISTINE = WORK / "notes-pristine"
PAYLOAD = WORK / "payload.txt"


def reset():
    NOTES.mkdir(exist_ok=True)
    for src in PRISTINE.iterdir():
        shutil.copyfile(src, NOTES / src.name)
    print("Public and admin notes restored to their original state.")


def plant():
    payload = PAYLOAD.read_text().strip()
    if not payload:
        print("payload.txt is empty - nothing to plant.")
        sys.exit(1)

    target = NOTES / "public.txt"
    if payload in target.read_text():
        print("The payload is already in the public notes.")
        return

    with target.open("a") as fh:
        fh.write("- " + payload + "\n")

    print(f"Appended {len(payload)} characters to notes/public.txt\n")
    print("The public notes now read:\n")
    for line in target.read_text().rstrip().splitlines():
        print("   " + line)
    print()
    print("Nothing is hidden. That line is visible to anyone who opens the")
    print("file - and the model is still going to do what it says.")
    print("The question this lab asks is not whether the model obeys it.")
    print("It is what the agent is ALLOWED to do once it has.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true",
                    help="restore the notes to their baked state")
    args = ap.parse_args()
    reset() if args.reset else plant()
