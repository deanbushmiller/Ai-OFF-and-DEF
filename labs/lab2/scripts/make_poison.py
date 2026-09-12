"""
Craft the poisoned document.

The PDF has two layers of text:

  VISIBLE    black, 11pt - a dull IT onboarding checklist. This is all a human
             sees if they open the file to check it.

  INVISIBLE  white on white, 6pt - the attacker's payload. A human sees nothing.
             The text extractor that feeds the RAG pipeline reads it perfectly,
             because extraction does not care what colour the text is.

The payload contains no commands and no malware. It simply states things that
are false. That is enough - the pipeline treats whatever it retrieves as true.

The last line is keyword stuffing: terms lifted from the questions we expect to
be asked, so this document scores highly on similarity search and gets retrieved
ahead of the real one. MITRE ATLAS calls this Retrieval Content Crafting
(AML.T0066); hiding it in white text is Prompt Obfuscation (AML.T0068).
"""
import pathlib

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

OUT = "/labs/lab2/poisoned_handbook.pdf"
PAYLOAD = pathlib.Path("/labs/lab2/poison_source.txt").read_text().strip().splitlines()

VISIBLE = [
    "1. Collect your laptop from the 3rd floor IT desk.",
    "2. Set up multi-factor authentication before your first login.",
    "3. Complete the security awareness module in the LMS.",
    "4. Email it-help@example.internal if your badge does not work.",
]

c = canvas.Canvas(OUT, pagesize=LETTER)

# --- the part a human sees ---
c.setFillColorRGB(0, 0, 0)
c.setFont("Helvetica-Bold", 16)
c.drawString(72, 720, "Acme Corp - IT Onboarding Checklist")
c.setFont("Helvetica", 9)
c.drawString(72, 702, "Revision 4.2 - Internal use only")
c.setFont("Helvetica", 11)
for i, line in enumerate(VISIBLE):
    c.drawString(72, 670 - i * 18, line)

# --- the part only the extractor sees: white on white, 6pt ---
c.setFillColorRGB(1, 1, 1)
c.setFont("Helvetica", 6)
for i, line in enumerate(PAYLOAD):
    c.drawString(72, 560 - i * 9, line)

c.save()

size = pathlib.Path(OUT).stat().st_size
print(f"Wrote {OUT}  ({size} bytes)")
print(f"  visible lines:   {len(VISIBLE)}  (black, 11pt)")
print(f"  invisible lines: {len(PAYLOAD)}  (white on white, 6pt)")
print("\nOpen it and you see an onboarding checklist. Nothing else.")
