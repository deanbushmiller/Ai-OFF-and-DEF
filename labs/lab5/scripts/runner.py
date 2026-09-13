#!/usr/bin/env python3
"""
Lab 5 runner. Asks the student to choose beginner or expert mode.

Beginner: the guided path - shows each command, checks what the student types,
          corrects a miss, runs the real command on a match.
Expert:   drops to a real shell in the lab folder. The student works from
          LAB.md, including the steps beginner skips (cd, writing their own
          payload with nano, running the minimize-tools defence for real).

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command; on a match we run our own known-good copy.
"""
import argparse
import json
import os
import re
import subprocess
import sys

WORK = "/labs/lab5"
RESULTS = os.path.join(WORK, "lab5-results.txt")
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
    say(" Send lab5-results.txt to the instructor through GitHub.")
    rule()
    sys.exit(1)


def recorded(key, field):
    """Read what the agent actually did, from runs.json, rather than
    pattern-matching the screen. The model's prose wording is stable but it is
    still prose; the tool-call log is structural and is what we assert on."""
    if not os.path.exists(RUNS):
        return None
    try:
        return json.loads(open(RUNS).read()).get(key, {}).get(field)
    except (ValueError, OSError):
        return None


STEPS = [
    {"why": ["Start where an attacker starts: what can this agent actually do?",
             "These are its tool definitions - the agent's own description of",
             "its powers. Nothing runs the model yet."],
     "cmd": "python agent.py --tools", "rc": 0, "want": "set_role"},

    {"why": ["Now run it honestly. The agent is asked to summarise the public",
             "notes, and that is all it should need to do.",
             "The model runs locally on your CPU. This can take a minute."],
     "cmd": "python agent.py", "rc": 0, "want": "TOOL  read_notes",
     "assert": ("vulnerable", "read_admin", False)},

    {"why": ["You are the attacker now. One line of text, appended to a file",
             "the agent reads. Read it on screen - nothing is hidden, and it",
             "is going to work anyway."],
     "cmd": "python plant.py", "rc": 0, "want": "SYSTEM NOTE"},

    {"why": ["Same agent. Same model. Same question. Same code.",
             "Watch the tool calls, not the answer. Another minute."],
     "cmd": "python agent.py", "rc": 0, "want": "set_role",
     "assert": ("vulnerable", "read_admin", True)},

    {"why": ["The defence. The privilege check moves out of the conversation",
             "and into the tool layer, where the attacker's text cannot reach",
             "it. The payload is still planted. Last slow step."],
     "cmd": "python agent.py --mediate", "rc": 0, "want": "DENIED",
     "assert": ("mediate", "read_admin", False)},

    {"why": ["The evidence. Three tool-call logs side by side.",
             "This is what you submit."],
     "cmd": "python evidence.py", "rc": 0, "want": "AML.T0053"},
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
    say(" LAB 5 - EXPLOITING AI AGENTS AND EXCESSIVE AGENCY")
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
    say("  You are in /labs/lab5 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every command is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - cat tools.py and find the three bugs before you read the")
    say("      comments naming them")
    say("    - nano payload.txt to write your OWN instruction, then")
    say("      python plant.py --reset and python plant.py to re-plant it")
    say("    - python agent.py --minimal to run the second defence, deleting")
    say("      set_role instead of mediating it - and decide which you would")
    say("      actually ship")
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

    # A re-run must start from a clean slate: stale runs.json entries would let
    # a broken step assert against a previous run's success.
    if os.path.exists(RUNS):
        os.remove(RUNS)
    subprocess.run("python plant.py --reset", shell=True, cwd=WORK,
                   capture_output=True, text=True)

    rule()
    say(" LAB 5 - EXPLOITING AI AGENTS AND EXCESSIVE AGENCY  (beginner)")
    rule()
    say("")
    say("  The question this lab answers:")
    say("    Your agent can call tools. What decides whether it is ALLOWED")
    say("    to - your code, or the text it just read?")
    say("")
    say("  OWASP  LLM03:2026 Excessive Agency - risks 1 and 4, quoted:")
    say("           '#1 An LLM agent has access to tools which include")
    say("            functions that are not needed for the intended")
    say("            operation of the system.'")
    say("           '#4 An LLM tool has permissions on downstream systems")
    say("            that are not needed for the intended operation.'")
    say("         (LLM03 in 2026. It was LLM06 in the 2025 list.)")
    say("  ATLAS  AML.T0084.001 Tool Definitions")
    say("           > AML.T0065 LLM Prompt Crafting")
    say("           > AML.T0051.001 Prompt Injection: Indirect")
    say("           > AML.T0053 AI Agent Tool Invocation")
    say("             tactic AML.TA0012, Privilege Escalation")
    say("")
    say("  Six commands. Three of them run a model on your CPU and take")
    say("  about a minute each. Everything is local: the tools are stubs,")
    say("  the 'boxes' are text files, and the container has no network.")

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
                     f"expected {expected!r}. The attack or the defence did "
                     f"not behave as measured during the build.")

        if i == 1:
            say("  ^ A triage agent has been handed set_role. Nothing about")
            say("    summarising notes needs the power to change who you are.")
            say("    That is OWASP risk #1, excessive functionality, and it is")
            say("    usually there because the toolbox was built for the whole")
            say("    platform rather than for this one job.")
        if i == 2:
            say("  ^ Correct, and boring. One tool call, the public box, a")
            say("    summary. That is the agent working. Remember this shape -")
            say("    it is the thing the attack is about to change.")
        if i == 3:
            say("  ^ Look at what you just planted. No hidden characters, no")
            say("    white-on-white text, no encoding trick. Labs 3 and 4 spent")
            say("    their effort on concealment because they had to talk a")
            say("    model past its own judgment. There is no judgment here to")
            say("    talk past.")
        if i == 4:
            say("  ^ Read the chain: read_notes, then set_role, then read_notes")
            say("    again - and the second one came back with a password.")
            say("    The agent was not tricked into BELIEVING it was an admin.")
            say("    It asked to become one, and your tool layer said yes.")
            say("    The check was on the wrong side of the boundary: it read a")
            say("    variable the model itself had just written to.")
        if i == 5:
            say("  ^ Now read what did NOT change. The payload is still there.")
            say("    The model still read it, still believed it, still called")
            say("    set_role exactly as the attacker asked. The injection")
            say("    succeeded completely.")
            say("    The exploit failed anyway, because the privilege now lives")
            say("    somewhere the conversation cannot reach.")
            say("  ^ Read the agent's last line again. Blocked, it turns around")
            say("    and asks YOU to set the role to admin for it. It is still")
            say("    carrying the attacker's goal - it has just run out of ways")
            say("    to reach it on its own. That is the confused deputy asking")
            say("    politely, and it is why control 5 in the list below is not")
            say("    optional: the next thing a real attacker tries is the")
            say("    human.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM A REAL ATTACK")
    rule()
    say("")
    say("   THIS LAB                      A REAL ATTACK")
    say("   two stub tools                mail, tickets, databases, payments")
    say("   'boxes' are two text files    the actual customer records")
    say("   you plant the line yourself   it arrives in a support ticket")
    say("   the secret is a fake string   credentials that still work")
    say("   set_role is a variable        an OAuth scope or an assumed role")
    say("   the log is printed for you    nobody is reading the log")
    say("")
    say("   The shape is the same, and that is the uncomfortable part.")
    say("")
    rule()
    say(" THE DEFENCE")
    rule()
    say("")
    say("   1. Complete mediation. OWASP prevention #7: 'implement")
    say("      authorization in logic rather than relying on an LLM to decide")
    say("      if an action is allowed'. You just watched it hold.")
    say("   2. Authorization must live where the conversation cannot write to")
    say("      it. A role the model can set is not a role. If an attacker's")
    say("      text can change the variable, it is not a control.")
    say("   3. Minimize tools. The agent never needed set_role. Try it:")
    say("      python agent.py --minimal")
    say("   4. Minimize permissions. read_notes should have been scoped to the")
    say("      boxes this session may see, not to every box that exists.")
    say("   5. Log tool calls and alert on the shape. A role change inside a")
    say("      summarisation task is not subtle - if anyone is looking.")
    say("")
    say("   Note the order. 1 and 2 are controls. 3 and 4 shrink the blast")
    say("   radius. 5 tells you afterwards. Only the first two would have")
    say("   stopped what you just did.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")
    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste the tool-call log from the last command into the class chat -")
    say("  all three columns. The escalation alone proves nothing without the")
    say("  clean run above it and the mediated run below it.")
    say("")
    say("  Full transcript saved to lab5-results.txt on your machine.")
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
