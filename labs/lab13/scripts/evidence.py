"""The evidence table, and the regression check that costs no model time.

    python evidence.py

Two halves.

1. WHAT HAPPENED. One row per agent run, read from the audit log: how many calls,
   how many denied, where the denial landed, and whether the session was
   escalated. The gate number walking 3 -> 2 -> 1 down that column is the lab.

2. WHAT WOULD HAPPEN NOW. The clean run's logged calls, re-decided under the
   policy as it stands after the tune. This is the half people skip, and here it
   is free: it is a pure function over the log, no model, no network, instant.

   It is also what a real change-control process does. You do not ship a policy
   change by arguing about it; you replay yesterday's traffic against it and look
   at what would have changed. A tightened rule that breaks legitimate traffic is
   not a fix - it is the reason the next person leaves the rule loose.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from lab13lib import RULES, load_policy, read_log, replay      # noqa: E402

W = 68
GATE = {"not_on_allowlist": 1, "credential_revoked": 2,
        "outside_purpose": 3, "within_purpose": 3, "no_such_tool": 1}


def main():
    recs = read_log()
    pol = load_policy()
    purpose = pol["purpose"]

    print("=" * W)
    print(" LAB 13 EVIDENCE")
    print("=" * W)
    if not recs:
        print("\n  (no runs recorded - run the agent first)\n")
        return

    print()
    print("  run  calls  denied  stopped at                  escalated")
    print("  " + "-" * (W - 4))
    runs = sorted({r.get("run", 0) for r in recs})
    for run in runs:
        rows = [r for r in recs if r.get("run", 0) == run]
        denied = [r for r in rows if r["verdict"] == "DENY"]
        where = RULES[denied[0]["rule"]] if denied else "(nothing denied)"
        esc = "yes" if any(r["action"].startswith("set_role:")
                           and r["verdict"] == "ALLOW" for r in rows) else "no"
        print(f"  {run:>3}  {len(rows):>5}  {len(denied):>6}  {where:<26}  {esc}")

    denials = [r for r in recs if r["verdict"] == "DENY"]
    if denials:
        gates = [GATE[r["rule"]] for r in denials]
        print()
        print("  Gate the privileged call died at, run by run: "
              + " -> ".join(str(g) for g in gates))
        if len(set(gates)) > 1 and gates[-1] < gates[0]:
            print("  It moved EARLIER. That is the recovery, measured rather")
            print("  than asserted.")

    # ---- the regression check -------------------------------------------
    first = min(runs)
    clean = [r for r in recs if r.get("run", 0) == first]
    print()
    print("=" * W)
    print(" REGRESSION CHECK - the clean run, replayed against today's policy")
    print("=" * W)
    print()
    print(f"  Run {first} was the legitimate triage task. Its calls, re-decided")
    print(f"  under policy.json as it stands now (purpose {purpose!r}):")
    print()
    broke = 0
    for rec, verdict, rule in replay(clean, pol):
        changed = "" if verdict == rec["verdict"] else "   <- CHANGED"
        if verdict != rec["verdict"] and verdict == "DENY":
            broke += 1
        print(f"    {rec['action']:<22}  was {rec['verdict']:<5}  "
              f"now {verdict:<5}{changed}")
    print()
    if broke:
        print(f"  {broke} legitimate call(s) would now be refused. The policy is")
        print("  too tight. That is a finding, not a success.")
    else:
        print("  No legitimate call changed verdict. The tightened policy costs")
        print("  nothing on real traffic - which is the argument you will need")
        print("  the first time somebody asks you to loosen it again.")
    print()
    print("  No model was run to produce this. It is arithmetic over the log.")
    print("=" * W)


if __name__ == "__main__":
    main()
