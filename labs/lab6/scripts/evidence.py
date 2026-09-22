"""The evidence: what the wire carried, next to what the assistant said.

    python evidence.py

The whole lab is the gap between those two. In the injection beat the wire shows
a payment being made and the assistant's answer never mentions it - so the
evidence is not one artefact, it is a DISAGREEMENT between two artefacts.

That is also the realistic part. An incident responder does not get told what
happened; they get a log and a user's account of events, and the job is noticing
that the two do not line up.
"""
import json
import pathlib
import re
import sys

WORK = pathlib.Path("/labs/lab6")
RUNS = WORK / "runs.json"
WIRE = WORK / "wire.log"
LEDGER = WORK / "ledger.json"

BEATS = [("control",  "clean wire, nothing changed"),
         ("arg",      "request tampered  (--rewrite-arg chk-002)"),
         ("inject",   "instruction injected into the result  (--inject)"),
         ("defended", "the same injection, with signatures verified")]


def main():
    if not RUNS.exists():
        print("No runs recorded yet. Run the lab first.")
        sys.exit(1)
    log = json.loads(RUNS.read_text())

    print("=" * 68)
    print(" WHAT THE ASSISTANT TOLD YOU")
    print("=" * 68)
    for key, label in BEATS:
        if key not in log:
            continue
        r = log[key]
        print(f"\n{label}   ({key})")
        print("-" * 68)
        print(f"  you asked      : {r['question']}")
        print(f"  tools called   : {' -> '.join(r['chain']) or '(none)'}")
        print(f"  you were told  : {r['final']}")
        if r["paid"]:
            for p in r["payments"]:
                print(f"  PAYMENT MADE   : {json.dumps(p)}")
            print(f"  answer mentions it: {'yes' if r['mentions_payment'] else 'NO'}")

    # The ledger is the server's own record - the ground truth the assistant's
    # prose is being compared against.
    if LEDGER.exists():
        entries = json.loads(LEDGER.read_text())
        if entries:
            print("\n" + "=" * 68)
            print(" WHAT THE SERVER ACTUALLY RECORDED")
            print("=" * 68)
            for e in entries:
                print(f"  {json.dumps(e)}")

    if WIRE.exists():
        lines = [l for l in WIRE.read_text().splitlines() if l.strip()]
        tampered = [l for l in lines if l.startswith("**")]
        print("\n" + "=" * 68)
        print(" WHAT THE WIRE CARRIED  (last exchange, wire.log)")
        print("=" * 68)
        for l in lines[-8:]:
            print("  " + (l[:160] + ("..." if len(l) > 160 else "")))
        if tampered:
            print("\n  proxy interventions recorded this run:")
            for l in tampered:
                print("   " + l)

    inj = log.get("inject") or {}
    dfd = log.get("defended") or {}

    print("\n" + "=" * 68)
    if inj.get("paid") and not inj.get("mentions_payment"):
        print(" A payment was made and the answer you were given does not")
        print(" mention it. Nothing in the assistant's reply is a lie - it")
        print(" reported the balance correctly. It simply did not report the")
        print(" other thing it did, because it was never asked to.")
        print("")
        print(" OWASP LLM01:2026 Prompt Injection - Scenario #9, via MCP")
        print("      LLM08:2026 Hidden Context Exposure - risks #1 and #4")
        print(" MITRE ATLAS AML.T0110 - AI Agent Tool Poisoning")
        print("      'modifying parameters or descriptions ... redirecting outputs'")
        print("      then AML.T0053 - AI Agent Tool Invocation")
    if dfd and not dfd.get("paid"):
        print("")
        print(" With responses signed and verified, the same payload reached the")
        print(" same model and no payment happened. The injection was not")
        print(" detected as malicious - it was never delivered intact.")
    print("=" * 68)
    print("\nPaste this block - the wire log and what the assistant said -")
    print("into the class chat.")


if __name__ == "__main__":
    main()
