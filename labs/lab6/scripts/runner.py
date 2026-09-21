#!/usr/bin/env python3
"""
Lab 6 runner. Asks the student to choose beginner or expert mode.

Beginner: the guided path - shows each command, checks what the student types,
          corrects a miss, runs the real command on a match.
Expert:   drops to a real shell in the lab folder. The student works from
          LAB.md, including the steps beginner skips (starting the server, proxy
          and client as three separate processes, and writing their own payload).

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command; on a match we run our own known-good copy.
"""
import argparse
import json
import os
import re
import subprocess
import sys

WORK = "/labs/lab6"
RESULTS = os.path.join(WORK, "lab6-results.txt")
RUNS = os.path.join(WORK, "runs.json")
LEDGER = os.path.join(WORK, "ledger.json")
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
    say(" Send lab6-results.txt to the instructor via email or post to class Q&A.")
    rule()
    sys.exit(1)


def recorded(key, field):
    """Assert on what the client recorded, not on what scrolled past."""
    if not os.path.exists(RUNS):
        return None
    try:
        return json.loads(open(RUNS).read()).get(key, {}).get(field)
    except (ValueError, OSError):
        return None


STEPS = [
    {"why": ["Start where an attacker starts: what does this MCP server say it",
             "can do? This prints the tool list exactly as the server sends it.",
             "No model runs yet."],
     "cmd": "python mitm.py --tools", "rc": 0, "want": "inputSchema"},

    {"why": ["Now a normal question, end to end. The proxy is watching and",
             "changing nothing. Read the JSON-RPC going past.",
             "The model runs locally on your CPU. This can take a minute."],
     "cmd": "python mitm.py --beat control", "rc": 0, "want": "4820.55",
     "assert": ("control", "paid", False)},

    {"why": ["Your first edit, and it is on the REQUEST. The proxy changes which",
             "account is asked about. You are still asking about chk-001.",
             "Another minute."],
     "cmd": "python mitm.py --rewrite-arg chk-002 --beat arg", "rc": 0,
     "want": "17.02", "assert": ("arg", "paid", False)},

    {"why": ["Now the RESPONSE, and this time the payload is an instruction",
             "rather than a number. Watch the tool calls, not the answer.",
             "The slowest step - up to two minutes."],
     "cmd": "python mitm.py --inject --beat inject", "rc": 0,
     "want": "send_payment", "assert": ("inject", "paid", True)},

    {"why": ["The defence. The server now signs every response and the proxy",
             "verifies it. Same injection, same payload, same everything else."],
     "cmd": "python mitm.py --inject --verify --beat defended", "rc": 0,
     "want": "SIGNATURE MISMATCH", "assert": ("defended", "paid", False)},

    {"why": ["The same defence against the FIRST attack. No model needed - watch",
             "the signature check itself. This one should worry you."],
     "cmd": "python mitm.py --rewrite-arg chk-002 --verify --wire-only", "rc": 0,
     "want": "17.02"},

    {"why": ["The evidence. What the wire carried, next to what you were told."],
     "cmd": "python evidence.py", "rc": 0, "want": "AML.T0110"},
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
    say(" LAB 6 - MCP AND INTERFACE HIJACKING")
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
    say("  You are in /labs/lab6 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every command is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - start the three processes yourself, in three terminals or with &:")
    say("        python mcp_server.py &")
    say("        python proxy.py --inject &")
    say("        python mcp_client.py")
    say("      mitm.py does this for you in beginner mode; doing it by hand is")
    say("      how you see that they are three separate programs on a network.")
    say("    - nano payload.txt to write your OWN instruction, then re-run.")
    say("      Four phrasings were measured while building this lab and two of")
    say("      the four failed. See whether yours lands.")
    say("    - python mitm.py --rewrite-result 999999.00, the beat the guided")
    say("      path skips, and ask why it is the least interesting of the three.")
    say("    - read proxy.py. It is about 120 lines and it is the whole attack.")
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

    # A re-run starts clean, or a stale runs.json could satisfy an assertion
    # that this run never actually earned.
    for f in (RUNS, LEDGER):
        if os.path.exists(f):
            os.remove(f)

    rule()
    say(" LAB 6 - MCP AND INTERFACE HIJACKING  (beginner)")
    rule()
    say("")
    say("  The question this lab answers:")
    say("    Your model talks to its tools over a protocol. What proves that")
    say("    the answer it got back is the answer the server sent?")
    say("")
    say("  OWASP  LLM01:2026 Prompt Injection - Scenario #9, quoted:")
    say("           'Trusted-Backend Indirect Injection through MCP. An")
    say("            attacker plants text in a low-privilege channel ... and")
    say("            the developer's LLM reads it under elevated credentials.'")
    say("         Three real 2025 incidents are named in that scenario.")
    say("         LLM08:2026 Hidden Context Exposure - risks 1 and 4, the tool")
    say("           descriptions and schemas you are about to read.")
    say("  ATLAS  AML.T0084.001 Tool Definitions")
    say("           > AML.T0110 AI Agent Tool Poisoning   <- the core technique")
    say("             'modifying parameters or descriptions ... or")
    say("              redirecting outputs'")
    say("           > AML.T0051.001 > AML.T0053")
    say("")
    say("  Seven commands, four of which run a model on your CPU. Everything")
    say("  is local: three processes on 127.0.0.1 inside this container, no")
    say("  port published, no network. No money exists.")

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
        if step.get("assert"):
            key, field, expected = step["assert"]
            got = recorded(key, field)
            if got != expected:
                fail(f"Step {i}: runs.json[{key!r}][{field!r}] is {got!r}, "
                     f"expected {expected!r}. The attack or the defence did not "
                     f"behave as measured during the build.")

        if i == 1:
            say("  ^ You just read something the user never sees. The tool")
            say("    descriptions and schemas go into the model's instructions")
            say("    verbatim, and the SERVER chooses that text. OWASP calls")
            say("    this hidden context and says to assume it is discoverable.")
        if i == 2:
            say("  ^ Correct, and boring. One tools/call, the right account, the")
            say("    right balance. Note what went past on the wire: plain JSON,")
            say("    no signature, no checksum, nothing tying the answer to the")
            say("    server that sent it.")
        if i == 3:
            say("  ^ Read the answer again. It names YOUR account, chk-001, and")
            say("    gives you a balance from a different one. You asked the right")
            say("    question; something else answered a different one. There is")
            say("    no wording here a defender could pattern-match.")
            say("    ATLAS AML.T0110 calls this 'modifying parameters'.")
        if i == 4:
            say("  ^ A payment happened. Now read what you were TOLD: the answer")
            say("    is an ordinary balance reply and never mentions it.")
            say("    The instruction arrived inside a tool RESULT, which this")
            say("    client pastes into the conversation with no label saying")
            say("    'this is data, not an instruction'.")
            say("    OWASP lists 'an MCP server's output' as an untrusted surface")
            say("    for exactly this reason.")
        if i == 5:
            say("  ^ Refused. The server signed the exact bytes of its answer and")
            say("    the proxy's edit broke the signature. Same payload, same")
            say("    model, same client - and nothing happened. Integrity, not")
            say("    cleverness.")
        if i == 6:
            say("  ^ And there is the problem. 17.02 again. The signature was")
            say("    VALID, because the server honestly signed an honest answer")
            say("    to the question it was honestly asked - the wrong question.")
            say("    You signed the answer. Nobody signed the question.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM A REAL ATTACK")
    rule()
    say("")
    say("   THIS LAB                      A REAL ATTACK")
    say("   you are handed the proxy      the position is bought with a")
    say("                                 poisoned server or package")
    say("   a --rewrite flag              persistent, hidden tampering")
    say("   two stub tools                real payments, files, repos")
    say("   payment is a printed string   money actually leaves")
    say("   the wire log is printed       nobody is reading the log")
    say("")
    say("   Three real 2025 incidents took the shape of step 4: a poisoned")
    say("   GitHub issue that exfiltrated private repos, a Supabase MCP server")
    say("   that dumped a production database, and the postmark-mcp package")
    say("   that BCC'd email from about 300 organisations.")
    say("")
    rule()
    say(" THE DEFENCE")
    rule()
    say("")
    say("   1. Authenticate the channel in BOTH directions. You watched signing")
    say("      the response stop two attacks and miss the third. Sign or")
    say("      authenticate the request too, or use a channel that does it for")
    say("      you. A one-way check protects one direction.")
    say("   2. Treat tool output as data, never as instruction. Render it")
    say("      quoted and labelled, so an instruction inside a result cannot")
    say("      read as a turn in the conversation.")
    say("   3. Do not trust tool descriptions either. They are hidden context")
    say("      the server controls, and the client pasted them straight into")
    say("      the system prompt.")
    say("   4. Pinning is necessary and NOT sufficient - OWASP says so in the")
    say("      entry itself: it does not stop 'a payload shipped in the pinned")
    say("      version or tool-description poisoning that leaves the version")
    say("      unchanged'. Diff what the server advertises, every run.")
    say("   5. Keep the privileged action behind a check the channel cannot")
    say("      reach. That is lab 5's lesson and it is what would have saved")
    say("      step 4.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")
    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste the evidence block from the last command into the class chat -")
    say("  the wire log next to what the assistant said. The disagreement")
    say("  between those two is the finding.")
    say("")
    say("  Full transcript saved to lab6-results.txt on your machine.")
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
