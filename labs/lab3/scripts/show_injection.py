"""
Show the gap between what a reader sees and what the assistant reads.

Colour, display:none and HTML comments are rendering instructions. They tell a
browser what to paint. They are not a property of the text, and a scraper that
strips tags ignores them completely.
"""
import re
import sys
import urllib.request

url = sys.argv[1]
html = urllib.request.urlopen(url, timeout=10).read().decode("utf-8", "replace")

hidden = []
for m in re.finditer(r'<div[^>]*display:\s*none[^>]*>(.*?)</div>', html, re.S | re.I):
    hidden.append(("display:none", m.group(1)))
for m in re.finditer(r'<!--(.*?)-->', html, re.S):
    body = m.group(1).strip()
    if len(body) > 60 and "=====" not in body:
        hidden.append(("HTML comment", body))

visible = re.sub(r'<div[^>]*display:\s*none[^>]*>.*?</div>', ' ', html, flags=re.S | re.I)
visible = re.sub(r'<!--.*?-->', ' ', visible, flags=re.S)
visible = re.sub(r'<(script|style).*?</\1>', ' ', visible, flags=re.S | re.I)
visible = re.sub(r'<[^>]+>', ' ', visible)
visible = re.sub(r'\s+', ' ', visible).strip()

print(f"{url}\n")
print("WHAT A READER SEES IN THE BROWSER:")
print("-" * 70)
print("  " + visible[:300] + ("..." if len(visible) > 300 else ""))
print("-" * 70)
print(f"\nHIDDEN FROM THE READER, READ BY THE ASSISTANT - {len(hidden)} block(s):")
print("-" * 70)
for how, body in hidden:
    print(f"  [{how}]")
    for line in re.sub(r"\s+", " ", body).strip().split(". "):
        if line.strip():
            print(f"      {line.strip()[:66]}")
    print()
print("-" * 70)
if not hidden:
    print("\nNo hidden blocks. This is the clean page.")
else:
    print("\nThe browser paints none of that. The scraper reads all of it.")
