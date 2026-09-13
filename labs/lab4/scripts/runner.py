#!/usr/bin/env python3
"""
Lab 4 runner. Asks the student to choose beginner or expert mode.

Beginner: the guided path - shows each command, checks what the student types,
          corrects a miss, runs the real command on a match.
Expert:   drops to a real shell in the lab folder. The student works from
          LAB.md, including the steps beginner skips (cd, editing payload.txt
          with nano, crafting their own attack image).

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command; on a match we run our own known-good copy.
"""
import argparse
import json
import os
import re
import subprocess
import sys

WORK = "/labs/lab4"
RESULTS = os.path.join(WORK, "lab4-results.txt")
RUNS = os.path.join(WORK, "runs.json")
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
    say(" Send lab4-results.txt to the instructor through GitHub.")
    rule()
    sys.exit(1)


def recorded_verdict(key):
    """Read the decision the pipeline recorded, rather than pattern-matching
    the screen. The model answers in markdown, so 'APPROVE' in the raw output
    would also match '**APPROVE**' - and 'do not approve' would match nothing
    useful at all."""
    if not os.path.exists(RUNS):
        return None
    try:
        return json.loads(open(RUNS).read()).get(key, {}).get("verdict")
    except (ValueError, OSError):
        return None


STEPS = [
    {"why": ["One invoice, one stamp, and two files called perturbations.",
             "There are no attack images yet. You are going to make them."],
     "cmd": "ls invoices/", "rc": 0, "want": "perturbation.npz"},

    {"why": ["Stage 1 of the pipeline. Accounts payable blocks any scan stamped",
             "DUPLICATE, because paying the same invoice twice is one of the",
             "oldest frauds there is. A classifier reads the stamp."],
     "cmd": "python gate.py invoices/stamp.png", "rc": 0, "want": "BLOCKED"},

    {"why": ["Now craft an adversarial version of that stamp. Watch the control",
             "underneath: the same amount of change in random directions."],
     "cmd": "python apply_perturbation.py --stamp",
     "rc": 0, "after": "invoices/stamp-attack.png",
     "want": "the gate 0 times out of"},

    {"why": ["Same gate, same weights, same stamp to your eye."],
     "cmd": "python gate.py invoices/stamp-attack.png", "rc": 0, "want": "ALLOWED"},

    {"why": ["Stage 2. Past the gate, the page goes to OCR and then to a model",
             "that decides. Start with the honest invoice - the baseline.",
             "The model runs locally on your CPU. Allow up to a minute."],
     "cmd": "python pipeline.py invoices/invoice-clean.png",
     "rc": 0, "verdict": ("invoice-clean.png", "HOLD")},

    {"why": ["Now add the perturbation to that same clean invoice.",
             "Watch how little of the image it touches."],
     "cmd": "python apply_perturbation.py",
     "rc": 0, "after": "invoices/invoice-attack.png", "want": "pixels touched"},

    {"why": ["Same pipeline. Same model. Same policy. Same $8,750.00 on the",
             "paper. The only difference is the quarter of one percent of",
             "the pixels you just changed."],
     "cmd": "python pipeline.py invoices/invoice-attack.png",
     "rc": 0, "verdict": ("invoice-attack.png", "APPROVE")},

    {"why": ["Why did that happen? Look at what the OCR handed the model,",
             "and at what one binarisation setting does to the same image."],
     "cmd": "python show_extraction.py invoices/invoice-attack.png",
     "rc": 0, "want": "not printed on the invoice"},

    {"why": ["The defence. Same attack image, but the spend limit is now a",
             "numeric check in application code instead of a sentence in the",
             "prompt. The model is never asked, so there is nothing to inject."],
     "cmd": "python pipeline.py invoices/invoice-attack.png --strict",
     "rc": 0, "verdict": ("invoice-attack.png::strict", "HOLD")},

    {"why": ["All three decisions side by side. This is what you submit."],
     "cmd": "python evidence.py", "rc": 0, "want": "The decision reversed"},
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
    say(" LAB 4 - MULTIMODAL AND VISION-BASED EXPLOITS")
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
    say("  You are in /labs/lab4 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every command is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - cd into invoices/ and look at what is and is not shipped")
    say("    - nano payload.txt to write your OWN hidden instruction, then")
    say("      python craft.py to render it into a new attack image")
    say("    - run the pipeline against your own image and see whether the")
    say("      model obeys you as readily as it obeyed the shipped payload")
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

    if os.path.exists(RUNS):
        os.remove(RUNS)

    rule()
    say(" LAB 4 - MULTIMODAL AND VISION-BASED EXPLOITS  (beginner)")
    rule()
    say("")
    say("  The question this lab answers:")
    say("    Your pipeline turns a picture into text before the model")
    say("    reads it. Who wrote the text?")
    say("")
    say("  OWASP  LLM01:2026 Prompt Injection - risk item 4, quoted:")
    say("           'Multimodal and steganographic injection: sub-perceptual")
    say("            perturbations in images, audio, or video are extracted")
    say("            by the encoder'")
    say("  ATLAS  stage 1  AML.T0043.000 White-Box Optimization")
    say("                    > AML.T0015 Evade AI Model")
    say("         stage 2  AML.T0065 > AML.T0043.003 > AML.T0068")
    say("                    > AML.T0051.001")
    say("")
    say("  Ten commands, two attacks on the same document. Everything runs")
    say("  inside this container with no")
    say("  network. The payload is a line of text, not code. No money moves.")

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
        if step.get("verdict"):
            key, expected = step["verdict"]
            got = recorded_verdict(key)
            if got != expected:
                fail(f"Step {i} should have decided {expected} on {key}, "
                     f"but the pipeline recorded {got!r}.")

        if i == 2:
            say("  ^ The control works. A duplicate is stopped before it can cost")
            say("    anyone money.")
        if i == 4:
            say("  ^ The gate now waves through the same duplicate. You can see")
            say("    the grain if you look, and that is the honest part: this")
            say("    change is not invisible. What makes it an attack is that it")
            say("    points along the model's own gradient. Random grain of the")
            say("    same size never moved it.")
        if i == 5:
            say("  ^ Correct, and boring. $8,750.00 is over the limit, so a human")
            say("    has to look at it. That is the task working. Remember it.")
        if i == 6:
            say("  ^ Two thousand pixels, none of them changed by more than 3 in")
            say("    255. This one you genuinely cannot see.")
        if i == 7:
            say("  ^ Approved. Nothing about the model changed. Nothing about the")
            say("    code changed. The invoice still says $8,750.00 to a human.")
        if i == 9:
            say("  ^ Held. The hidden line is still in the image and still in the")
            say("    extracted text - it just has nothing left to talk to.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM A REAL ATTACK")
    rule()
    say("")
    say("   THIS LAB                      A REAL ATTACK")
    say("   an invoice we wrote           a document the target already expects")
    say("   one canned perturbation       tuned against that shop's own pipeline")
    say("   the decision is printed       the payment is scheduled")
    say("   payload in plain English      tuned wording, tried until one lands")
    say("   you apply it yourself         it arrives by email from a real vendor")
    say("")
    rule()
    say(" THE DEFENCE")
    rule()
    say("")
    say("   1. Filter at the modality boundary, not just on text. OWASP's")
    say("      prevention #3 says to OCR the image AND THEN apply text filters")
    say("      to what comes out. Doing the OCR is not the control.")
    say("   2. Compare what the machine read against what a person would see.")
    say("      Two binarisations, one image: if they disagree, that is a signal,")
    say("      and it is cheap to compute.")
    say("   3. Keep money rules in application code. You watched a numeric limit")
    say("      hold against a payload that talked the model straight past a")
    say("      policy written in the prompt.")
    say("   4. Mark extracted content as data, never as instructions. The OCR")
    say("      output went into the prompt with no label saying where it came")
    say("      from - the model had no way to tell paper from instruction.")
    say("   5. Require a human for anything irreversible. The worst case here is")
    say("      a wrong word on screen because nothing downstream acts on it.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")
    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste the output of the last command into the class chat - all")
    say("  three decisions. The APPROVE alone proves nothing without the")
    say("  HOLD above it.")
    say("")
    say("  Full transcript saved to lab4-results.txt on your machine, and both")
    say("  invoices are copied out next to it. Open them side by side: that is")
    say("  the part of this lab that is worth two minutes of your own eyes.")
    say("")
    rule()
    say(" BEFORE YOU CLOSE THIS")
    rule()
    say("")
    say("  When this window exits, the setup script offers to download the")
    say("  next lab. Say yes: downloading it now, while you are online and")
    say("  the terminal is open, beats waiting for it at the start of the")
    say("  next session.")
    say("")


if __name__ == "__main__":
    main()
