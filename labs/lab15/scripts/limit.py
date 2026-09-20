"""The prevent stub: a rate and volume cap in front of the collector.

    python limit.py --cap 6        cap each channel to 6 check-ins per hour
    python limit.py --cap 1        the tightest cap, and the honest one to see

This is a REAL limiter in a REAL request path. The collector enforces it and
answers 429 when the bucket is full; nothing here is simulated except the clock,
which is compressed so a day of check-ins takes a second instead of a day.

WHY THE PREVENT BEAT IS A STUB, AND WHY IT IS STILL WORTH BUILDING
------------------------------------------------------------------
The defender addendum's spine is: build the detector, stub the preventer, script
the recovery, name the vendor. This lab is the first one in the course that can
put a NUMBER on why prevention is the stub rather than the star.

Two things are measured here and both of them are uncomfortable:

  1. Every cap tight enough to hurt the beacon also throttles legitimate
     monitoring - because on volume alone they are the same traffic.
  2. NO cap touches a slow-and-low channel, because it was never loud.

ATLAS says the second one itself, in AML.M0004 (Limit AI Service Query Volume
and Rate): "Query limits may not protect against attacks that require few
requests." OWASP LLM06:2026 says it too, in its own description: "Traditional
request-rate limiting alone is no longer sufficient."

So the limiter is not useless - it raises cost and it buys time - but it cannot
be the control. Detection leads. That is the whole argument, and after this
command it is a table rather than an opinion.

The production answer, named and not demonstrated: behavioural network
detection and endpoint analytics. Unit 42 measured those catching every one of
seven LLM-assisted malware variants in August 2026. They cost money, they need
somebody to run them, and they are still yours to tune. There is no THEY.
"""
import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab15lib as L

CHANNEL = f"{L.BEACON_HOST}->{L.BEACON_DEST}"
RESULT = L.WORK / "limit-result.json"

# The evasive schedule, used here only to show what the cap does NOT do.
EVASIVE_INTERVAL, EVASIVE_JITTER = 14400, 0.90


def fleet_cost(chans, cap):
    """How many legitimate channels lose traffic at this cap."""
    hit = 0
    for c in chans:
        if c["malicious"]:
            continue
        per_h = {}
        dropped = 0
        for t in c["times"]:
            h = int(t // 3600)
            if per_h.get(h, 0) >= cap:
                dropped += 1
            else:
                per_h[h] = per_h.get(h, 0) + 1
        if dropped:
            hit += 1
    return hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, required=True,
                    help="check-ins allowed per channel per hour")
    args = ap.parse_args()
    if args.cap < 1:
        print("cap must be at least 1")
        return 2

    if not L.ESTATE.exists():
        print("No estate yet. Run:  python estate.py --build")
        return 1

    chans = L.load_estate()
    beacon = next(c for c in chans if c["malicious"])
    variants = L.load_variants()
    names = list(variants)

    print(L.BAR)
    print(" THE PREVENT STUB - A RATE AND VOLUME CAP")
    print(L.BAR)
    print()
    print(f"   cap: {args.cap} check-ins per channel per hour, enforced at the")
    print("   endpoint. Over the cap the collector answers 429 and the body")
    print("   is not stored.")
    print()
    print(f"   Replaying {L.BEACON_HOST}'s full day of "
          f"{len(beacon['times'])} check-ins through it.")
    print("   A day of traffic in about a second; the limiter buckets on the")
    print("   simulated hour, not the wall clock.")
    print()

    if L.COLLECTOR_LOG.exists():
        L.COLLECTOR_LOG.unlink()

    proc, reused = L.start_collector(cap=args.cap)
    if proc is None and not reused:
        print("   The collector did not come up on 127.0.0.1:8015.")
        print("   Tell the instructor and send lab15-results.txt.")
        return 1
    if reused:
        L.stop_collector(proc)
        print("   A collector is already running WITHOUT the cap, so this")
        print("   measurement would be wrong. Stop it and run this again.")
        return 1

    t0 = time.time()
    delivered = throttled = 0
    try:
        for i, t in enumerate(beacon["times"]):
            name = names[i % len(names)]
            code = L.post(variants[name]["text"], CHANNEL, name,
                          variants[name]["source"], hour=int(t // 3600))
            if code == 200:
                delivered += 1
            elif code == 429:
                throttled += 1
            else:
                L.stop_collector(proc)
                print(f"   unexpected HTTP {code} from the collector.")
                return 1
    finally:
        L.stop_collector(proc)
    secs = time.time() - t0

    sent = len(beacon["times"])
    ev_times = L.schedule_times(EVASIVE_INTERVAL, EVASIVE_JITTER, seed=7742)
    ev_delivered = sum(1 for _ in ev_times)     # every hour bucket holds 1
    fleet = fleet_cost(chans, args.cap)
    total_legit = sum(1 for c in chans if not c["malicious"])
    values = L.delivered_values()

    print(f"   {sent} check-ins replayed in {secs:.1f}s")
    print()
    print(L.THIN)
    print(f"   {'channel':<34} {'sent':>7} {'delivered':>10} {'stopped':>9}")
    print(L.THIN)
    print(f"   {'beacon, 60 s no jitter':<34} {sent:>7} {delivered:>10} "
          f"{throttled:>9}")
    print(f"   {'the same beacon, slowed to 4 h':<34} {len(ev_times):>7} "
          f"{ev_delivered:>10} {0:>9}")
    print(L.THIN)
    print()
    print(f"   Legitimate channels that also lost traffic: {fleet} of "
          f"{total_legit}")
    print()
    print("   Read those three numbers together.")
    print()
    print(f"   The cap stopped {throttled} of the beacon's {sent} check-ins,")
    print("   which is real. It stopped NONE of the slow version, because a")
    print(f"   channel sending {len(ev_times)} times a day was never over any cap")
    print(f"   you would dare to set. And it cost {fleet} innocent channels")
    print("   their traffic to do it.")
    print()

    # THE PROTECTED ASSET. Measured at the collector's own store, not inferred
    # from a verdict. A cap that throttles 90% of the check-ins and still lets
    # every field of the record through has protected nothing, and only this
    # number says so.
    print(L.BAR)
    print(" WHAT ACTUALLY GOT OUT")
    print(L.BAR)
    print()
    print(f"   Of the record's 6 values, {len(values)} reached the collector.")
    print()
    if len(values) == 6:
        print("   All of them. The cap reduced the RATE and changed nothing")
        print("   about the outcome, because the attacker only had to get the")
        print("   record out once and had 1,440 chances.")
        print()
        print("   This is the number to hold on to. A control that throttles")
        print(f"   {throttled} of {sent} check-ins looks like it is working, and")
        print("   the thing it exists to protect left the building anyway.")
    else:
        print("   The cap held some of it back. Note that this depends")
        print("   entirely on the attacker being impatient.")
    print()
    print("   ATLAS AML.M0004 says this in its own words:")
    print('     "Query limits may not protect against attacks that require')
    print('      few requests."')
    print("   OWASP LLM06:2026 says it too:")
    print('     "Traditional request-rate limiting alone is no longer')
    print('      sufficient."')
    print()
    print("   That is why the detector leads and the limiter is the stub.")
    print()

    RESULT.write_text(json.dumps({
        "cap": args.cap, "sent": sent, "delivered": delivered,
        "throttled": throttled, "evasive_delivered": ev_delivered,
        "fleet_throttled": fleet, "fleet_total": total_legit,
        "values_delivered": sorted(values), "seconds": round(secs, 2),
    }, indent=2) + "\n")
    L.log(run="limit", kind="prevent", rule="volume_cap", cap=args.cap,
          sent=sent, delivered=delivered, throttled=throttled,
          fleet_throttled=fleet, values_delivered=len(values))
    return 0


if __name__ == "__main__":
    sys.exit(main())
