"""Step one of any document pipeline: turn the picture into text.

    python ocr.py invoices/invoice-clean.png
    python ocr.py invoices/invoice-attack.png

This is lab 4's OCR, unchanged: tesseract with local adaptive binarisation and
--psm 4. Nothing here is a control. It is the thing the controls stand in front
of, and you need to see its output before any of them make sense.
"""
import sys

from lab11lib import lines_of, ocr_text, resolve

if len(sys.argv) < 2:
    print("usage: python ocr.py <image>")
    sys.exit(64)

path = resolve(sys.argv[1])
text = ocr_text(path)
lines = lines_of(text)

print(f"OCR: {path.name}")
print("  tesseract, adaptive threshold, --psm 4 - the pipeline's own settings")
print()
for i, line in enumerate(lines, 1):
    print(f"  {i:>2}  {line}")
print()
print(f"  {len(lines)} lines, {len(text)} characters. This is the text the")
print("  pipeline hands on. Whoever wrote it, the next stage treats it as")
print("  the invoice.")
