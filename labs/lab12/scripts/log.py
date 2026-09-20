"""Read the firewall's request log back in a form a person can act on.

    python log.py

The log is the point of this lab. A firewall that blocks is useful; a firewall
that blocks AND writes down what it saw is the only kind you can tune, because
tuning needs evidence of what got through, and what got through is by
definition the thing you did not notice.

MITRE ATLAS AML.M0024, against indirect prompt injection, in its own words:
"Telemetry logging can help identify if unsafe prompts have been submitted to
the LLM."
"""
import sys

sys.path.insert(0, "/labs/lab12")
from lab12lib import log_read

W = 68


def main():
    records = log_read()
    if not records:
        print("\n  The log is empty. Run firewall.py against a page first.\n")
        return

    print()
    print("=" * W)
    print(" FIREWALL REQUEST LOG")
    print("=" * W)

    leaks = []
    for i, r in enumerate(records, 1):
        page = r["url"].rsplit("/", 1)[-1]
        detected = r.get("detected")
        filtered = r.get("filtered")

        if r["direction"] == "inbound":
            fams = ",".join(r["families"]) or "-"
            print(f"\n  {i:>2}. IN   {page}")
            print(f"      severity {r['severity']:<9} block_at {r['block_at']:<9}"
                  f" families: {fams}")
        else:
            hit = ",".join(r["rules_matched"]) or "-"
            print(f"\n  {i:>2}. OUT  {page}")
            print(f"      rules: {hit}")
            for name, redacted in sorted(r.get("markers", {}).items()):
                print(f"      {name} = {redacted}")

        verdict = "BLOCKED" if filtered else "allowed"
        print(f"      detected={str(detected).lower():<6} "
              f"filtered={str(filtered).lower():<6} -> {verdict}")

        # The signature worth learning: a rule fired and nothing was done.
        if detected and not filtered:
            print("      ^ A RULE MATCHED AND THE REQUEST WAS ALLOWED THROUGH.")
            leaks.append((i, page, r.get("severity"), r.get("block_at")))

    print()
    print("=" * W)
    if leaks:
        print(" WHAT THE LOG IS TELLING YOU")
        print("=" * W)
        for i, page, sev, floor in leaks:
            print(f"\n  Request {i}, {page}: the firewall rated it {sev} and was")
            print(f"  set to block only at {floor}, so it let it through.")
        print("\n  The firewall was not blind. It saw the injection, scored it,")
        print("  wrote it down, and did nothing - because the threshold said so.")
        print("  That is CVE-2026-60086 in one line of a log file.")
        print("\n  Read the threshold:   cat rules.json")
    else:
        print(" No request was detected and allowed. Nothing got past the gate.")
    print("=" * W)
    print()


if __name__ == "__main__":
    main()
