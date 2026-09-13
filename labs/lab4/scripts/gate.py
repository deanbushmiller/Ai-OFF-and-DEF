"""Stage 1 of the pipeline: does this scan carry a DUPLICATE stamp?

    python gate.py invoices/stamp.png
    python gate.py invoices/stamp-attack.png

A scan stamped DUPLICATE is blocked and never reaches the payment queue. This
is a real accounts-payable control - duplicate-payment fraud is one of the
oldest tricks there is - and automating it means a model looks at the stamp.

The model is in gate-weights.npz. Open stamp_gate.py if you want to see how it
was trained; it is logistic regression over 16,384 pixels, about twenty lines.
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image

from stamp_gate import CLASSES, WEIGHTS, probability, score, to_input

LOG = pathlib.Path("/labs/lab4/runs.json")

if len(sys.argv) < 2:
    raise SystemExit("usage: python gate.py <stamp image>")

path = pathlib.Path(sys.argv[1])
if not path.exists():
    print(f"No such image: {path}")
    print("If you have not built the attack stamp yet, run:")
    print("    python apply_perturbation.py --stamp")
    raise SystemExit(1)

data = np.load(WEIGHTS, allow_pickle=False)
w, b = data["w"], float(data["b"])

x = to_input(Image.open(path).convert("L"))
if x.shape != w.shape:
    raise SystemExit(f"{path.name} is not a {int(len(w) ** 0.5)}px stamp crop.")

z = score(x, w, b)
label = CLASSES[1] if z > 0 else CLASSES[0]
confidence = probability(z) if z > 0 else 1.0 - probability(z)

print(f"Stage 1 gate: {path.name}")
print(f"  reads the stamp as : {label}")
print(f"  confidence         : {confidence:.3f}")
print(f"  raw score          : {z:+.3f}   (positive = {CLASSES[1]} = allowed through)")
print()
if label == CLASSES[1]:
    print("  ALLOWED - this scan goes on to the OCR and approval stage.")
else:
    print("  BLOCKED - a duplicate never reaches the payment queue.")

log = json.loads(LOG.read_text()) if LOG.exists() else {}
log["gate::" + path.name] = {"image": path.name, "label": label,
                             "confidence": round(confidence, 4),
                             "score": round(z, 3),
                             "allowed": label == CLASSES[1]}
LOG.write_text(json.dumps(log, indent=2))
