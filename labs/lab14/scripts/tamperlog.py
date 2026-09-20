"""DETECT: print the tamper log. This is the buildable core of the lab.

    python tamperlog.py             every record
    python tamperlog.py --last      only the most recent run
    python tamperlog.py --diff      only the descriptor diffs

One record per gate, per run, PASS and BLOCK alike.

  MITRE ATLAS AML.M0024, AI Telemetry Logging: "implement logging of the
  intermediate steps of agentic actions and decisions, data access and tool use"

A log that only records blocks cannot tell you the check ran. That is why the
clean run writes PASS records and why this lab opens by reading them.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab14lib as L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", action="store_true")
    ap.add_argument("--diff", action="store_true")
    a = ap.parse_args()

    recs = L.read_log()
    if not recs:
        print("The tamper log is empty. Run ask.py first.")
        return

    if a.last:
        last = recs[-1]["run"]
        recs = [r for r in recs if r["run"] == last]

    if a.diff:
        shown = 0
        for r in recs:
            if r.get("diff"):
                shown += 1
                print(f"\n=== {r['run']} :: {r['tool']} :: {r['rule']} ===")
                print(f"  pinned    sha256:{r.get('pinned','?')[:16]}...")
                print(f"  advertised sha256:{r.get('sha256','?')[:16]}...")
                print()
                for line in r["diff"].splitlines():
                    print("  " + line)
        if not shown:
            print("No descriptor diffs logged. Nothing has changed since it was pinned.")
        return

    run = None
    for r in recs:
        if r["run"] != run:
            run = r["run"]
            print(f"\n=== run: {run} " + "=" * max(0, 54 - len(str(run))))
        if r["kind"] == "outcome":
            print(f"  ---- chain: {r.get('chain')}   payment made: {r.get('paid')}")
            continue
        print(L.verdict_line(r))
        if r.get("diff"):
            print("        (a diff was logged - see `python tamperlog.py --diff`)")
    print()


if __name__ == "__main__":
    main()
