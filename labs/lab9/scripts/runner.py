#!/usr/bin/env python3
"""
Lab 9 guided runner. The student types every command.

SECURITY NOTE: nothing the student types is ever executed. Their input is
only compared to the expected command. On a match we run our own known-good
copy of that string. This is a security course, and this lab especially.
"""
import argparse
import os
import re
import subprocess
import sys

WORK = "/labs/lab9"
RESULTS = os.path.join(WORK, "lab9-results.txt")
WIDTH = 64

_log = open(RESULTS, "w", encoding="utf-8")


def say(text=""):
    print(text)
    _log.write(text + "\n")
    _log.flush()


def rule(ch="="):
    say(ch * WIDTH)


def normalize(s):
    """Trim outer spaces, collapse repeated inner spaces. Flags, filenames
    and case stay exact."""
    return re.sub(r"\s+", " ", s.strip())


def fail(msg):
    say("")
    rule()
    say(" LAB ERROR - stopping here rather than showing you a wrong result.")
    say("")
    say("   " + msg)
    say("")
    say(" This is a problem with the lab, not with anything you did.")
    say(" Send lab9-results.txt to the instructor through GitHub.")
    rule()
    sys.exit(1)


STEPS = [
    {
        "why": [
            "Build the four artifacts you will defend against. Same real",
            "bert-tiny weights in all four; the difference is one key.",
            "  clean     nothing added",
            "  poisoned  runs a command on load        (lab 1's file)",
            "  beacon    opens a connection on load",
            "  corrupt   poisoned, with its stream clipped one byte short",
        ],
        "cmd": "python make_model.py --all",
        "expect_rc": 0,
        "after": "bert_tiny_corrupt.pt",
    },
    {
        "why": [
            "PREVENT. The gate is what stands between a hub and your build.",
            "Hash the file, scan it, apply your own rules.",
            "Start with the genuine article. Expect: allowed.",
        ],
        "cmd": "python gate.py bert_tiny_clean.pt",
        "expect_rc": 0,
        "expect_contains": "ALLOWED into the build",
        "impact": [
            "^ The scanner read the whole file and found nothing. That is",
            "  what a real, unmodified download from a real hub looks like.",
        ],
    },
    {
        "why": [
            "Now the poisoned file from lab 1. Same weights, one extra key.",
            "Expect: blocked - and read WHICH line blocked it.",
        ],
        "cmd": "python gate.py bert_tiny_poisoned.pt",
        "expect_rc": 1,
        "expect_contains": "BLOCKED by rules.json",
        "impact": [
            "^ Blocked by rules.json - your own list, not the scanner's.",
            "  posix.system was in your rules before the scan even ran.",
        ],
    },
    {
        "why": [
            "The corrupt file. Its pickle stream stops one byte early, so",
            "the scanner cannot finish reading it.",
            "The question is not what the scanner found. It is what your",
            "gate does when the scanner cannot answer.",
        ],
        "cmd": "python gate.py bert_tiny_corrupt.pt",
        "expect_rc": 1,
        "expect_contains": "No verdict is not a clean verdict",
        "impact": [
            "^ Fail closed. rules.json says on_scanner_error = block, so a",
            "  file nobody could read does not get the benefit of the doubt.",
            "  Two models sat on Hugging Face for eight months in 2025",
            "  because a scanner errored and a gate read that as fine.",
        ],
    },
    {
        "why": [
            "DETECT. The gate read the file. This RUNS it, on purpose,",
            "somewhere it cannot reach anything: a separate process, no",
            "network, and an audit hook watching every import, command and",
            "socket call. Start with the clean file, so you know what quiet",
            "looks like.",
        ],
        "cmd": "python sandboxed_load.py bert_tiny_clean.pt",
        "expect_rc": 0,
        "expect_contains": "nothing. No commands, no sockets",
        "impact": [
            "^ Nothing. Remember this screen - it is your baseline, and it",
            "  is the half of the evidence people forget to collect.",
        ],
    },
    {
        "why": [
            "Now load the corrupt file - the one your gate just refused.",
            "It is broken, so the load cannot finish. Watch what happens",
            "before it fails.",
        ],
        "cmd": "python sandboxed_load.py bert_tiny_corrupt.pt",
        "expect_rc": 1,
        "expect_contains": "EXECUTED  os.system",
        "impact": [
            "^ Read the order. The payload ran, THEN the load fell over.",
            "  Pickle executes as it reads, so a broken file is not a safe",
            "  file - the damage is done before the error appears. That is",
            "  exactly how the nullifAI models worked.",
        ],
    },
    {
        "why": [
            "The beacon file. Its payload does not run a command - it opens",
            "a socket to 203.0.113.10:4444.",
            "This container has no network at all, and the hook refuses the",
            "call as well. Two controls, and you get to see the address.",
        ],
        "cmd": "python sandboxed_load.py bert_tiny_beacon.pt",
        "expect_rc": 1,
        "expect_contains": "BLOCKED   socket.getaddrinfo",
        "impact": [
            "^ Blocked before connect() was ever called. You now know the",
            "  address and the port the artifact wanted - which is an",
            "  indicator you can act on, and you got it without letting a",
            "  single packet leave.",
        ],
    },
    {
        "why": [
            "RECOVER. Contain it: move the file out of the build path, and",
            "record its hash with the evidence your sandbox produced.",
            "Moved, not deleted. You cannot investigate what you destroyed.",
        ],
        "cmd": "python quarantine.py bert_tiny_beacon.pt",
        "expect_rc": 0,
        "expect_contains": "now on the block list",
        "impact": [
            "^ The hash is recorded with the reason and the evidence. The",
            "  gate refuses that file from now on without scanning it.",
        ],
    },
    {
        "why": [
            "TUNE. A block list catches the file you already saw. This step",
            "re-uploads the same payload with one byte changed - a new hash",
            "your block list has never seen - and asks the gate again.",
            "Then it adds your sandbox's own indicator to rules.json.",
        ],
        "cmd": "python tune.py --add socket.create_connection",
        "expect_rc": 0,
        "expect_contains": "BLOCKED by rules.json: socket.create_connection",
        "impact": [
            "^ Same verdict, different authority. Before the edit, a vendor's",
            "  denylist was the only thing standing there. picklescan has had",
            "  58 published CVEs since February 2025, every one a way past",
            "  that list. Now you have a rule of your own as well.",
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
    say("  You are in /labs/lab9 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Expert runs the whole command list. Beginner mode runs only the")
    say("  lines marked with a B.")
    say("")
    say("  The steps beginner never sees:")
    say("    - edit the gate's policy by hand instead of running tune.py:")
    say("        nano rules.json")
    say("      add \"socket.create_connection\" to blocked_globals, and look")
    say("      hard at on_scanner_error while you are in there.")
    say("    - read what you recorded:   cat blocklist.json")
    say("    - read the raw evidence:    cat sandbox-log.jsonl")
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
    say(" LAB 9 - DEFENDING THE MODEL SUPPLY CHAIN")
    rule()
    say("")
    say("  Lab 1 asked what you just put on your machine.")
    say("  This lab is the answer: the gate that stops it, the sandbox that")
    say("  catches what the gate missed, and the loop that closes afterwards.")
    say("")
    say("  Defends  lab 1 - data and model supply chain poisoning")
    say("  OWASP    LLM04:2026 Supply Chain  (risks 3 and 4)")
    say("           LLM05:2026 Data and Model Poisoning  (scenario 7)")
    say("  ATLAS    defends AML.T0115.001 > AML.T0010.003 > AML.T0011.000")
    say("           with  AML.M0016  Vulnerability Scanning")
    say("                 AML.M0011  Restrict Library Loading")
    say("                 AML.M0024  AI Telemetry Logging")
    say("")
    say("  Nothing leaves this container. The payloads are an echo and a")
    say("  connection to a documentation address that routes nowhere.")


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
    say("  Nine commands. Read each one before you run it.")
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
    say("   the gate        clean allowed, poisoned blocked, corrupt")
    say("                   blocked because nobody could read it")
    say("   the sandbox     clean silent; os.system with its argument;")
    say("                   a blocked connection with its address")
    say("   the quarantine  the hash, the date, the reason, the evidence")
    say("   your rule       one indicator you produced yourself")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")

    rule()
    say(" HOW THIS DIFFERS FROM A REAL DEFENCE")
    rule()
    say("")
    say("   THIS LAB                      PRODUCTION")
    say("   one scanner                   scanner + signature + format policy")
    say("   a child process               a VM or a hardened runner")
    say("   an audit hook                 kernel-level isolation, seccomp")
    say("   a JSON file of hashes         an artifact registry and a ticket")
    say("   you ran it by hand            CI runs it on every artifact")
    say("   four files                    thousands, continuously")
    say("")

    rule()
    say(" THE PART YOU SHOULD NOT MISS")
    rule()
    say("")
    say("  The audit hook you just used is TELEMETRY, NOT A BOUNDARY.")
    say("  Code that is already running in that process has already won; it")
    say("  reports what happened, it does not guarantee what cannot.")
    say("")
    say("  The boundary was the container and --network none the whole time.")
    say("")
    say("  In August 2026 a coding agent was hijacked by a website summary")
    say("  task: a file named struct.py inside a downloaded archive shadowed")
    say("  the standard library, so importing base64 ran the attacker's code.")
    say("  60-80% success, against a vendor benchmark that reported 0.00%.")
    say("  The benchmark was not lying. It just did not contain that chain.")
    say("")
    say("  A classifier is not a sandbox, and a vendor's number is not a")
    say("  control. Isolation and egress policy are.")
    say("")

    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste TWO things into the class chat:")
    say("    1. the blocklist.json entry you created")
    say("    2. the sandbox line showing the blocked connection")
    say("")
    say("  Full transcript saved to lab9-results.txt on your machine.")
    say("")
    rule()
    say(" BEFORE YOU CLOSE THIS")
    rule()
    say("")
    say("  When this window exits, the setup script offers to download the")
    say("  next lab. Say yes. Lab 10 shares almost every layer with this one,")
    say("  so it is a small download and no waiting next session.")
    say("")


if __name__ == "__main__":
    main()
