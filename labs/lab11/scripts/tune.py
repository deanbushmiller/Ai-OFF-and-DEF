"""RECOVER, second half - tune the controls with what the log just taught you.

    python tune.py                       tighten auto-accept to 0.90, add your indicator
    python tune.py --confidence 0.80     a different threshold
    python tune.py --indicator "finance director"   a phrase of your own choosing

Two edits to rules.json, and both come from your own evidence:

  1. The auto-accept confidence goes from 0.50 to 0.90. The perturbed stamp
     scored ORIGINAL at about 0.61 and went to payment. Now it is held. The
     clean duplicate scored 1.000 and is still blocked - a tighter threshold
     costs nothing on the case that was already right.
  2. The first words of the line your comparison caught become an indicator in
     your own rule list. The four shipped patterns are somebody else's judgement
     about what an instruction looks like, written before your incident. This
     one exists because your own detector produced it.

Expert mode makes the same two edits with `nano rules.json`.
"""
import argparse
import re
import subprocess
import sys

from lab11lib import INVOICES, QUEUE, WORK, load_rules, log_event, read_log, save_rules

WIDTH = 68


def run_inspect(path):
    proc = subprocess.run([sys.executable, str(WORK / "inspect.py"), str(path)],
                          capture_output=True, text=True)
    fired = [l.strip() for l in (proc.stdout or "").splitlines()
             if l.strip().startswith(("RULE", "YOUR RULE"))]
    return ("FLAG" if proc.returncode else "PASS"), fired


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confidence", type=float, default=0.90)
    ap.add_argument("--indicator", default=None)
    args = ap.parse_args()
    if not 0.5 <= args.confidence <= 0.999:
        print("Pick a threshold between 0.50 and 0.999.")
        return 64

    rules = load_rules()
    events = read_log()
    mismatches = [e for e in events if e["kind"] == "compare" and e["verdict"] == "MISMATCH"]

    indicator = args.indicator
    source_line = None
    if indicator is None:
        if not mismatches:
            print("No mismatch in the log to learn from. Run compare.py on the")
            print("doctored invoice first, or pass --indicator \"some phrase\".")
            return 66
        source_line = mismatches[-1]["extra"][0]
        words = re.findall(r"[a-z]+", source_line.lower())
        indicator = " ".join(words[:4])
    indicator = indicator.strip()
    if len(indicator) < 4:
        print("That indicator is too short to mean anything: " + repr(indicator))
        return 64

    # The doctored invoice is wherever route.py left it.
    target = None
    for e in reversed(events):
        if e["kind"] == "compare" and e["verdict"] == "MISMATCH":
            for folder in (QUEUE, INVOICES):
                if (folder / e["image"]).exists():
                    target = folder / e["image"]
                    break
        if target:
            break

    print("=" * WIDTH)
    print(" TUNE THE CONTROLS")
    print("=" * WIDTH)
    print()

    if target:
        verdict, fired = run_inspect(target)
        print(f"  BEFORE, the content check on {target.parent.name}/{target.name}:")
        print(f"    {verdict}")
        for f in fired:
            print("      " + f)
        print()

    old = float(rules["auto_accept_confidence"])
    rules["auto_accept_confidence"] = args.confidence
    already = indicator.lower() in [i.lower() for i in rules.get("your_indicators", [])]
    if not already:
        rules.setdefault("your_indicators", []).append(indicator)
    save_rules(rules)

    print("  rules.json, two edits:")
    print(f"    auto_accept_confidence   {old:.2f}  ->  {args.confidence:.2f}")
    if already:
        print(f"    your_indicators          already contains {indicator!r}")
    else:
        print(f"    your_indicators          + {indicator!r}")
        if source_line:
            print(f"                             (from the line your comparison caught:")
            print(f"                              {source_line[:56]}...)")
    print()

    if target:
        verdict, fired = run_inspect(target)
        print("  AFTER:")
        print(f"    {verdict}")
        for f in fired:
            print("      " + f)
        print()
        print("  Same verdict. Different authority.")
        print()
        print("    the four patterns   somebody else's judgement about what an")
        print("                        instruction looks like, written before")
        print("                        your incident, and right about this one")
        print("    the comparison      caught it without reading a word of it")
        print("    your indicator      catches this wording at the door, and it")
        print("                        exists because your own detector found it")
        print()

    print(f"  And the gate: an ORIGINAL below {args.confidence:.2f} is now held for a person.")
    print("  Re-run it on the perturbed stamp and watch the same score land")
    print("  somewhere different.")
    print("=" * WIDTH)
    log_event({"kind": "tune", "image": "rules.json", "verdict": "UPDATED",
               "detail": f"auto-accept {old:.2f} -> {args.confidence:.2f}; indicator {indicator!r}"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
