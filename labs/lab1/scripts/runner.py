#!/usr/bin/env python3
"""
Lab 1 guided runner. The student types every command.

SECURITY NOTE: nothing the student types is ever executed. Their input is
only compared to the expected command. On a match we run our own known-good
copy of that string. This is a security course; the lab should not itself
contain an eval-what-the-user-typed bug.
"""
import argparse
import os
import re
import subprocess
import sys

WORK = "/labs/lab1"
RESULTS = os.path.join(WORK, "lab1-results.txt")
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
    say(" Send lab1-results.txt to the instructor via email or post to class Q&A.")
    rule()
    sys.exit(1)


STEPS = [
    {
        "why": [
            "Before you run anything, read it.",
            "This is the script that builds both model files. Look for",
            "__reduce__ - that is the whole attack, in three lines.",
        ],
        "cmd": "cat make_model.py",
        "expect_rc": 0,
        "after": None,
    },
    {
        "why": [
            "Build a model file from the genuine bert-tiny weights,",
            "saved exactly as they came. Nothing added.",
        ],
        "cmd": "python make_model.py --clean",
        "expect_rc": 0,
        "after": "bert_tiny_clean.pt",
    },
    {
        "why": [
            "Scan the clean file. picklescan reads the pickle opcodes",
            "WITHOUT running them, looking for a GLOBAL opcode that imports",
            "a system-execution primitive paired with a REDUCE opcode.",
            "Expect: no threats.",
        ],
        "cmd": "picklescan -p bert_tiny_clean.pt -g",
        "expect_rc": 0,
        "after": None,
    },
    {
        "why": [
            "Same script, same weights, one word different on the command",
            "line. This time it adds the hidden payload object.",
        ],
        "cmd": "python make_model.py --poison",
        "expect_rc": 0,
        "after": "bert_tiny_poisoned.pt",
    },
    {
        "why": [
            "Scan the poisoned file. Same scanner, same model, same command",
            "except the filename.",
            "Expect: 1 infected file, and a dangerous global.",
        ],
        "cmd": "picklescan -p bert_tiny_poisoned.pt -g",
        "expect_rc": 1,
        "after": None,
    },
    {
        "why": [
            "One scanner is one opinion. Before we get a second one, see",
            "what a .pt file really is: a ZIP archive with a pickle inside.",
            "This pulls that pickle out as data.pkl.",
        ],
        "cmd": "python unpack.py bert_tiny_poisoned.pt",
        "expect_rc": 0,
        "after": "data.pkl",
    },
    {
        "why": [
            "Now a different tool, built on the opposite idea.",
            "picklescan uses a DENYLIST - it knows which imports are bad.",
            "fickling uses an ALLOWLIST - it knows which are safe and",
            "distrusts all the rest, so it is noisier on purpose.",
        ],
        "cmd": "fickling --check-safety --print-results data.pkl",
        # fickling exits 1 when it judges the file unsafe - same as picklescan.
        "expect_rc": 1,
        "expect_contains": "overtly malicious",
        "after": None,
    },
]


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--challenge", action="store_true",
                    help="hide the command, show only the description")
    ap.add_argument("--auto", action="store_true",
                    help="run every command without prompting (for testing)")
    args = ap.parse_args()

    rule()
    say(" LAB 1 - DATA AND MODEL SUPPLY CHAIN POISONING")
    rule()
    say("")
    say("  The question this lab answers:")
    say("    If you download a model from a public hub, what did you")
    say("    actually just put on your machine?")
    say("")
    say("  You will type seven commands. Read each one before you run it.")
    say("  If you mistype, you get told what the command should be.")
    say("")
    say("  OWASP  LLM04:2026 Supply Chain  (was LLM03:2025)")
    say("         LLM05:2026 Data and Model Poisoning  (was LLM04:2025)")
    say("  ATLAS  AML.T0058 > AML.T0018.000 > AML.T0010.003 > AML.T0011.000")
    say("")
    say("  Nothing leaves this container. The payload runs one echo.")

    total = len(STEPS)
    typed = 0
    for i, step in enumerate(STEPS, start=1):
        how = ask(step, i, total, args.challenge, args.auto)
        if how == "typed":
            typed += 1
        rc, output = run(step["cmd"])

        if step["expect_rc"] is not None and rc != step["expect_rc"]:
            fail(f"Step {i} ({step['cmd']}) returned {rc}, expected {step['expect_rc']}.")
        if step["after"] and not os.path.exists(os.path.join(WORK, step["after"])):
            fail(f"Step {i} should have created {step['after']}, but it does not exist.")
        # fickling exits 0 even when it flags a file, so check the text as well.
        want = step.get("expect_contains")
        if want and want not in output:
            fail(f"Step {i} output should have contained {want!r}, but did not.")

        if i == 3:
            say("  ^ Infected files: 0. That is what clean looks like. Remember it.")
        if i == 7:
            say("  ^ Read the LAST line before the warning, and the wording it")
            say("    reserves for it: 'overtly malicious'. Everything above it")
            say("    is fickling distrusting torch's own legitimate imports -")
            say("    that is the cost of an allowlist. Two tools, two methods,")
            say("    same conclusion.")
        if i == 5:
            say("  ^ Infected files: 1. Dangerous global: posix.system.")
            say("")
            say("    You read os.system in the script. The file records")
            say("    posix.system, because on Linux os is a thin wrapper over")
            say("    posix. Same function. Renaming an import does not hide")
            say("    you from a scanner.")

    say("")
    rule()
    say(" THE EVIDENCE - the two scans, side by side")
    rule()
    say("")
    say("   bert_tiny_clean.pt      Infected files: 0")
    say("   bert_tiny_poisoned.pt   Infected files: 1   posix.system")
    say("")
    say("   Same script. Same weights. Same scanner. One extra key.")
    say("   And a second, independent scanner agrees.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")

    rule()
    say(" HOW THIS DIFFERS FROM A REAL ATTACK")
    rule()
    say("")
    say("   THIS LAB                      A REAL ATTACK")
    say("   the command is echo           reverse shell, stealer, miner")
    say("   key says _security_demo_      key named to blend in with weights")
    say("   file stays in this container  file uploaded to a public hub")
    say("   a 17.8 MB test model          a model pulled by thousands")
    say("   you scanned before loading    victim loads, never scans")
    say("   built to be caught            built to survive the scanner")
    say("")

    rule()
    say(" WHAT THIS LAB DID NOT PROVE")
    rule()
    say("")
    say("  You just watched a scanner catch an attack. Do not leave")
    say("  thinking scanners make you safe. OWASP 2026 calls scanners and")
    say("  safe-loader flags defence in depth, NOT guarantees:")
    say("")
    say("    - nullifAI: models on Hugging Face using broken or compressed")
    say("      pickle streams that fire BEFORE a scanner reaches the bad")
    say("      byte  (Zanki, 2025)")
    say("    - picklescan itself has had zero-days  (Cohen, 2025)")
    say("    - torch.load weights_only has had a bypass  (CVE-2025-32434)")
    say("    - ShadowLogic: a backdoor in the computation graph of a 'safe'")
    say("      format like ONNX, with no code to find at all")
    say("      (Wickens et al., 2024)")
    say("")
    say("  THE DEFENCE, in order of cost:")
    say("    1. Prefer safetensors. It cannot execute code by design.")
    say("    2. Scan every pickle model you did not build yourself.")
    say("    3. Keep torch.load(weights_only=True).")
    say("    4. Verify provenance: signatures and hashes, not hub reputation.")
    say("")

    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste BOTH scan summaries into the class chat - the clean one")
    say("  and the poisoned one. The pair is the proof, not either alone.")
    say("")
    say("  Full transcript saved to lab1-results.txt on your machine.")
    say("")
    rule()
    say(" BEFORE YOU CLOSE THIS")
    rule()
    say("")
    say("  When this window exits, the setup script offers to download the")
    say("  next lab. Say yes. It is a small download because the labs share")
    say("  most of their layers, and it means no waiting next session.")
    say("")


if __name__ == "__main__":
    main()
