"""Confirm the control actually held. Expert mode; the runner calls it too.

    python check.py

EVERY ASSERTION KEYS ON A RULE TOKEN, A COUNT, OR THE COLLECTOR'S OWN STORE -
NEVER ON PROSE, INCLUDING OUR OWN.

Lab 13 established it for the MODEL's output: under a tightened policy the model
said "I have verified that the admin box is readable" when it had verified
nothing. Lab 14 found the same trap one step closer to home - a runner assertion
matched OUR sentence "does not match its pin", somebody reworded the message
during a cosmetic fix, and the lab died with LAB ERROR. The fault was in the
assertion, not the lab. We reword our own text far more often than the model
rewords its.

AND CHECK 8 IS THE ONE THAT MATTERS MOST.

Lab 14's hardest-won rule: a detect-and-log control will happily log a clean
bill of health for a configuration that protects nothing. At least one assertion
has to measure the PROTECTED ASSET directly. Here that asset is the record, and
check 8 reads how many of its six values actually reached the collector, from
the collector's own store. A detector that alerted on all 193 channels would
score 100% recall and protect nothing; only check 8 would notice.

Exit 0 if every check passes, 1 otherwise.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab15lib as L

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  - {detail}" if detail else ""))


def main():
    recs = L.read_log()
    if not recs:
        print("No detector log. Run the lab first.")
        return 1

    def first(**m):
        for r in recs:
            if all(r.get(k) == v for k, v in m.items()):
                return r
        return None

    def last(**m):
        out = None
        for r in recs:
            if all(r.get(k) == v for k, v in m.items()):
                out = r
        return out

    print("\n" + L.BAR)
    print("  check.py - did the control hold?")
    print(L.BAR)

    cfg = L.load_detector()
    vals = L.field_values()
    variants = L.load_variants()

    # 1. the content limb catches every one of lab 7's measured variants.
    #    Recomputed from the shipped bodies, not read back from a verdict.
    caught = sum(1 for v in variants.values()
                 if L.content_hits(v["text"], vals)[0] >= cfg["limits"]["min_fields"])
    check("the record_values limb catches every measured variant",
          caught == len(variants),
          f"{caught}/{len(variants)}, including base64 and hex")

    # 2. ... and the signature rule does not. The contrast is the lesson.
    sig = sum(1 for v in variants.values() if L.signature_limb(v["text"]))
    check("the signature rule misses the two encodings",
          sig == len(variants) - 2,
          f"{sig}/{len(variants)} - base64 and hex need no AI at all")

    # 3. the controls do not trip. Required by the conventions file:
    #    "Always ship the random-noise control."
    controls = {
        "clean-telemetry": ("agent_id=EDR-AGENT-0041, host=WKSTN-09, "
                            "user=mroberts, ts=2026-09-13T14:02:11Z, seq=1, "
                            "status=idle"),
        "clean-backup": ("job=nightly-full, host=WKSTN-09, bytes=4182233, "
                         "ts=2026-09-13T02:11:00Z, status=ok"),
        "noise-1": "kQ3mZ, pL9wX=7, tR2v, hN8c=aa, wE4q, zY6b=idle",
        "noise-2": "8f2a1c, 0xDEADBEEF, ..., ---, ???, 000000",
        "noise-3": "the quick brown fox jumps over the lazy dog, twice, daily",
        "noise-base64": "zK9xQm4pLw7vRt2yHn5bJc8dFg3sAe6uXi1oZk0qYw==",
    }
    tripped = [n for n, t in controls.items()
               if L.content_hits(t, vals)[0] >= cfg["limits"]["min_fields"]]
    check("no clean or random-noise control trips the limb",
          not tripped,
          f"0/{len(controls)}" if not tripped else f"tripped: {tripped}")

    # 4. lab 7's detector on the estate is genuinely bad. If this stops being
    #    true the estate has drifted and the whole lab's premise is gone.
    l7 = first(detector="lab7")
    if l7:
        check("lab 7's detector on the estate is high-recall, low-precision",
              l7["tp"] >= 1 and l7["fp"] > 100,
              f"TP {l7['tp']} / FP {l7['fp']}, precision {l7['precision']}")

    # 5. the tuned threshold separates cleanly
    t = last(kind="tune", rule="above_threshold")
    if t:
        check("at the tuned threshold the estate is clean",
              t["tp"] >= 1 and t["fp"] == 0,
              f"TP {t['tp']} / FP {t['fp']} at threshold {t['threshold']}")

    # 6. THE DELIBERATE MISS. This one is SUPPOSED to fail to alert, and the
    #    lab is broken if it does not - there would be nothing to recover from.
    ev = first(run="evade")
    if ev:
        check("the split-payload channel was MISSED before the tune",
              ev["rule"] == "below_threshold",
              f"score {ev.get('score')} < threshold {ev.get('threshold')}")

    # 7. and the window tune catches it, at no cost in false positives
    w = last(rule="window_per_channel")
    if w:
        check("the window tune catches it",
              w["tp"] >= 1, f"TP {w['tp']}")
        check("and the wider window cost no false positives",
              w["fp"] == 0, f"FP {w['fp']}")

    # 8. THE PROTECTED ASSET, measured at the collector's own store.
    #    Not a verdict. Not a count of alerts. What actually left.
    delivered = L.delivered_values()
    check("the record's delivered values are measured, not inferred",
          isinstance(delivered, set) and len(delivered) > 0,
          f"{len(delivered)}/{len(vals)} of the record reached the collector")

    lim = L.WORK / "limit-result.json"
    if lim.exists():
        d = json.loads(lim.read_text())
        # The uncomfortable one. The cap throttled most of the traffic and the
        # record left anyway. If this ever came out the other way the lab would
        # be teaching that rate limiting is a data-loss control. It is not.
        check("the rate cap throttled traffic and did NOT stop the record",
              d["throttled"] > 0 and len(d["values_delivered"]) == len(vals),
              f"{d['throttled']}/{d['sent']} stopped, "
              f"{len(d['values_delivered'])}/{len(vals)} values out anyway")
        check("and the cap cost legitimate channels their traffic",
              d["fleet_throttled"] > 0,
              f"{d['fleet_throttled']} of {d['fleet_total']} innocent channels")

    # 9. the live-generated variant, if the student ran it. Asserted on the
    #    FIELD COUNT, never on the model's wording.
    live = first(kind="regression")
    if live:
        check("the freshly generated variant was caught by field count",
              live["fields"] >= cfg["limits"]["min_fields"],
              f"{live['fields']}/{live['total']} values survived wording "
              f"nobody predicted")

    print(L.BAR)
    print(f"  {len(PASS)} of {len(PASS) + len(FAIL)} PASS")
    print(L.BAR + "\n")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
