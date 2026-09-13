"""Add a shipped perturbation to a clean image.

    python apply_perturbation.py            the invoice, for the OCR stage
    python apply_perturbation.py --stamp    the stamp, for the stage 1 gate

This is the "craft the adversarial input" step, except the crafting was done
for you: perturbation.npz holds the pixel-by-pixel difference between an honest
invoice and an attacker's version of it. Real attackers tune this by hand or
optimise it against the target; you are applying a canned one.

MITRE ATLAS calls the shipped file AML.T0043 Craft Adversarial Data, and this
one is subtechnique .003, Manual Modification - placed by hand, not optimised.
"""
import argparse
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
INVOICES = HERE / "invoices"
CLEAN = INVOICES / "invoice-clean.png"
DELTA = INVOICES / "perturbation.npz"
ATTACK = INVOICES / "invoice-attack.png"

STAMP = INVOICES / "stamp.png"
STAMP_DELTA = INVOICES / "stamp-perturbation.npz"
STAMP_ATTACK = INVOICES / "stamp-attack.png"

ap = argparse.ArgumentParser()
ap.add_argument("--stamp", action="store_true",
                help="attack the stage 1 gate instead of the OCR stage")
args = ap.parse_args()

if args.stamp:
    from stamp_gate import (CLASSES, WEIGHTS, random_control, score, to_image,
                            to_input)

    clean = to_input(Image.open(STAMP).convert("L"))
    bundle = np.load(STAMP_DELTA)
    delta, eps255 = bundle["delta"], int(bundle["eps255"])
    adv = np.clip(clean + delta, 0.0, 1.0)
    to_image(adv).save(STAMP_ATTACK)

    weights = np.load(WEIGHTS, allow_pickle=False)
    w, b = weights["w"], float(weights["b"])
    flips, tries = random_control(clean, w, b, eps255)
    changed = int((np.abs(adv - clean) * 255 > 0.5).sum())

    print("Applied stamp-perturbation.npz to stamp.png")
    print(f"  wrote {STAMP_ATTACK}")
    print()
    print("  What actually changed:")
    print(f"    pixels touched : {changed:,} of {clean.size:,}  ({100 * changed / clean.size:.1f}% of the stamp)")
    print(f"    largest change : {eps255} of 255  ({100 * eps255 / 255:.1f}% of the brightness range)")
    print()
    print("  The control, so you know this is not just a flaky model:")
    print(f"    the SAME amount of change in {tries} random directions flipped")
    print(f"    the gate {flips} times out of {tries}.")
    print()
    print("  It is not the size of the change. It is the direction - straight up")
    print("  the gradient of the model's own score.")
    print()
    print(f"  Now run:  python gate.py invoices/{STAMP_ATTACK.name}")
    raise SystemExit(0)

clean = np.array(Image.open(CLEAN).convert("RGB"), dtype=np.int16)
delta = np.load(DELTA)["delta"]

if delta.shape != clean.shape:
    raise SystemExit(f"Perturbation shape {delta.shape} does not fit the "
                     f"invoice {clean.shape}. The lab assets are inconsistent.")

attack = np.clip(clean + delta, 0, 255).astype(np.uint8)
Image.fromarray(attack).save(ATTACK)

d = np.abs(np.array(Image.fromarray(attack).convert("L"), dtype=int)
           - np.array(Image.open(CLEAN).convert("L"), dtype=int))
changed = int((d > 0).sum())

print("Applied perturbation.npz to invoice-clean.png")
print(f"  wrote {ATTACK}")
print()
print("  What actually changed:")
print(f"    pixels touched : {changed:,} of {d.size:,}  ({100 * changed / d.size:.3f}% of the image)")
print(f"    largest change : {int(d.max())} of 255  ({100 * int(d.max()) / 255:.1f}% of the brightness range)")
print(f"    file on disk   : {DELTA.stat().st_size:,} bytes")
print()
print("  Nothing here is code. It is arithmetic on pixel values.")
print("  Open both PNGs side by side after the lab and try to spot the difference.")
