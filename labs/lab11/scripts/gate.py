"""The stamp gate from lab 4, with the two things a defender adds.

    python gate.py invoices/stamp.png
    python gate.py invoices/stamp-attack.png

Lab 4's gate is here unchanged: logistic regression over 25,600 pixels, trained
at build time, deciding DUPLICATE (blocked) or ORIGINAL (allowed). Added:

  1. A random-noise control, printed every time the image differs from the
     reference stamp. The same size of change, thirty random directions. This
     is what separates "the model changed its mind" from "the model is fragile".
     Without it a sharp student will rightly say nothing was shown.
  2. An auto-accept confidence threshold, from rules.json. An ORIGINAL verdict
     below it is HELD for a person instead of going to payment. rules.json ships
     it at 0.50 - the vulnerable configuration. tune.py raises it.

Both go in the mismatch log. A HELD item is written to review-queue/ with a
record, by this script, because the gate is where the decision happened.
"""
import json
import shutil
import sys

import numpy as np
from PIL import Image

from lab11lib import INVOICES, QUEUE, load_rules, log_event, resolve, sha256
from stamp_gate import CLASSES, WEIGHTS, probability, random_control, score, to_input

if len(sys.argv) < 2:
    print("usage: python gate.py <stamp image>")
    sys.exit(64)

rules = load_rules()
threshold = float(rules["auto_accept_confidence"])
path = resolve(sys.argv[1])
reference = INVOICES / "stamp.png"

data = np.load(WEIGHTS, allow_pickle=False)
w, b = data["w"], float(data["b"])


def evaluate(p):
    x = to_input(Image.open(p).convert("L"))
    if x.shape != w.shape:
        print(f"{p.name} is not a {int(len(w) ** 0.5)}px stamp crop.")
        sys.exit(1)
    z = score(x, w, b)
    label = CLASSES[1] if z > 0 else CLASSES[0]
    confidence = probability(z) if z > 0 else 1.0 - probability(z)
    return x, label, confidence


x_ref, ref_label, ref_conf = evaluate(reference)
x, label, confidence = evaluate(path)

delta = np.abs(x - x_ref)
changed = int((delta * 255 > 0.5).sum())
eps255 = int(round(float(delta.max()) * 255))

print(f"STAMP GATE: {path.name}                auto-accept confidence: {threshold:.2f}")
print(f"  reference  {reference.name:<18} {ref_label:<10} confidence {ref_conf:.3f}   "
      f"{'BLOCKED' if ref_label == CLASSES[0] else 'allowed'}")
print(f"  this image {'':<18} {label:<10} confidence {confidence:.3f}")

flips, tries = 0, 0
if eps255 > 0:
    flips, tries = random_control(x_ref, w, b, eps255)
    print(f"  difference from the reference: {changed:,} pixels, largest change {eps255} of 255")
    print(f"  the control: the same {eps255}/255 in {tries} random directions flipped the "
          f"gate {flips} of {tries} times")
else:
    print("  identical to the reference stamp")
print()

if label == CLASSES[0]:
    verdict = "BLOCKED"
    print("  BLOCKED - a duplicate never reaches the payment queue.")
elif confidence >= threshold:
    verdict = "ALLOWED"
    print(f"  ALLOWED - {label} at {confidence:.3f} meets the {threshold:.2f} auto-accept")
    print("  threshold. This scan goes on to payment with nobody looking at it.")
else:
    verdict = "HELD"
    QUEUE.mkdir(exist_ok=True)
    shutil.copyfile(path, QUEUE / path.name)
    record = {"image": path.name, "sha256": sha256(path), "routed_by": "gate.py",
              "reasons": [f"gate: {label} at {confidence:.3f} is below the "
                          f"{threshold:.2f} auto-accept threshold"],
              "evidence": {"label": label, "confidence": round(confidence, 4),
                           "threshold": threshold, "largest_change_of_255": eps255,
                           "noise_control": f"{flips}/{tries}"}}
    (QUEUE / (path.stem + ".json")).write_text(json.dumps(record, indent=2) + "\n")
    print(f"  HELD - {label} at {confidence:.3f} is below the {threshold:.2f} auto-accept")
    print(f"  threshold. Copied to review-queue/{path.name} with a record, for a")
    print("  person to look at. Nothing is paid until they do.")

log_event({"kind": "gate", "image": path.name, "verdict": verdict, "label": label,
           "confidence": round(confidence, 4), "threshold": threshold,
           "changed_pixels": changed, "largest_change_of_255": eps255,
           "noise_flips": flips, "noise_tries": tries})
