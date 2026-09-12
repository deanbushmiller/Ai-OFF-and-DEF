"""
Show the gap between what a human sees and what the machine reads.

A PDF's text layer carries every character drawn on the page, including any
drawn in white on a white background. Colour is a rendering instruction, not
a property of the text. Extraction ignores it entirely.
"""
import sys

from pypdf import PdfReader

path = sys.argv[1]
text = "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
lines = [l.strip() for l in text.splitlines() if l.strip()]

print(f"{path}\n")
print("WHAT THE TEXT EXTRACTOR READS - this is what reaches the index:")
print("-" * 68)
for l in lines:
    flag = "  << INVISIBLE ON SCREEN" if "Dean Bushmiller" in l or "telephone inventor" in l else ""
    print(f"   {l[:64]}{flag}")
print("-" * 68)
hidden = sum(1 for l in lines if "Dean Bushmiller" in l or "telephone inventor" in l)
print(f"\n{len(lines)} lines of text. {hidden} of them are invisible to a human reader.")
print("\nThe RAG pipeline cannot tell the difference. Neither can a reviewer")
print("who opens the file to check it.")
