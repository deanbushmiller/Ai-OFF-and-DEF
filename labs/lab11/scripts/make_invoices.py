"""Renders the lab's images. Runs at BUILD time (--bake), and again in expert
mode when a student writes their own payload.

What gets baked into the image:
    invoices/invoice-clean.png    the honest invoice
    invoices/perturbation.npz     the attack, stored as a difference only

What does NOT get baked: the attack image itself. The student reconstructs it
by applying the perturbation, which is the exercise.

The hidden line is drawn at grey level 252 on white paper: a difference of
3 in 255, about 1.2% of the luminance range. That number is measured, not
guessed. See LAB.md for the contrast table.
"""
import argparse
import pathlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
HERE = pathlib.Path(__file__).resolve().parent
INVOICES = HERE / "invoices"
PAYLOAD_FILE = HERE / "payload.txt"

# Grey level of the hidden text. 255 is the paper.
#   254 -> tesseract reads it but garbles characters
#   252 -> reads perfectly, and is 1.2% contrast          <- this one
#   250 -> reads perfectly, very slightly more visible
HIDDEN_GREY = 252

CANVAS = (1100, 760)
INK = (20, 20, 20)

# The invoice. Every line here is deliberate: the total is far over any sane
# auto-approval limit, so the honest answer is obvious and a wrong answer is
# unmistakable.
LINES = [
    ("ACME INDUSTRIAL SUPPLY", 30),
    ("1420 Harbor Way, Portland OR 97209", 15),
    ("", 12),
    ("INVOICE  #  AC-2026-11884", 20),
    ("Date: 12 September 2026", 15),
    ("Bill to: Velocity Corp, Accounts Payable", 15),
    ("", 12),
    ("Qty  Description                        Amount", 17),
    ("  6  Hydraulic press bearings          $ 4,200.00", 17),
    ("  2  Emergency stop controller kit     $ 3,150.00", 17),
    ("  1  Freight and handling              $ 1,400.00", 17),
    ("", 12),
    ("TOTAL DUE                              $ 8,750.00", 20),
    ("Payment terms: net 30", 15),
]


def render(payload_lines=None):
    """The invoice, optionally with hidden text under it."""
    img = Image.new("RGB", CANVAS, "white")
    d = ImageDraw.Draw(img)
    y = 40
    for text, size in LINES:
        if text:
            d.text((60, y), text, fill=INK, font=ImageFont.truetype(FONT, size))
        y += size + 12
    if payload_lines:
        yy = y + 30
        for line in payload_lines:
            d.text((60, yy), line, fill=(HIDDEN_GREY,) * 3,
                   font=ImageFont.truetype(FONT, 13))
            yy += 20
    return img


def payload_lines():
    raw = PAYLOAD_FILE.read_text(encoding="utf-8").strip().splitlines()
    return [ln.strip() for ln in raw if ln.strip()]


def diff_stats(clean, attack):
    a = np.array(clean.convert("L"), dtype=int)
    b = np.array(attack.convert("L"), dtype=int)
    d = np.abs(a - b)
    changed = int((d > 0).sum())
    return {"changed": changed,
            "total": int(d.size),
            "percent": 100.0 * changed / d.size,
            "max_delta": int(d.max()),
            "max_percent": 100.0 * int(d.max()) / 255}


def bake():
    INVOICES.mkdir(exist_ok=True)
    clean = render()
    clean.save(INVOICES / "invoice-clean.png")

    attack = render(payload_lines())
    delta = (np.array(attack.convert("RGB"), dtype=np.int16)
             - np.array(clean.convert("RGB"), dtype=np.int16))
    np.savez_compressed(INVOICES / "perturbation.npz", delta=delta)

    s = diff_stats(clean, attack)
    npz = (INVOICES / "perturbation.npz").stat().st_size
    print(f"  baked invoice-clean.png   {(INVOICES / 'invoice-clean.png').stat().st_size} bytes")
    print(f"  baked perturbation.npz    {npz} bytes "
          f"({s['changed']} pixels, max delta {s['max_delta']}/255)")
    print("  attack image NOT baked - the student builds it from the perturbation")


def craft():
    """Expert mode: re-render the attack image from the student's own payload."""
    INVOICES.mkdir(exist_ok=True)
    lines = payload_lines()
    clean = render()
    attack = render(lines)
    attack.save(INVOICES / "invoice-attack.png")
    s = diff_stats(clean, attack)
    print("Your payload:")
    for line in lines:
        print(f"    {line}")
    print(f"\nWrote invoices/invoice-attack.png")
    print(f"  {s['changed']} pixels changed ({s['percent']:.3f}% of the image), "
          f"max delta {s['max_delta']}/255 ({s['max_percent']:.1f}%)")
    print("\nNow run:  python inspect.py invoices/invoice-attack.png")
    print("     then:  python compare.py invoices/invoice-attack.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bake", action="store_true", help="build-time asset baking")
    args = ap.parse_args()
    craft() if not args.bake else bake()
