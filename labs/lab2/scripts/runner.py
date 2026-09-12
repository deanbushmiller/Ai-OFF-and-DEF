#!/usr/bin/env python3
"""
Lab 2 runner. Asks the student to choose beginner or expert mode.

Beginner: the guided path from lab 1 - shows each command, checks what the
          student types, corrects a miss, runs the real command on a match.
Expert:   drops to a real shell in the lab folder. The student works from
          LAB.md, including the steps beginner skips (cd, editing with nano).

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command; on a match we run our own known-good copy.
"""
import argparse
import os
import re
import subprocess
import sys

WORK = "/labs/lab2"
RESULTS = os.path.join(WORK, "lab2-results.txt")
WIDTH = 68

_log = open(RESULTS, "w", encoding="utf-8")


def say(t=""):
    print(t)
    _log.write(t + "\n")
    _log.flush()


def rule(ch="="):
    say(ch * WIDTH)


def normalize(s):
    return re.sub(r"\s+", " ", s.strip())


def fail(msg):
    say("")
    rule()
    say(" LAB ERROR - stopping rather than showing you a wrong result.")
    say("")
    say("   " + msg)
    say("")
    say(" This is a problem with the lab, not with anything you did.")
    say(" Send lab2-results.txt to the instructor through GitHub.")
    rule()
    sys.exit(1)


Q1 = 'Who invented the telephone?'
Q2 = 'Who painted the Mona Lisa?'

STEPS = [
    {"why": ["This is the company knowledge base - 15 documents, one per",
             "historical figure. Plain text, nothing unusual."],
     "cmd": "ls corpus/", "rc": 0},
    {"why": ["Embed all 15 documents into a searchable index.",
             "This is what a real ingestion pipeline does to a SharePoint",
             "or wiki export."],
     "cmd": "python rag.py build", "rc": 0, "after": "index.npz"},
    {"why": ["Ask the pipeline a question. It retrieves the most similar",
             "documents, then answers using only those.",
             "This is ground truth. Note the answer AND the scores."],
     "cmd": f'python rag.py ask "{Q1}"', "rc": 0, "want": "Bell"},
    {"why": ["Now read the attack before you run it.",
             "Look for the two text layers, and for the last line of the",
             "payload - that is keyword stuffing, so the poison ranks first."],
     "cmd": "cat make_poison.py", "rc": 0},
    {"why": ["Build the poisoned PDF. It looks like an IT onboarding",
             "checklist. The payload is white text on a white background."],
     "cmd": "python make_poison.py", "rc": 0, "after": "poisoned_handbook.pdf"},
    {"why": ["See the gap. This prints what the TEXT EXTRACTOR reads,",
             "which is not what a human sees on the page."],
     "cmd": "python peek_pdf.py poisoned_handbook.pdf", "rc": 0, "want": "Dean Bushmiller"},
    {"why": ["Add the PDF to the knowledge base - the way a document gets",
             "uploaded to a wiki, or synced from a shared drive.",
             "Nobody reviews it. Nothing checks where it came from."],
     "cmd": "python rag.py ingest poisoned_handbook.pdf", "rc": 0},
    {"why": ["Ask the exact same question again.",
             "Same model. Same code. Same question. One new document."],
     "cmd": f'python rag.py ask "{Q1}"', "rc": 0, "want": "Dean Bushmiller"},
    {"why": ["And a completely unrelated question, to show this is not a",
             "one-off. One document poisoned the whole knowledge base."],
     "cmd": f'python rag.py ask "{Q2}"', "rc": 0, "want": "Dean Bushmiller"},
    {"why": ["The evidence, side by side. This is what you submit."],
     "cmd": "python rag.py evidence", "rc": 0},
]


def ask_step(step, n, total, challenge, auto):
    say("")
    rule()
    say(f" STEP {n} of {total}")
    rule()
    say("")
    for line in step["why"]:
        say("  " + line)
    say("")
    if challenge:
        say("  CHALLENGE MODE - work the command out yourself.")
    else:
        say("  The command:")
        say("")
        say("      " + step["cmd"])
    say("")
    if auto:
        say("  [auto mode] " + step["cmd"])
        return "auto"
    misses = 0
    while True:
        try:
            raw = input("  type or paste the command > ")
        except (EOFError, KeyboardInterrupt):
            say("")
            say("  (no input - running the command so the lab can continue)")
            return "auto"
        _log.write(f"  type or paste the command > {raw}\n")
        if not raw.strip():
            continue
        if normalize(raw) == normalize(step["cmd"]):
            return "typed"
        misses += 1
        if misses >= 2:
            say("")
            say("  Still not matching, so here it is, running for you:")
            say("      " + step["cmd"])
            return "shown"
        say("")
        say("  Not quite. The command should be:  " + step["cmd"])
        say("")


def run(cmd):
    say("")
    say("  $ " + cmd)
    say("  " + "-" * (WIDTH - 2))
    p = subprocess.run(cmd, shell=True, cwd=WORK, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    for line in out.rstrip("\n").split("\n"):
        say("  " + line)
    say("")
    return p.returncode, out


def choose_mode(auto):
    if auto:
        return "1"
    rule()
    say(" LAB 2 - RAG AND SEMANTIC INGESTION ATTACKS")
    rule()
    say("")
    say("  Choose your mode:")
    say("    [1] Beginner  - the lab shows each command; you type or paste")
    say("                    it and it is checked")
    say("    [2] Expert    - you type the real commands yourself in a shell,")
    say("                    working from LAB.md")
    say("")
    say("  You can re-run the lab to switch.")
    say("")
    while True:
        try:
            c = input("  Mode [1/2] > ").strip()
        except (EOFError, KeyboardInterrupt):
            return "1"
        if c in ("1", "2", ""):
            return c or "1"


def expert_shell():
    say("")
    rule()
    say(" EXPERT MODE")
    rule()
    say("")
    say("  You are in /labs/lab2 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every command is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - cd into the lab folder yourself")
    say("    - edit poison_source.txt with nano and put your OWN name in it,")
    say("      then rebuild the PDF and watch the answer change")
    say("")
    say("  When you are done, run this to check your work:")
    say("      python check.py")
    say("")
    say("  Type 'exit' to leave the container.")
    say("")
    _log.close()
    os.chdir(WORK)
    os.execvp("/bin/bash", ["/bin/bash"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--challenge", action="store_true")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--expert", action="store_true")
    args = ap.parse_args()

    if args.expert or choose_mode(args.auto) == "2":
        expert_shell()
        return

    rule()
    say(" LAB 2 - RAG AND SEMANTIC INGESTION ATTACKS  (beginner)")
    rule()
    say("")
    say("  The question this lab answers:")
    say("    If anyone can add a document to the knowledge base your")
    say("    assistant reads, who decides what is true?")
    say("")
    say("  OWASP  LLM01:2026 Prompt Injection (indirect, via retrieved content)")
    say("         LLM07:2026 Misinformation")
    say("         LLM09:2026 Vector and Embedding Weaknesses (the retrieval step)")
    say("  ATLAS  AML.T0064 > AML.T0066 > AML.T0068 > AML.T0051.001 > AML.T0070")
    say("")
    say("  Ten commands. Nothing leaves this container. The payload is a")
    say("  false sentence, not code.")

    total = len(STEPS)
    typed = 0
    for i, step in enumerate(STEPS, 1):
        how = ask_step(step, i, total, args.challenge, args.auto)
        if how == "typed":
            typed += 1
        rc, out = run(step["cmd"])
        if step.get("rc") is not None and rc != step["rc"]:
            fail(f"Step {i} ({step['cmd']}) returned {rc}, expected {step['rc']}.")
        if step.get("after") and not os.path.exists(os.path.join(WORK, step["after"])):
            fail(f"Step {i} should have created {step['after']}, but it does not exist.")
        want = step.get("want")
        if want and want not in out:
            fail(f"Step {i} output should have contained {want!r}. "
                 f"The lab did not behave as designed.")
        if i == 3:
            say("  ^ Correct. Remember the score on bell.txt - you will see it beaten.")
        if i == 8:
            say("  ^ The same question now returns the attacker's answer.")
            say("    Look at the retrieval scores: poisoned_handbook.pdf outranked")
            say("    bell.txt. Nothing was hacked. A document was added.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM A REAL ATTACK")
    rule()
    say("")
    say("   THIS LAB                      A REAL ATTACK")
    say("   payload names a person        payload names a phishing URL or a")
    say("     you know is not the answer    plausible wrong policy")
    say("   one obvious PDF               dozens of documents, drip-fed")
    say("   local corpus, 15 documents    SharePoint, Confluence, a ticket queue")
    say("   you ingest it yourself        an outsider uploads it and waits")
    say("   white text, easy to find      Unicode tricks, metadata, alt text")
    say("")
    rule()
    say(" THE DEFENCE")
    rule()
    say("")
    say("   1. Treat retrieved text as DATA, never as instructions. Mark it")
    say("      in the prompt so the model can tell it apart.")
    say("   2. Gate ingestion. Who may add documents, and who reviewed them?")
    say("   3. Keep provenance per chunk, and show it with the answer, so a")
    say("      user can see the source that produced it.")
    say("   4. Extract and inspect the full text layer at upload time. White")
    say("      text and zero-width characters are visible to a scanner.")
    say("   5. Prefer ground-truth sources for facts that matter, and make")
    say("      the assistant cite them.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")
    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste the output of the last command into the class chat - the")
    say("  BEFORE and AFTER block. Both halves, or it proves nothing.")
    say("")
    say("  Full transcript saved to lab2-results.txt on your machine.")
    say("")
    rule()
    say(" BEFORE YOU CLOSE THIS")
    rule()
    say("")
    say("  When this window exits, the setup script offers to download the")
    say("  next lab. Say yes - it is a small download because the labs share")
    say("  most of their layers.")
    say("")


if __name__ == "__main__":
    main()
