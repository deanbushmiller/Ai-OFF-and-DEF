"""Both decisions side by side. This is what you submit."""
import json
import pathlib

LOG = pathlib.Path("/labs/lab4/runs.json")
if not LOG.exists():
    print("No runs recorded yet. Run the pipeline first.")
    raise SystemExit(0)

runs = json.loads(LOG.read_text())
W = 72

ROWS = [
    ("invoice-clean.png", "CLEAN INVOICE"),
    ("invoice-attack.png", "ATTACK INVOICE"),
    ("invoice-attack.png::strict", "ATTACK INVOICE, limit enforced in code"),
]

print("=" * W)
print(" EVIDENCE - two stages of one pipeline, both defeated by pixels")
print("=" * W)

g_clean = runs.get("gate::stamp.png")
g_attack = runs.get("gate::stamp-attack.png")
if g_clean or g_attack:
    print("\n  STAGE 1 - the duplicate-stamp gate")
    for r, label in ((g_clean, "clean stamp "), (g_attack, "attack stamp")):
        if r:
            print(f"    {label} : {r['label']:<10} "
                  f"conf {r['confidence']:.3f}  score {r['score']:+.2f}  "
                  f"{'ALLOWED' if r['allowed'] else 'BLOCKED'}")

print("\n  STAGE 2 - the OCR and approval step")
for key, label in ROWS:
    r = runs.get(key)
    if not r:
        continue
    flag = "payload in the extracted text: " + ("YES" if r["payload_extracted"] else "no")
    print(f"\n    {label}")
    print(f"      verdict : {r['verdict']}")
    print(f"      OCR     : {r['ocr_chars']} characters, {flag}")
    for i in range(0, min(len(r["answer"]), 240), 62):
        print(f"      {'said    : ' if i == 0 else '          '}{r['answer'][i:i + 62]}")

clean = runs.get("invoice-clean.png")
attack = runs.get("invoice-attack.png")
strict = runs.get("invoice-attack.png::strict")

print("\n" + "=" * W)
if clean and attack and clean["verdict"] == "HOLD" and attack["verdict"] == "APPROVE":
    if g_attack and g_attack["allowed"]:
        print(" Two ML checks stood between a duplicate invoice and a payment.")
        print(" Both were defeated by changing pixels, and neither model was")
        print(" touched: no weights, no code, no prompt.")
        print()
    print(" The decision reversed. The model did not change, the code did not")
    print(" change, the policy did not change. A quarter of one percent of the")
    print(" pixels changed, by 3 parts in 255, and the invoice was approved.")
    if strict and strict["verdict"] == "HOLD":
        print()
        print(" With the spend limit enforced in application code, the same image")
        print(" and the same payload get nowhere: the model was never asked.")
elif clean and attack:
    print(f" Clean: {clean['verdict']}.  Attack: {attack['verdict']}.")
    print(" That is not the expected pair - tell the instructor.")
else:
    print(" Run the pipeline on both invoices before submitting.")
print("=" * W)
