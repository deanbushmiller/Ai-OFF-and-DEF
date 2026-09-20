"""The tool-call audit log. This is the detect beat, and it is the buildable core.

    python audit.py

ATLAS AML.M0024, AI Telemetry Logging, against AML.T0053 - eight words:

    "Log AI agent tool invocations to detect malicious calls."

OWASP LLM03:2026 is blunter about what a log is and is not. Preventions 8 and 9
sit under a heading that reads: "The following options WILL NOT PREVENT Excessive
Agency but can limit the level of damage caused." The log is not the control. It
is how you find out the control was configured wrong - which is the only reason
anyone ever fixes one.

Every ATTEMPTED call is here, allowed and denied alike. A log that records only
what it blocked cannot tell you what it let through.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from lab13lib import RULES, read_log                          # noqa: E402

W = 68


def main():
    recs = read_log()
    print("=" * W)
    print(" TOOL-CALL AUDIT LOG      audit-log.jsonl")
    print("=" * W)
    if not recs:
        print("\n  (empty - no agent run has been recorded yet)\n")
        return

    runs = sorted({r.get("run", 0) for r in recs})
    for run in runs:
        rows = [r for r in recs if r.get("run", 0) == run]
        print(f"\n  RUN {run}   purpose={rows[0]['purpose']!r}   "
              f"{len(rows)} call(s)")
        print("  " + "-" * (W - 4))
        for r in rows:
            print(f"  {r['verdict']:<5}  {r['action']:<22}  {RULES[r['rule']]}")
            if r["verdict"] == "DENY":
                print(f"         {r['reason']}")

    # The jump: a privileged action reached in the same run as a role change.
    # Naming it is the difference between a log and a log somebody reads.
    for run in runs:
        rows = [r for r in recs if r.get("run", 0) == run]
        tools = [r["tool"] for r in rows]
        if "set_role" in tools and any(r["action"] == "read_notes:admin"
                                       for r in rows):
            i = tools.index("set_role")
            print("\n" + "=" * W)
            print(" THE JUMP - read run %d again, three records in a row" % run)
            print("=" * W)
            for r in rows[max(0, i - 1):i + 2]:
                print(f"   {r['verdict']:<5}  {r['action']}")
            print()
            print("   A triage task read the public notes, changed its own role,")
            print("   and went for the admin box. Nothing in the tool NAMES says")
            print("   that is wrong - read_notes appears twice with opposite")
            print("   verdicts. The argument is what tells them apart.")
            break

    allowed = [r for r in recs if r["verdict"] == "ALLOW"]
    denied = [r for r in recs if r["verdict"] == "DENY"]
    print("=" * W)
    print(f" {len(recs)} call(s) recorded: {len(allowed)} allowed, "
          f"{len(denied)} denied")
    if any(r["tool"] == "set_role" and r["verdict"] == "ALLOW" for r in recs):
        print()
        print(" THE UNCOMFORTABLE LINE: set_role was ALLOWED.")
        print(" The privileged read was stopped at the last of three gates,")
        print(" with a valid credential in hand. Look at policy.json and ask")
        print(" why a triage agent may change its own role at all.")
    print("=" * W)


if __name__ == "__main__":
    main()
