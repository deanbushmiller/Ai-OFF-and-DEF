"""The evidence to submit, plus the regression check the tune is supposed to pass.

    python evidence.py

Two halves.

THE STORY. Every run in this session, what the control saw, and where each
refusal happened. The `stopped at` column is the finding: watch it move outward
as you drop the server, and watch service come back when you re-pin.

THE REPLAY, and it is free. Every message the clean run logged is re-checked
against the trust list as it stands NOW. No model runs; this is a pure function
over the log. That is also what a real change-control process does - replay
yesterday's traffic against the proposed rule before shipping it. If the tune
broke legitimate traffic, this is where it shows.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab14lib as L
import verify


def main():
    recs = L.read_log()
    if not recs:
        print("Nothing logged yet. Run ask.py first.")
        return 0

    runs = []
    for r in recs:
        if not runs or runs[-1][0] != r["run"]:
            runs.append((r["run"], []))
        runs[-1][1].append(r)

    print(L.BAR)
    print("  WHAT THE CONTROL SAW")
    print(L.BAR)
    print("  %-22s %-26s %-7s %s" % ("run", "stopped at", "paid", "outcome"))
    for name, rs in runs:
        blocks = [r for r in rs if r["verdict"] == "BLOCK"]
        outcome = next((r for r in rs if r["kind"] == "outcome"), None)
        repin = any(r["verdict"] == "REPIN" for r in rs)
        if blocks:
            first = min(blocks, key=lambda r: L.gate_of(r["rule"]))
            where = L.label_of(first["rule"])
        else:
            where = "nothing blocked"
        paid = "YES" if (outcome and outcome.get("paid")) else "no"
        if outcome:
            what = f"answered, {len(outcome.get('chain') or [])} tool call(s)"
        elif any(r["kind"] == "server" and r["verdict"] == "BLOCK" for r in rs):
            what = "OUTAGE - no tool was available"
        else:
            what = "no model run"
        if repin:
            what += "  (served the pinned copy)"
        print("  %-22s %-26s %-7s %s" % (name, where, paid, what))

    diffs = [r for r in recs if r.get("diff")]
    print()
    print(L.BAR)
    print("  DESCRIPTOR DIFFS  (%d)" % len(diffs))
    print(L.BAR)
    if not diffs:
        print("  none - nothing has changed since it was pinned")
    for r in diffs:
        print(f"\n  {r['run']} :: {r['tool']} :: {r['rule']}")
        for line in r["diff"].splitlines():
            print("    " + line)

    # ---- the replay --------------------------------------------------------
    print()
    print(L.BAR)
    print("  REGRESSION REPLAY - the clean run, re-checked against the trust")
    print("  list as it stands now. No model runs.")
    print(L.BAR)
    clean = [r for r in recs
             if r["kind"] == "result" and r["run"].startswith("clean")]
    if not clean:
        print("  no clean run on file to replay")
    else:
        ok = True
        for r in clean:
            text = r.get("text", "")
            _, refused = verify.check_result("replay", r["tool"], text)
            verdict = "BLOCK" if refused else "  ok  "
            if refused:
                ok = False
            print(f"  {verdict}  {r['tool']}  {text.splitlines()[0][:44]!r}")
        print()
        if ok:
            print("  ^ Every message the clean run made is STILL ALLOWED. The tune")
            print("    cost nothing on legitimate traffic. That is the check that")
            print("    almost nobody runs, and it is why allow-lists get left loose.")
        else:
            print("  ^ THE TUNE BROKE LEGITIMATE TRAFFIC. In production this is the")
            print("    outage you ship at 2am. Loosen the rule and replay again.")

    print()
    print(L.BAR)
    print("  Submit: this output, plus tamper-log.jsonl and trust.json.")
    print("  The DIFF is the finding. Everything else is context.")
    print(L.BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
