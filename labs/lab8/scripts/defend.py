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
temptation will be strongest on AML.M0024 and AML.M0033, which each cover five of the
seven labs - and those are exactly the two that most deserve a whole lab rather than a
paragraph.

Every control here is a real ATLAS mitigation ID read out of MITRE's own data at
/opt/lab-assets/atlas/atlas.json. Nothing in this file is our opinion about what you
should do; it is what MITRE publishes, plus a pointer to the part-2 lab that covers it.

REWRITTEN FOR ATLAS v2026.08, 2026-09-22
----------------------------------------
On ATLAS 5.6.0 beat 7's lesson was "9 of your 20 techniques have no published
mitigation; the covered ones are the older classical-ML attacks". On v2026.08 that is
false: 18 of 20 are covered and the two left are AML.T0065 LLM Prompt Crafting and
AML.T0110 AI Agent Tool Poisoning - lab 6's core. So beat 7 now teaches three things the
data does support: the standard moved (5.6.0 -> v2026.08, printed side by side), a
technique being "covered" by a broad mitigation is not the same as having a specific
control, and the remaining gap is the agent tool layer.
"""
import argparse
import lab8lib as L

# MEASURED, NOT LIVE DATA. The course techniques that had NO mitigation in ATLAS 5.6.0 -
# the release this lab first shipped on (2026-09-14), frozen since June 2026 at
# atlas-navigator-data/main/dist/stix-atlas.json. Measured 2026-09-22 by distilling that
# file with this lab's own fetch_assets.py parser. Only 5.6.0 history lives here; every
# CURRENT number the lab prints is read from atlas.json. If a technique listed here ever
# leaves course.json, show_gaps() simply skips it.
ATLAS_OLD = "5.6.0"
UNMITIGATED_IN_OLD = ["AML.T0064", "AML.T0066", "AML.T0068", "AML.T0070", "AML.T0065",
                      "AML.T0084.001", "AML.T0110", "AML.T0016.002", "AML.T0096"]
# Same measurement: the mitigation IDs in v2026.08 that 5.6.0 did not have.
NEW_SINCE_OLD = ["AML.M0035", "AML.M0036", "AML.M0037", "AML.M0038"]

WORDS = {1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX", 7: "SEVEN"}


def labs_using(c, tid):
    return [int(n) for n in sorted(c, key=int) if tid in c[n]["chain"]]


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
        print(f" {WORDS.get(len(top), len(top))} CONTROLS COVER AT LEAST FIVE "
              "OF YOUR SEVEN LABS")
        L.rule("-")
        print()
        for m in top:
            print(f"   {len(cov[m])} of 7  {m}  {a['mitigations'][m]['name']}")
        print()
        print("   Notice what KIND of control tops the list. The broadest ones are")
        print("   broad on purpose: a red team, guardrails, logging, validation.")
        print("   None of them is specific to any one attack you ran - which is")
        print("   exactly why each one maps to so many of them.")
        print()
        if "AML.M0035" in top:
            print(f"   {a['mitigations']['AML.M0035']['name']} (AML.M0035) touches "
                  f"{len(cov['AML.M0035'])} of 7, and it is the one you")
            print("   already know: attacking your own system on purpose to find out")
            print("   what breaks. That is what you spent part 1 doing.")
            print()
        if "AML.M0024" in top and "AML.M0033" in top:
            print("   And the two that have defended every other kind of system for")
            print("   thirty years are still here: log what the model and its tools")
            print("   actually did (AML.M0024), and validate what crosses every")
            print("   boundary into and out of them (AML.M0033). Not a model, not a")
            print("   product. Unglamorous, and still the core of the answer.")
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
        print(f"          -> part 2, lab {lab['part2_lab']}: {lab['part2']}")
        print()
    print("   One line each, on purpose. Every control above is the subject of a")
    print("   full lab in the second half of this course. If you want to know HOW,")
    print("   that is where it is - and a paragraph here would be worse than")
    print("   nothing, because it would feel like enough.")
    print()
    L.save_score("defend", {"controls": len(cov), "top": top,
                            "top_labs": [len(cov[m]) for m in top]})


def show_gaps(a, c):
    bare = L.unmitigated(a, c)
    total = L.all_course_techniques(c)
    ver = a.get("atlas_version", "")

    L.head("WHERE THE PUBLISHED GUIDANCE RUNS OUT")
    print(f"   Of the {len(total)} techniques you used across seven labs, MITRE ATLAS")
    print(f"   {ver} publishes a mitigation for {len(total) - len(bare)}.")
    print()
    print(f"   For {len(bare)} of them it publishes NOTHING.")
    print()
    dated = sorted(bare, key=lambda x: a["techniques"][x].get("created") or "")
    print(f"     {'technique':<16} {'':<40} {'added':<11} your labs")
    for t in dated:
        cores = [n for n in sorted(c, key=int) if c[n]["core"] == t]
        tag = f"  <- the core of lab {', '.join(cores)}" if cores else ""
        print(f"     {t:<16} {L.tech_name(a, t):<40} "
              f"{a['techniques'][t].get('created') or '?':<11} "
              f"{', '.join(str(x) for x in labs_using(c, t))}{tag}")
    print()

    # --- the standard moved: 5.6.0 against the release baked into this image
    old = [t for t in UNMITIGATED_IN_OLD if t in total]
    closed = [t for t in old if t not in bare]
    L.rule("-")
    print(" THE STANDARD MOVED WHILE THIS COURSE WAS BEING WRITTEN")
    L.rule("-")
    print()
    print(f"   This lab was first built on ATLAS {ATLAS_OLD}. There, {len(old)} of these")
    print(f"   same {len(total)} techniques had no mitigation at all. In {ver}, "
          f"{len(closed)} of")
    print(f"   those {len(old)} have one:")
    print()
    for t in closed:
        mits = a["techniques"][t]["mitigations"]
        print(f"     {t:<16} {L.tech_name(a, t):<36} now {', '.join(mits)}")
    print()
    everywhere = [t for t, v in a["techniques"].items() if not v.get("mitigations")]
    print(f"   (Across the WHOLE matrix, {len(everywhere)} of {len(a['techniques'])} "
          f"techniques in {ver} still")
    print("   have none. Your 20 are better covered than the matrix as a whole.)")
    print()
    print("   ATLAS is a living standard, and it is moving fast. A coverage map")
    print("   is a snapshot with a release number on it - read the number before")
    print("   you quote the result.")
    print()

    # --- covered is not the same as solved
    used = {}
    for t in closed:
        for m in a["techniques"][t]["mitigations"]:
            used.setdefault(m, []).append(t)
    common = sorted(used.items(), key=lambda x: (-len(x[1]), x[0]))[:3]
    L.rule("-")
    print(" COVERED IS NOT THE SAME AS SOLVED")
    L.rule("-")
    print()
    print("   Look at what closed those gaps. Mostly broad controls, mapped")
    print("   onto more techniques than before:")
    print()
    for m, ts in common:
        new = f"  (new since {ATLAS_OLD})" if m in NEW_SINCE_OLD else ""
        print(f"     {m}  {a['mitigations'][m]['name']:<36} "
              f"closes {len(ts)}{new}")
    print()
    print("   A broad mitigation mapped to a technique tells you where to START.")
    print("   It does not tell you what specifically stops that attack. That")
    print("   gap - between 'there is a mitigation' and 'this is the control' -")
    print("   is the work, and part 2 is where you do it.")
    print()

    # --- the frontier
    L.rule("-")
    print(" THE FRONTIER IS THE AGENT'S TOOL LAYER")
    L.rule("-")
    print()
    frontier = [n for n in sorted(c, key=int) if c[n]["core"] in bare]
    cores = [c[n]["core"] for n in sorted(c, key=int)]
    print(f"   Of your seven labs, {WORDS.get(len(frontier), len(frontier))} "
          f"{'has a core technique' if len(frontier) == 1 else 'have core techniques'}")
    print("   with no published mitigation:")
    print()
    for n in frontier:
        t = c[n]["core"]
        print(f"     lab {n}  {c[n]['title']}")
        print(f"            {t}  {L.tech_name(a, t)}, in ATLAS since "
              f"{a['techniques'][t].get('created') or '?'}")
    print()
    if [c[n]["core"] for n in frontier] == ["AML.T0110"]:
        print("   That is the attack on what an agent's TOOLS tell it - the MCP")
        print("   channel you sat on in lab 6. Every other lab's core technique now")
        print("   has at least one published control. This one has none, not even")
        print("   a broad one. That is not a criticism of MITRE; it is what the edge")
        print("   of the field looks like, and it is where the next attacks are.")
        print()
    side = [t for t in bare if t not in cores]
    if side:
        where = sorted({x for t in side for x in labs_using(c, t)})
        print(f"   The other gap, {', '.join(f'{t} {L.tech_name(a, t)}' for t in side)},")
        print(f"   is a supporting step in labs {' and '.join(str(x) for x in where)}"
              " - no lab is built around it.")
        print()

    L.rule("-")
    print(" WHICH IS WHY THERE IS A PART 2")
    L.rule("-")
    print()
    print("   This course is the first half. You have spent it attacking, because")
    print("   the fastest way to understand a defence is to have beaten one.")
    print()
    print("   The second half is seven defender labs, one for each attack you")
    print("   ran, taught in this order:")
    print()
    for name in L.part2_order():
        who = [n for n in sorted(c, key=int) if c[n]["part2"] == name]
        pl = c[who[0]]["part2_lab"] if who else "?"
        tag = f"pairs with your lab {who[0]}" if who else ""
        print(f"     lab {pl:<3} {name:<38} {tag}")
    print()
    print("   Where MITRE names a control, those labs build it. Where MITRE has")
    if frontier:
        n = frontier[0]
        print(f"   nothing yet - lab {c[n]['part2_lab']}, against what you did in lab {n} -"
              " they build")
    else:
        print("   nothing yet, they build")
    print("   something anyway and tell you honestly that it is ahead of the")
    print("   standard. That is the more useful half, and it only works because")
    print("   you did this half first.")
    print()
    L.save_score("gaps_defence", {"total": len(total), "unmitigated": len(bare),
                                  "techniques": bare, "atlas_version": ver,
                                  "unmitigated_in_" + ATLAS_OLD: len(old),
                                  "closed_since": closed})


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
