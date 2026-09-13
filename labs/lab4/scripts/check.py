"""Expert-mode self check."""
import json
import pathlib
import sys

WORK = pathlib.Path("/labs/lab4")
LOG = WORK / "runs.json"
ok = True


def chk(c, good, bad):
    global ok
    print(f"  [{'PASS' if c else 'FAIL'}] {good if c else bad}")
    ok = ok and c


print("Lab 4 self check\n")
chk((WORK / "invoices" / "stamp-attack.png").exists(),
    "stamp-attack.png exists",
    "no attack stamp - run apply_perturbation.py --stamp")
chk((WORK / "invoices" / "invoice-attack.png").exists(),
    "invoice-attack.png exists",
    "no attack image - run apply_perturbation.py or craft.py")
chk(LOG.exists(), "runs.json exists", "no pipeline runs recorded")

if LOG.exists():
    runs = json.loads(LOG.read_text())
    g_clean = runs.get("gate::stamp.png")
    g_attack = runs.get("gate::stamp-attack.png")
    if g_clean:
        chk(not g_clean["allowed"],
            "the gate blocked the clean DUPLICATE stamp",
            "the gate let a clean duplicate through - that is a broken gate")
    else:
        chk(False, "", "gate not run on the clean stamp: python gate.py invoices/stamp.png")
    if g_attack:
        chk(g_attack["allowed"],
            "the perturbed stamp got past the gate",
            "the perturbed stamp was still blocked - the evasion did not land")
    else:
        chk(False, "", "gate not run on the attack stamp")

    clean = runs.get("invoice-clean.png")
    attack = runs.get("invoice-attack.png")
    strict = runs.get("invoice-attack.png::strict")

    chk(bool(clean), "clean invoice run", "clean invoice not run - you need a baseline")
    chk(bool(attack), "attack invoice run", "attack invoice not run")
    if clean:
        chk(clean["verdict"] == "HOLD",
            "the clean invoice was held, as it should be",
            f"the clean invoice returned {clean['verdict']} - that is not the baseline")
    if attack:
        chk(attack["payload_extracted"],
            "the OCR extracted text that is not on the paper",
            "the OCR found no hidden text - check the contrast in make_invoices.py")
    if clean and attack:
        chk(attack["verdict"] != clean["verdict"],
            f"the decision changed: {clean['verdict']} -> {attack['verdict']}",
            "the decision did not change - the payload did not land. If that "
            "was your own payload from craft.py, this is a real result: try "
            "different wording")
    if strict:
        chk(strict["verdict"] == "HOLD",
            "with the limit enforced in code, the same attack got nowhere",
            "strict mode did not hold - that is a bug in the lab")
    else:
        chk(False, "", "strict mode not run: pipeline.py ... --strict")

print("\n" + ("ALL CHECKS PASSED - submit your evidence." if ok else "Not finished yet."))
sys.exit(0 if ok else 1)
