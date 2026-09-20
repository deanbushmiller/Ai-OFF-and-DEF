#!/usr/bin/env python3
"""
Lab 13 runner. Asks the student to choose beginner or expert mode.

Beginner: shows each command, checks what the student types, corrects a miss,
          runs the real command on a match.
Expert:   drops to a real shell in the lab folder, working from LAB.md.

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command; on a match we run our own known-good copy.
This is separate from, and must not be confused with, the BROKER the lab teaches
- the broker gates what the AGENT may call; this gates what the RUNNER may run.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

WORK = "/labs/lab13"
RESULTS = os.path.join(WORK, "lab13-results.txt")
POLICY = os.path.join(WORK, "policy.json")
POLICY_PRISTINE = os.path.join(WORK, "policy.default.json")
LOGFILE = os.path.join(WORK, "audit-log.jsonl")
NOTES = os.path.join(WORK, "notes")
PRISTINE = os.path.join(WORK, "notes-pristine")
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
    say(" Send lab13-results.txt to the instructor through GitHub.")
    rule()
    sys.exit(1)


def reset_state():
    """Start every run from the shipped policy, clean notes and an empty log.

    Without this, a second run of the lab starts with the credential already
    revoked and set_role already off the allow-list, so step 5 would block at
    gate 1 and the lab would silently skip its own lesson. Lab 12 hit exactly
    this and it is cheap to prevent.
    """
    if os.path.exists(POLICY_PRISTINE):
        shutil.copyfile(POLICY_PRISTINE, POLICY)
    if os.path.exists(LOGFILE):
        os.remove(LOGFILE)
    if os.path.isdir(PRISTINE):
        os.makedirs(NOTES, exist_ok=True)
        for name in os.listdir(PRISTINE):
            shutil.copyfile(os.path.join(PRISTINE, name),
                            os.path.join(NOTES, name))


STEPS = [
    {"why": ["A normal triage task, through the broker. The agent reads the",
             "public notes and answers. One call, one ALLOW.",
             "This is the baseline: the control not interfering."],
     "cmd": "python agent.py", "rc": 0, "want": "BROKER ALLOW",
     "after": "audit-log.jsonl"},

    {"why": ["Every attempted tool call is recorded, with the verdict on each.",
             "ATLAS AML.M0024: 'Log AI agent tool invocations to detect",
             "malicious calls.' Right now there is nothing to detect."],
     "cmd": "python audit.py", "rc": 0, "want": "TOOL-CALL AUDIT LOG"},

    {"why": ["The attacker's entire move: one visible line, appended to a file",
             "the agent is supposed to read. Nothing is hidden. In February",
             "2026 the real version of this line was a GitHub issue title."],
     "cmd": "python plant.py", "rc": 0, "want": "Nothing is hidden"},

    {"why": ["The same command as step 1, the same agent, the same model.",
             "The only thing that changed is one line in a notes file.",
             "Watch what the agent tries to do, and where it is stopped."],
     "cmd": "python agent.py", "rc": 0, "want": "BROKER DENY"},

    {"why": ["Read the log. Three records in a row tell the whole story,",
             "and read_notes appears twice with opposite verdicts."],
     "cmd": "python audit.py", "rc": 0, "want": "THE JUMP"},

    {"why": ["So why was set_role allowed at all? The answer is in the file",
             "the broker reads before every call. Three values in here are",
             "wrong; the log just told you which."],
     "cmd": "cat policy.json", "rc": 0, "want": "purpose_scope"},

    {"why": ["Recovery, first move: revoke the scoped credential the blocked",
             "call tried to use. One field, in a file the agent cannot write."],
     "cmd": "python revoke.py", "rc": 0, "want": "CREDENTIAL REVOCATION"},

    {"why": ["Re-run the attack. The agent still escalates - revoking a",
             "credential does not stop a compromise, it limits it. Watch the",
             "denial move to a different gate."],
     "cmd": "python agent.py", "rc": 0, "want": "gate 2"},

    {"why": ["Recovery, second move: take set_role off what a triage run may",
             "call at all. OWASP prevention 1, and CSA's own finding on the",
             "Cline compromise: 'automated issue triage does not require",
             "shell execution, filesystem writes, or network access.'"],
     "cmd": "python tighten.py", "rc": 0, "want": "ALLOW-LIST CHANGE"},

    {"why": ["Re-run the attack one last time, then read the evidence.",
             "The denial should now land at the FIRST gate, and the session",
             "role should never change at all."],
     "cmd": "python agent.py && python evidence.py",
     "rc": 0, "want": "LAB 13 EVIDENCE"},
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
    say(" LAB 13 - DEFENDING AI AGENTS")
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
    say("  You are in /labs/lab13 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every command is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - edit policy.json with nano instead of running revoke.py and")
    say("      tighten.py, and decide for yourself what to change")
    say("    - add a second purpose, 'incident', that IS entitled to")
    say("      read_notes:admin, and watch the same tool call be allowed for")
    say("      one purpose and denied for another")
    say("    - run 'python agent.py --tools' and compare what the model is")
    say("      told it can do against what the broker will actually permit")
    say("")
    say("  The container has no network at all. Nothing here reaches out.")
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
    say(" LAB 13 - DEFENDING AI AGENTS  (beginner)")
    rule()
    say("")
    say("  Lab 5 showed you an agent with too many tools and no real")
    say("  authorization. This lab is the control you put in front of it.")
    say("")
    say("  The question it answers is not 'did the model get tricked'.")
    say("  The model WILL get tricked, in every run below. It is:")
    say("")
    say("    once the agent has been hijacked and holds a valid")
    say("    credential, what decides whether the call runs?")
    say("")
    say("  OWASP  LLM03:2026 Excessive Agency - prevention 7, quoted:")
    say("           'an independent pre-execution policy decision point")
    say("            between the tool and the downstream system'")
    say("         LLM01:2026 Prompt Injection is the trigger")
    say("  ATLAS  AML.T0084.001 > AML.T0051.001 > AML.T0053 > AML.T0085.001,")
    say("           countered with AML.M0028 / M0026 (the broker),")
    say("           M0024 (the log), M0027 (revocation), M0035 (the tune)")
    say("")
    say("  Ten commands. Everything is local: the agent, the tools, the")
    say("  model and the log. The container runs with no network at all.")
    say("")
    say("  The 'admin notes' in this lab are two lines of fake text in a")
    say("  file in this container. Nothing here is real and nothing leaves.")

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
        # Every one of these keys on a BROKER VERDICT, never on the model's prose
        # - see the note at the top of check.py for why that is not a style
        # preference.
        if i == 4:
            if "set_role:admin" not in out or "read_notes:admin" not in out:
                fail("Step 4 should have shown the agent calling set_role and "
                     "then read_notes on the admin box. The attack did not "
                     "reproduce, so there is nothing for the broker to stop.")
            if "gate 3" not in out:
                fail("Step 4's denial should have landed at gate 3, the "
                     "declared purpose. The policy has drifted.")
            if "the session was escalated" not in out:
                fail("Step 4 should have escalated the session. If the role "
                     "never changed, the broker is not being tested.")
            say("  ^ Read that twice. The broker ALLOWED set_role - it is on")
            say("    triage's allow-list - so the session really did become")
            say("    admin. The credential for the admin box was valid and")
            say("    active. The call was refused anyway, at the only gate")
            say("    that asks what the run is FOR.")
            say("    Identity is not intent.")
        if i == 5:
            say("  ^ read_notes appears twice, ALLOW then DENY. The tool name")
            say("    is identical; the argument is not. A policy written")
            say("    against tool names cannot tell those two calls apart -")
            say("    which is OWASP's 'excessive permissions' in one line.")
        if i == 8:
            if "gate 2" not in out:
                fail("Step 8's denial should have moved to gate 2, the scoped "
                     "credential. revoke.py did not take effect.")
            say("  ^ The denial moved from gate 3 to gate 2, and the agent")
            say("    still escalated. Revoking a credential did not prevent")
            say("    the compromise - it limited it. Both facts are useful.")
        if i == 10:
            if "gate 1" not in out:
                fail("Step 10's denial should have landed at gate 1, the "
                     "allow-list. tighten.py did not take effect.")
            if "the session was escalated" in out:
                fail("Step 10 should NOT have escalated the session. With "
                     "set_role off the allow-list the role must never change.")
            say("  ^ Gate 1. The role never changed, and the chain is shorter")
            say("    than it was in step 4 - the attempt died before it")
            say("    started. That is what 'denied earlier' looks like.")
            say("")
            say("  ^ And note the agent's own last sentence. In at least one")
            say("    of these runs it will claim it verified or read something")
            say("    it was refused. It did not. The model narrates the")
            say("    instruction it was given, not the outcome it got - which")
            say("    is precisely why the log, and not the answer, is the")
            say("    record of what an agent did.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM A REAL DEFENCE")
    rule()
    say("")
    say("   THIS LAB                      PRODUCTION")
    say("   one JSON policy file,         Cedar or Rego, versioned,")
    say("     three gates                   reviewed, with a test suite")
    say("   a purpose string set at       delegated user context carried")
    say("     launch                        across every chained call")
    say("   one credential flipped to     short-lived scoped tokens that")
    say("     active:false                  expire on their own")
    say("   one log file                  a pipeline with retention,")
    say("                                   alerting and a SIEM")
    say("   one hand edit                 a policy-change process with an")
    say("                                   owner and a time to close")
    say("   the broker runs inside the    an out-of-process decision point")
    say("     same process as the agent     the agent cannot reach, plus OS")
    say("                                   isolation and egress control")
    say("   four tool calls               thousands a second, and the")
    say("                                   latency budget is real")
    say("")
    say("   The shape is real. The scale is not. And that last row matters:")
    say("   a broker the agent could edit would be lab 5's bug again, one")
    say("   level up.")
    say("")
    rule()
    say(" WHAT TO TAKE AWAY")
    rule()
    say("")
    say("   1. Identity is not intent. The agent authenticated, held a valid")
    say("      credential and called a permitted tool. None of that answers")
    say("      the question 'is this call part of the job'.")
    say("   2. The model's account of the run is not evidence. It told you")
    say("      it had verified the admin box. It had been refused.")
    say("   3. Log the ALLOWS too. The record that mattered most in this lab")
    say("      was set_role being permitted - and a log of denials only would")
    say("      not have contained it.")
    say("   4. Revoking and tightening are different moves. One limits a")
    say("      compromise; the other prevents it. Do both, and know which is")
    say("      which when you are explaining it afterwards.")
    say("   5. Test the fix against the attack AND against normal traffic.")
    say("      The replay in step 10 costs nothing and is the argument you")
    say("      need the first time somebody asks you to loosen the policy.")
    say("   6. The production answer to the prevent half is bought, not")
    say("      built - a policy decision point in front of the tool gateway,")
    say("      such as Amazon Bedrock AgentCore Policy (Cedar) or Open")
    say("      Policy Agent. It costs latency, a policy language to")
    say("      maintain, and a dependency in the hot path. It is still")
    say("      yours to run, monitor and tune. There is no THEY.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")
    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste the output of the last command into the class chat - the")
    say("  whole table. The line that matters is the gate column walking")
    say("  3 -> 2 -> 1 while the clean run keeps passing.")
    say("")
    say("  Full transcript saved to lab13-results.txt on your machine.")
    say("")
    rule()
    say(" BEFORE YOU CLOSE THIS")
    rule()
    say("")
    say("  When this window exits, the setup script offers to download the")
    say("  next lab. Say yes - lab 14 is the same dependency tier as this")
    say("  one, so it shares the big model layer and the download is small.")
    say("")


if __name__ == "__main__":
    main()
