"""Expert-mode self-check. Confirms the evidence is real, without walking through it.

    python check.py

Beginner mode asserts as it goes and cannot finish in a wrong state. Expert mode
has no rails: the student ran the commands in their own order, possibly with
their own interval and jitter, possibly with a different set of formats. This
says whether it worked.

It checks the recorded numbers, not screen text. An expert who chose 10800s /
90% jitter instead of 7200s / 95% gets a different slowdown, and that is fine -
what must hold is the structure: content variation beat D1 only where the model
was not involved, D2 caught everything, and going clean on D3 cost throughput.
"""
import json
import pathlib
import sys

WORK = pathlib.Path("/labs/lab7")
VARIANTS = WORK / "variants.json"
RESULTS = WORK / "results.json"
LOG = WORK / "collector.log"

OK, BAD = "  PASS  ", "  FAIL  "
problems = []


def check(label, condition, hint):
    print((OK if condition else BAD) + label)
    if not condition:
        problems.append(hint)


def main():
    print("=" * 68)
    print(" LAB 7 SELF-CHECK")
    print("=" * 68)
    print()

    if not RESULTS.exists():
        print("No results.json. Run at least these:")
        print("    python variants.py --formats json,csv,kv,xml,urlq")
        print("    python variants.py --encode base64,hex")
        print("    python beacon.py --all")
        print("    python detect.py --signature")
        print("    python detect.py --structural")
        print("    python detect.py --behaviour --interval 7200 --jitter 0.95")
        return 1

    res = json.loads(RESULTS.read_text())
    store = json.loads(VARIANTS.read_text()) if VARIANTS.exists() else {}
    model = {k: v for k, v in store.items() if v["source"] == "model"}
    py = {k: v for k, v in store.items() if v["source"] == "python"}

    check("the model generated variants", len(model) >= 3,
          "fewer than 3 model variants - run: python variants.py "
          "--formats json,csv,kv,xml,urlq")
    if model:
        complete = [k for k, v in model.items() if not v["missing"]]
        check("every field survived every model variant",
              len(complete) == len(model),
              "a model variant lost fields: "
              + ", ".join(k for k in model if model[k]["missing"])
              + ". ini and syslog do this - they were measured and are not in "
                "the format list for that reason.")

    check("base64 and hex were produced in python", len(py) >= 2,
          "run: python variants.py --encode base64,hex")

    check("the collector received them",
          LOG.exists() and len(LOG.read_text().splitlines()) >= len(store),
          "collector.log is short or missing - run: python beacon.py --all")

    sig = res.get("signature")
    check("the signature detector ran", bool(sig),
          "run: python detect.py --signature")
    if sig:
        check("the signature rule missed something",
              len(sig["missed"]) > 0,
              "D1 caught everything. Did you send the base64 and hex variants? "
              "They are the only two that get past it.")
        from_model = [m for m in sig["missed"]
                      if store.get(m, {}).get("source") == "model"]
        check("nothing the MODEL wrote got past the signature rule",
              len(from_model) == 0,
              "a model variant got past D1: " + ", ".join(from_model)
              + ". That is new - it did not happen in any measured run. Tell "
                "the instructor, it is interesting.")

    struct = res.get("structural")
    check("the structural detector ran", bool(struct),
          "run: python detect.py --structural")
    if struct:
        check("the structural detector caught everything",
              struct["caught"] == struct["total"],
              f"D2 missed {struct['missed']}. It should catch all of them - "
              "if you added a variant by hand it may have dropped fields.")

    beh = res.get("behaviour")
    check("the behavioural detector ran", bool(beh),
          "run: python detect.py --behaviour")
    if beh:
        check("you got under the behavioural detector",
              beh["flagged"] is False,
              "still FLAGGED at interval="
              f"{beh['interval']:g}s jitter={beh['jitter']:.0%}. Jitter alone "
              "will not do it - the volume limb counts, and it does not care "
              "how irregular you are. Try: --interval 7200 --jitter 0.95")
        if beh["flagged"] is False:
            check("and it cost you throughput",
                  beh["records_per_hour"] < 60.0,
                  "you are clean AND as fast as the baseline, which should be "
                  "impossible with the volume limb in play. Tell the instructor.")

    print()
    print("=" * 68)
    if problems:
        print(f" {len(problems)} thing(s) to look at:")
        for p in problems:
            print("   - " + p)
        print("=" * 68)
        return 1

    rate = (beh or {}).get("records_per_hour") or 60.0
    print(" Everything checks out.")
    print("")
    print(f" You rendered one record {len(store)} ways, {len(model)} of them with a")
    print(" language model. The signature rule missed exactly the renderings the")
    print(" model could NOT produce. A twenty-line detector that ignores format")
    print(" caught all of them. And the detector that never read your payload at")
    print(f" all cost you {60.0 / rate:.0f}x throughput to get under.")
    print("")
    print(" MITRE ATLAS AML.T0016.002 -> AML.T0043.003 -> AML.T0015")
    print(" Case studies AML.CS0000 (C2 traffic detector) and AML.CS0044 (LAMEHUG)")
    print(" OWASP LLM10:2026 Improper Output Handling, Scenario #2")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())
