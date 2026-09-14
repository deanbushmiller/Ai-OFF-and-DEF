"""Beats 3, 4 and 5 - the ATLAS coverage picture.

    python coverage.py            the matrix, with your labs on it
    python coverage.py --gaps     the four tactics you never touched, and why
    python coverage.py --spine    the one technique that runs through the course

Reads MITRE's data (/opt/lab-assets/atlas/atlas.json) and this course's answer key
(course.json). Prints no opinion that is not derived from one of those two.
"""
import argparse
import lab8lib as L

# Why each untouched tactic is untouched. These are design decisions with reasons, not
# omissions, and the Exfiltration one is the most important sentence in the lab.
WHY_NOT = {
    "AML.TA0000": ("AI Model Access",
                   "Every lab already handed you the model, locally, with full access.",
                   "There was nothing to gain access TO."),
    "AML.TA0013": ("Credential Access",
                   "Ruled out in writing by every lab's safety limits:",
                   "'no real credential theft'. Not an oversight - a boundary."),
    "AML.TA0015": ("Lateral Movement",
                   "Needs more than one host. Every lab is a single container",
                   "on your own machine, by design."),
    "AML.TA0010": ("Exfiltration",
                   "A SAFETY DECISION, TAKEN FOUR TIMES.",
                   ""),
}

EXFIL = [
 "   An external endpoint was proposed at lab 3, reconsidered at labs 5 and 6,",
 "   and closed permanently at lab 7. The reasoning was the same every time:",
 "",
 "     - no lab needed it. Every teaching point survived a local endpoint.",
 "     - it breaks the offline rule that lets you do these labs on a plane.",
 "     - one expired certificate and every remote student fails at once.",
 "     - and the one that settled it: you are security professionals on work",
 "       laptops. A machine that runs a 'hacking lab' and then beacons to an",
 "       unfamiliar domain is the TEXTBOOK EDR detection. Lab 7 would have had",
 "       you tuning the check-in interval of a real one. It would have filed",
 "       incident tickets at your employers, by design.",
 "",
 "   So lab 7 printed what a real operator's endpoint WOULD have received, and",
 "   stopped there. The empty column is the lesson: designing a safe lab means",
 "   deciding what you will NOT demonstrate, and saying why.",
]


def show_matrix(a, c):
    covered = L.covered_tactics(a, c)
    techs = L.all_course_techniques(c)
    L.head("YOUR COVERAGE OF THE MITRE ATLAS MATRIX")
    print(f"   {len(techs)} distinct techniques across 7 labs.")
    print(f"   {len(covered)} of {len(a['tactics'])} ATLAS tactics.\n")
    per = {}
    for t in techs:
        for tac in a["techniques"].get(t, {}).get("tactics", []):
            per.setdefault(tac, []).append(t)
    for tac in a["tactic_order"]:
        name = a["tactics"][tac]["name"]
        hits = per.get(tac, [])
        mark = "[X]" if hits else "[ ]"
        print(f"   {mark} {tac}  {name:<24} {len(hits) or '':>2}"
              + (f"  {', '.join(sorted(hits))}" if hits else ""))
    print()
    print("   That is a coverage map. It is the same artifact a security team")
    print("   builds for its own estate - which techniques are we exposed to,")
    print("   which do we detect - and you just built one from attacks you ran")
    print("   yourself.")
    print()
    L.save_score("coverage", {"techniques": len(techs), "tactics": len(covered),
                              "tactics_total": len(a["tactics"])})


def show_gaps(a, c):
    covered = L.covered_tactics(a, c)
    missing = [t for t in a["tactic_order"] if t not in covered]
    L.head("THE FOUR TACTICS YOU NEVER TOUCHED")
    print("   An empty column on a coverage map is a question, not a verdict.")
    print("   Here are the answers.\n")
    for tac in missing:
        name, line1, line2 = WHY_NOT.get(tac, (a["tactics"][tac]["name"], "", ""))
        print(f"   {tac}  {name}")
        if line1:
            print(f"       {line1}")
        if line2:
            print(f"       {line2}")
        print()
    if "AML.TA0010" in missing:
        for line in EXFIL:
            print(line)
        print()
    L.save_score("gaps", {"missing": missing})


def show_spine(a, c):
    freq = L.technique_frequency(c)
    ranked = sorted(freq.items(), key=lambda x: (-len(x[1]), x[0]))
    L.head("THE SPINE OF THE COURSE")
    print("   Seven labs that felt completely different. Here is how much they")
    print("   actually had in common.\n")
    print(f"   {'labs':>4}  {'technique':<16} {'':<44}")
    for t, labs in ranked:
        if len(labs) < 2:
            continue
        print(f"   {len(labs):>4}  {t:<16} {L.tech_name(a, t):<44} {labs}")
    singles = [t for t, l in ranked if len(l) == 1]
    print(f"\n   {len(singles):>4}  techniques appear in exactly one lab\n")
    top, labs = ranked[0]
    print(f"   {top} - {L.tech_name(a, top)} - is in {len(labs)} of the 7.")
    print()
    print("   If you remember one identifier from this entire course, that is")
    print("   the one. Indirect prompt injection is not one attack among many;")
    print("   it is the delivery mechanism for most of them. The payload")
    print("   changed every time. The way it arrived did not.")
    print()
    L.save_score("spine", {"technique": top, "labs": labs})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gaps", action="store_true")
    ap.add_argument("--spine", action="store_true")
    args = ap.parse_args()
    a, c = L.atlas(), L.course()
    if args.gaps:
        show_gaps(a, c)
    elif args.spine:
        show_spine(a, c)
    else:
        show_matrix(a, c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
