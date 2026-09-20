"""Expert-mode self-check.

    python check.py

Beginner mode asserts as it goes and cannot finish in a wrong state. Expert mode
has no rails: you ran the pieces in your own order and edited rules.json by
hand. This says whether the defence actually holds together.

It checks the recorded evidence and the files on disk, not what scrolled past.
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image

from lab11lib import INVOICES, QUEUE, load_rules, read_log, sha256
from stamp_gate import CLASSES, WEIGHTS, score, to_input

OK, BAD = "  PASS  ", "  FAIL  "
problems = []


def check(label, cond, hint):
    print((OK if cond else BAD) + label)
    if not cond:
        problems.append(hint)


def main():
    print("=" * 68)
    print(" LAB 11 SELF-CHECK")
    print("=" * 68)
    print()

    rules = load_rules()
    events = read_log()
    checks = [e for e in events if e["kind"] == "content-check"]
    compares = [e for e in events if e["kind"] == "compare"]
    gates = [e for e in events if e["kind"] == "gate"]

    check("a clean document passed the content check (your baseline)",
          any(e["verdict"] == "PASS" for e in checks),
          "run: python inspect.py invoices/invoice-clean.png")
    check("a document was flagged by the content check",
          any(e["verdict"] == "FLAG" for e in checks),
          "run: python inspect.py on the doctored invoice")
    check("the comparison found a line a person would not see",
          any(e["verdict"] == "MISMATCH" and e["extra"] for e in compares),
          "run: python compare.py on the doctored invoice")
    check("the comparison also ran clean on a clean document",
          any(e["verdict"] == "MATCH" for e in compares),
          "run: python compare.py invoices/invoice-clean.png - a detector with no baseline is a guess")

    records = sorted(QUEUE.glob("*.json")) if QUEUE.exists() else []
    routed = []
    for r in records:
        try:
            rec = json.loads(r.read_text())
        except ValueError:
            continue
        img = QUEUE / rec.get("image", "")
        if img.exists() and sha256(img) == rec.get("sha256"):
            routed.append(rec)
    check("a flagged item sits in review-queue/ with a record whose hash matches the file",
          bool(routed),
          "run: python route.py (or hold a stamp with gate.py after tuning)")
    invoices_routed = [r for r in routed if r.get("routed_by") == "route.py"]
    check("the flagged invoice is no longer in the pipeline's inbox",
          bool(invoices_routed) and not any((INVOICES / r["image"]).exists()
                                            for r in invoices_routed),
          "route.py moves it out of invoices/; if you re-created it with craft.py, route again")

    check("auto_accept_confidence was tightened above the shipped 0.50",
          float(rules.get("auto_accept_confidence", 0)) > 0.5,
          "raise auto_accept_confidence in rules.json, or run: python tune.py")
    check("you added an indicator of your own to rules.json",
          bool(rules.get("your_indicators")),
          "add a phrase to your_indicators in rules.json, or run: python tune.py")
    check("the gate held a perturbed stamp after tuning",
          any(e["verdict"] == "HELD" for e in gates),
          "run: python gate.py invoices/stamp-attack.png after tightening the threshold")
    check("the noise control was run and did not flip the gate",
          any(e["noise_tries"] > 0 and e["noise_flips"] == 0 for e in gates),
          "gate.py prints the control whenever the image differs from the reference")

    ref = INVOICES / "stamp.png"
    still_blocked = False
    if ref.exists() and pathlib.Path(WEIGHTS).exists():
        d = np.load(WEIGHTS, allow_pickle=False)
        z = score(to_input(Image.open(ref).convert("L")), d["w"], float(d["b"]))
        still_blocked = z <= 0
    check("the clean DUPLICATE stamp is still blocked (tightening cost nothing there)",
          still_blocked, "the reference stamp should still score DUPLICATE - if not, the weights are wrong")

    print()
    if problems:
        print(f" NOT DONE YET. {len(problems)} thing(s) to finish:")
        print()
        for hint in problems:
            print("   - " + hint)
        print()
        print("=" * 68)
        return 1

    print(" ALL CHECKS PASS.")
    print()
    print(" You have the evidence the lab asks for: the clean and doctored OCR")
    print(" text, the mismatch log naming the hidden line, the gate with its")
    print(" noise control, and the held item after you tightened the threshold.")
    print()
    print(" Paste the MISMATCH block and the HELD block into the class chat.")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())
