"""Beat 8 - the evidence, in a format the rest of the industry already reads.

    python export.py

Writes atlas-layer.json: an ATLAS Navigator layer file. Drag it into the Navigator at

    https://atlas.mitre.org/navigator

and your seven labs light up on the real matrix, scored and annotated. It is the same
artifact a security team produces for its own estate. Nothing to submit - review it and
bring your questions.

THE FORMAT WAS CHECKED AGAINST MITRE'S OWN PUBLISHED LAYERS, NOT GUESSED
-----------------------------------------------------------------------
2026-09-14, ATLAS 5.6.0: diffed against the two layers in the (now deprecated)
atlas-navigator-data/dist/default-navigator-layers/. The first draft got three things
wrong that would have stopped a student's evidence from loading:

  domain      must be "atlas-atlas". The draft said "atlas-mitigations", which is not a
              domain the Navigator knows.
  versions    MITRE then shipped layer 4.3 / navigator 4.6.4.
  tactic      each entry needs the tactic SHORTNAME ("defense-evasion"), and a technique
              that sits under several tactics needs ONE ENTRY PER TACTIC. AML.T0015 is
              under three. Without that it does not place on the matrix properly.

2026-09-22, ATLAS v2026.08: re-checked against the layer MITRE publishes WITH that
release (atlas-data release v2026.08, navigator-atlas_layer_matrix.json). Its domain is
still "atlas-atlas" and its tactic entries still use shortnames, but its versions are now
layer 4.5 / navigator 5.3.2, and it carries metadata atlas_data_version = "2026.08". Both
are matched below. If this ever stops loading, diff it against that file again before
debugging anything else.
"""
import json
import lab8lib as L

# Scored by how many of the seven labs used the technique, so the heat map means
# something: the darker it is, the more of the course ran through it.
COLORS = ["#ffe0b2", "#ffb74d", "#fb8c00", "#e65100", "#bf360c"]


def main():
    a, c = L.atlas(), L.course()
    freq = L.technique_frequency(c)
    answers = L.load_answers()

    entries = []
    for tid, labs in sorted(freq.items()):
        n = len(labs)
        core_for = [k for k in sorted(c, key=int) if c[k]["core"] == tid]
        comment = f"Lab{'s' if n > 1 else ''} {', '.join(str(x) for x in labs)}"
        if core_for:
            comment += f" | core technique of lab {', '.join(core_for)}"
        mits = a["techniques"].get(tid, {}).get("mitigations", [])
        comment += (f" | ATLAS mitigations: {', '.join(mits)}" if mits
                    else " | NO published ATLAS mitigation")
        # One entry per tactic, exactly as MITRE's own layers do it.
        tac_ids = a["techniques"].get(tid, {}).get("tactics", []) or [None]
        for tac in tac_ids:
            entry = {
                "techniqueID": tid,
                "score": n,
                "color": COLORS[min(n, len(COLORS)) - 1],
                "comment": comment,
                "enabled": True,
                "showSubtechniques": True,
            }
            short = a["tactics"].get(tac, {}).get("shortname") if tac else None
            if short:
                entry["tactic"] = short
            entries.append(entry)

    layer = {
        "name": "SecLLM Bootcamp - labs 1-7",
        # Matching the layer MITRE publishes with ATLAS v2026.08. Change these only
        # to match what MITRE ships with the release fetch_assets.py is pinned to.
        "versions": {"layer": "4.5", "navigator": "5.3.2"},
        "domain": "atlas-atlas",
        "metadata": [{"name": "atlas_data_version",
                      "value": a.get("atlas_version", "").lstrip("v")}],
        "description": ("Techniques exercised hands-on across labs 1-7 of the SecLLM "
                        "bootcamp. Score = how many labs used the technique. Generated "
                        f"by lab 8 from MITRE ATLAS {a.get('atlas_version', '')}."),
        "filters": {"platforms": []},
        "sorting": 3,
        "layout": {"layout": "side", "showID": True, "showName": True},
        "hideDisabled": True,
        "techniques": entries,
        "gradient": {"colors": [COLORS[0], COLORS[-1]], "minValue": 1,
                     "maxValue": max(len(v) for v in freq.values())},
        "showTacticRowBackground": True,
        "tacticRowBackground": "#dddddd",
        "selectTechniquesAcrossTactics": True,
    }
    L.LAYER.write_text(json.dumps(layer, indent=2))

    L.head("YOUR EVIDENCE")
    print(f"   Wrote {L.LAYER.name}  -  {L.LAYER.stat().st_size/1024:.1f} KB")
    print(f"   {len(freq)} techniques in {len(entries)} matrix cells, scored 1 to "
          f"{max(len(v) for v in freq.values())}")
    print("   by how many of your labs used each one.")
    print()
    print("   This is an ATLAS Navigator layer file. Open")
    print("     https://atlas.mitre.org/navigator")
    print("   choose 'Open Existing Layer' -> 'Upload from local', and drop this")
    print("   file in. Your seven labs appear on the real matrix, coloured by how")
    print("   often each technique came up, with the mitigations in the comments.")
    print()
    print("   The README next to this lab has the link and the steps again.")
    print()
    L.rule("-")
    print(" THE MAPPING YOU PRODUCED")
    L.rule("-")
    print()
    print(f"   {'lab':<4} {'technique':<15} {'OWASP 2026':<22} part 2")
    for n in sorted(c, key=int):
        lab = c[n]
        got = answers.get(n, lab["core"])
        print(f"   {n:<4} {got:<15} {'+'.join(lab['owasp']):<22} lab {lab['part2_lab']}")
    print()
    print("   Nothing - You have the atlas-layer.json. Review it and prepare")
    print("   to ask questions.")
    print()
    L.save_score("export", {"techniques": len(freq), "cells": len(entries),
                            "bytes": L.LAYER.stat().st_size})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
