"""Print the tool-call logs side by side. This is the evidence the student pastes.

    python evidence.py

Reads runs.json, which agent.py writes after every run, and shows the chains
next to each other. The whole lab is in the shape of these three columns: the
attack does not make the agent smarter or the model worse, it adds two calls in
the middle that should never have been possible.

Why the log and not the answer: the answer is prose and varies in wording; the
call chain is structural. An auditor reviewing a real incident reads exactly
this - what did the agent DO - not what it said afterwards.
"""
import json
import pathlib
import sys

WORK = pathlib.Path("/labs/lab5")
LOG = WORK / "runs.json"

LABELS = [
    ("vulnerable", "clean / attacked"),
    ("mediate", "with complete mediation"),
    ("minimal", "with set_role removed"),
]


def fmt(call):
    args = call.get("args") or {}
    if call["tool"] == "answer":
        return "answer(...)"
    inner = ", ".join(f"{k}={json.dumps(v)}" for k, v in args.items())
    denied = str(call.get("result", "")).startswith("DENIED")
    return f"{call['tool']}({inner})" + ("   <- DENIED" if denied else "")


def main():
    if not LOG.exists():
        print("No runs recorded yet. Run the agent first.")
        sys.exit(1)

    log = json.loads(LOG.read_text())

    print("=" * 68)
    print(" TOOL-CALL LOG")
    print("=" * 68)

    for key, label in LABELS:
        if key not in log:
            continue
        run = log[key]
        print(f"\n{label}   ({key})")
        print("-" * 68)
        for i, call in enumerate(run["calls"], 1):
            print(f"  {i}. {fmt(call)}")
        print(f"\n  role at launch : {run['launched_as']}")
        print(f"  role at end    : {run['role_at_end']}"
              + ("   <- ESCALATED" if run["escalated"] else ""))
        print(f"  read the admin box: {'YES' if run['read_admin'] else 'no'}")

    print("\n" + "=" * 68)

    vuln = log.get("vulnerable", {})
    med = log.get("mediate", {})

    if vuln.get("read_admin"):
        print(" The agent read a box its session was never entitled to read.")
        print(" It was not tricked into believing it was an admin - it simply")
        print(" ASKED to be one, and the tool layer said yes.")
        print("")
        print(" OWASP LLM03:2026 Excessive Agency, risks #1 and #4")
        print(" MITRE ATLAS AML.T0053 - AI Agent Tool Invocation")
        print("   tactic AML.TA0012, Privilege Escalation")

    if med:
        print("")
        if med.get("escalated") is False and not med.get("read_admin"):
            print(" With complete mediation the SAME payload still reached the")
            print(" model, and the model still tried. The tool layer refused.")
            print(" The injection succeeded. The exploit did not.")
        elif not med.get("read_admin"):
            print(" With complete mediation the admin box stayed shut.")

    print("=" * 68)
    print("\nPaste this block - all three columns - into the class chat.")


if __name__ == "__main__":
    main()
