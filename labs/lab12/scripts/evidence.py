"""The block the student pastes into the class chat.

Four lines from the log, in order, and they only mean something together: the
clean pass, the injection that was stopped, the injection that was NOT stopped,
and the same injection stopped after the tune.
"""
import sys

sys.path.insert(0, "/labs/lab12")
from lab12lib import load_rules, log_read

W = 68


def main():
    records = log_read()
    rules = load_rules()

    print()
    print("=" * W)
    print(" LAB 12 EVIDENCE - paste this whole block")
    print("=" * W)
    print()
    print(f"  {'page':<24} {'dir':<4} {'sev':<9} {'det':<6} {'filt':<6} verdict")
    print(f"  {'-'*24} {'-'*4} {'-'*9} {'-'*6} {'-'*6} -------")
    for r in records:
        page = r["url"].rsplit("/", 1)[-1]
        sev = r.get("severity", "-")
        det = str(r.get("detected")).lower()
        filt = str(r.get("filtered")).lower()
        verdict = "BLOCKED" if r.get("filtered") else "allowed"
        print(f"  {page:<24} {r['direction'][:3]:<4} {sev:<9} {det:<6} "
              f"{filt:<6} {verdict}")

    leaked = [r for r in records
              if r.get("detected") and not r.get("filtered")]
    print()
    print(f"  block_at is now: {rules['block_at']}")
    print(f"  requests detected but not filtered: {len(leaked)}")
    print()
    print("  The line that matters is the one where detected=true and")
    print("  filtered=false. The firewall saw it and let it through.")
    print()
    print("=" * W)
    print()


if __name__ == "__main__":
    main()
