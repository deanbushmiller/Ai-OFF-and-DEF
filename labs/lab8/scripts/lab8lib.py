"""Shared loading and lookup for lab 8. No third-party imports anywhere in this lab.

Two data files, and the difference between them matters:

  /opt/lab-assets/atlas/atlas.json   MITRE's data, distilled at build time. Not ours.
  /labs/lab8/course.json             what THIS COURSE taught, generated from the labs.

course.json was produced by lab-research/lab8/gen_course.py, which reads every
student-facing file of labs 1-7 (runner.py, LAB.md, README.md) and refuses to emit a key
containing any technique the student was never shown. That matters because the
lab-research review files disagree with the shipped labs in two places - lab 1's OWASP
numbering and lab 4's ATLAS chain - and a recap lab that marked a correct answer wrong
would be worse than no recap lab at all.
"""
import json
import pathlib

WORK = pathlib.Path("/labs/lab8")
ATLAS_PATH = pathlib.Path("/opt/lab-assets/atlas/atlas.json")
COURSE_PATH = WORK / "course.json"
ANSWERS = WORK / "answers.json"
SCORE = WORK / "score.json"
LAYER = WORK / "atlas-layer.json"
WORKSHEET = WORK / "worksheet.txt"

WIDTH = 68


def atlas():
    return json.loads(ATLAS_PATH.read_text())


def course():
    """The seven labs. course.json also carries part2_order alongside them."""
    return json.loads(COURSE_PATH.read_text())["labs"]


def part2_order():
    """The order part 2 is actually taught in.

    Deliberately separate from each lab's `part2` counterpart, because the two are
    NOT the same ordering and the instructor was explicit about it on 2026-09-14:
    "these do not need to map directly to the previous day, but that is the correct
    order". Lab 2's counterpart is part 2's first lab; lab 1's is its fourth.
    """
    return json.loads(COURSE_PATH.read_text()).get("part2_order", [])


def tech_name(a, tid):
    """Full name, parent included, the way MITRE writes it."""
    t = a["techniques"].get(tid)
    if not t:
        return "(unknown technique)"
    if t.get("parent"):
        return f"{a['techniques'][t['parent']]['name']}: {t['name']}"
    return t["name"]


def all_course_techniques(c):
    seen = []
    for n in sorted(c, key=int):
        for t in c[n]["chain"]:
            if t not in seen:
                seen.append(t)
    return seen


def covered_tactics(a, c):
    out = set()
    for t in all_course_techniques(c):
        out |= set(a["techniques"].get(t, {}).get("tactics", []))
    return out


def technique_frequency(c):
    freq = {}
    for n in sorted(c, key=int):
        for t in set(c[n]["chain"]):
            freq.setdefault(t, []).append(int(n))
    return freq


def mitigation_coverage(a, c):
    """Which labs each ATLAS mitigation touches, via the techniques those labs used."""
    per = {}
    for n in sorted(c, key=int):
        for t in c[n]["chain"]:
            for m in a["techniques"].get(t, {}).get("mitigations", []):
                per.setdefault(m, set()).add(int(n))
    return {m: sorted(v) for m, v in per.items()}


def unmitigated(a, c):
    return [t for t in all_course_techniques(c)
            if not a["techniques"].get(t, {}).get("mitigations")]


def load_answers():
    if ANSWERS.exists():
        try:
            return json.loads(ANSWERS.read_text())
        except ValueError:
            pass
    return {}


def save_answers(d):
    ANSWERS.write_text(json.dumps(d, indent=2))


def save_score(key, value):
    d = {}
    if SCORE.exists():
        try:
            d = json.loads(SCORE.read_text())
        except ValueError:
            d = {}
    d[key] = value
    SCORE.write_text(json.dumps(d, indent=2))


def rule(ch="="):
    print(ch * WIDTH)


def head(title):
    rule()
    print(f" {title}")
    rule()
    print()


def validate(a, c):
    """Is the answer key still consistent with itself and with MITRE's data?

    FOUND BY SABOTAGE, 2026-09-14. Changing one lab's `core` to another lab's
    technique produced a completely green run: every step passed, and the lab
    taught a wrong answer without a murmur. The step assertions only counted
    techniques and tactics, and a swapped core changes neither.

    Three invariants, all cheap:
      1. every technique in every chain exists in MITRE's data
      2. each lab's core technique is IN that lab's own chain
      3. the seven cores are seven DIFFERENT techniques - which is what makes
         "the one technique that IS this lab" a meaningful question at all

    Returns a list of problems, empty when the key is sound.
    """
    problems = []
    for n in sorted(c, key=int):
        lab = c[n]
        for tid in lab["chain"]:
            if tid not in a["techniques"]:
                problems.append(f"lab {n}: {tid} is not in the ATLAS data")
        if lab["core"] not in lab["chain"]:
            problems.append(
                f"lab {n}: core {lab['core']} is not in that lab's own chain")
    cores = [c[n]["core"] for n in sorted(c, key=int)]
    dupes = {x for x in cores if cores.count(x) > 1}
    for d in sorted(dupes):
        labs = [n for n in sorted(c, key=int) if c[n]["core"] == d]
        problems.append(
            f"{d} is the core technique of more than one lab ({', '.join(labs)}) - "
            "each lab's core must be the technique unique to it")
    return problems
