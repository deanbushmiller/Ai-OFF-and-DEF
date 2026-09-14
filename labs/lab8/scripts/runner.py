#!/usr/bin/env python3
"""
Lab 8 runner. Asks the student to choose beginner or expert mode.

Beginner: the guided path - shows each step, checks what the student types,
          corrects a miss, runs the real step on a match.
Expert:   drops to a real shell in the lab folder. The student fills in
          worksheet.txt with nano and grades it themselves.

This is the recap lab. There is no model and no attack: every step is instant, and
the 12-15 minutes is reading and thinking rather than waiting on a CPU.

SECURITY NOTE: nothing the student types is ever executed. Their input is only
compared to the expected command; on a match we run our own known-good copy.
"""
import argparse
import contextlib
import json
import os
import re
import subprocess
import sys

WORK = "/labs/lab8"
RESULTS = os.path.join(WORK, "lab8-results.txt")
SCORE = os.path.join(WORK, "score.json")
ANSWERS = os.path.join(WORK, "answers.json")
LAYER = os.path.join(WORK, "atlas-layer.json")
WORKSHEET = os.path.join(WORK, "worksheet.txt")
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
    say(" Send lab8-results.txt to the instructor through GitHub.")
    rule()
    sys.exit(1)


def recorded(key, field):
    if not os.path.exists(SCORE):
        return None
    try:
        return json.loads(open(SCORE).read()).get(key, {}).get(field)
    except (ValueError, OSError):
        return None


STEPS = [
    {"why": ["Eight hours of work, on one screen. Read it before you map it -",
             "the point of this lab is seeing seven separate labs as one thing."],
     "cmd": "python recap.py", "rc": 0, "want": "LAB 7",
     "asserts": [("recap", "labs", 7)]},

    {"why": ["The only typing in this lab. For each of the seven, name the ONE",
             "ATLAS technique that IS that lab. The full chain is shown; pick",
             "from it. Seven answers, checked as you go."],
     "cmd": "python mapping.py", "rc": 0, "want": "of 7",
     "asserts": [("map", "answered", 7)]},

    {"why": ["Now put them on the matrix. This is a coverage map - the same",
             "artifact a security team builds for its own estate."],
     "cmd": "python coverage.py", "rc": 0, "want": "ATLAS tactics",
     "asserts": [("coverage", "techniques", 20), ("coverage", "tactics", 12)]},

    {"why": ["Four columns are empty. An empty column on a coverage map is a",
             "question, not a verdict - so here are the answers."],
     "cmd": "python coverage.py --gaps", "rc": 0, "want": "Exfiltration"},

    {"why": ["Seven labs that felt completely different. Here is how much they",
             "actually had in common."],
     "cmd": "python coverage.py --spine", "rc": 0, "want": "AML.T0051.001",
     "asserts": [("spine", "technique", "AML.T0051.001")]},

    {"why": ["Switch sides. These are the controls MITRE itself names for the",
             "techniques you used - real ATLAS mitigation IDs, not our advice."],
     "cmd": "python defend.py", "rc": 0, "want": "AML.M0024"},

    {"why": ["And the honest part. For a good fraction of what you attacked,",
             "MITRE publishes no control at all. Look at WHICH ones."],
     "cmd": "python defend.py --gaps", "rc": 0, "want": "part 2",
     "asserts": [("gaps_defence", "unmitigated", 9)]},

    {"why": ["Your evidence, in a format the rest of the industry already reads:",
             "an ATLAS Navigator layer file you can load at atlas.mitre.org."],
     "cmd": "python export.py", "rc": 0, "want": "atlas-layer.json",
     "asserts": [("export", "techniques", 20)]},
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


class _Tee:
    """Write to the terminal and the transcript at once.

    Needed because the quiz runs IN-PROCESS (see run_quiz_inline) and therefore
    prints through the same stdout the runner is logging.
    """

    def __init__(self, stream, log):
        self._stream, self._log = stream, log

    def write(self, s):
        self._stream.write(s)
        self._log.write(s)
        return len(s)

    def flush(self):
        self._stream.flush()
        self._log.flush()

    def isatty(self):
        return self._stream.isatty()


def run_quiz_inline():
    """Step 2 asks the student seven questions, and it must NOT be a subprocess.

    MEASURED THE HARD WAY: with the quiz as a child process, the runner's own
    input() and the child's input() are two readers on one stdin. On a terminal
    that happens to work, because input() does not read ahead. On a PIPE - which
    is how every scripted test of the typed path runs - the parent's buffered
    read swallows the answers meant for the child, and the lab reports "0 of 7"
    and "You typed 2 of 8" while looking fine to a human.

    One process, one reader. Importing it also means the quiz's prompts land in
    the transcript, which the subprocess version lost.
    """
    import mapping
    with contextlib.redirect_stdout(_Tee(sys.stdout, _log)):
        return mapping.run_quiz(False)


def run(cmd, interactive=False):
    say("")
    say("  $ " + cmd)
    say("  " + "-" * (WIDTH - 2))
    if interactive:
        rc = run_quiz_inline()
        say("")
        return rc, _reread()
    p = subprocess.run(cmd, shell=True, cwd=WORK, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    for line in out.rstrip("\n").split("\n"):
        say("  " + line)
    say("")
    return p.returncode, out


def _reread():
    """An interactive step prints straight to the terminal, so the assertions read
    the recorded state instead of captured text."""
    try:
        return open(SCORE).read()
    except OSError:
        return ""


def choose_mode(auto):
    if auto:
        return "1"
    rule()
    say(" LAB 8 - OFFENSIVE RECAP AND TRANSITION TO DEFENSE")
    rule()
    say("")
    say("  Choose your mode:")
    say("    [1] Beginner  - the lab shows each command; you type or paste")
    say("                    it and it is checked")
    say("    [2] Expert    - you fill in the mapping yourself in a shell,")
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
    say("  You are in /labs/lab8 with a real shell.")
    say("")
    say("  Your guide is LAB.md in this folder. Run:   less LAB.md")
    say("  Every step is listed there. Expert runs the whole list;")
    say("  beginner mode only runs the ones marked with a B.")
    say("")
    say("  Expert-only steps beginner skips:")
    say("    - fill the mapping in BY HAND, with no multiple choice:")
    say("        python mapping.py --worksheet")
    say("        nano worksheet.txt")
    say("        python mapping.py --grade")
    say("      The worksheet shows each lab's full ATLAS chain and asks you for")
    say("      the one technique that IS that lab. No hints, no second try.")
    say("    - read course.json. It is this lab's answer key, and it was")
    say("      GENERATED from labs 1-7 rather than typed - it refuses to contain")
    say("      a technique your own labs never showed you.")
    say("    - cat /opt/lab-assets/atlas/atlas.json | python -m json.tool | less")
    say("      That is MITRE ATLAS, distilled at build time. Everything this lab")
    say("      claims about mitigations comes out of that file.")
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
    for f in (SCORE, ANSWERS, LAYER, WORKSHEET):
        if os.path.exists(f):
            os.remove(f)


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

    # The answer key is checked BEFORE anything is taught. A key that disagrees
    # with MITRE's data, or with itself, must never reach a student - and the
    # step assertions alone did not catch a swapped core technique.
    sys.path.insert(0, WORK)
    import lab8lib
    bad = lab8lib.validate(lab8lib.atlas(), lab8lib.course())
    if bad:
        fail("The answer key does not hold up:\n     "
             + "\n     ".join(bad)
             + "\n\n   course.json is generated by lab-research/lab8/gen_course.py."
               "\n   Re-run it against labs 1-7 rather than editing it by hand.")

    rule()
    say(" LAB 8 - OFFENSIVE RECAP AND TRANSITION TO DEFENSE  (beginner)")
    rule()
    say("")
    say("  The question this lab answers:")
    say("    You have attacked seven things. What does that add up to?")
    say("")
    say("  There is no attack in this lab. You take the seven attacks you ran")
    say("  yourself and turn them into a defender's map: an ATLAS coverage")
    say("  picture, the controls MITRE names for them, and an honest account of")
    say("  where the published guidance runs out.")
    say("")
    say("  THIS IS THE FIRST HALF OF A TWO-PART COURSE. Part 2 is seven")
    say("  defender labs over the same ground from the other side. So this lab")
    say("  NAMES the controls and stops there - it is an introduction, and")
    say("  anything more would feel like enough when it is not.")
    say("")
    say("  ATLAS  the full matrix, at /opt/lab-assets/atlas/atlas.json")
    say("         20 techniques, 12 of 16 tactics, across your seven labs")
    say("  OWASP  8 of the 10 entries in the 2026 list")
    say("")
    say("  Eight steps. No model, nothing to wait for - the time is reading")
    say("  time. Everything is local and the container has no network.")

    total = len(STEPS)
    typed = 0
    for i, step in enumerate(STEPS, 1):
        how = ask_step(step, i, total, args.challenge, args.auto)
        if how == "typed":
            typed += 1
        # Step 2 is a conversation with the student, not a command with output, so
        # it needs the real stdin and must not have its output captured.
        is_map = step["cmd"] == "python mapping.py"
        interactive = is_map and not args.auto
        cmd = step["cmd"] + (" --auto" if is_map and args.auto else "")
        rc, out = run(cmd, interactive=interactive)

        if step.get("rc") is not None and rc != step["rc"]:
            fail(f"Step {i} ({cmd}) returned {rc}, expected {step['rc']}.")
        want = step.get("want")
        if want and not interactive and want not in out:
            fail(f"Step {i} output should have contained {want!r}. "
                 f"The lab did not behave as designed.")
        for key, field, expected in step.get("asserts", ()):
            got = recorded(key, field)
            if got != expected:
                fail(f"Step {i}: score.json[{key!r}][{field!r}] is {got!r}, "
                     f"expected {expected!r}. The answer key and the ATLAS data "
                     f"have drifted apart.")

        if i == 1:
            say("  ^ Seven labs, seven ways in, and not one of them was theory.")
            say("    Hold that list in your head for the next seven minutes.")
        if i == 2:
            unaided = recorded("map", "unaided")
            say(f"  ^ You named {unaided} of 7 without help. The number matters less")
            say("    than the vocabulary: 'we did a lab about MCP' is a story, and")
            say("    'AML.T0110, AI Agent Tool Poisoning' is something your")
            say("    detection team can actually search for.")
        if i == 3:
            say("  ^ That is a coverage map, and you built it from attacks you ran")
            say("    rather than from a vendor's slide. 12 of 16 tactics is a lot")
            say("    of ground for eight hours.")
        if i == 4:
            say("  ^ Read the Exfiltration one again. Nothing in this course ever")
            say("    sent data to an external endpoint, and that was decided four")
            say("    separate times, on purpose. Designing a safe lab means")
            say("    choosing what you will NOT demonstrate - and saying why.")
        if i == 5:
            say("  ^ Five of seven. Indirect prompt injection is not one attack")
            say("    among many; it is how most of the others were delivered. The")
            say("    payload changed every time. The way it arrived did not.")
            say("  ^ If you remember one identifier from this course, that is it.")
        if i == 6:
            say("  ^ Two controls cover five of your seven labs, and notice how")
            say("    unglamorous they are: log what the model and its tools did,")
            say("    and validate what crosses every boundary. Not a product. Not")
            say("    a filter. The two things that have defended every other kind")
            say("    of system for thirty years.")
        if i == 7:
            n = recorded("gaps_defence", "unmitigated")
            say(f"  ^ {n} of your 20 techniques have NO published mitigation, and")
            say("    every one of them is new. The ones that DO have controls are")
            say("    the older, classical machine-learning attacks.")
            say("  ^ The defensive literature is about a year behind the offensive")
            say("    literature. That is not a criticism of MITRE - it is what the")
            say("    field looks like right now, and it is why part 2 exists.")
        if i == 8:
            say("  ^ That file loads into the real ATLAS Navigator at")
            say("    atlas.mitre.org/navigator. It is a professional artifact, it")
            say("    is yours, and it took eight hours of attacking to earn it.")

    say("")
    rule()
    say(" HOW THIS DIFFERS FROM REAL PRACTICE")
    rule()
    say("")
    say("   THIS LAB                      A REAL COVERAGE MAP")
    say("   seven lab exercises           your estate's actual systems")
    say("   techniques you were taught    techniques found by threat intel")
    say("   MITRE's published controls    the controls YOU have deployed")
    say("   scored by lab count           scored by detection confidence")
    say("")
    say("   The method is the same and it is the part worth keeping. The inputs")
    say("   are the part you go and get on Monday.")
    say("")
    rule()
    say(" WHAT PART 1 ADDS UP TO")
    rule()
    say("")
    say("   1. The model believes what it reads. Labs 2, 3 and 4 were three")
    say("      different delivery routes for one idea.")
    say("   2. The model does what it is PERMITTED to do, not what you intended.")
    say("      Labs 5 and 6.")
    say("   3. Nothing on the wire between a model and its tools is")
    say("      authenticated unless you authenticate it. Lab 6.")
    say("   4. An attacker with an LLM is good at exactly the part defenders")
    say("      stopped keying on years ago. Lab 7.")
    say("   5. And the supply chain was already a solved problem that nobody")
    say("      solved. Lab 1.")
    say("")
    say("   The defensive answer to most of that, today, is: log what happened,")
    say("   and validate what crosses a boundary. Part 2 is where you build it.")
    say("")
    say(f"   You typed {typed} of {total} commands correctly.")
    say("")
    rule()
    say(" PROOF OF COMPLETION")
    rule()
    say("")
    say("  Submit atlas-layer.json - or a screenshot of it loaded in the ATLAS")
    say("  Navigator at atlas.mitre.org/navigator - through the class chat or")
    say("  GitHub. The README has the steps.")
    say("")
    say("  Full transcript saved to lab8-results.txt on your machine.")
    say("")
    rule()
    say(" THAT IS THE END OF PART 1")
    rule()
    say("")
    say("  Eight labs. You have attacked a model supply chain, a RAG corpus, a")
    say("  web-reading assistant, an OCR pipeline, an agent's tool layer, an MCP")
    say("  channel, and a detector - and then mapped the lot.")
    say("")
    say("  Check you have submitted evidence for all eight before you go.")
    say("")
    say("  Part 2 is the other half: seven defender labs, starting with")
    say("  semantic firewalls and RAG validation and ending with automated")
    say("  red teaming.")
    say("")


if __name__ == "__main__":
    main()
