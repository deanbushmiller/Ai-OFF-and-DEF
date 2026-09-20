"""BUILD TIME ONLY. Reconstruct lab 4's two attack images from the shipped
perturbations, so the student receives them as a defender would receive a
document: already doctored.

Lab 4 deliberately did NOT bake these - the student built them, because
applying the perturbation was the attack exercise. This is the defend lab. The
student is the person the document arrives at, and spending two of ten commands
re-running lab 4's attack would teach nothing new.

Runs after make_invoices.py --bake and stamp_gate.py --bake, in the same RUN.
"""
import pathlib

import numpy as np
from PIL import Image

from stamp_gate import to_image, to_input

HERE = pathlib.Path(__file__).resolve().parent
INVOICES = HERE / "invoices"

# The invoice: RGB delta, max 3/255, ~2,000 pixels.
clean = np.array(Image.open(INVOICES / "invoice-clean.png").convert("RGB"), dtype=np.int16)
delta = np.load(INVOICES / "perturbation.npz")["delta"]
assert delta.shape == clean.shape, "perturbation does not fit the invoice"
attack = np.clip(clean + delta, 0, 255).astype(np.uint8)
Image.fromarray(attack).save(INVOICES / "invoice-attack.png")
d = np.abs(attack.astype(int) - clean.astype(int)).max(axis=2)
print(f"  baked invoice-attack.png   {int((d > 0).sum()):,} pixels changed, max delta {int(d.max())}/255")

# The stamp: FGSM delta in model-input space, eps from the bundle.
stamp = to_input(Image.open(INVOICES / "stamp.png").convert("L"))
bundle = np.load(INVOICES / "stamp-perturbation.npz")
adv = np.clip(stamp + bundle["delta"], 0.0, 1.0)
to_image(adv).save(INVOICES / "stamp-attack.png")
print(f"  baked stamp-attack.png     eps {int(bundle['eps255'])}/255")
