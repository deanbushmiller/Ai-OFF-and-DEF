#!/usr/bin/env python3
"""
Lab 12 runner. Asks the student to choose beginner or expert mode.

Beginner: shows each command, checks what the student types, corrects a miss,
          runs the real command on a match.
Expert:   drops to a real shell in the lab folder, working from LAB.md.

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command; on a match we run our own known-good copy.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

WORK = "/labs/lab12"
RESULTS = os.path.join(WORK, "lab12-results.txt")
RULES = os.path.join(WORK, "rules.json")
RULES_PRISTINE = os.path.join(WORK, "rules.default.json")
LOGFILE = os.path.join(WORK, "firewall-log.jsonl")
WIDTH = 68
BASE = "http://news.acme.com:8012"

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
    say(" Send lab12-results.txt to the instructor via email or post to class Q&A.")
    rule()
    sys.exit(1)


def reset_state():
    """Start every run from the shipped threshold and an empty log.

    Without this, a student who re-runs the lab starts at block_at HIGH with the
    previous run's leak already in the log, and step 4 quietly blocks instead of
    leaking - which would make the lab teach nothing on its second run.
    """
    if os.path.exists(RULES_PRISTINE):
        shutil.copyfile(RULES_PRISTINE, RULES)
    if os.path.exists(LOGFILE):
        os.remove(LOGFILE)


STEPS = [
    {"why": ["This is Acme's internal news page, served inside this container",
             "on 127.0.0.1 only. Start with the firewall's own rule file -",
             "four detector families, and one threshold."],
     "cmd": "cat rules.json", "rc": 0, "want": "block_at"},

    {"why": ["A clean page, through the firewall. Nothing matches, so the",
             "request reaches the model and the answer comes back.",
             "This is the baseline: the control not interfering."],
     "cmd": f"python firewall.py {BASE}/article.html",
     "rc": 0, "want": "no detector family matched", "after": "firewall-log.jsonl"},

    {"why": ["Every request is logged in both directions, whatever the",
             "verdict. A firewall that only records what it blocked cannot",
             "tell you what it missed."],
     "cmd": "python log.py", "rc": 0, "want": "FIREWALL REQUEST LOG"},

    {"why": ["Now the injected page from lab 3. A hidden div, an order to",
             "ignore the article, and a demand to reply with a fixed string.",
             "Three separate families fire, plus the concealment check."],
     "cmd": f"python firewall.py {BASE}/article-poisoned.html",
     "rc": 0, "want": "VERDICT: BLOCK"},

    {"why": ["A different page. Same kind of attack, quieter: no 'ignore',",
             "no fake system header. Just a format demand, hidden in a div.",
             "Watch the severity, and watch what the firewall does about it."],
     "cmd": f"python firewall.py {BASE}/memo-leak.html",
     "rc": 0, "want": "OUTBOUND"},

    {"why": ["Read the log again. One of these requests matched a rule and",
             "was allowed through anyway. Find it."],
     "cmd": "python log.py", "rc": 0, "want": "A RULE MATCHED"},

    {"why": ["Close the gap. One field, from CRITICAL to HIGH.",
             "Nothing else about the firewall changes."],
     "cmd": "python tune.py", "rc": 0, "want": "RULE CHANGE"},

    {"why": ["The same page, the same command, the same model. The only",
             "thing that changed is the rule file."],
     "cmd": f"python firewall.py {BASE}/memo-leak.html",
     "rc": 0, "want": "VERDICT: BLOCK"},

    {"why": ["The half people skip. A tighter rule that breaks real traffic",
             "is not a fix - it is the reason the next person sets the",
             "threshold too loose. Re-check the clean page."],
     "cmd": f"python firewall.py {BASE}/article.html",
     "rc": 0, "want": "VERDICT: ALLOW"},

    {"why": ["The whole story in one table. This is what you submit."],
     "cmd": "python evidence.py", "rc": 0, "want": "LAB 12 EVIDENCE"},
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
    say(" LAB 12 - DEFENDING AGAINST PROMPT INJECTION")
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
    say("  You are in /labs/lab12 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every command is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - edit rules.json with nano instead of running tune.py, and")
    say("      decide for yourself what to change")
    say("    - fetch site/memo-smuggled.html, where the payload is hidden with")
    say("      invisible Unicode instead of CSS")
    say("    - write your own payload into a page and watch a phrase rule miss")
    say("      a rephrasing it was never written for")
    say("")
    say("  The mock site is already running on 127.0.0.1:8012 inside this")
    say("  container. It is not published to your machine; read it with curl.")
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

    reset_state()

    if args.expert or choose_mode(args.auto) == "2":
        expert_shell()
        return

    rule()
    say(" LAB 12 - DEFENDING AGAINST PROMPT INJECTION  (beginner)")
    rule()
    say("")
    say("  Lab 3 showed you that a page can hijack an assistant.")
    say("  This lab is the control you put around it, and the question")
    say("  it answers is not 'does the firewall work'. It is:")
    say("")
    say("    when the firewall sees the attack and lets it through anyway,")
    say("    how do you find out?")
    say("")
    say("  OWASP  LLM01:2026 Prompt Injection - Scenario #2, quoted:")
    say("           'A user asks an assistant to summarize a web page")
    say("            containing hidden instructions.'")
    say("         LLM02:2026 Sensitive Information Disclosure - the way out")
    say("  ATLAS  AML.T0068 > AML.T0051.001 > AML.T0057, countered with")
    say("           AML.M0020 / M0033 (scan), M0024 (log), M0035 (tune)")
    say("")
    say("  Ten commands. Everything is local: the site, the model and the")
    say("  log. The container runs with no network at all.")
    say("")
    say("  The 'support key' in this lab is fake and exists only in this")
    say("  container. It is a canary. It is never sent anywhere.")

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

        # Content assertions beyond `want`, where the teaching point IS the value.
        if i == 5:
            if "severity HIGH" not in out:
                fail("Step 5 should have rated memo-leak.html HIGH. "
                     "The detector families have drifted.")
            if "VERDICT: BLOCK. The response is suppressed" not in out:
                fail("Step 5 should have been stopped by the OUTBOUND scan. "
                     "The model did not leak the marker, so the lab has no leak "
                     "to teach from.")
            say("  ^ Read that twice. The inbound firewall ALLOWED it - two")
            say("    families is HIGH, and the gate only blocks CRITICAL.")
            say("    The model then did what the page told it to.")
            say("    The OUTBOUND scan is the only reason you did not just")
            say("    read a secret off your own screen.")
        if i == 6:
            say("  ^ detected=true, filtered=false. The firewall was not blind.")
            say("    It saw it, scored it, wrote it down, and did nothing.")
            say("    The reason is one field in rules.json, which you read in")
            say("    step 1: the gate blocks at CRITICAL, which needs three")
            say("    families. The page that got through scored two.")
            say("    That is CVE-2026-60086, and it shipped in a real product.")
        if i == 8:
            say("  ^ Same page, same model, same command. The model was never")
            say("    called this time - the request died at the gate.")
        if i == 9:
            say("  ^ And the clean page still passes. The fix cost nothing on")
            say("    legitimate traffic, which is the argument you will need")
            say("    when someone asks you to loosen it again.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM A REAL DEFENCE")
    rule()
    say("")
    say("   THIS LAB                      PRODUCTION")
    say("   four regex families in one    a maintained classifier, inline,")
    say("     JSON file                     retrained against live attacks")
    say("   severity = how many           scoring calibrated per surface")
    say("     families matched              and per tenant")
    say("   one regex for one known       classifiers plus NER - OWASP:")
    say("     marker                        'regex fails on encoded and")
    say("                                   cross-lingual output'")
    say("   one log file                  a pipeline with retention,")
    say("                                   alerting and a SIEM")
    say("   one hand edit                 a rule-change process with an")
    say("                                   owner and a time to close")
    say("   three requests                thousands a second, and the")
    say("                                   latency budget is real")
    say("")
    say("   The shape is real. The scale is not.")
    say("")
    rule()
    say(" WHAT TO TAKE AWAY")
    rule()
    say("")
    say("   1. The firewall's job is not only to block. It is to write down")
    say("      what it saw, including what it decided to allow. Without")
    say("      that line in the log, this lab has no step 6 and no fix.")
    say("   2. A threshold is a decision, and decisions rot. CVE-2026-60086")
    say("      is not a clever bypass - it is a number nobody revisited.")
    say("   3. Two sides, not one. The inbound scan missed it; the outbound")
    say("      scan caught it. Either alone would have been a bad day.")
    say("   4. Test the fix against the attack AND against normal traffic.")
    say("      Half a test is how thresholds end up loose.")
    say("   5. The production answer to the prevent half is bought, not")
    say("      built - Azure AI Content Safety Prompt Shields scans the")
    say("      prompt and up to five documents in one call. It costs money,")
    say("      adds 100-300 ms, and sends your content off-site to be read.")
    say("      It is still yours to run, monitor and tune. There is no THEY.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")
    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste the output of the last command into the class chat - the")
    say("  whole table. The line that matters is the one where detected is")
    say("  true and filtered is false.")
    say("")
    say("  Full transcript saved to lab12-results.txt on your machine.")
    say("")
    rule()
    say(" BEFORE YOU CLOSE THIS")
    rule()
    say("")
    say("  When this window exits, the setup script offers to download the")
    say("  next lab. Say yes - lab 13 is the same dependency tier as this")
    say("  one, so it shares the big model layer and the download is small.")
    say("")


if __name__ == "__main__":
    main()
