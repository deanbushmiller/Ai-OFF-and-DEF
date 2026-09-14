"""Expert-mode self-check.

    python check.py

Beginner mode asserts as it goes and cannot finish in a wrong state. Expert mode has no
rails: the student filled worksheet.txt by hand and ran the pieces in their own order.
This says whether the recap actually holds together.

It checks the recorded numbers, not screen text.
"""
import json
import lab8lib as L

OK, BAD = "  PASS  ", "  FAIL  "
problems = []


def check(label, cond, hint):
    print((OK if cond else BAD) + label)
    if not cond:
        problems.append(hint)


def main():
    a, c = L.atlas(), L.course()
    print("=" * 68)
    print(" LAB 8 SELF-CHECK")
    print("=" * 68)
    print()

    if not L.SCORE.exists():
        print("No score.json. Run at least these:")
        print("    python recap.py")
        print("    python mapping.py --worksheet   (then nano worksheet.txt)")
        print("    python mapping.py --grade")
        print("    python coverage.py")
        print("    python defend.py --gaps")
        print("    python export.py")
        return 1

    s = json.loads(L.SCORE.read_text())
    answers = L.load_answers()

    check("the recap ran", bool(s.get("recap")), "run: python recap.py")

    check("you mapped all seven labs",
          len(answers) == len(c),
          f"only {len(answers)} of {len(c)} answered - run: python mapping.py --grade "
          "(after filling in worksheet.txt), or python mapping.py")

    wrong = [n for n in sorted(c, key=int)
             if answers.get(n) not in [c[n]["core"]] + c[n].get("accepts", [])]
    check("every mapping is correct", not wrong,
          f"wrong or blank for lab(s) {', '.join(wrong)} - the answer for each is "
          "printed by python mapping.py --grade")

    cov = s.get("coverage") or {}
    check("the coverage map was built", bool(cov), "run: python coverage.py")
    if cov:
        check("coverage matches the course",
              cov.get("techniques") == len(L.all_course_techniques(c))
              and cov.get("tactics") == len(L.covered_tactics(a, c)),
              "coverage.py recorded numbers that do not match course.json - "
              "tell the instructor, the answer key and the data have drifted")

    gd = s.get("gaps_defence") or {}
    check("you saw where the guidance runs out", bool(gd),
          "run: python defend.py --gaps")
    if gd:
        check("the unmitigated count matches MITRE's data",
              gd.get("unmitigated") == len(L.unmitigated(a, c)),
              "the recorded gap count disagrees with atlas.json - tell the instructor")

    ex = s.get("export") or {}
    check("you exported an ATLAS Navigator layer", bool(ex) and L.LAYER.exists(),
          "run: python export.py")
    if L.LAYER.exists():
        try:
            layer = json.loads(L.LAYER.read_text())
            valid = (isinstance(layer.get("techniques"), list)
                     and layer["techniques"]
                     and all("techniqueID" in t for t in layer["techniques"]))
        except ValueError:
            valid = False
        check("the layer file is valid Navigator JSON", valid,
              "atlas-layer.json is not loadable - re-run python export.py")

    print()
    print("=" * 68)
    if problems:
        print(f" {len(problems)} thing(s) to look at:")
        for p in problems:
            print("   - " + p)
        print("=" * 68)
        return 1

    spine = (s.get("spine") or {}).get("technique", "AML.T0051.001")
    print(" Everything checks out.")
    print("")
    print(f" You mapped seven attacks you ran yourself onto "
          f"{len(L.all_course_techniques(c))} ATLAS")
    print(f" techniques across {len(L.covered_tactics(a, c))} of "
          f"{len(a['tactics'])} tactics, found that {spine} runs")
    print(" through most of the course, named the controls MITRE publishes, and")
    print(f" found the {len(L.unmitigated(a, c))} techniques it publishes nothing for.")
    print("")
    print(" atlas-layer.json is your evidence. Part 2 is where you build the")
    print(" other half.")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
