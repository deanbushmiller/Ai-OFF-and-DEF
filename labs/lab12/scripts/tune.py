"""Close the gap the log revealed: tighten the gate by one step.

    python tune.py

This is the recovery beat, and it is deliberately one field. A real rule change
is a ticket, an owner, a review and a deploy; the shape is the same and the
scale is not. What matters is the sequence, which this lab does in full:
a control failed -> the log showed it -> the gap was closed -> the fix was
verified against the attack AND against legitimate traffic.

That last clause is the one people skip. A gate you tighten without re-testing
the clean case is how thresholds end up loose in the first place: somebody
tightened one, broke real traffic, got shouted at, and widened it back further
than it started.
"""
import json
import pathlib
import sys

sys.path.insert(0, "/labs/lab12")
from lab12lib import ORDER, RULES

W = 68


def main():
    rules = json.loads(RULES.read_text())
    before = rules["block_at"]

    if before == "MEDIUM":
        print("\n  block_at is already MEDIUM - the tightest this gate goes.\n")
        return

    after = ORDER[ORDER.index(before) - 1]
    rules["block_at"] = after

    # Rewrite in place, preserving the file's shape so the student can diff it.
    RULES.write_text(json.dumps(rules, indent=2) + "\n")

    print()
    print("=" * W)
    print(" RULE CHANGE")
    print("=" * W)
    print()
    print("  rules.json, one field:")
    print()
    print(f'    - "block_at": "{before}"')
    print(f'    + "block_at": "{after}"')
    print()
    print(f"  The firewall will now stop anything it rates {after} or worse.")
    print("  Nothing else changed: same detector families, same phrases, same")
    print("  model, same pages.")
    print()
    print("  Two things to check next, and you need BOTH:")
    print(f"    1. the page that leaked is now blocked")
    print(f"    2. the clean page still gets through")
    print()
    print("=" * W)
    print()


if __name__ == "__main__":
    main()
