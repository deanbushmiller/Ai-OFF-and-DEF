#!/usr/bin/env python3
"""
Lab 14 runner. Asks the student to choose beginner or expert mode.

Beginner: shows each command, checks what the student types, corrects a miss,
          runs the real command on a match.
Expert:   drops to a real shell in the lab folder, working from LAB.md.

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command; on a match we run our own known-good copy.
This is separate from, and must not be confused with, the INTEGRITY CHECK the
lab teaches - that one gates what the MCP server may tell the model; this one
gates what the RUNNER may run.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

WORK = "/labs/lab14"
RESULTS = os.path.join(WORK, "lab14-results.txt")
TRUST = os.path.join(WORK, "trust.json")
TRUST_PRISTINE = os.path.join(WORK, "trust.default.json")
LOGFILE = os.path.join(WORK, "tamper-log.jsonl")
STATE = os.path.join(WORK, "server-state.json")
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
    say(" Send lab14-results.txt to the instructor via email or post to class Q&A.")
    rule()
    sys.exit(1)


def reset_state():
    """Start every run from the shipped trust list, no poison and an empty log.

    Without this a second run begins with the server already dropped and
    serve_pinned already true, so the descriptor beat would never block and the
    lab would silently skip its own lesson. Lab 12 hit this with its rule file
    and lab 13 with its policy file; it is cheap to prevent and expensive to
    debug on thirty remote laptops.
    """
    if os.path.exists(TRUST_PRISTINE):
        shutil.copyfile(TRUST_PRISTINE, TRUST)
    for path in (LOGFILE, STATE):
        if os.path.exists(path):
            os.remove(path)


# LAB14_RUN names the run in the tamper log. check.py and evidence.py key on
# these prefixes, so they are part of the contract, not cosmetics.
STEPS = [
    {"why": ["A normal question, answered over MCP. The host checks the server",
             "against its trust list, checks each tool descriptor against the",
             "copy it pinned, then lets the model see them.",
             "This is the baseline: the control not interfering."],
     "cmd": "LAB14_RUN=clean python ask.py", "rc": 0, "want": "4820.55",
     "after": "tamper-log.jsonl"},

    {"why": ["Read the log. Three records, all PASS, one per gate.",
             "ATLAS AML.M0024. A log that only records BLOCKS cannot tell you",
             "the check ran at all - which is why the clean run is step 2."],
     "cmd": "python tamperlog.py", "rc": 0, "want": "gate 2  descriptor pin"},

    {"why": ["The server is compromised. It now appends an instruction to the",
             "RESULT of get_balance, mixed in with the real balance so the tool",
             "still looks like it worked. ATLAS AML.T0110.002.",
             "No model runs here - this is the attacker's move, and it is free."],
     "cmd": "python poison.py --result", "rc": 0, "want": "Runtime Response"},

    {"why": ["Same question, same model, same host. The only thing that changed",
             "is what the server sends back. Watch gate 3."],
     "cmd": "LAB14_RUN=result python ask.py", "rc": 0, "want": "result_off_schema"},

    {"why": ["Now the same attack with the control OFF - which is exactly what",
             "lab 6's client did. This is the run the defence exists to stop.",
             "Note what the assistant does with the appended instruction."],
     "cmd": "LAB14_RUN=undefended python ask.py --no-verify",
     "rc": 0, "want": "PAYMENT WAS MADE"},

    {"why": ["A different poison, and the one that matters most. The server now",
             "returns a DIFFERENT balance. Nothing is appended. Nothing is",
             "malformed. Watch the control pass it."],
     "cmd": "python poison.py --rewrite && LAB14_RUN=rewrite python ask.py",
     "rc": 0, "want": "999999.00"},

    {"why": ["Now the descriptor itself. The server changes the DESCRIPTION of",
             "get_balance - the text the user never sees and the model always",
             "does. ATLAS AML.T0110.000. This is the famous MCP attack."],
     "cmd": "python poison.py --descriptor && LAB14_RUN=swapped python ask.py",
     "rc": 0, "want": "SERVER DROPPED"},

    {"why": ["The diff. This is the finding, and it is the output to paste.",
             "One line, added to help text, by a server you approved last month."],
     "cmd": "python tamperlog.py --diff", "rc": 0, "want": "audit-9931"},

    {"why": ["Recovery, first move: drop the server from the trust list, then",
             "watch WHERE the refusal happens. It should move outward - gate 1,",
             "before a single descriptor is even read."],
     "cmd": "python drop.py && LAB14_RUN=dropped python ask.py --wire-only",
     "rc": 0, "want": "REFUSED before the call was made"},

    {"why": ["Recovery, second move: you reviewed the diff and rejected it, so",
             "re-pin the copy you approved and serve THAT. Then read the",
             "evidence, including the free replay of the clean run."],
     "cmd": "python repin.py && LAB14_RUN=repinned python ask.py "
            "&& python evidence.py",
     "rc": 0, "want": "WHAT THE CONTROL SAW"},
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
    say(" LAB 14 - DEFENDING MCP TOOL CALLS")
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
    say("  You are in /labs/lab14 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every command is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Start here - the control is 80 lines and you should read it:")
    say("      cat verify.py")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - edit trust.json with nano instead of running drop.py and")
    say("      repin.py, and decide for yourself what to pin")
    say("    - pin the POISONED descriptor on purpose, then re-run, and watch")
    say("      the control wave it through. A pin is only as good as the")
    say("      review that produced it")
    say("    - run 'python ask.py --tools' to see the raw descriptors the")
    say("      server advertises, before any check touches them")
    say("    - tighten SHAPES in verify.py so the rewritten balance is caught")
    say("      too, then ask yourself what you had to assume to do it")
    say("")
    say("  The container has no network at all. The MCP server is a local")
    say("  process on 127.0.0.1:8014 and nothing reaches out.")
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
    say(" LAB 14 - DEFENDING MCP TOOL CALLS  (beginner)")
    rule()
    say("")
    say("  Lab 6 put an attacker on the wire between an honest client and an")
    say("  honest MCP server. This lab drops the attacker and compromises the")
    say("  SERVER instead, because that is the real threat model: you connect")
    say("  an agent to software somebody else operates, and that software")
    say("  chooses the text your model reads.")
    say("")
    say("  The question it answers is not 'did the model get tricked'.")
    say("  It is:")
    say("")
    say("    what does the host verify before a tool call runs?")
    say("")
    say("  OWASP  LLM01:2026 Prompt Injection - prevention 10, quoted:")
    say("           'Pin, sign, and verify every MCP server and third-party")
    say("            tool package, audit tool descriptions for hidden")
    say("            instructions, and monitor tool composition.'")
    say("         LLM08:2026 Hidden Context Exposure, risks 1 and 4")
    say("         Agentic cross-map ASI04 - MCP servers and tool registries")
    say("           are ASI04's supply chain, not LLM04's")
    say("  ATLAS  AML.T0084.001 > AML.T0110.000 / AML.T0110.002 >")
    say("           AML.T0051.001 > AML.T0053, with AML.T0109 as the update")
    say("           path. Controls borrowed from AML.M0014 (the pin),")
    say("           M0033 (the schema check), M0024 (the log), M0023 (the")
    say("           trust list). M0013, code signing, is the one we name.")
    say("")
    say("  Read that ATLAS line twice. ATLAS 2026.08 maps NO mitigation to")
    say("  AML.T0110 or to any of its three sub-techniques. Every control in")
    say("  this lab is borrowed from a neighbouring technique, because the")
    say("  defender's own framework has not caught up with this attack yet.")
    say("")
    say("  Ten commands. Everything is local: the MCP server, the host, the")
    say("  model and the log. The container runs with no network at all, and")
    say("  the server binds 127.0.0.1:8014 inside it.")
    say("")
    say("  The 'accounts' are two lines of fake data and the 'payment' is an")
    say("  entry in a list. Nothing here is real and nothing leaves.")

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

        # Content assertions beyond `want`, where the teaching point IS the
        # value. Every one keys on a VERDICT RECORD or the server's own ledger,
        # never on the model's prose - see the note at the top of check.py.
        if i == 4:
            if "result_off_schema" not in out:
                fail("Step 4's poisoned result should have been blocked at "
                     "gate 3. The schema check did not fire.")
            if "PAYMENT WAS MADE" in out:
                fail("Step 4 made a payment. The control did not hold, and "
                     "the lab must not tell you it did.")
            say("  ^ The instruction was in the tool's RESULT, mixed in with a")
            say("    real balance so the call looked like it worked. It never")
            say("    reached the model, so there was nothing to obey.")
        if i == 5:
            if "audit-9931" not in out:
                fail("Step 5 should have shown the assistant paying audit-9931 "
                     "with the control off. The attack did not reproduce, so "
                     "there is nothing for the control to stop.")
            say("  ^ That is the same server, the same question and the same")
            say("    model as step 4. The only difference is one flag on the")
            say("    host. Compare the two tamper-log runs if you want to see")
            say("    the control's absence recorded as plainly as its presence.")
        if i == 6:
            if "result_off_schema" in out:
                fail("Step 6's rewritten balance should have PASSED the "
                     "control. If it was blocked, SHAPES in verify.py has "
                     "drifted and the lab's honest limit is no longer honest.")
            say("  ^ The control passed it, and it is wrong. `balance is")
            say("    999999.00 USD` matches the declared shape perfectly, so")
            say("    gate 3 has nothing to object to.")
            say("    You checked the shape; nobody checked the source.")
            say("    The answer to this is a SIGNED tool call - ATLAS M0013 -")
            say("    which binds a message to who produced it, not to how it")
            say("    is formatted. Lab 6 built that HMAC and watched it work.")
            say("    This lab names it rather than rebuilding it, so that you")
            say("    can see what a schema check alone does and does not buy.")
        if i == 7:
            if "descriptor_changed" not in out:
                fail("Step 7's poisoned descriptor should have been blocked at "
                     "gate 2 by the pin. The hash comparison did not fire.")
            say("  ^ Two things happened and only one of them is the lesson.")
            say("    The pin caught it - that is the control working.")
            say("    And the assistant could not answer at all - that is the")
            say("    control's COST, and it is real. Pinning adds a review")
            say("    step and will block a legitimate update until somebody")
            say("    re-pins it. You are about to be that somebody.")
        if i == 9:
            if "not_in_trust_list" not in out:
                fail("Step 9's refusal should have moved to gate 1, the trust "
                     "list. drop.py did not take effect.")
            say("  ^ Gate 1. Nothing was read, nothing was hashed, nothing was")
            say("    sent. That is what 'refused earlier' looks like, and it")
            say("    is a different control from the one that fired in step 7.")
        if i == 10:
            if "serving YOUR pinned copy" not in out:
                fail("Step 10 should have served the pinned known-good copy. "
                     "repin.py did not take effect.")
            if "4820.55" not in out:
                fail("Step 10 should have restored the correct balance. "
                     "Service did not come back after the re-pin.")
            say("  ^ Service is back, on the descriptor YOU approved rather")
            say("    than the one the server is still advertising. The")
            say("    poisoned text never reached the model in any run where")
            say("    the control was on.")
            say("")
            say("  ^ And look at the replay. Every message the clean run made")
            say("    is still allowed. The tune cost nothing on legitimate")
            say("    traffic - which is the argument you need the first time")
            say("    somebody asks you to turn the check off.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM A REAL DEFENCE")
    rule()
    say("")
    say("   THIS LAB                      PRODUCTION")
    say("   one JSON trust list,          a tool registry with provenance,")
    say("     two tools                     owners and a review process")
    say("   sha256 of a descriptor        signed tool definitions bound to")
    say("                                   an approved version (ETDI,")
    say("                                   Sigstore)")
    say("   one regex per tool shape      full JSON Schema validation, plus")
    say("                                   scanning for imperative language")
    say("   one log file                  a pipeline with retention,")
    say("                                   alerting and a SIEM")
    say("   one hand edit to re-pin       a change process with an owner and")
    say("                                   a target time to close")
    say("   the check runs inside the     an out-of-process vetting gateway")
    say("     host process                  the agent cannot reach")
    say("   one server, two tools         dozens of servers, hundreds of")
    say("                                   tools, and latency is real")
    say("")
    say("   The shape is real. The scale is not. And that last row matters:")
    say("   a validator the compromised server could edit would be lab 6's")
    say("   bug again, one level up.")
    say("")
    rule()
    say(" WHAT TO TAKE AWAY")
    rule()
    say("")
    say("   1. A tool description is not documentation. It is instructions")
    say("      your model reads and your user never sees. Treat it like")
    say("      code: version it, diff it, review the diff.")
    say("   2. Pin the CONTENT, not the version. OWASP says so in its own")
    say("      caveat: pinning 'does not stop tool-description poisoning")
    say("      that leaves the version unchanged'. A hash moves when the")
    say("      text moves. A version number does not.")
    say("   3. Log the PASSes too. The clean run's three PASS records are")
    say("      the only thing that proves the check was running at all.")
    say("   4. Dropping and re-pinning are different moves. One removes the")
    say("      server; the other restores service on terms you chose. Know")
    say("      which is which when you are explaining it afterwards.")
    say("   5. Your control has a shape, and attacks that fit the shape get")
    say("      through. The rewritten balance passed every gate. Knowing")
    say("      exactly what your control does not cover is worth more than")
    say("      believing it covers everything.")
    say("   6. The production answer to the prevent half is bought, not")
    say("      built - signed tool calls through a vetting MCP gateway, such")
    say("      as ETDI's attestation or Sigstore-backed artifact signing.")
    say("      Cursor shipped the cheap version of this lab in v1.3 after")
    say("      CVE-2025-54136: any change to an MCP config, 'including")
    say("      something as small as adding a space', now forces a new")
    say("      approval. It costs a review step on every update, and it is")
    say("      still yours to run and tune. There is no THEY.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")
    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste the output of the last command into the class chat - the")
    say("  whole table - together with the diff from step 8. The line that")
    say("  matters is the 'stopped at' column moving outward while the clean")
    say("  run keeps passing.")
    say("")
    say("  Full transcript saved to lab14-results.txt on your machine.")
    say("")
    rule()
    say(" BEFORE YOU CLOSE THIS")
    rule()
    say("")
    say("  When this window exits, the setup script offers to download the")
    say("  next lab. Say yes - lab 15 is the same dependency tier as this")
    say("  one, so it shares the big model layer and the download is small.")
    say("")


if __name__ == "__main__":
    main()
