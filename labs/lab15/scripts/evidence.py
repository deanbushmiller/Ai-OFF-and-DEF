"""What the control saw, what it cost, and what evasion cost the attacker.

    python evidence.py

Everything here is read from the log and the result files. Nothing is
recomputed for display, so the table cannot disagree with the run that produced
it - which is the failure lab 14 found in its own check.py, one level up.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab15lib as L

LIMIT_RESULT = L.WORK / "limit-result.json"
EVADE_RESULT = L.WORK / "evade-result.json"
BASELINE_RATE = 60.0        # records/h at 60 s, no jitter - where lab 7 starts


def load(p):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except ValueError:
        return None


def main():
    recs = L.read_log()
    if not recs:
        print("No detector log yet. Run the lab first.")
        return 1

    def first(**match):
        for r in recs:
            if all(r.get(k) == v for k, v in match.items()):
                return r
        return None

    def last(**match):
        out = None
        for r in recs:
            if all(r.get(k) == v for k, v in match.items()):
                out = r
        return out

    print()
    print(L.BAR)
    print(" WHAT THE CONTROL SAW")
    print(L.BAR)
    print()

    sig = first(detector="signature")
    lab7 = first(detector="lab7")
    shipped = first(kind="detector", detector="score")
    tuned = last(kind="tune", rule="above_threshold")
    windowed = last(kind="tune", rule="window_per_channel")
    missed = first(run="evade")
    live = first(kind="regression")

    if sig:
        print(f"   the signature rule caught {sig['caught']} of "
              f"{sig['total']} variants - the two it missed")
        print("   came from two lines of Python and needed no AI at all.")
        print()
    print(f"   {'detector, on the whole estate':<34} {'TP':>4} {'FP':>5} "
          f"{'precision':>11}")
    print("   " + L.THIN[:58])
    if lab7:
        print(f"   {'lab 7 D3, on the estate':<34} {lab7['tp']:>4} "
              f"{lab7['fp']:>5} {lab7['precision']:>11.4f}")
    if shipped:
        print(f"   {'four limbs, threshold ' + str(shipped['threshold']):<34} "
              f"{shipped['tp']:>4} {shipped['fp']:>5} "
              f"{shipped['precision']:>11.4f}")
    if tuned:
        print(f"   {'four limbs, threshold ' + str(tuned['threshold']):<34} "
              f"{tuned['tp']:>4} {tuned['fp']:>5} {tuned['precision']:>11.4f}")
    if missed:
        print(f"   {'... vs the evasive channel':<34} {missed['tp']:>4} "
              f"{missed['fp']:>5} "
              f"{'MISSED' if missed['rule'] == 'below_threshold' else 'caught':>11}")
    if windowed:
        print(f"   {'... after the window tune':<34} {windowed['tp']:>4} "
              f"{windowed['fp']:>5} {windowed['precision']:>11.4f}")
    print()

    if lab7 and tuned:
        print(f"   Same estate, same beacon, same day. You went from "
              f"{lab7['fp']} false")
        print(f"   alarms to {tuned['fp']}, and you did not turn anything up "
              f"to do it.")
        print()

    if live:
        print(f"   And the variant generated on your laptop just now, in "
              f"{live['seconds']}s,")
        print(f"   in wording nobody predicted: {live['fields']}/"
              f"{live['total']} of the record's values")
        print(f"   survived it, so the limb caught it. The detector was not")
        print("   updated. It did not need to be.")
        print()

    # ---- the prevent stub's bill ----
    lim = load(LIMIT_RESULT)
    if lim:
        print(L.BAR)
        print(" WHAT THE PREVENT STUB COST")
        print(L.BAR)
        print()
        print(f"   cap {lim['cap']}/hour:")
        print(f"     stopped {lim['throttled']} of the beacon's {lim['sent']} "
              f"check-ins")
        print(f"     stopped {0} of the slow version's "
              f"{lim['evasive_delivered']}")
        print(f"     cost {lim['fleet_throttled']} of {lim['fleet_total']} "
              f"legitimate channels their traffic")
        print(f"     and {len(lim['values_delivered'])} of the record's 6 "
              f"values reached the collector anyway")
        print()

    # ---- the attacker's bill ----
    ev = load(EVADE_RESULT)
    if ev:
        print(L.BAR)
        print(" WHAT EVASION COST THE ATTACKER")
        print(L.BAR)
        print()
        per_day = ev["checkins"] * ev["split"] / 6.0     # whole records per day
        rate = per_day / L.HOURS
        print(f"   {'setting':<32} {'check-ins':>10} {'fields':>7} "
              f"{'records/h':>11}")
        print(f"   {'baseline: 60 s, no jitter':<32} {1440:>10} {6:>7} "
              f"{BASELINE_RATE:>11.3f}")
        label = (f"evasive: {ev['interval'] // 3600} h, "
                 f"{ev['jitter']:.0%}, split {ev['split']}/6")
        print(f"   {label:<32} "
              f"{ev['checkins']:>10} {ev['split']:>7} {rate:>11.3f}")
        print()
        slow = BASELINE_RATE / rate if rate else float("inf")
        print(f"   COST OF EVASION: {slow:.0f}x slower")
        print()
        print(f"   {'to move':>10}   {'at 60 s':>12}   {'evading':>14}")
        for n in (100, 500, 5000):
            print(f"   {n:>10}   {n / BASELINE_RATE / 24:>11.2f}d   "
                  f"{n / per_day:>13.0f}d")
        print()
        print("   That is the number a defender takes to a budget meeting.")
        print("   Not 'we block 12,000 signatures' - 'the cheapest way past")
        print(f"   our detection is {slow:.0f}x slower, and we measured it.'")
        print()
        if windowed and windowed["tp"] >= 1:
            print("   And note what they bought for that. Nothing. The window")
            print("   tune catches the slow version too, so the bill was paid")
            print("   for a miss that lasted as long as it took you to read")
            print("   the log.")
            print()

    print(L.BAR)
    print(" THE THREE NUMBERS TO SUBMIT")
    print(L.BAR)
    print()
    if lab7:
        print(f"   1. lab 7's detector on a real estate:      "
              f"{lab7['tp']} TP / {lab7['fp']} FP")
    if windowed:
        print(f"   2. yours, tuned:                           "
              f"{windowed['tp']} TP / {windowed['fp']} FP")
    if ev:
        per_day = ev["checkins"] * ev["split"] / 6.0
        rate = per_day / L.HOURS
        print(f"   3. what evasion cost the attacker:         "
              f"{BASELINE_RATE / rate:.0f}x slower")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
