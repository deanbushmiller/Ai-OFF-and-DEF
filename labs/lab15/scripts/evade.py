"""The operator noticed they were caught, and changed how they check in.

    python evade.py               slow, jittered, and split across check-ins
    python evade.py --split 1     one value per check-in. Expert mode

THIS IS NOT AN ATTACK EXERCISE AND THERE IS NO SEARCH LOOP
-----------------------------------------------------------
One configuration, fixed, chosen by us and written down. The student does not
tune it, does not score variants against the detector, and is never asked to
find a setting that passes. That loop is an offensive tool no matter whose badge
it wears - rejected by the instructor at lab 7, 2026-09-13, and the rule holds
pointed either way.

What this command exists for is the beat the whole defend half is built around:
YOUR CONTROL WILL MISS SOMETHING, AND YOU FIND OUT FROM THE LOG.

THE THREE MOVES, AND WHY THEY WORK TOGETHER
-------------------------------------------
    interval 60 s  -> 4 h      kills limb 3, volume
    jitter 0 -> 90%            kills limb 2 at lab 7's cv < 0.35 ... and NOT
                               at ours. 90% jitter is cv 0.68, still nothing
                               like a person. This move fails, and that is the
                               point of limb 2's threshold
    split 2 of 6 values        kills limb 4, because no single message carries
                               enough of the record to reach 4 fields

Only rarity survives, the score falls to 2, and a threshold of 4 misses it.

The attacker paid for all three. evidence.py prices it.
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab15lib as L

CHANNEL = f"{L.BEACON_HOST}->{L.BEACON_DEST}"
RESULT = L.WORK / "evade-result.json"

EVASIVE_INTERVAL = 14400        # 4 hours
EVASIVE_JITTER = 0.90


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=int, default=2, choices=(1, 2, 3),
                    help="values per check-in, out of the record's 6")
    args = ap.parse_args()

    if not L.ESTATE.exists():
        print("No estate yet. Run:  python estate.py --build")
        return 1

    chans = L.load_estate()
    cfg = L.load_detector()
    counts = L.dest_host_counts(chans)
    vals = sorted(L.field_values())

    # The beacon channel is REPLACED, not added: it is the same operator on the
    # next day, not a second intruder. Adding one would quietly double the
    # estate's true positives and make every precision number wrong.
    times = L.schedule_times(EVASIVE_INTERVAL, EVASIVE_JITTER, seed=7742)
    for c in chans:
        if c["malicious"]:
            c["times"] = times
            c["interval"] = EVASIVE_INTERVAL
            c["jitter"] = EVASIVE_JITTER
            c["software"] = "beacon-evasive"
    L.ESTATE.write_text(json.dumps(chans))

    # New day, new log. The old renderings are last night's traffic.
    if L.COLLECTOR_LOG.exists():
        L.COLLECTOR_LOG.unlink()

    print(L.BAR)
    print(" THE NEXT DAY")
    print(L.BAR)
    print()
    print("   Same workstation, same destination, same record to move. The")
    print("   operator changed three things and nothing else:")
    print()
    print(f"     interval   60 s   ->  {EVASIVE_INTERVAL} s  ({EVASIVE_INTERVAL // 3600} h)")
    print(f"     jitter     0%     ->  {EVASIVE_JITTER:.0%}")
    print(f"     payload    all 6 values -> {args.split} per check-in")
    print()

    proc, reused = L.start_collector()
    if proc is None and not reused:
        print("   The collector did not come up on 127.0.0.1:8015.")
        return 1

    messages = []
    try:
        i = 0
        for n, t in enumerate(times):
            chunk = ", ".join(vals[(i + k) % 6] for k in range(args.split))
            i = (i + args.split) % 6
            messages.append(chunk)
            code = L.post(chunk, CHANNEL, f"split{args.split}", "python",
                          hour=int(t // 3600))
            if code != 200:
                L.stop_collector(proc)
                print(f"   unexpected HTTP {code} from the collector.")
                return 1
    finally:
        L.stop_collector(proc)

    print(f"   {len(times)} check-ins delivered. Here is every one of them:")
    print()
    for m in messages:
        print(f"     {m}")
    print()

    lim = cfg["limits"]
    per_msg = max(L.content_hits(m)[0] for m in messages)
    cv = L.cadence(times, lim["min_events"])

    print(L.BAR)
    print(" WHAT THE DETECTOR SEES")
    print(L.BAR)
    print()
    beacon = next(c for c in chans if c["malicious"])
    l = L.limbs(beacon, counts, cfg, L.payload_for(beacon))
    s, alert = L.verdict(l, cfg)
    w = cfg["weights"]
    print(f"   {'limb':<18} {'fires':>6} {'weight':>7}   why")
    print(f"   {'rare_dest':<18} {('YES' if l['rare_dest'] else 'no'):>6} "
          f"{w['rare_dest']:>7}   one host has ever contacted that address")
    print(f"   {'machine_cadence':<18} {('YES' if l['machine_cadence'] else 'no'):>6} "
          f"{w['machine_cadence']:>7}   "
          + (f"cv {cv:.3f}" if cv is not None else
             f"only {len(times)} events - below min_events "
             f"{lim['min_events']}, cannot judge"))
    print(f"   {'high_volume':<18} {('YES' if l['high_volume'] else 'no'):>6} "
          f"{w['high_volume']:>7}   {len(times)} check-ins, cap is "
          f"{lim['volume_max']}")
    print(f"   {'record_values':<18} {('YES' if l['record_values'] else 'no'):>6} "
          f"{w['record_values']:>7}   best single message carries {per_msg} of "
          f"6, needs {lim['min_fields']}")
    print()
    print(f"   SCORE {s}    THRESHOLD {cfg['threshold']}    "
          f"VERDICT {'ALERT' if alert else 'MISSED'}")
    print()

    tp, fp, fn, _ = L.confusion(chans, counts, cfg, L.payload_for)
    print(f"   Across the estate: TP {tp}   FP {fp}   FN {fn}")
    print()
    if not alert:
        print("   Your detector missed it, and it did not miss it by much.")
        print("   Three of four limbs went dark and the fourth is not worth 4")
        print("   on its own - deliberately, because 72 innocent browsing")
        print("   channels are also rare.")
        print()
        print("   So do NOT reach for the threshold. You already measured what")
        print("   that costs: threshold 3 is 72 false positives. The dial is")
        print("   not the fix and it never was.")
        print()
        print("   Look at the messages above instead. Every value of the")
        print("   record is in there. Not in any ONE of them - across all of")
        print("   them. Your limb asks the wrong question, not at the wrong")
        print("   level.")
        print()
        print("       python detect.py --window channel")
        print()

    RESULT.write_text(json.dumps({
        "interval": EVASIVE_INTERVAL, "jitter": EVASIVE_JITTER,
        "split": args.split, "checkins": len(times),
        "cv": (round(cv, 3) if cv is not None else None),
        "best_per_message": per_msg,
        "score": s, "threshold": cfg["threshold"], "alert": alert,
        "tp": tp, "fp": fp, "fn": fn,
        "values_delivered": sorted(L.delivered_values()),
    }, indent=2) + "\n")
    L.log(run="evade", kind="detector", detector="score",
          rule="above_threshold" if alert else "below_threshold",
          threshold=cfg["threshold"], window=cfg["window"],
          score=s, tp=tp, fp=fp, fn=fn, limbs=l)
    return 0


if __name__ == "__main__":
    sys.exit(main())
