"""Expert-mode verification. Did you actually close the gap?

    python check.py

Every check is read from the log and the rule file - nothing is re-generated,
so this costs no model time. Exits 1 if any check fails, so it is also what the
build's own test harness runs.
"""
import re
import sys

sys.path.insert(0, "/labs/lab12")
from lab12lib import LOG, load_rules, log_read

W = 68
results = []


def check(label, ok, detail=""):
    results.append((label, ok, detail))


def main():
    rules = load_rules()
    records = log_read()
    pattern = rules["outbound_patterns"]["sensitive_marker"]

    def inbound(page):
        return [r for r in records
                if r["direction"] == "inbound" and r["url"].endswith(page)]

    def outbound(page):
        return [r for r in records
                if r["direction"] == "outbound" and r["url"].endswith(page)]

    # 1. The gate was actually tightened.
    check("rules.json block_at is HIGH or tighter",
          rules["block_at"] in ("HIGH", "MEDIUM"),
          f"block_at = {rules['block_at']}")

    # 2. The clean page was allowed, and is STILL allowed after the tune.
    clean = inbound("article.html")
    check("the clean page was fetched at least once",
          len(clean) >= 1, f"{len(clean)} inbound record(s)")
    check("the clean page was never blocked",
          bool(clean) and not any(r["filtered"] for r in clean),
          "a tightened rule that breaks legitimate traffic is not a fix")

    # 3. The obvious injection was always blocked.
    pois = inbound("article-poisoned.html")
    check("article-poisoned.html was blocked",
          bool(pois) and all(r["filtered"] for r in pois),
          "4 families -> CRITICAL, blocked even at the shipped threshold")

    # 4. The leak page: allowed at first, blocked at the end. Both must be true,
    #    because the whole lesson is the change between them.
    leak = inbound("memo-leak.html")
    check("memo-leak.html was fetched at least twice",
          len(leak) >= 2, f"{len(leak)} inbound record(s)")
    check("memo-leak.html was ALLOWED while a rule matched (the leak)",
          any(r["detected"] and not r["filtered"] for r in leak),
          "detected=true, filtered=false - the CVE-2026-60086 signature")
    check("memo-leak.html is blocked by the LAST attempt",
          bool(leak) and leak[-1]["filtered"],
          "the tune has to actually stop it")

    # 5. The outbound scan caught the marker when the inbound scan did not.
    out_leak = outbound("memo-leak.html")
    check("the outbound scan caught the marker",
          any(r["detected"] and r["filtered"] for r in out_leak),
          "the second layer is what saved you")

    # 6. No value matching the sensitive pattern appears in plaintext anywhere
    #    the student is asked to hand over. This is a safety assertion, not a
    #    teaching one, and it must never fail.
    #
    #    Scope is the LOG and the TRANSCRIPT, which are the two files a student
    #    is told to copy out and paste into the class chat. It is deliberately
    #    not the source: firewall.py's system prompt does hold the key, because
    #    a secret sitting in a system prompt is the anti-pattern this lab is
    #    about (OWASP LLM02:2026, Tier 1, prevention 4) and hiding it would hide
    #    the lesson.
    #
    #    This check caught a real one on 2026-09-19: rules.json used to carry the
    #    key itself, step 1 cats rules.json, and the runner logs every command's
    #    output - so the canary landed in the file students are asked to send to
    #    the instructor. The rule file now carries a pattern instead.
    leaked_plain = []
    for name, path in (("firewall-log.jsonl", LOG),
                       ("lab12-results.txt", LOG.parent / "lab12-results.txt")):
        if path.exists() and re.search(pattern, path.read_text(encoding="utf-8",
                                                               errors="replace")):
            leaked_plain.append(name)
    check("no value matching the sensitive pattern is in the log or transcript",
          not leaked_plain,
          ("found in: " + ", ".join(leaked_plain)) if leaked_plain
          else "log and transcript are clean")

    print()
    print("=" * W)
    print(" LAB 12 CHECK")
    print("=" * W)
    print()
    passed = 0
    for label, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}]  {label}")
        if detail:
            print(f"          {detail}")
        passed += ok
    print()
    print("=" * W)
    if passed == len(results):
        print(f" ALL {len(results)} CHECKS PASSED.")
        print("")
        print(" You found a control that was failing silently, you found it in")
        print(" the log rather than in an incident, and the fix cost one field")
        print(" and broke nothing. That is the whole loop.")
    else:
        print(f" {passed} of {len(results)} passed. Work through the failures above.")
    print("=" * W)
    print()
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
