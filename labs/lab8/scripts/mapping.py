"""Beat 2 - the only typing in the lab.

Named mapping.py rather than map.py so that `import map` never shadows the builtin in
the runner, which calls run_quiz() in-process. See the note in runner.py.

    python mapping.py                 seven questions, checked
    python mapping.py --worksheet     write worksheet.txt for expert mode
    python mapping.py --grade         grade a worksheet.txt the student filled in

For each lab, name the ONE ATLAS technique that is the lab. Not the whole chain - the
technique that, if you removed it, the attack stops being that attack.

Answers are compared case-insensitively with whitespace collapsed, but the ID itself must
be exact: AML.T0053 and AML.T0051 are different techniques and a recap lab that shrugs at
the difference is not worth running.
"""
import argparse
import re
import lab8lib as L

HINT = {
 "1": "the pathway, not the payload: how did the backdoored model REACH the victim?",
 "2": "the named end state, not the delivery: what was left behind in the corpus?",
 "3": "the instruction arrived inside content the assistant was asked to read.",
 "4": "the instructions were hidden where a human reader could not see them.",
 "5": "the agent used a tool it should never have been able to reach.",
 "6": "you sat on the wire and changed what the tool layer said.",
 "7": "you varied the surface of a beacon to get past a detector.",
}


def normalise(s):
    return re.sub(r"\s+", "", s.strip().upper())


def ask(n, lab, a, auto):
    print()
    L.rule("-")
    print(f" LAB {n} - {lab['title']}")
    L.rule("-")
    print(f"   {lab['oneline']}")
    print(f"   hint: {HINT[n]}")
    print(f"   the chain was: {' > '.join(lab['chain'])}")
    print()
    accepted = [lab["core"]] + lab.get("accepts", [])
    if auto:
        print(f"   [auto mode] {lab['core']}")
        return lab["core"], True
    misses = 0
    while True:
        try:
            raw = input("   which ONE is the lab? > ")
        except (EOFError, KeyboardInterrupt):
            print(f"\n   (no input - filling in {lab['core']})")
            return lab["core"], False
        if not raw.strip():
            continue
        if normalise(raw) in [normalise(x) for x in accepted]:
            extra = ""
            if normalise(raw) != normalise(lab["core"]):
                extra = f"  (and {lab['core']} would also be right)"
            print(f"   correct - {L.tech_name(a, lab['core'])}{extra}")
            return lab["core"], True
        misses += 1
        if misses >= 2:
            print(f"\n   The answer is:  {lab['core']}  {L.tech_name(a, lab['core'])}")
            return lab["core"], False
        print(f"\n   Not quite. The answer should be one of: "
              f"{', '.join(accepted)}\n")


def run_quiz(auto):
    a, c = L.atlas(), L.course()
    L.head("MAP YOUR OWN ATTACKS ONTO ATLAS")
    print("   Seven labs. For each one, name the single ATLAS technique that IS")
    print("   that lab - the one that, if you took it away, the attack stops")
    print("   being that attack.")
    print()
    print("   The full chain is shown for each. Pick from it.")
    answers, right = {}, 0
    for n in sorted(c, key=int):
        ans, ok = ask(n, c[n], a, auto)
        answers[n] = ans
        right += 1 if ok else 0
    L.save_answers(answers)
    L.save_score("map", {"answered": len(answers), "unaided": right})
    print()
    L.rule()
    print(f" {right} of {len(c)} without help.")
    L.rule()
    print()
    print("   Seven attacks, seven techniques, and you have now named all of")
    print("   them in MITRE's vocabulary rather than ours. That is the")
    print("   difference between 'we did a lab about MCP' and a finding your")
    print("   detection team can act on.")
    print()
    return 0


def write_worksheet():
    c = L.course()
    lines = [
        "# LAB 8 WORKSHEET - expert mode",
        "#",
        "# For each lab, write the ONE ATLAS technique that IS that lab, after the",
        "# '=' sign. The full chain each lab taught is shown as a comment.",
        "#",
        "# When you are done:   python mapping.py --grade",
        "#",
    ]
    for n in sorted(c, key=int):
        lab = c[n]
        lines += ["", f"# lab {n} - {lab['title']}",
                  f"#   {lab['oneline']}",
                  f"#   chain: {' > '.join(lab['chain'])}",
                  f"lab{n}="]
    L.WORKSHEET.write_text("\n".join(lines) + "\n")
    print(f"Wrote {L.WORKSHEET}")
    print("Fill it in with:   nano worksheet.txt")
    print("Then grade it with: python mapping.py --grade")
    return 0


def grade():
    a, c = L.atlas(), L.course()
    if not L.WORKSHEET.exists():
        print("No worksheet.txt yet. Create one with:  python mapping.py --worksheet")
        return 1
    given = {}
    for line in L.WORKSHEET.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        m = re.match(r"lab(\d)\s*=\s*(\S+)?$", line)
        if m and m.group(2):
            given[m.group(1)] = m.group(2)
    L.head("WORKSHEET")
    right = 0
    for n in sorted(c, key=int):
        lab = c[n]
        accepted = [lab["core"]] + lab.get("accepts", [])
        got = given.get(n)
        ok = got is not None and normalise(got) in [normalise(x) for x in accepted]
        right += ok
        mark = "  ok  " if ok else ("  --  " if got is None else " WRONG")
        print(f"  {mark}  lab {n}  you: {got or '(blank)':<16} "
              f"answer: {lab['core']}  {L.tech_name(a, lab['core'])}")
    print()
    print(f"  {right} of {len(c)}.")
    print()
    if right == len(c):
        L.save_answers({n: c[n]["core"] for n in c})
    else:
        L.save_answers({n: given.get(n, "") for n in c})
    L.save_score("map", {"answered": len(given), "unaided": right})
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--worksheet", action="store_true")
    ap.add_argument("--grade", action="store_true")
    args = ap.parse_args()
    if args.worksheet:
        return write_worksheet()
    if args.grade:
        return grade()
    return run_quiz(args.auto)


if __name__ == "__main__":
    raise SystemExit(main())
