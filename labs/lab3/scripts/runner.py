#!/usr/bin/env python3
"""
Lab 3 runner. Asks the student to choose beginner or expert mode.

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

WORK = "/labs/lab3"
RESULTS = os.path.join(WORK, "lab3-results.txt")
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
    say(" Send lab3-results.txt to the instructor through GitHub.")
    rule()
    sys.exit(1)


Q1 = 'x'
Q2 = 'x'

STEPS = [
    {"why": ["This is a mock corporate news site, served inside this container",
             "on 127.0.0.1 only. Nothing leaves your machine.",
             "Two pages. They look identical in a browser."],
     "cmd": "ls site/", "rc": 0},
    {"why": ["Fetch the clean page the way the assistant will - as raw text.",
             "An ordinary business article about quarterly results."],
     "cmd": "curl -s http://news.acme.com:8003/article.html | head -20", "rc": 0},
    {"why": ["Now ask the assistant to summarise it. This is the baseline:",
             "the task working correctly.",
             "The model runs locally. First answer takes a few seconds."],
     "cmd": "python assistant.py http://news.acme.com:8003/article.html",
     "rc": 0, "after": "runs.json"},
    {"why": ["Read the attack before you run it. Look for the hidden block -",
             "a display:none div and an HTML comment. A browser paints",
             "neither. Note it pretends to be a system instruction."],
     "cmd": "tail -25 site/article-poisoned.html", "rc": 0, "want": "PWNED"},
    {"why": ["See the gap directly: what a reader sees, then what the",
             "assistant reads."],
     "cmd": "python show_injection.py http://news.acme.com:8003/article-poisoned.html",
     "rc": 0, "want": "HIDDEN FROM THE READER"},
    {"why": ["Same assistant. Same command. Same model. Same question.",
             "The only thing that changed is which page it read."],
     "cmd": "python assistant.py http://news.acme.com:8003/article-poisoned.html",
     "rc": 0, "want": "PWNED"},
    {"why": ["Both runs side by side. This is what you submit."],
     "cmd": "python evidence.py", "rc": 0},
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
    say(" LAB 3 - ADVANCED PROMPT INJECTION")
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
    say("  You are in /labs/lab3 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every command is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - cd into site/ and look at both pages yourself")
    say("    - edit the injected block in article-poisoned.html with nano,")
    say("      write your OWN instruction, and watch the assistant obey it")
    say("")
    say("  The mock site is already running on 127.0.0.1:8003.")
    say("  If you started the container with -p 127.0.0.1:8003:8003 you can")
    say("  also open http://localhost:8003/article-poisoned.html in your own")
    say("  browser - it looks like an ordinary news article.")
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
    say(" LAB 3 - ADVANCED PROMPT INJECTION  (beginner)")
    rule()
    say("")
    say("  The question this lab answers:")
    say("    Your assistant reads a web page you did not write.")
    say("    Whose instructions is it following?")
    say("")
    say("  OWASP  LLM01:2026 Prompt Injection - risk item 2, quoted:")
    say("           'attacker instructions ride in a RAG passage, WEB PAGE,")
    say("            document, or email and run when the content enters")
    say("            the context'")
    say("  ATLAS  AML.T0066 > AML.T0068 > AML.T0051.001 / .002")
    say("")
    say("  Seven commands. The mock site is served on 127.0.0.1 inside this")
    say("  container - nothing leaves your machine. The payload is a string,")
    say("  not code.")

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
            say("  ^ Correct, and boring. That is the task working. Remember it.")
        if i == 6:
            say("  ^ It abandoned the summary entirely.")
            say("    Nothing about the model changed. Nothing about the code")
            say("    changed. One kilobyte of hidden text in a page it read.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM A REAL ATTACK")
    rule()
    say("")
    say("   THIS LAB                      A REAL ATTACK")
    say("   the payload says PWNED-LAB3   exfiltrates data, or sends")
    say("                                   the user to a phishing page")
    say("   one page, clearly labelled    a page on a site the target")
    say("     poisoned                      already trusts")
    say("   you point the assistant       the assistant finds it via")
    say("     at it                         search or a link")
    say("   the model only speaks         it calls a tool, sends mail,")
    say("                                   moves money")
    say("   hidden with display:none      zero-width characters,")
    say("                                   homoglyphs, alt text, metadata")
    say("")
    rule()
    say(" THE DEFENCE")
    rule()
    say("")
    say("   1. Mark retrieved content as DATA, not instructions. Wrap it,")
    say("      label it, tell the model where the boundary is. It cannot")
    say("      respect a boundary you never drew.")
    say("   2. Constrain the role in the system prompt. A tight \"you")
    say("      summarise, nothing else\" is measurably harder to hijack")
    say("      than \"help the user with this page\". We tested that.")
    say("   3. Validate the output against a schema before anything")
    say("      downstream uses it. A summary that is not a summary should")
    say("      fail a check.")
    say("   4. Strip what a human cannot see at fetch time - display:none,")
    say("      comments, zero-width characters. If the reader cannot see")
    say("      it, the model should not read it.")
    say("   5. Give the assistant no capability it does not need. This one")
    say("      can only talk. That is why the worst case here is an")
    say("      embarrassing sentence.")
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
    say("  Full transcript saved to lab3-results.txt on your machine.")
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
