#!/usr/bin/env python3
"""
Lab 10 guided runner. The student types every command.

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command. On a match we run our own known-good copy of
that string. This is a security course.
"""
import argparse
import os
import re
import subprocess
import sys

WORK = "/labs/lab10"
RESULTS = os.path.join(WORK, "lab10-results.txt")
WIDTH = 64

_log = open(RESULTS, "w", encoding="utf-8")


def say(text=""):
    print(text)
    _log.write(text + "\n")
    _log.flush()


def rule(ch="="):
    say(ch * WIDTH)


def normalize(s):
    """Trim outer spaces, collapse repeated inner spaces. Flags, filenames and
    case stay exact."""
    return re.sub(r"\s+", " ", s.strip())


def fail(msg):
    say("")
    rule()
    say(" LAB ERROR - stopping here rather than showing you a wrong result.")
    say("")
    say("   " + msg)
    say("")
    say(" This is a problem with the lab, not with anything you did.")
    say(" Send lab10-results.txt to the instructor via email or post to class Q&A.")
    rule()
    sys.exit(1)


CANARY_Q = "Who invented the telephone?"

STEPS = [
    {
        "why": [
            "PREVENT. The validator is what stands between a document and",
            "your index. Three rules: refuse ink a human cannot read, refuse",
            "a document with no recorded origin, refuse one that claims to",
            "answer too many different questions.",
            "Start with the 15 documents you already trust. Expect: all pass.",
        ],
        "cmd": "python validate.py corpus/",
        "expect_rc": 0,
        "expect_contains": "15 of 15 documents may be embedded",
        "impact": [
            "^ Fifteen documents, fifteen passes, and every one of them covers",
            "  exactly one topic. That is your baseline, and it is the half of",
            "  the evidence people forget to collect.",
        ],
    },
    {
        "why": [
            "Build the poisoned document from lab 2. Same script, same",
            "payload. A human opening it sees an IT onboarding checklist.",
        ],
        "cmd": "python make_poison.py",
        "expect_rc": 0,
        "after": "poisoned_handbook.pdf",
    },
    {
        "why": [
            "Now run the same validator against it.",
            "Read WHICH rules fire, and read what rule 1 says it found -",
            "that is the text a reviewer opening this file cannot see.",
        ],
        "cmd": "python validate.py poisoned_handbook.pdf",
        "expect_rc": 1,
        "expect_contains": "RULE 1  invisible text",
        "impact": [
            "^ Three rules fired. Rule 1 is the one that matters most: the",
            "  payload is drawn in white on a white page at 6pt, so a human",
            "  reviewer approves a clean-looking checklist while the extractor",
            "  reads every word. Review is not a control against invisible text.",
        ],
    },
    {
        "why": [
            "Index the 15 documents you trust. Each chunk carries the",
            "provenance tag of the document it came from.",
        ],
        "cmd": "python rag.py build",
        "expect_rc": 0,
        "expect_contains": "15 chunks carry a provenance tag",
        "after": "index.npz",
    },
    {
        "why": [
            "DETECT. The canary: one question whose correct answer you",
            "already know, asked after every ingest.",
            "Ask it now, on the clean index, so you know what right looks",
            "like.",
        ],
        "cmd": "python canary.py ask",
        "expect_rc": 0,
        "expect_contains": "CANARY HOLDS",
        "impact": [
            "^ Alexander Graham Bell, from bell.txt, score 0.723. Written to",
            "  canary-log.jsonl. Nothing clever happened here and nothing was",
            "  supposed to.",
        ],
    },
    {
        "why": [
            "Now poison the index - and note what you have to do to manage",
            "it. Your own validator already refused this document, so the",
            "pipeline will not take it without --force.",
            "Type the --force. It is the most honest line in the lab.",
        ],
        "cmd": "python rag.py ingest poisoned_handbook.pdf --force",
        "expect_rc": 0,
        "expect_contains": "UNTAGGED",
        "impact": [
            "^ Eleven chunks went in, all UNTAGGED, over a refusal you",
            "  overrode yourself. Somebody does this in every organisation,",
            "  usually to unblock a demo, usually on a Friday.",
        ],
    },
    {
        "why": [
            "Ask the canary again. Same question, same pipeline, same model.",
            "One document entered the index.",
        ],
        "cmd": "python canary.py ask",
        "expect_rc": 0,
        "expect_contains": "CANARY CHANGED",
        "impact": [
            "^ The answer changed and nothing broke. No error, no exception,",
            "  no alert anywhere else in the system - it retrieved a document",
            "  and answered from it, exactly as designed. Without the canary",
            "  you would find out when a user did.",
        ],
    },
    {
        "why": [
            "The retrieval log. This is the question a detector has to be",
            "able to answer: WHICH document drove that answer?",
        ],
        "cmd": "python rag.py log",
        "expect_rc": 0,
        "expect_contains": "poisoned_handbook.pdf",
        "impact": [
            "^ 0.772 against bell.txt's 0.723. The poisoned chunk did not",
            "  break the ranking - it won it, by 0.049. Note the tag beside",
            "  it: UNTAGGED. You are about to spend that.",
        ],
    },
    {
        "why": [
            "RECOVER. You do not need to know which document was poisoned.",
            "You need to know which documents you can account for.",
            "Purge everything with no provenance tag.",
        ],
        "cmd": "python purge.py --untagged",
        "expect_rc": 0,
        "expect_contains": "index now holds 15 chunks",
        "impact": [
            "^ Eleven chunks gone, by tag, without anyone identifying the",
            "  attack. That option only exists because rule 2 wrote a tag on",
            "  the way in. Without it the only safe recovery is rebuilding the",
            "  whole index - instant here, days on a real corpus.",
        ],
    },
    {
        "why": [
            "Re-ask the canary and confirm the answer is restored.",
            "A purge you have not verified is a hope, not a recovery.",
        ],
        "cmd": "python canary.py check",
        "expect_rc": 0,
        "expect_contains": "RESTORED",
        "impact": [
            "^ Bell is back, from bell.txt, at exactly the score it had",
            "  before. Detected, contained, verified - and you can prove all",
            "  three from the logs rather than from memory.",
        ],
    },
    {
        "why": [
            "TUNE. The index is clean, and exactly as easy to poison as it",
            "was ten minutes ago. This step re-issues the same payload under",
            "a name nobody would question, then adds YOUR indicator to",
            "rules.json.",
        ],
        "cmd": "python tune.py --add invisible-text",
        "expect_rc": 0,
        "expect_contains": "Same verdict. Different authority",
        "impact": [
            "^ Rules 1-3 were somebody else's judgement, written before your",
            "  incident. The canary caught it only after it was already",
            "  answering your users. Your rule catches it at the door, and it",
            "  exists because your own detector produced it.",
        ],
    },
]


def choose_mode(auto):
    if auto:
        return "1"
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
            choice = input("  Mode [1/2] > ").strip()
        except (EOFError, KeyboardInterrupt):
            return "1"
        _log.write("  Mode [1/2] > " + choice + "\n")
        if choice in ("1", "2", ""):
            return choice or "1"


def expert_shell():
    say("")
    rule()
    say(" EXPERT MODE")
    rule()
    say("")
    say("  You are in /labs/lab10 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Expert runs the whole command list. Beginner mode runs only the")
    say("  lines marked with a B.")
    say("")
    say("  The steps beginner never sees:")
    say("    - edit the validator's policy by hand instead of running tune.py:")
    say("        nano rules.json")
    say("      add \"invisible-text\" to blocked_indicators, and look hard at")
    say("      canary_similarity while you are in there. Drop it to 0.50 and")
    say("      re-run the validator over corpus/ - a clean document starts")
    say("      failing. That is the cost of a tighter threshold, measured.")
    say("    - ask the canary NOBODY configured, before the purge and after:")
    say("        python canary.py second")
    say("      Same corpus, same poisoned document, a question you were not")
    say("      watching. Before the purge both are wrong and only one alerts.")
    say("      After it, both are right - because you purged the document by")
    say("      tag rather than correcting an answer.")
    say("    - read what you recorded:   cat canary-log.jsonl")
    say("                                cat retrieval-log.jsonl")
    say("                                cat purge-log.json")
    say("    - purge by document instead of by tag:")
    say("        python purge.py --source poisoned_handbook.pdf")
    say("")
    say("  When you think the defence holds, prove it:")
    say("        python check.py")
    say("")
    say("  Type  exit  when you are done. Your transcript stops here, so")
    say("  copy anything you want to submit before you leave.")
    say("")
    _log.flush()
    os.chdir(WORK)
    os.execv("/bin/bash", ["/bin/bash"])


def ask(step, n, total, challenge, auto):
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
    proc = subprocess.run(cmd, shell=True, cwd=WORK, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    for line in output.rstrip("\n").split("\n"):
        say("  " + line)
    say("")
    return proc.returncode, output


def banner():
    rule()
    say(" LAB 10 - DEFENDING RAG INGESTION")
    rule()
    say("")
    say("  Lab 2 showed you that one document can change what an assistant")
    say("  believes. This lab is the answer: the validator that refuses it,")
    say("  the canary that catches what the validator missed, and the purge")
    say("  that puts the corpus back.")
    say("")
    say("  Defends  lab 2 - RAG and semantic ingestion attacks")
    say("  OWASP    LLM09:2026 Vector and Embedding Weaknesses  (risk 3;")
    say("           preventions 2, 4, 5 and 6)")
    say("           LLM07:2026 Misinformation")
    say("  ATLAS    defends AML.T0066 > AML.T0068 > AML.T0070")
    say("           with  AML.M0020  Generative AI Guardrails")
    say("                 AML.M0024  AI Telemetry Logging")
    say("                 AML.M0033  Input and Output Validation")
    say("")
    say("  Nothing leaves this container. The payload is a visible demo")
    say("  string that states things which are simply false.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--challenge", action="store_true",
                    help="hide the command, show only the description")
    ap.add_argument("--auto", action="store_true",
                    help="run every command without prompting (for testing)")
    args = ap.parse_args()

    banner()

    if choose_mode(args.auto) == "2":
        expert_shell()
        return

    say("")
    say("  Eleven commands. Read each one before you run it.")
    say("  If you mistype, you get told what the command should be.")

    total = len(STEPS)
    typed = 0
    for i, step in enumerate(STEPS, start=1):
        how = ask(step, i, total, args.challenge, args.auto)
        if how == "typed":
            typed += 1
        rc, output = run(step["cmd"])

        if step.get("expect_rc") is not None and rc != step["expect_rc"]:
            fail(f"Step {i} ({step['cmd']}) returned {rc}, expected {step['expect_rc']}.")
        if step.get("after") and not os.path.exists(os.path.join(WORK, step["after"])):
            fail(f"Step {i} should have created {step['after']}, but it does not exist.")
        want = step.get("expect_contains")
        if want and want not in output:
            fail(f"Step {i} output should have contained {want!r}, but did not.")

        for line in step.get("impact", []):
            say("  " + line)

    say("")
    rule()
    say(" THE EVIDENCE - four pieces, and you need all four")
    rule()
    say("")
    say("   the validator   15 of 15 clean documents pass; the poisoned one")
    say("                   is refused, by three rules, one of which a human")
    say("                   reviewer could not have reproduced")
    say("   the canary      Bell before, the attacker's name after, Bell again")
    say("   the log         0.772 against 0.723, naming the poisoned chunk")
    say("                   and its missing provenance tag")
    say("   your rule       one indicator you produced yourself")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")

    rule()
    say(" HOW THIS DIFFERS FROM A REAL DEFENCE")
    rule()
    say("")
    say("   THIS LAB                      PRODUCTION")
    say("   three rules                   content inspection on ingest AND")
    say("                                 on retrieved context")
    say("   a JSON file of tags           signed provenance, per trust tier")
    say("   one canary question           a canary suite, run in CI")
    say("   a local delete                bounded deletion, reconciled by audit")
    say("   you ran it by hand            CI runs it on every ingest batch")
    say("   15 documents                  millions, continuously")
    say("")

    rule()
    say(" THE PART YOU SHOULD NOT MISS")
    rule()
    say("")
    say("  A canary only ever proves the questions you thought of.")
    say("")
    say("  Yours covered the telephone. The same document also claimed the")
    say("  light bulb, the Mona Lisa, penicillin and the World Wide Web -")
    say("  and if your one canary had been about any other subject in that")
    say("  corpus, it would have held, correctly, while four other answers")
    say("  were wrong.")
    say("")
    say("  That is not an argument against canaries. It is the argument for")
    say("  the validator in front of it and the provenance tag underneath")
    say("  it: detection you scoped is detection with a known gap, and the")
    say("  controls that do not depend on guessing the question are the ones")
    say("  that close it.")
    say("")
    say("  Note also what this lab did NOT fix. Look at build_prompt() in")
    say("  rag.py - retrieved text still goes into the prompt unlabelled,")
    say("  exactly as in lab 2. Defending ingestion does not defend the")
    say("  prompt boundary. That is lab 12.")
    say("")

    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste TWO things into the class chat:")
    say("    1. the canary pair - the answer before and after the poison")
    say("    2. the retrieval-log line naming poisoned_handbook.pdf as the")
    say("       source, with its score and its UNTAGGED provenance")
    say("")
    say("  Full transcript saved to lab10-results.txt on your machine.")
    say("")
    rule()
    say(" BEFORE YOU CLOSE THIS")
    rule()
    say("")
    say("  When this window exits, the setup script offers to download the")
    say("  next lab. Say yes - it is a small download and no waiting next")
    say("  session.")
    say("")


if __name__ == "__main__":
    main()
