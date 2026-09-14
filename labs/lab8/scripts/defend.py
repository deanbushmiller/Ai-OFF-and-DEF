"""Beats 6 and 7 - the introduction to defense, and where the guidance runs out.

    python defend.py          the controls MITRE names for what you did
    python defend.py --gaps   the techniques MITRE names no control for

INTRODUCTION ONLY. INSTRUCTOR DECISION, 2026-09-14.
---------------------------------------------------
This lab NAMES controls and says what each one does in one line. It does not configure
anything, show any code, or work any examples. Part 2 of this course carries a full
defender lab for every attack lab in part 1, and every control named here is the subject
of one of them.

If a student asks "yes, but HOW do I do telemetry logging on an agent?", the honest and
correct answer is "that is a part-2 lab". Do not let this file grow a worked example. The
temptation will be strongest on AML.M0024 and AML.M0033, which between them cover five of
the seven labs - and those are exactly the two that most deserve a whole lab rather than a
paragraph.

Every control here is a real ATLAS mitigation ID read out of MITRE's own data at
/opt/lab-assets/atlas/atlas.json. Nothing in this file is our opinion about what you
should do; it is what MITRE publishes, plus a pointer to the part-2 lab that covers it.
"""
import argparse
import lab8lib as L


def show_controls(a, c):
    cov = L.mitigation_coverage(a, c)
    ranked = sorted(cov.items(), key=lambda x: (-len(x[1]), x[0]))

    L.head("THE CONTROLS MITRE NAMES FOR WHAT YOU JUST DID")
    print("   These are ATLAS mitigation IDs, taken from MITRE's own data - not")
    print("   our advice. Ranked by how many of your seven labs each one touches.")
    print()
    print(f"   {'labs':>4}  {'id':<12} control")
    for m, labs in ranked[:10]:
        print(f"   {len(labs):>4}  {m:<12} {a['mitigations'][m]['name']:<48} {labs}")
    print()

    top = [m for m, labs in ranked if len(labs) >= 5]
    if top:
        L.rule("-")
        print(" TWO CONTROLS COVER FIVE OF YOUR SEVEN LABS")
        L.rule("-")
        print()
        for m in top:
            print(f"   {m}  {a['mitigations'][m]['name']}")
        print()
        print("   Log what the model and its tools actually did, and validate what")
        print("   crosses every boundary into and out of them.")
        print()
        print("   That is the whole of part 1's defensive answer, and it is worth")
        print("   noticing how unglamorous it is. Not a model, not a filter, not a")
        print("   product. Logging and validation - the two things that have")
        print("   defended every other kind of system for thirty years.")
        print()

    L.rule("-")
    print(" PER LAB - THE CONTROL, AND WHO TEACHES IT PROPERLY")
    L.rule("-")
    print()
    for n in sorted(c, key=int):
        lab = c[n]
        # The controls for the technique that IS the lab come first; everything
        # else its chain touches follows. Alphabetical order put "Sanitize
        # Training Data" at the top of the supply-chain lab, which is not wrong
        # but is not the answer either.
        core_m = sorted(a["techniques"].get(lab["core"], {}).get("mitigations", []))
        rest = sorted({m for t in lab["chain"]
                       for m in a["techniques"].get(t, {}).get("mitigations", [])}
                      - set(core_m))
        mits = core_m + rest
        print(f"   LAB {n}  {lab['title']}")
        if core_m:
            for m in mits[:3]:
                star = " <- for this lab's core technique" if m in core_m[:1] else ""
                print(f"          {m}  {a['mitigations'][m]['name']}{star}")
            if len(mits) > 3:
                print(f"          ... and {len(mits) - 3} more across the chain")
        elif mits:
            print(f"          NONE for {lab['core']}, this lab's core technique.")
            for m in mits[:2]:
                print(f"          {m}  {a['mitigations'][m]['name']}"
                      f"  (elsewhere in the chain)")
        else:
            print("          MITRE publishes NO mitigation for this lab's chain.")
        print(f"          -> part 2: {lab['part2']}")
        print()
    print("   One line each, on purpose. Every control above is the subject of a")
    print("   full lab in the second half of this course. If you want to know HOW,")
    print("   that is where it is - and a paragraph here would be worse than")
    print("   nothing, because it would feel like enough.")
    print()
    L.save_score("defend", {"controls": len(cov),
                            "top": [m for m, l in ranked if len(l) >= 5]})


def show_gaps(a, c):
    bare = L.unmitigated(a, c)
    total = L.all_course_techniques(c)

    L.head("WHERE THE PUBLISHED GUIDANCE RUNS OUT")
    print(f"   Of the {len(total)} techniques you used across seven labs, MITRE")
    print(f"   publishes a mitigation for {len(total) - len(bare)}.")
    print()
    print(f"   For {len(bare)} of them it publishes NOTHING.")
    print()
    dated = sorted(bare, key=lambda x: a["techniques"][x].get("created") or "")
    print(f"     {'technique':<16} {'':<50} added to ATLAS")
    for t in dated:
        print(f"     {t:<16} {L.tech_name(a, t):<50} "
              f"{a['techniques'][t].get('created') or '?'}")
    print()
    if dated:
        first = a["techniques"][dated[0]].get("created") or "?"
        last = a["techniques"][dated[-1]].get("created") or "?"
        print(f"   Every one of them was added between {first} and {last}.")
        print()
    L.rule("-")
    print(" LOOK AT WHICH ONES")
    L.rule("-")
    print()
    print("   Read that date column. Every technique MITRE has no answer for is")
    print("   a RECENT one - RAG poisoning, prompt obfuscation, retrieval content")
    print("   crafting, agent tool poisoning, obtaining a generative model as an")
    print("   attack capability.")
    print()
    print("   The techniques that DO have published mitigations are the older,")
    print("   classical machine-learning ones: model poisoning, supply chain,")
    print("   model evasion.")
    print()
    print("   The defensive literature is roughly a year behind the offensive")
    print("   literature, and you can see the gap by reading the dates.")
    print()
    print("   That is not a criticism of MITRE. It is what the field looks like")
    print("   right now, and it is the honest answer to 'so what do I do about")
    print("   this?' - for a good fraction of what you attacked this week, the")
    print("   published answer does not exist yet.")
    print()
    L.rule("-")
    print(" WHICH IS WHY THERE IS A PART 2")
    L.rule("-")
    print()
    print("   This course is the first half. You have spent it attacking, because")
    print("   the fastest way to understand a defence is to have beaten one.")
    print()
    print("   The second half is seven defender labs, taught in this order:")
    print()
    for i, name in enumerate(L.part2_order(), 1):
        who = [n for n in sorted(c, key=int) if c[n]["part2"] == name]
        tag = f"closest to your lab {who[0]}" if who else ""
        print(f"     {i}.  {name:<44} {tag}")
    print()
    print("   The right-hand column is the nearest counterpart, not a day-for-day")
    print("   pairing - part 2 is taught in its own order, and some of it draws on")
    print("   more than one of the attacks you ran. Your lab 2 is where it starts;")
    print("   your lab 1 is not picked up until its fourth day.")
    print()
    print("   Where MITRE has a control, those labs build it. Where MITRE has")
    print("   nothing yet, they build something anyway and tell you honestly that")
    print("   it is ahead of the standard. That is the more useful half, and it")
    print("   only works because you did this half first.")
    print()
    L.save_score("gaps_defence", {"total": len(total), "unmitigated": len(bare),
                                  "techniques": bare})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gaps", action="store_true")
    args = ap.parse_args()
    a, c = L.atlas(), L.course()
    if args.gaps:
        show_gaps(a, c)
    else:
        show_controls(a, c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
