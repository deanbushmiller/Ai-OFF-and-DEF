#!/usr/bin/env python3
"""
Lab 11 guided runner. The student types every command.

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command. On a match we run our own known-good copy of
that string. This is a security course.
"""
import argparse
import os
import re
import subprocess
import sys

WORK = "/labs/lab11"
RESULTS = os.path.join(WORK, "lab11-results.txt")
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
    say(" Send lab11-results.txt to the instructor through GitHub.")
    rule()
    sys.exit(1)


STEPS = [
    {
        "why": [
            "Start where lab 4's pipeline starts: the picture becomes text.",
            "This is the honest invoice, through the pipeline's own OCR.",
            "Count the lines. You will need the number in a moment.",
        ],
        "cmd": "python ocr.py invoices/invoice-clean.png",
        "expect_rc": 0,
        "expect_contains": "11 lines",
    },
    {
        "why": [
            "PREVENT. The content check: after the OCR, before anything acts",
            "on the text. Four patterns and a length limit, all in rules.json.",
            "Expect: pass. A control with no clean baseline is a guess.",
        ],
        "cmd": "python inspect.py invoices/invoice-clean.png",
        "expect_rc": 0,
        "expect_contains": "PASS",
    },
    {
        "why": [
            "Now the doctored invoice - the one lab 4 built. To your eye it is",
            "the same document. Same OCR. Count the lines again.",
        ],
        "cmd": "python ocr.py invoices/invoice-attack.png",
        "expect_rc": 0,
        "expect_contains": "SYSTEM NOTE",
        "impact": [
            "^ Twelve lines. The twelfth is printed at 1.2% contrast - grey",
            "  252 on white 255 - and the OCR read it as cleanly as the total.",
            "  Nobody scrolling an invoice queue would ever see it.",
        ],
    },
    {
        "why": [
            "The same content check on the doctored text.",
            "Read WHICH rules fire. Every one of them is looking at the words.",
        ],
        "cmd": "python inspect.py invoices/invoice-attack.png",
        "expect_rc": 1,
        "expect_contains": "FLAG",
        "impact": [
            "^ Caught - by rules somebody wrote before this invoice existed.",
            "  Reword the payload and they miss. OWASP says so in the same",
            "  sentence that recommends them. That is why the next step does",
            "  not read the words at all.",
        ],
    },
    {
        "why": [
            "DETECT. Two renderings of each image through the SAME OCR:",
            "the image as it is, and the image with every mark fainter than",
            "15% contrast erased - what a person sees. Any line the model",
            "reads that a person would not see is a mismatch, whatever it says.",
        ],
        "cmd": "python compare.py invoices/invoice-clean.png invoices/invoice-attack.png",
        "expect_rc": 0,
        "expect_contains": "MISMATCH - 1 line",
        "impact": [
            "^ Clean: 11 and 11, match. Doctored: 11 and 12, one line the model",
            "  read that no reviewer could have. This check never looked at",
            "  what the line said. It cannot be rephrased past.",
        ],
    },
    {
        "why": [
            "The mismatch log. Every decision so far, in order, in one file.",
            "This is the question a detector must be able to answer later:",
            "WHICH document said that, and what exactly did it say?",
        ],
        "cmd": "python log.py",
        "expect_rc": 0,
        "expect_contains": "invoice-attack.png",
    },
    {
        "why": [
            "The other half of lab 4: the DUPLICATE-stamp gate, and the stamp",
            "that was nudged 7/255 to flip it. Two things are new. A random-",
            "noise control: the same size of change, thirty random directions.",
            "And an auto-accept confidence threshold, shipped at 0.50.",
        ],
        "cmd": "python gate.py invoices/stamp-attack.png",
        "expect_rc": 0,
        "expect_contains": "ALLOWED",
        "impact": [
            "^ ORIGINAL at about 0.61, and it went to payment. The control is",
            "  the honest part: thirty random changes of the same size flipped",
            "  the gate 0 times. This is not a fragile model. It is a model",
            "  pushed along its own gradient - and 0.61 is not confidence, it",
            "  is a coin that landed. At 0.50, the gate paid it anyway.",
        ],
    },
    {
        "why": [
            "RECOVER, part one. Nothing flagged should sit in the pipeline's",
            "inbox. Route it to a person, with the evidence and the file hash.",
        ],
        "cmd": "python route.py",
        "expect_rc": 0,
        "expect_contains": "review-queue/invoice-attack.png",
        "after": "review-queue/invoice-attack.png",
        "impact": [
            "^ Out of invoices/, into review-queue/, with a record naming the",
            "  hidden line and the file's hash. A flagged document does not",
            "  get a worse score. It gets a person.",
        ],
    },
    {
        "why": [
            "RECOVER, part two. Tune with what your own log just taught you:",
            "raise the auto-accept threshold, and add the first words of the",
            "line your comparison caught to a rule list that is yours.",
        ],
        "cmd": "python tune.py",
        "expect_rc": 0,
        "expect_contains": "Same verdict. Different authority",
        "impact": [
            "^ Four patterns, one comparison, and now one rule of your own.",
            "  The verdict did not change. What changed is that one of the",
            "  reasons for it came from your incident instead of a textbook.",
        ],
    },
    {
        "why": [
            "Same stamp, same gate, same score. One number in rules.json moved.",
        ],
        "cmd": "python gate.py invoices/stamp-attack.png",
        "expect_rc": 0,
        "expect_contains": "HELD",
        "impact": [
            "^ Held. 0.61 did not change; what it is allowed to do did. And the",
            "  clean duplicate still scores 1.000 and is still blocked - the",
            "  tighter threshold cost nothing on the case that was already",
            "  right. That trade is the one you should be able to explain.",
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
    say("  You are in /labs/lab11 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Expert runs the whole command list. Beginner mode runs only the")
    say("  lines marked with a B.")
    say("")
    say("  The steps beginner never sees:")
    say("    - edit the policy by hand instead of running tune.py:")
    say("        nano rules.json")
    say("      raise auto_accept_confidence, add a phrase to your_indicators.")
    say("      Then move visible_contrast_percent - below 1.2, then past 70 -")
    say("      and re-run compare.py on BOTH invoices. Watch the hidden line")
    say("      count as visible at one end and the print itself vanish at the")
    say("      other. That is a threshold, measured, with its edges.")
    say("    - write your OWN payload and see which control catches it:")
    say("        nano payload.txt")
    say("        python craft.py")
    say("        python inspect.py invoices/invoice-attack.png")
    say("        python compare.py invoices/invoice-attack.png")
    say("      Reword it until inspect.py passes it. compare.py will not.")
    say("    - the clean stamp through the tightened gate:")
    say("        python gate.py invoices/stamp.png")
    say("    - read what you recorded:   cat mismatch-log.jsonl")
    say("                                cat review-queue/*.json")
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
    say(" LAB 11 - DEFENDING MULTIMODAL INPUT")
    rule()
    say("")
    say("  Lab 4 showed you that a pipeline reads more out of a picture than")
    say("  a person does, and acts on it. This lab is the answer: a check on")
    say("  what came out of the OCR, a comparison between what the machine")
    say("  read and what a person would see, a log of every gap, a human")
    say("  path for anything flagged, and a threshold you tighten yourself.")
    say("")
    say("  Defends  lab 4 - multimodal and vision-based exploits")
    say("  OWASP    LLM01:2026 Prompt Injection - risk 4, Scenario 6;")
    say("           prevention 3 (filter at the modality boundary) built,")
    say("           prevention 7 (human confirmation) built")
    say("           LLM02:2026 risk 4 - cross-modal transformation bypasses")
    say("           single-modality DLP")
    say("  ATLAS    defends AML.T0068 > AML.T0051.001")
    say("                   AML.T0043 > AML.T0015")
    say("           with  AML.M0020  Generative AI Guardrails")
    say("                 AML.M0033  Input and Output Validation")
    say("                 AML.M0024  AI Telemetry Logging")
    say("                 AML.M0015  Adversarial Input Detection")
    say("")
    say("  No language model runs in this lab. Every result is arithmetic on")
    say("  pixels and text, and it is the same on every machine, every time.")
    say("  Nothing leaves this container.")


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
    say("  Ten commands. Read each one before you run it.")
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
    say("   the OCR text      11 lines clean, 12 doctored, the twelfth at")
    say("                     1.2% contrast")
    say("   the mismatch log  the comparison naming the line a person would")
    say("                     not see, without reading a word of it")
    say("   the gate          ORIGINAL at about 0.61, noise control 0 of 30,")
    say("                     ALLOWED at 0.50")
    say("   the held item     the same score, HELD at 0.90, and the clean")
    say("                     duplicate still blocked at 1.000")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")

    rule()
    say(" HOW THIS DIFFERS FROM A REAL DEFENCE")
    rule()
    say("")
    say("   THIS LAB                      PRODUCTION")
    say("   four patterns in a file       content inspection on every field,")
    say("                                 every document, at scale")
    say("   two renderings of one image   rendering at the resolution AND the")
    say("                                 preprocessing the model actually sees")
    say("   a JSONL file                  an audit trail with retention and")
    say("                                 alerting")
    say("   a folder called review-queue  a ticketed workflow with an owner")
    say("                                 and a deadline")
    say("   one threshold, edited by hand per-field confidence, calibrated on")
    say("                                 your own documents")
    say("   two images                    thousands a day")
    say("")

    rule()
    say(" THE PART YOU SHOULD NOT MISS")
    rule()
    say("")
    say("  The OCR was never unsure. Look at the doctored invoice's text")
    say("  again: the hidden line came out as cleanly as the total, and if")
    say("  you asked the OCR engine how confident it was, it would say 90%.")
    say("  A pipeline that holds anything the OCR is unsure about holds")
    say("  nothing here. There is nothing wrong with the text. The only")
    say("  thing wrong with it is that a person cannot see it.")
    say("")
    say("  That is why the comparison, not a confidence floor, is the control")
    say("  on the OCR side - and why the confidence threshold belongs on the")
    say("  classifier side, where 0.61 really is a coin landing.")
    say("")
    say("  Note also what this lab did NOT fix. The comparison ran on the")
    say("  file you were sent. A real pipeline resizes the image before the")
    say("  model sees it, and an attacker who knows that can hide text that")
    say("  only appears AFTER the resize. Compare at the resolution the")
    say("  model sees, not the one you received.")
    say("")

    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste TWO things into the class chat:")
    say("    1. the MISMATCH block from step 5 - the line the model read")
    say("       that a person would not see")
    say("    2. the HELD block from step 10 - the same 0.61 that was paid")
    say("       at step 7, held at step 10")
    say("")
    say("  Full transcript saved to lab11-results.txt on your machine, and")
    say("  the invoices and review-queue folders are copied out next to it.")
    say("  Open invoice-clean.png and review-queue/invoice-attack.png side")
    say("  by side. That is worth two minutes of your own eyes.")
    say("")
    rule()
    say(" BEFORE YOU CLOSE THIS")
    rule()
    say("")
    say("  When this window exits, the setup script offers to download the")
    say("  next lab. Say yes - doing it now, while you are online, means no")
    say("  waiting next session.")
    say("")


if __name__ == "__main__":
    main()
