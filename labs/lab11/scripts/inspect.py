"""PREVENT - the content check on extracted text.

    python inspect.py invoices/invoice-clean.png
    python inspect.py invoices/invoice-attack.png

OWASP LLM01:2026 prevention 3, in its own words: "Run OCR over images ... then
apply text filters to the extracted content." Lab 4's pipeline did the first
half and skipped the second. This is the second half.

It is a rule check, and it is honest about being one. The rules in rules.json
look for text that reads like an instruction rather than like data: a directive
verb, a system-or-policy marker, a claim of prior approval, a line far longer
than any field on the form. OWASP's next sentence is the caveat: "Semantic
filters are evadable by rephrasing or encoding." Expert mode lets you prove
that with your own payload - and then watch compare.py catch it anyway, because
compare.py does not care what the text SAYS.

Exit code 1 on a flag, so a pipeline can stop on it.
"""
import re
import sys

from lab11lib import lines_of, load_rules, log_event, ocr_text, resolve

if len(sys.argv) < 2:
    print("usage: python inspect.py <image>")
    sys.exit(64)

rules = load_rules()
path = resolve(sys.argv[1])
lines = lines_of(ocr_text(path))

hits = []                                  # (rule label, line number, line)
for i, line in enumerate(lines, 1):
    for r in rules["instruction_patterns"]:
        if re.search(r["regex"], line, re.IGNORECASE):
            hits.append((r["name"], i, line))
    if len(line) > rules["max_line_chars"]:
        hits.append((f"line length {len(line)} > {rules['max_line_chars']}", i, line))
    for phrase in rules.get("your_indicators", []):
        if phrase.lower() in line.lower():
            hits.append(("YOUR RULE  " + repr(phrase), i, line))

print(f"CONTENT CHECK: {path.name}")
print(f"  {len(lines)} lines of extracted text, checked against {len(rules['instruction_patterns'])} "
      f"patterns, a length limit, and {len(rules.get('your_indicators', []))} indicator(s) of your own")
print()

if not hits:
    print("  PASS - nothing in the extracted text reads like an instruction.")
    log_event({"kind": "content-check", "image": path.name, "verdict": "PASS",
               "rules": [], "lines": []})
    sys.exit(0)

for label, i, line in hits:
    shown = line if len(line) <= 52 else line[:49] + "..."
    print(f"  {'RULE' if not label.startswith('YOUR') else '    '}  {label:<36} line {i}: {shown}")
flagged = sorted({i for _, i, _ in hits})
print()
print(f"  FLAG - {len(hits)} rule(s) fired on line{'s' if len(flagged) > 1 else ''} "
      f"{', '.join(str(i) for i in flagged)}. This text must not drive an action.")
log_event({"kind": "content-check", "image": path.name, "verdict": "FLAG",
           "rules": [label for label, _, _ in hits],
           "lines": [lines[i - 1] for i in flagged]})
sys.exit(1)
