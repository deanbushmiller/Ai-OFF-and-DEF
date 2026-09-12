"""Expert-mode self check. Confirms the evidence exists and the attack worked."""
import json
import pathlib
import sys

LAB = pathlib.Path("/labs/lab2")
ok = True


def chk(cond, good, bad):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {good if cond else bad}")
    ok = ok and cond


print("Lab 2 self check\n")
chk((LAB / "index.npz").exists(), "index.npz exists", "index.npz missing - run: python rag.py build")
chk((LAB / "poisoned_handbook.pdf").exists(), "poisoned_handbook.pdf exists",
    "poisoned PDF missing - run: python make_poison.py")

log_path = LAB / "answers.json"
chk(log_path.exists(), "answers.json exists", "no answers recorded - ask a question first")

if log_path.exists():
    log = json.loads(log_path.read_text())
    changed = [q for q, runs in log.items() if len(runs) > 1 and runs[0]["answer"] != runs[-1]["answer"]]
    chk(bool(changed), f"{len(changed)} question(s) changed answer after ingestion",
        "no question changed answer - ask the same question before AND after ingesting")
    poisoned = [q for q, runs in log.items() if runs[-1]["top_source"].endswith(".pdf")]
    chk(bool(poisoned), "the poisoned PDF is now the top retrieval result",
        "the poisoned PDF never outranked the real document")

print("\n" + ("ALL CHECKS PASSED - submit your evidence." if ok else "Not finished yet. See above."))
sys.exit(0 if ok else 1)
