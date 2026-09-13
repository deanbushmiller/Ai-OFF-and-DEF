"""What the OCR actually handed to the model - and what one setting changes.

    python show_extraction.py invoices/invoice-attack.png

Prints the extracted text, marks the lines that are not on the paper, then runs
the SAME image through the SAME OCR with tesseract's default global threshold,
where the hidden line does not exist.

Also writes an enhanced copy of the image so you can see the line with your own
eyes after the lab.
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageFilter

from pipeline import extra_lines, ocr_text

WIDTH = 70
image = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                     else "/labs/lab4/invoices/invoice-attack.png")
if not image.exists():
    raise SystemExit(f"No such image: {image}\nRun  python apply_perturbation.py  first.")

adaptive = ocr_text(image, method=1)
extra = extra_lines(adaptive)

print("=" * WIDTH)
print(" WHAT THE PIPELINE READ   (thresholding_method=1, local adaptive)")
print("=" * WIDTH)
for line in adaptive.splitlines():
    if not line.strip():
        continue
    mark = ">>>" if line in extra else "   "
    print(f" {mark} {line}")
print()
if extra:
    print(f" The {len(extra)} line(s) marked >>> are not printed on the invoice.")
    print(" No human reviewer approving this document would have seen them.")
else:
    print(" No extra text found. Either this is the clean invoice, or the")
    print(" perturbation was not applied.")

global_otsu = ocr_text(image, method=0)
print()
print("=" * WIDTH)
print(" THE SAME IMAGE, ONE SETTING CHANGED   (thresholding_method=0, global)")
print("=" * WIDTH)
print(f" {len(global_otsu)} characters extracted, versus {len(adaptive)} above.")
print(" The hidden line is gone:",
      "yes" if not extra_lines(global_otsu, method=0) else "no")
print()
print(" Global Otsu picks ONE brightness threshold for the whole page. Paper is")
print(" 255 and print is near 20, so the split lands around mid-grey and every")
print(" lighter mark is discarded as paper. Local adaptive thresholding splits")
print(" the page into tiles, and in a tile of blank paper a 1.2% mark is the")
print(" darkest thing there - so it becomes ink.")
print()
print(" Neither setting is wrong. The local one is what you choose when real")
print(" scans are faded and the OCR keeps missing legitimate text. That is the")
print(" uncomfortable part: the quality fix is the attack surface.")

# An enhanced copy, so the line is visible to a person too. Same idea as the
# adaptive threshold above: compare each pixel to its neighbourhood, not to a
# single number for the whole page.
grey = Image.open(image).convert("L")
local_mean = np.array(grey.filter(ImageFilter.BoxBlur(8)), dtype=float)
enhanced = np.where(np.array(grey, dtype=float) < local_mean - 0.5, 0, 255)
out = image.with_name(image.stem + "-enhanced.png")
Image.fromarray(enhanced.astype(np.uint8)).save(out)
print()
print(f" Wrote {out.name} - open it after the lab and the line is plain to see.")
