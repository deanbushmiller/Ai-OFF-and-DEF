#!/usr/bin/env python3
"""
Lab 7 runner. Asks the student to choose beginner or expert mode.

Beginner: the guided path - shows each command, checks what the student types,
          corrects a miss, runs the real command on a match.
Expert:   drops to a real shell in the lab folder. The student works from
          LAB.md, including the steps beginner skips (running the collector as
          its own process, editing schedule.txt with nano, and trying formats
          that were measured to fail).

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command; on a match we run our own known-good copy.
"""
import argparse
import json
import os
import re
import subprocess
import sys

WORK = "/labs/lab7"
RESULTS = os.path.join(WORK, "lab7-results.txt")
STATE = os.path.join(WORK, "results.json")
VARIANTS = os.path.join(WORK, "variants.json")
LOG = os.path.join(WORK, "collector.log")
SCHEDULE = os.path.join(WORK, "schedule.txt")
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
    say(" Send lab7-results.txt to the instructor via email or post to class Q&A.")
    rule()
    sys.exit(1)


def recorded(key, field):
    """Assert on what the detectors recorded, not on what scrolled past."""
    if not os.path.exists(STATE):
        return None
    try:
        return json.loads(open(STATE).read()).get(key, {}).get(field)
    except (ValueError, OSError):
        return None


def model_variants_complete():
    """Every model variant kept every field. This is the assertion that would
    have caught ini and syslog, both of which look fine and drop data."""
    try:
        store = json.loads(open(VARIANTS).read())
    except (ValueError, OSError):
        return None
    model = [v for v in store.values() if v["source"] == "model"]
    if not model:
        return None
    return all(not v["missing"] for v in model)


STEPS = [
    {"why": ["Ask the model to re-encode the check-in record into five ordinary",
             "data formats. You will see the exact prompt before it is sent.",
             "Five generations on your CPU - about a minute, longer on 2 cores."],
     "cmd": "python variants.py --formats json,csv,kv,xml,urlq", "rc": 0,
     "want": "LAB-BEACON-7742"},

    {"why": ["Two more renderings, and the model has nothing to do with these.",
             "base64 and hex, from two lines of Python. Instant."],
     "cmd": "python variants.py --encode base64,hex", "rc": 0,
     "want": "base64"},

    {"why": ["Send all of them to the collector on 127.0.0.1:8007 inside this",
             "container. Nothing leaves your machine and no port is published.",
             "From here on, the detectors only see the collector's log."],
     "cmd": "python beacon.py --all", "rc": 0, "want": "collector.log"},

    {"why": ["The rule most environments actually have: one string, one match.",
             "Which of your variants get past it?"],
     "cmd": "python detect.py --signature", "rc": 0, "want": "D1 caught",
     "asserts": [("signature", "total", 8), ("signature", "caught", 6),
                 ("signature", "missed", ["base64", "hex"])]},

    {"why": ["Now a detector that does not care what format anything is in. It",
             "decodes, splits, and counts how many of the record's values are",
             "still there. Twenty lines."],
     "cmd": "python detect.py --structural", "rc": 0, "want": "D2 caught",
     "asserts": [("structural", "caught", 8), ("structural", "missed", [])]},

    {"why": ["A third detector, and this one never reads your payload at all.",
             "It reads the two numbers in schedule.txt: how often you check in",
             "and how much you randomise it."],
     "cmd": "python detect.py --behaviour", "rc": 0, "want": "FLAGGED",
     # BOTH limbs, not just the verdict. Sabotaging the volume limb left the
     # verdict correct (regularity still trips at zero jitter) while the lab's
     # closing claim - that volume is what costs - had quietly become false.
     "asserts": [("behaviour", "flagged", True),
                 ("behaviour", "volume_tripped", True),
                 ("behaviour", "regularity_tripped", True),
                 ("behaviour", "events", 1440),
                 ("behaviour", "records_per_hour", 60.0)]},

    {"why": ["Your turn. Slow the beacon down and randomise it hard, and see",
             "whether you can get under both limbs. Watch the throughput line",
             "as well as the verdict - it is the part that matters."],
     "cmd": "python detect.py --behaviour --interval 7200 --jitter 0.95",
     # The schedule seed is fixed, so 0.75 records/h is exact, not approximate.
     # This is the number the whole lab closes on: assert it.
     "rc": 0, "want": "CLEAN",
     "asserts": [("behaviour", "flagged", False),
                 ("behaviour", "volume_tripped", False),
                 ("behaviour", "regularity_tripped", False),
                 ("behaviour", "records_per_hour", 0.75)]},

    {"why": ["The evidence. What you spent, what you got, and what it cost."],
     "cmd": "python evidence.py", "rc": 0, "want": "AML.T0015"},
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
    say(" LAB 7 - AI-POWERED ATTACK ORCHESTRATION")
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
    say("  You are in /labs/lab7 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every command is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - run the collector as its own process and watch it, instead of")
    say("      letting beacon.py start and stop it for you:")
    say("        python collector.py &")
    say("        curl -s -X POST --data-binary @record.txt \\")
    say("             -H 'X-Lab-Variant: byhand' http://127.0.0.1:8007/checkin")
    say("        cat collector.log")
    say("      Doing it by hand is how you see that the detector's whole view of")
    say("      this incident is one append-only log file.")
    say("    - nano schedule.txt and choose your own interval and jitter, then")
    say("        python detect.py --behaviour")
    say("      Find the FASTEST setting that still comes out clean. The guided")
    say("      path hands you 7200s / 95%, which is not the optimum.")
    say("    - try a format that was measured to FAIL:")
    say("        python variants.py --formats ini")
    say("      It is refused with the measurement, because ini returns bare")
    say("      [section] headers and drops every value - confidently, and")
    say("      identically on three runs. Read the top of variants.py for the")
    say("      full table, including why base64 comes from Python.")
    say("    - read detect.py. It is the only defensive code in the lab and D2")
    say("      is twenty lines.")
    say("")
    say("  When you are done, run this to check your work:")
    say("      python check.py")
    say("")
    say("  Type 'exit' to leave the container.")
    say("")
    _log.close()
    os.chdir(WORK)
    os.execvp("/bin/bash", ["/bin/bash"])


def reset_state():
    """A re-run starts clean, or stale files could satisfy an assertion this
    run never earned. schedule.txt is rewritten because step 7 edits it."""
    for f in (STATE, VARIANTS, LOG):
        if os.path.exists(f):
            os.remove(f)
    try:
        text = open(SCHEDULE).read()
        text = re.sub(r"^interval=.*$", "interval=60", text, flags=re.M)
        text = re.sub(r"^jitter=.*$", "jitter=0.0", text, flags=re.M)
        open(SCHEDULE, "w").write(text)
    except OSError:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--challenge", action="store_true")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--expert", action="store_true")
    args = ap.parse_args()

    if args.expert or choose_mode(args.auto) == "2":
        expert_shell()
        return

    reset_state()

    rule()
    say(" LAB 7 - AI-POWERED ATTACK ORCHESTRATION  (beginner)")
    rule()
    say("")
    say("  The question this lab answers:")
    say("    An LLM can rewrite your beacon a hundred ways in a minute.")
    say("    What does that actually buy you?")
    say("")
    say("  In labs 3 to 6 the model was the victim. Here it is YOUR tool, and")
    say("  you are the attacker. You have one record to move off a workstation")
    say("  and three detectors in the way.")
    say("")
    say("  ATLAS leads the mapping for this lab, and that is deliberate:")
    say("    AML.T0016.002  Obtain Capabilities: Generative AI")
    say("                   'obtain generative AI models or tools, such as")
    say("                    large language models, to assist them in various")
    say("                    steps of their operation ... serve them locally")
    say("                    using frameworks such as Ollama or vLLM'")
    say("    AML.T0043.003  Craft Adversarial Data: Manual Modification")
    say("    AML.T0015      Evade AI Model  <- the core technique")
    say("")
    say("    Two real case studies, not hypotheticals:")
    say("    AML.CS0000     Palo Alto evaded a deep-learning detector for")
    say("                   malware C2 traffic by varying header fields. The")
    say("                   crafted packets were called benign, >80% confidence.")
    say("    AML.CS0044     LAMEHUG (APT28, 2025) called a Qwen 2.5 model to")
    say("                   generate its commands. You are about to use the")
    say("                   same model family, three sizes down.")
    say("")
    say("  OWASP comes second here, and the reason is worth one sentence:")
    say("  the Top 10 for LLM Applications describes risks in software you")
    say("  BUILD. An attacker using an LLM to help them work is a fact about")
    say("  the threat landscape, not a vulnerability in your application - so")
    say("  this is the one lab in the course whose topic sits outside it.")
    say("    LLM10:2026 Improper Output Handling, Scenario #2 - 'the LLM can")
    say("      encode the sensitive data and send it, without any output")
    say("      validation or filtering, to an attacker-controlled server'")
    say("    LLM02:2026 via OWASP's own ATLAS cross-map - 'Base64 and hex")
    say("      encodings defeat regex and blocklist data-loss filters'")
    say("")
    say("  Eight commands, one of which runs a model on your CPU. The record is")
    say("  one line of text with a lab marker in it, the collector is a Python")
    say("  http.server on 127.0.0.1 inside this container, and the container has")
    say("  no network. Nothing executes, nothing persists, nothing connects out.")

    total = len(STEPS)
    typed = 0
    for i, step in enumerate(STEPS, 1):
        how = ask_step(step, i, total, args.challenge, args.auto)
        if how == "typed":
            typed += 1
        rc, out = run(step["cmd"])

        if step.get("rc") is not None and rc != step["rc"]:
            fail(f"Step {i} ({step['cmd']}) returned {rc}, expected {step['rc']}.")
        want = step.get("want")
        if want and want not in out:
            fail(f"Step {i} output should have contained {want!r}. "
                 f"The lab did not behave as designed.")
        for key, field, expected in step.get("asserts", ()):
            got = recorded(key, field)
            if got != expected:
                fail(f"Step {i}: results.json[{key!r}][{field!r}] is {got!r}, "
                     f"expected {expected!r}. The attack or the detector did not "
                     f"behave as measured during the build.")

        if i == 1:
            complete = model_variants_complete()
            if complete is None:
                fail("Step 1 wrote no model variants to variants.json.")
            if not complete:
                fail("A model variant lost one of the record's field values. "
                     "Every format in the list was measured at 6/6 fields on "
                     "three runs, so this is a real change in behaviour.")
            say("  ^ Five renderings of the same record, every field intact, in")
            say("    about a minute. That is the part the marketing is about, and")
            say("    it is real - the model is genuinely good at this.")
            say("  ^ Now read the prompt again. It asked for a format change and")
            say("    nothing else. No jailbreak, no roleplay, nothing a safety")
            say("    filter would refuse and nothing a prompt scanner would flag.")
            say("    The offence is not in the prompt. It is in what you do next.")
            say("  ^ Look closely at the CSV. You asked for a header row and one")
            say("    data row and got six key,value lines. It did not do what it")
            say("    was told, and it did it identically every time. Hold on to")
            say("    that - it comes back in step 2.")
        if i == 2:
            say("  ^ Two lines of standard library, no model, correct every time.")
            say("  ^ The model cannot do this. Measured on this exact model at")
            say("    temperature 0: asked for base64 it loops for 49 seconds and")
            say("    produces garbage, and with a stricter prompt it answers")
            say("    'SGVsbG8gd29ybGQ=' - which is base64 for 'Hello world'. It")
            say("    returned a memorised string instead of encoding your input.")
            say("    Hex fails the same way. A model is a paraphraser, not a")
            say("    computer: it cannot do an exact transform on data it has not")
            say("    seen. Encoding, checksums, crypto and packing are all exact")
            say("    transforms.")
            say("  ^ This is why LAMEHUG used a Qwen model for command TEXT and")
            say("    ordinary code for everything that had to be right. Real")
            say("    operators already know where the tool stops.")
        if i == 3:
            say("  ^ From here on the detectors read collector.log and nothing")
            say("    else. They never see variants.json. That asymmetry is real:")
            say("    a defender does not get the attacker's working files, only")
            say("    what arrived.")
        if i == 4:
            missed = recorded("signature", "missed") or []
            say("  ^ Your five AI variants: all caught. The 40 seconds of")
            say("    generation bought nothing at all against this rule.")
            say(f"  ^ The {len(missed)} that got through - {', '.join(missed)} - are")
            say("    the two the model could not write. The evasion that worked")
            say("    came from base64.b64encode, and it is free.")
            say("  ^ This is ATLAS AML.CS0000 in miniature: Palo Alto's crafted")
            say("    C2 packets were called benign with over 80% confidence, and")
            say("    what they did was remove header fields. Surface work beats")
            say("    surface rules.")
        if i == 5:
            say("  ^ All of them. Including base64 and hex.")
            say("  ^ D2 never asks what format anything is in. It decodes what")
            say("    looks encoded, splits on everything, and counts how many of")
            say("    the record's values survived. Every variant still carries")
            say("    the record, because the record is the thing you needed to")
            say("    send - so the record is what a good detector keys on.")
            say("  ^ Polymorphic and undetectable are not the same word. AML.CS0032")
            say("    is the field version: attackers modified brand logos, evaded")
            say("    the visual-similarity model, and the other components of the")
            say("    ensemble caught the phishing sites anyway.")
        if i == 6:
            cv = recorded("behaviour", "cv")
            say("  ^ Flagged, and not one byte of your payload was read. Every")
            say("    variant you generated is invisible to this detector, and so")
            say("    is every variant you could ever generate.")
            say(f"  ^ Both limbs tripped: 1440 check-ins is far over the volume")
            say(f"    threshold, and a cv of {cv} says you are a timer.")
            say("  ^ Content was never the only signal. This is a crude two-limb")
            say("    version of what RITA scores on - interval consistency, size")
            say("    uniformity and dispersion.")
        if i == 7:
            beh = json.loads(open(STATE).read()).get("behaviour", {})
            rate = beh.get("records_per_hour", 0) or 0.01
            say("  ^ Clean. Read the throughput line again, though.")
            say(f"  ^ You went from 60.00 records an hour to {rate:.2f}. That is")
            say(f"    {60.0 / rate:.0f}x slower. Moving 500 records went from 8")
            say(f"    hours to {500 / rate / 24:.0f} days.")
            say("  ^ And notice WHICH limb forced that. Jitter alone beats the")
            say("    regularity limb for free - it was measured at 60s with 60%")
            say("    jitter: clean on regularity, and slightly FASTER than the")
            say("    baseline. It is the volume limb that costs, because no")
            say("    amount of irregularity changes a count.")
            say("  ^ That is the lesson: one detector dimension is nearly free to")
            say("    beat. Two orthogonal ones are a bill, and the defender sets")
            say("    the price.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM A REAL ATTACK")
    rule()
    say("")
    say("   THIS LAB                      A REAL ATTACK")
    say("   the record is one text line   variation is tied to a live payload")
    say("   a mock collector on loopback  infrastructure the operator owns")
    say("   the marker is LAB-BEACON      no marker, and nothing announces itself")
    say("   you try two settings by hand  they iterate against a copy of the")
    say("                                 detector until something passes")
    say("   our own three detectors       an ensemble, tuned, and updated")
    say("")
    say("   Two of those gaps are on purpose and worth naming.")
    say("")
    say("   We do NOT ship a loop that tests variants against the detector and")
    say("   refines until one passes. That is an offensive tool no matter how")
    say("   harmless the payload is, and it is the one thing this lab was")
    say("   explicitly built without.")
    say("")
    say("   And the collector is on 127.0.0.1, not on a real domain. A work")
    say("   laptop that runs a hacking lab and then beacons on a timer to an")
    say("   unfamiliar host is the textbook EDR detection. Step 3 printed what")
    say("   a real operator's endpoint would have logged, and stopped there.")
    say("")
    rule()
    say(" THE DEFENCE")
    rule()
    say("")
    say("   1. Key on the record, not the rendering. D2 is twenty lines and it")
    say("      caught everything D1 missed. If your rule can be beaten by")
    say("      base64, it can be beaten by a first-year script and no AI at all.")
    say("   2. Normalise before you match. Decode, unescape, flatten, THEN")
    say("      apply the rule. Every detector in this lab that worked did this.")
    say("   3. Have a signal the payload cannot touch. Cadence, volume,")
    say("      destination rarity, session length. Those are what made the")
    say("      attacker pay.")
    say("   4. Make them orthogonal. One dimension is nearly free to beat -")
    say("      measured, at zero cost to the attacker's throughput. Two")
    say("      dimensions that fail independently force a real slowdown.")
    say("   5. Price your detectors, do not just count what they catch. '80x")
    say("      slower' is a number a defender can take to a budget meeting.")
    say("      'We block 12,000 signatures' is not.")
    say("   6. Do not buy 'AI-powered' as a threat multiplier without asking")
    say("      what it multiplies. Here it multiplied the thing that was")
    say("      already cheap and already caught.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")
    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste the three numbers from the last command into the class chat:")
    say("  what the model produced, what the signature rule missed, and the")
    say("  slowdown it took to go clean.")
    say("")
    say("  Full transcript saved to lab7-results.txt on your machine.")
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
    say("  Lab 8 is where the course turns around. You have now attacked an")
    say("  LLM six ways and used one as a weapon once. From here it is")
    say("  defence.")
    say("")


if __name__ == "__main__":
    main()
