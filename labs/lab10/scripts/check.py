"""Expert-mode self-check.

    python check.py

Beginner mode asserts as it goes and cannot finish in a wrong state. Expert mode
has no rails: you ran the pieces in your own order and edited rules.json by hand.
This says whether the defence actually holds together.

It checks the recorded evidence, not what scrolled past on screen.
"""
import json
import pathlib
import sys

LAB = pathlib.Path("/labs/lab10")
RULES = LAB / "rules.json"
CANARY_LOG = LAB / "canary-log.jsonl"
RETRIEVAL_LOG = LAB / "retrieval-log.jsonl"
PURGE_LOG = LAB / "purge-log.json"

OK, BAD = "  PASS  ", "  FAIL  "
problems = []


def check(label, cond, hint):
    print((OK if cond else BAD) + label)
    if not cond:
        problems.append(hint)


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def main():
    print("=" * 68)
    print(" LAB 10 SELF-CHECK")
    print("=" * 68)
    print()

    rules = read_json(RULES, {})
    canary = read_jsonl(CANARY_LOG)
    retrieval = read_jsonl(RETRIEVAL_LOG)
    purge = read_json(PURGE_LOG, {})

    check("the canary ran and wrote a log",
          bool(canary),
          "run: python canary.py ask")

    check("the canary answered correctly at least once",
          any(c["holds"] for c in canary),
          "ask the canary BEFORE ingesting the poison, so you have a baseline")

    check("the canary was caught answering wrongly",
          any(not c["holds"] for c in canary),
          "ingest the poisoned PDF with --force, then ask the canary again")

    poisoned_drove = [c for c in canary
                      if not c["holds"] and c["top_source"].endswith(".pdf")]
    check("the retrieval log names the poisoned chunk as the source",
          bool(poisoned_drove),
          "the log should show poisoned_handbook.pdf driving the wrong answer")

    check("the retrieval log records scores for every retrieval",
          bool(retrieval) and all("retrieved" in r for r in retrieval),
          "run: python rag.py ask \"Who invented the telephone?\"")

    check("a purge was recorded",
          bool(purge.get("chunks_removed")),
          "run: python purge.py --untagged")

    check("the canary was restored after the purge",
          bool(canary) and canary[-1]["holds"] and any(not c["holds"] for c in canary),
          "purge, rebuild the index, then run: python canary.py check")

    untagged_left = [r for r in retrieval[-1:] if
                     any(h.get("tag") == "UNTAGGED" for h in r.get("retrieved", []))]
    check("no untagged chunk is still being retrieved",
          not untagged_left,
          "purge the untagged chunks and rebuild: python rag.py build")

    check("you added an indicator of your own to rules.json",
          bool(rules.get("blocked_indicators")),
          'add an indicator to blocked_indicators in rules.json, '
          'or run: python tune.py --add invisible-text')

    print()
    if problems:
        print(" NOT DONE YET. " + str(len(problems)) + " thing(s) to finish:")
        print()
        for hint in problems:
            print("   - " + hint)
        print()
        print("=" * 68)
        return 1

    print(" ALL CHECKS PASS.")
    print()
    print(" You have the four pieces of evidence the lab asks for:")
    print("   the validator's verdicts, the canary before and after, the")
    print("   retrieval log naming the poisoned chunk, and the restored canary.")
    print()
    print(" Paste the canary pair and the retrieval-log line into the class")
    print(" chat. The pair is the proof.")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())
