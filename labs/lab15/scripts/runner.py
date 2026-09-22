#!/usr/bin/env python3
"""
Lab 15 runner. Asks the student to choose beginner or expert mode.

Beginner: shows each command, checks what the student types, corrects a miss,
          runs the real command on a match.
Expert:   drops to a real shell in the lab folder, working from LAB.md.

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command; on a match we run our own known-good copy.

ASSERTIONS KEY ON THE LOG, NOT ON THE SCREEN. Lab 14 broke itself by matching
its own sentence "does not match its pin" and then rewording it during a
cosmetic fix. So every check below reads detect-log.jsonl and tests a rule
token or a number. `want` is kept as a cheap smoke test on a string that is a
LABEL rather than a sentence, and nothing depends on it alone.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

WORK = "/labs/lab15"
RESULTS = os.path.join(WORK, "lab15-results.txt")
DETECTOR = os.path.join(WORK, "detector.json")
DETECTOR_PRISTINE = os.path.join(WORK, "detector.default.json")
LOGFILE = os.path.join(WORK, "detect-log.jsonl")
TRANSIENT = ("estate.json", "collector.log", "detect-log.jsonl",
             "limit-result.json", "evade-result.json")
WIDTH = 70

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
    for line in msg.split("\n"):
        say("   " + line)
    say("")
    say(" This is a problem with the lab, not with anything you did.")
    say(" Send lab15-results.txt to the instructor via email or post to class Q&A.")
    rule()
    sys.exit(1)


def reset_state():
    """Start every run from the shipped detector and an empty estate.

    Without this a second run begins with the threshold already tuned to 4 and
    the window already widened to per-channel, so steps 5 and 9 would have
    nothing to teach and the lab would silently skip its own lesson. Lab 12 hit
    this with its rule file, lab 13 with its policy file, lab 14 with its trust
    list. Three for three; it is cheap to prevent.
    """
    if os.path.exists(DETECTOR_PRISTINE):
        shutil.copyfile(DETECTOR_PRISTINE, DETECTOR)
    for name in TRANSIENT:
        p = os.path.join(WORK, name)
        if os.path.exists(p):
            os.remove(p)


def read_log():
    if not os.path.exists(LOGFILE):
        return []
    with open(LOGFILE, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def last(**match):
    out = None
    for r in read_log():
        if all(r.get(k) == v for k, v in match.items()):
            out = r
    return out


# --------------------------------------------------------------------------
# Step verifiers. Each returns None on success or a message on failure.
# They read the LOG. None of them reads the screen.
# --------------------------------------------------------------------------
def v_baseline():
    sig = last(detector="signature")
    l7 = last(detector="lab7")
    if not sig or not l7:
        return "Step 3 should have logged a signature and a lab7 verdict."
    if sig["caught"] != sig["total"] - 2:
        return (f"The signature rule caught {sig['caught']}/{sig['total']}; it "
                f"should miss exactly two - base64 and hex.")
    if l7["tp"] < 1:
        return "Lab 7's detector should still find the beacon."
    if l7["fp"] < 100:
        return (f"Lab 7's detector produced only {l7['fp']} false positives on "
                f"the estate. This lab's whole premise is that it produces "
                f"many. The estate has drifted.")
    return None


def v_score():
    r = last(kind="detector", detector="score")
    if not r:
        return "Step 4 should have logged a score verdict."
    if r["fp"] < 100:
        return (f"At the shipped threshold the detector produced {r['fp']} "
                f"false positives. It is supposed to be bad here - that is "
                f"what step 5 fixes.")
    return None


def v_sweep():
    r = last(kind="tune", rule="above_threshold")
    if not r:
        return "Step 5 should have written a tuned threshold to the log."
    if r["threshold"] != 4:
        return f"Step 5 set threshold {r['threshold']}, expected 4."
    if r["tp"] < 1 or r["fp"] != 0:
        return (f"At threshold 4 the estate should be TP>=1 / FP=0; got "
                f"TP {r['tp']} / FP {r['fp']}.")
    return None


def v_live():
    r = last(kind="regression")
    if not r:
        return "Step 6 should have logged a regression result."
    if r["fields"] < 4:
        return (f"The freshly generated variant kept only {r['fields']}/"
                f"{r['total']} of the record's values, so the limb missed it. "
                f"That is a real finding rather than a lab bug - tell the "
                f"instructor which format was generated.")
    return None


def v_limit():
    r = last(kind="prevent", rule="volume_cap")
    if not r:
        return "Step 7 should have logged a volume_cap record."
    if r["throttled"] <= 0:
        return "The cap throttled nothing. It is supposed to bite."
    if r["values_delivered"] != 6:
        return (f"Only {r['values_delivered']}/6 of the record reached the "
                f"collector. The lab's point is that the cap throttles the "
                f"traffic and the record leaves anyway.")
    if r["fleet_throttled"] <= 0:
        return "The cap cost the legitimate fleet nothing. It is supposed to."
    return None


def v_evade():
    r = last(run="evade")
    if not r:
        return "Step 8 should have logged an evade verdict."
    if r["rule"] != "below_threshold":
        return ("The split-payload channel was CAUGHT before the tune. It is "
                "supposed to be missed - without the miss there is nothing to "
                "recover from and step 9 has no lesson.")
    if r["fp"] != 0:
        return f"The evasive run produced {r['fp']} false positives; expected 0."
    return None


def v_window():
    r = last(rule="window_per_channel")
    if not r:
        return "Step 9 should have logged a window_per_channel record."
    if r["tp"] < 1:
        return ("Widening the window did not catch the split-payload channel. "
                "The recovery move failed.")
    if r["fp"] != 0:
        return (f"The wider window produced {r['fp']} false positives. It is "
                f"measured at zero - nothing legitimate carries the record.")
    return None


STEPS = [
    {"why": ["You are the SOC now. Build the day's check-in telemetry for a",
             "24-workstation estate: who talked to whom, how often.",
             "Watch the monitoring row and the beacon row."],
     "cmd": "python estate.py --build", "rc": 0, "want": "193 host",
     "after": "estate.json"},

    {"why": ["One workstation has been checking in to an address nothing else",
             "has ever contacted. Here is what landed at that endpoint -",
             "the ten renderings lab 7 measured, replayed as evidence.",
             "You are not generating these. You are receiving them."],
     "cmd": "python inbox.py", "rc": 0, "want": "WHAT A REAL OPERATOR",
     "after": "collector.log"},

    {"why": ["What you have today. First the signature rule most environments",
             "actually run, then lab 7's behavioural detector - the one you",
             "were on the wrong end of - pointed at a real estate instead of",
             "at one channel that was known to be malicious."],
     "cmd": "python detect.py --baseline", "rc": 0,
     "want": "FALSE POSITIVES", "verify": v_baseline},

    {"why": ["Four orthogonal limbs instead of two. Rarity, cadence, volume,",
             "and whether the record's values survive the rendering. Read the",
             "beacon's row, then read user-browsing's."],
     "cmd": "python detect.py --score", "rc": 0, "want": "record_values",
     "verify": v_score},

    {"why": ["Now the actual job: where do you put the line? Every threshold,",
             "priced against the whole estate. Then set it."],
     "cmd": "python detect.py --sweep --set 4", "rc": 0,
     "want": "threshold set to 4", "verify": v_sweep},

    {"why": ["Red-team your own control. Generate a variant that did not exist",
             "when your detector was written, in wording nobody predicted, and",
             "see whether a limb nobody updated still catches it.",
             "This is the only model call in the lab. ~7 s, longer on 2 cores."],
     "cmd": "python variants.py --live json", "rc": 0,
     "want": "record_values limb", "verify": v_live},

    {"why": ["The prevent half: a rate and volume cap in front of the",
             "collector. A real limiter in a real request path. Watch all",
             "three numbers, and then watch the last one."],
     "cmd": "python limit.py --cap 6", "rc": 0,
     "want": "WHAT ACTUALLY GOT OUT", "verify": v_limit},

    {"why": ["The operator noticed. Same host, same record, three changes:",
             "slower, jittered, and split across check-ins.",
             "This one is SUPPOSED to get past you. It is the most useful",
             "step in the lab."],
     "cmd": "python evade.py", "rc": 0, "want": "VERDICT MISSED",
     "verify": v_evade, "after": "evade-result.json"},

    {"why": ["Recovery. You already measured that lowering the threshold only",
             "brings the false positives back, so do not touch it. Change the",
             "matching WINDOW instead: reassemble the channel's day, then",
             "match."],
     "cmd": "python detect.py --window channel", "rc": 0,
     "want": "per channel", "verify": v_window},

    {"why": ["Check your work, then read the bill - yours and theirs."],
     "cmd": "python check.py && python evidence.py", "rc": 0,
     "want": "THE THREE NUMBERS TO SUBMIT"},
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
    say(" LAB 15 - DEFENDING AGAINST AI-SCALED ATTACKS")
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
    say("  You are in /labs/lab15 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every command is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Start here - the four limbs are 20 lines and you should read them:")
    say("      sed -n '/^def limbs/,/^def score/p' lab15lib.py")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - python detect.py --rarity-only")
    say("      Four boolean schemes over the same limbs. One of them is 1 TP")
    say("      and 0 FP and is beaten by jitter that costs the attacker")
    say("      nothing. This is why the detector scores instead of switching.")
    say("    - nano detector.json")
    say("      Change the WEIGHTS, not just the threshold. Try making rarity")
    say("      worth 4 on its own and re-run --score; then explain the 72.")
    say("    - python evade.py --split 1")
    say("      One value per check-in. Harder to split, and still reassembles.")
    say("    - python inbox.py --show")
    say("      Every body the collector holds, which is all a defender gets.")
    say("    - python variants.py --formats")
    say("      The formats measured to work on this model, and the four that")
    say("      were measured and FAIL.")
    say("")
    say("  The container has no network at all. The collector is a local")
    say("  process on 127.0.0.1:8015 and nothing reaches out.")
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
    say(" LAB 15 - DEFENDING AGAINST AI-SCALED ATTACKS  (beginner)")
    rule()
    say("")
    say("  In lab 7 you were the attacker. You asked a model for five")
    say("  renderings of one record, watched a signature rule catch all five,")
    say("  and got past it with two lines of Python that needed no AI at all.")
    say("  Then a behavioural detector caught you anyway and you paid 80x in")
    say("  throughput to go clean.")
    say("")
    say("  That detector had one channel to look at and already knew it was")
    say("  malicious. You are about to point it at an estate.")
    say("")
    say("  The question this lab answers is not 'does behavioural detection")
    say("  work'. It is:")
    say("")
    say("    how many colleagues do you wake up to catch one beacon?")
    say("")
    say("  OWASP  LLM10:2026 Improper Output Handling, scenario #2 - the")
    say("           encoded record sent to an attacker-controlled server")
    say("         LLM02:2026 Sensitive Information Disclosure - OWASP's own")
    say("           cross-map says base64 and hex 'defeat regex and blocklist")
    say("           data-loss filters'. Step 3 measures it")
    say("         LLM06:2026 - cited for its CONTROLS, not its risk. Its")
    say("           prevention 1 is your rate limit and its prevention 8 is")
    say("           'establish baselines of normal tool behavior'. The RISK")
    say("           it describes points the other way, at your own inference")
    say("           bill, and this lab is about traffic leaving. Say the")
    say("           mismatch out loud rather than forcing the fit")
    say("  ATLAS  counters AML.T0016.002 > AML.T0043.003 > AML.T0015 Evade AI")
    say("           Model. Controls: AML.M0004 (the rate limit, whose own")
    say("           text warns it 'may not protect against attacks that")
    say("           require few requests'), AML.M0024 (the log), AML.M0006")
    say("           (orthogonality). AML.M0039 AI Honeypots (added in ATLAS")
    say("           v2026.09) is the one we name but do not build.")
    say("")
    say("  Read that ATLAS line twice. Five of the seven mitigations ATLAS maps")
    say("  to AML.T0015 begin with the word 'Predictive' - they all assume you")
    say("  OWN the model being evaded and tell you to harden it. Not one of")
    say("  them is 'detect on a behavioural invariant outside the model',")
    say("  which is what a SOC facing AI-varied traffic actually does and what")
    say("  you are about to build. The framework has not caught up.")
    say("")
    say("  Ten commands. The estate is generated by the lab from fixed seeds -")
    say("  the SHAPE is real, the exact numbers are this generator's. One")
    say("  model call, everything else deterministic Python. The container")
    say("  has no network and the collector binds 127.0.0.1:8015 inside it.")

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
        verify = step.get("verify")
        if verify:
            problem = verify()
            if problem:
                fail(f"Step {i}: {problem}")

        # The impact statements. Every one is marked ^ and every one is keyed
        # to a NUMBER that just came out of the log, not to a sentence.
        if i == 1:
            say("  ^ The monitoring agent checks in 1441 times a day at cv")
            say("    0.011. The beacon checks in 1440 times at cv 0.000. On")
            say("    cadence they are the same traffic. One of them is yours.")
        if i == 3:
            l7 = last(detector="lab7")
            sig = last(detector="signature")
            say(f"  ^ The signature rule caught {sig['caught']} of "
                f"{sig['total']}. The two it missed were")
            say("    base64 and hex - the two the model could not write. The")
            say("    evasion that worked was free and needed no AI.")
            say("")
            say(f"  ^ Lab 7's behavioural detector: {l7['tp']} true positive, "
                f"{l7['fp']} false")
            say(f"    positives, precision {l7['precision']}. It is not broken.")
            say("    It is 100% recall, and on an estate that is the same thing")
            say("    as useless, because nobody reads 144 alerts a day twice.")
        if i == 5:
            r = last(kind="tune", rule="above_threshold")
            say(f"  ^ {r['fp']} false positives at threshold {r['threshold']}, "
                f"down from 144.")
            say("    You did not turn anything up. You asked four independent")
            say("    questions and required more than one answer.")
            say("")
            say("  ^ And look at the second table. Lab 7's dial, swept to catch")
            say("    a slow channel, peaks at 0.0127 and then gets worse. A")
            say("    threshold on ONE dimension cannot buy precision at any")
            say("    setting. That is the difference between tuning and design.")
        if i == 6:
            r = last(kind="regression")
            say(f"  ^ {r['fields']} of 6 values survived a rendering that did "
                f"not exist")
            say("    when your limb was written. The limb was not updated. The")
            say("    record is what the attacker NEEDED to send, so the record")
            say("    is what survives every rendering - including ones nobody")
            say("    has thought of yet.")
            say("")
            say("  ^ Note what this lab just checked: the field count, not the")
            say("    model's sentence. Lab 13 measured a model stating it had")
            say("    verified something it never did. Assert on structure.")
        if i == 7:
            r = last(kind="prevent", rule="volume_cap")
            say(f"  ^ The cap stopped {r['throttled']} of {r['sent']} check-ins "
                f"and cost")
            say(f"    {r['fleet_throttled']} legitimate channels their traffic - "
                f"and all 6 of the")
            say("    record's values reached the collector anyway.")
            say("")
            say("  ^ That is why prevention is the stub and detection leads.")
            say("    Not an opinion - ATLAS AML.M0004 says it in its own text,")
            say("    and OWASP LLM06 says 'traditional request-rate limiting")
            say("    alone is no longer sufficient'. You just measured both.")
        if i == 8:
            r = last(run="evade")
            say(f"  ^ Score {r['score']}, threshold {r['threshold']}, missed. "
                f"Three limbs went")
            say("    dark and the fourth is not worth 4 on its own - on purpose,")
            say("    because 72 innocent browsing channels are also rare.")
            say("")
            say("  ^ Do not reach for the threshold. You measured that already:")
            say("    threshold 3 is 72 false positives. The dial is not the fix,")
            say("    and knowing that BEFORE you touch it is the whole of step 5.")
        if i == 9:
            r = last(rule="window_per_channel")
            say(f"  ^ Caught, and still {r['fp']} false positives. The wider")
            say("    window cost nothing, because no legitimate channel carries")
            say("    the record's values at all.")
            say("")
            say("  ^ The tune was not a number. It was WHERE you looked: lab 7")
            say("    told you to normalise before you match, and this is that")
            say("    advice extended from format to time.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM A REAL DEFENCE")
    rule()
    say("")
    say("   THIS LAB                      PRODUCTION")
    say("   193 channels, one synthetic   millions of flows, continuously,")
    say("     day, fixed seed               over months of baseline")
    say("   the estate is generated by    the estate is the estate, and")
    say("     the lab                       nobody labelled it")
    say("   one channel is malicious      nothing is labelled; precision is")
    say("     and you were told             estimated from triage")
    say("   four limbs, hand-weighted     RITA-class scoring plus EDR plus")
    say("                                   DNS plus identity")
    say("   the tune is one edit          a change ticket, an owner and a")
    say("                                   target time to close")
    say("   0 false positives             there is no such thing. There is")
    say("                                   a budget, and somebody owns it")
    say("")
    say("   The shape is real. The scale is not, and neither is the luxury")
    say("   of knowing the answer.")
    say("")
    rule()
    say(" WHAT TO TAKE AWAY")
    rule()
    say("")
    say("   1. Recall without precision is not a control. 144 alerts a day to")
    say("      find one beacon is a detector that will be switched off by")
    say("      March, and then you have neither.")
    say("   2. Key on what the attacker CANNOT drop. Wording is free to vary;")
    say("      the record is the thing they needed to send. That is why a limb")
    say("      written before a variant existed still catches it.")
    say("   3. Orthogonal beats tight. One dimension turned up never got past")
    say("      0.0127 precision. Four independent questions got to 1.0000.")
    say("   4. Ask the right cadence question. 'Is this a timer' loses to free")
    say("      jitter. 'Is this not a person' does not, because bounded jitter")
    say("      is still bounded - 0.543 against a human's 4.482.")
    say("   5. When you miss something, change the control, not the dial. The")
    say("      dial was already measured and it costs 72 colleagues.")
    say("   6. Price your detector in both currencies. What it costs the")
    say("      attacker - 864x slower - and what it costs you - how many")
    say("      alerts. A defender who can only quote the first one loses the")
    say("      budget meeting.")
    say("   7. The good news, measured. Unit 42, August 2026: seven")
    say("      LLM-assisted malware variants built in six days, and behavioural")
    say("      detection and endpoint analytics caught all seven. Their words:")
    say("      'The AI component does not evade detection.' Cheap variation is")
    say("      real, and it loses to defenders who key on behaviour. You just")
    say("      built the small version of why.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")
    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Paste the three numbers from the last command into the class chat:")
    say("  lab 7's detector on a real estate, yours after tuning, and what")
    say("  evasion cost the attacker.")
    say("")
    say("  Full transcript saved to lab15-results.txt on your machine.")
    say("")
    rule()
    say(" BEFORE YOU CLOSE THIS")
    rule()
    say("")
    say("  Lab 16 is the last one and it is different: the red-team process")
    say("  that VALIDATES the controls you built in labs 9 to 15. It is")
    say("  instructor demo material and a take-home runbook, not a container")
    say("  to pull, so there is nothing to download here.")
    say("")
    say("  Step 6 was a one-command version of it: you attacked your own")
    say("  control with an input it had never seen. ATLAS calls that")
    say("  AML.M0035, AI Red Team, and its advice is to 'convert confirmed")
    say("  failures into regression tests, detection logic, monitoring")
    say("  requirements'. That is exactly what step 9 was.")
    say("")
    say("  Make sure you have submitted evidence for labs 9 through 15.")
    say("")


if __name__ == "__main__":
    main()
