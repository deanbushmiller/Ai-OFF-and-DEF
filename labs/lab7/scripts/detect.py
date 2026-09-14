"""Three detectors, in increasing order of how hard they are to beat.

    python detect.py --signature     the one-line rule
    python detect.py --structural    twenty lines that ignore the format
    python detect.py --behaviour     cadence only, never reads the payload
    python detect.py --behaviour --interval 7200 --jitter 0.95

OURS, NOT A PRODUCT
-------------------
Every rule here was written for this lab. Nothing is tuned against a named EDR,
NDR or IDS, and no real product's rules are reproduced. D3 is a deliberately
crude two-limb version of the idea behind RITA's beacon score, which scores on
interval consistency AND data-size uniformity AND dispersion. Read RITA if you
want the real thing: https://github.com/activecm/rita

WHY D3 HAS TWO LIMBS, MEASURED
------------------------------
The first version keyed on regularity alone - flag a source whose inter-arrival
gaps have a coefficient of variation below 0.35. It collapses immediately:

    60 s interval, 0%  jitter   cv 0.000   FLAGGED   60.0 records/h
    60 s interval, 60% jitter   cv 0.358   clean     61.0 records/h

Jitter beats a regularity-only detector and makes the attacker slightly FASTER.
Cost of evasion: 1x. A lab built on that would claim evasion is expensive while
demonstrating that it is free.

Adding an orthogonal VOLUME limb fixes it, because no amount of jitter changes a
count. That is the whole finding, and it is the lab's best line: one detector
dimension is nearly free to beat, two force a real bill.

See lab-research/lab7/probe-transcripts/q3_detectors.py and q3b_twolimb.py.

THERE IS NO --tune FLAG AND THERE MUST NEVER BE ONE
---------------------------------------------------
A loop that tests variants against a detector and refines until one passes is an
offensive tool regardless of what the payload is. Rejected by the instructor
2026-09-13. The student sets two numbers by hand, twice, and reads the bill.
"""
import argparse
import base64
import json
import pathlib
import random
import re
import statistics
import sys

WORK = pathlib.Path("/labs/lab7")
LOG = WORK / "collector.log"
RECORD = WORK / "record.txt"
SCHEDULE = WORK / "schedule.txt"
RESULTS = WORK / "results.json"

MARKER = "LAB-BEACON-7742"

# D2 threshold: how many of the record's six values must survive to call it a hit.
D2_MIN_FIELDS = 4

# D3 limbs. Both are judgement calls, and the instructor confirmed these numbers
# on 2026-09-13 - they are what sets where a student lands and therefore what the
# closing number is. A real product baselines each host instead of using a fixed
# count; that is a simplification worth saying out loud in the debrief.
D3_VOLUME_MAX = 24      # check-ins per 24 h, one workstation to one destination
D3_CV_MAX = 0.35        # regularity: stdev/mean of the gaps
D3_MIN_EVENTS = 12      # below this there is not enough signal to judge cadence
WINDOW_H = 24


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def entries():
    if not LOG.exists() or not LOG.read_text().strip():
        print("collector.log is empty. Send something first:")
        print("    python beacon.py --all")
        sys.exit(1)
    return [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]


def field_values():
    rec = RECORD.read_text().strip()
    return {v.strip() for _, v in (p.split("=", 1) for p in rec.split(", "))}


def read_schedule():
    interval, jitter = 60.0, 0.0
    for line in SCHEDULE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = (x.strip() for x in line.split("=", 1))
        try:
            if k == "interval":
                interval = float(v)
            elif k == "jitter":
                jitter = float(v)
        except ValueError:
            pass
    return interval, jitter


def write_schedule(interval, jitter):
    """Keep the file and the run in step, so evidence.py cannot disagree."""
    out, seen_i, seen_j = [], False, False
    for line in SCHEDULE.read_text().splitlines():
        stripped = line.split("#", 1)[0].strip()
        if stripped.startswith("interval="):
            out.append(f"interval={interval:g}")
            seen_i = True
        elif stripped.startswith("jitter="):
            out.append(f"jitter={jitter:g}")
            seen_j = True
        else:
            out.append(line)
    if not seen_i:
        out.append(f"interval={interval:g}")
    if not seen_j:
        out.append(f"jitter={jitter:g}")
    SCHEDULE.write_text("\n".join(out) + "\n")


def save_result(key, value):
    store = {}
    if RESULTS.exists():
        try:
            store = json.loads(RESULTS.read_text())
        except ValueError:
            store = {}
    store[key] = value
    RESULTS.write_text(json.dumps(store, indent=2))


# ---------------------------------------------------------------------------
# D1 - signature
# ---------------------------------------------------------------------------
def d1(text):
    """The whole detector. One line, and it is what most deployed rules are."""
    return MARKER.lower() in text.lower()


def run_signature():
    rows = entries()
    print("=" * 68)
    print(" D1  SIGNATURE DETECTOR")
    print("=" * 68)
    print()
    print(f"   The entire rule:   '{MARKER}'.lower() in body.lower()")
    print()
    print(f"   {'variant':<10} {'source':<8} verdict")
    caught = []
    for e in rows:
        hit = d1(e["body"])
        caught.append(hit)
        print(f"   {e['variant']:<10} {e['source']:<8} "
              f"{'CAUGHT' if hit else '  miss  <--'}")
    n, total = sum(caught), len(caught)
    print()
    print(f"   D1 caught {n} of {total}.")
    save_result("signature", {"caught": n, "total": total,
                              "missed": [e["variant"] for e, h
                                         in zip(rows, caught) if not h]})
    return n, total


# ---------------------------------------------------------------------------
# D2 - structural
# ---------------------------------------------------------------------------
def d2(text, values):
    """Peel the surface off, then count how many of the record's VALUES survive.

    It never asks what format the body is in. It decodes anything that looks like
    base64 or hex, percent-decodes, splits on everything that is not part of a
    value, and counts.
    """
    t = text
    for tok in re.findall(r"[A-Za-z0-9+/=]{24,}", t):
        try:
            dec = base64.b64decode(tok + "===").decode("utf-8")
            if dec.isprintable():
                t += "\n" + dec
        except Exception:
            pass
    for tok in re.findall(r"\b[0-9a-fA-F]{24,}\b", t):
        try:
            dec = bytes.fromhex(tok).decode("utf-8")
            if dec.isprintable():
                t += "\n" + dec
        except Exception:
            pass
    t = re.sub(r"%3A", ":", t, flags=re.I)
    toks = set(re.split(r"[^A-Za-z0-9:.\-]+", t))
    hits = len(values & toks)
    return hits >= D2_MIN_FIELDS, hits


def run_structural():
    rows = entries()
    values = field_values()
    print("=" * 68)
    print(" D2  STRUCTURAL DETECTOR")
    print("=" * 68)
    print()
    print("   Twenty lines. It does not know what a format is:")
    print("     1. decode anything that looks like base64 or hex, in place")
    print("     2. percent-decode")
    print("     3. split on everything that is not part of a value")
    print(f"     4. how many of the record's {len(values)} values are still there?")
    print(f"        {D2_MIN_FIELDS} or more is a hit")
    print()
    print(f"   {'variant':<10} {'source':<8} {'fields':<8} verdict")
    caught = []
    for e in rows:
        hit, hits = d2(e["body"], values)
        caught.append(hit)
        print(f"   {e['variant']:<10} {e['source']:<8} "
              f"{hits}/{len(values):<6} {'CAUGHT' if hit else '  miss'}")
    n, total = sum(caught), len(caught)
    print()
    print(f"   D2 caught {n} of {total}.")
    save_result("structural", {"caught": n, "total": total,
                               "missed": [e["variant"] for e, h
                                          in zip(rows, caught) if not h]})
    return n, total


# ---------------------------------------------------------------------------
# D3 - behavioural
# ---------------------------------------------------------------------------
def schedule_times(interval_s, jitter_frac, seed=7, hours=WINDOW_H):
    """A fixed seed, so every student on every machine sees the same numbers."""
    rng = random.Random(seed)
    t, out = 0.0, []
    while t < hours * 3600:
        out.append(t)
        t += interval_s * (1 + rng.uniform(-jitter_frac, jitter_frac))
    return out


def d3(times):
    volume = len(times) > D3_VOLUME_MAX
    regular, cv = False, None
    if len(times) >= D3_MIN_EVENTS:
        gaps = [b - a for a, b in zip(times, times[1:])]
        cv = statistics.pstdev(gaps) / statistics.mean(gaps)
        regular = cv < D3_CV_MAX
    return volume, regular, cv


def run_behaviour(interval=None, jitter=None):
    if interval is not None or jitter is not None:
        cur_i, cur_j = read_schedule()
        interval = cur_i if interval is None else interval
        jitter = cur_j if jitter is None else jitter
        write_schedule(interval, jitter)
    else:
        interval, jitter = read_schedule()

    times = schedule_times(interval, jitter)
    volume, regular, cv = d3(times)
    flagged = volume or regular
    rate = len(times) / WINDOW_H

    print("=" * 68)
    print(" D3  BEHAVIOURAL DETECTOR")
    print("=" * 68)
    print()
    print("   This one never reads your payload. Not one byte. Every variant you")
    print("   generated is invisible to it, and so is any variant you ever will.")
    print()
    print("   Eight check-ins is not a beacon pattern, so it reads the two")
    print("   numbers in schedule.txt and works out what a day of them looks")
    print("   like from the outside. Fixed seed: the same numbers on every")
    print("   machine.")
    print()
    print(f"   schedule.txt   interval={interval:g}s   jitter={jitter:.0%}")
    print()
    print(f"   over {WINDOW_H} h:  {len(times)} check-ins"
          + (f",  cv of the gaps {cv:.3f}" if cv is not None else
             ",  too few to judge cadence"))
    print()
    print("   Two limbs, and either one is enough:")
    print(f"     VOLUME      more than {D3_VOLUME_MAX} check-ins per {WINDOW_H} h"
          f"    ->  {'TRIPPED' if volume else 'clean'}")
    print(f"     REGULARITY  cv below {D3_CV_MAX}"
          f"                     ->  {'TRIPPED' if regular else 'clean'}")
    print()
    print(f"   VERDICT: {'FLAGGED' if flagged else 'CLEAN'}")
    print(f"   THROUGHPUT: {rate:.2f} records per hour")
    print()

    baseline_rate = 60.0     # 60 s interval, no jitter - where every student starts
    save_result("behaviour", {"interval": interval, "jitter": jitter,
                              "events": len(times),
                              "cv": (round(cv, 3) if cv is not None else None),
                              "volume_tripped": volume,
                              "regularity_tripped": regular,
                              "flagged": flagged,
                              "records_per_hour": round(rate, 2)})

    if flagged:
        if volume and regular:
            print("   You are a timer talking to a stranger. Both limbs agree.")
        elif volume:
            print("   The jitter worked - the regularity limb is clean. And it")
            print("   bought you nothing, because the volume limb does not care")
            print("   how irregular you are. It counts.")
        print()
        print("   Change the two numbers in schedule.txt and run this again,")
        print("   or pass them directly:")
        print("       python detect.py --behaviour --interval 7200 --jitter 0.95")
    else:
        slowdown = baseline_rate / rate if rate else float("inf")
        print(f"   You are clean. You are also {slowdown:.0f}x slower than where")
        print(f"   you started ({baseline_rate:.0f} records/h at 60 s, no jitter).")
        print()
        print("   THE BILL, for moving a fixed amount of data:")
        print(f"     {'records':>8}   {'at 60 s':>10}   {'at your setting':>16}")
        for n in (100, 500, 5000):
            print(f"     {n:>8}   {n / baseline_rate / 24:>9.2f}d   "
                  f"{n / rate / 24:>15.1f}d")
        print()
        print("   That is what evasion cost, and nothing about it is a bug you")
        print("   can engineer away. Beating a content detector is free. Beating")
        print("   an orthogonal one is a bill, and the defender gets to choose")
        print("   how big it is.")
    print()
    return flagged, rate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signature", action="store_true")
    ap.add_argument("--structural", action="store_true")
    ap.add_argument("--behaviour", action="store_true")
    ap.add_argument("--interval", type=float, default=None)
    ap.add_argument("--jitter", type=float, default=None)
    args = ap.parse_args()

    if args.jitter is not None and not 0.0 <= args.jitter <= 0.95:
        print("jitter must be between 0.0 and 0.95")
        return 2
    if args.interval is not None and args.interval < 1:
        print("interval must be at least 1 second")
        return 2

    if args.signature:
        run_signature()
    elif args.structural:
        run_structural()
    elif args.behaviour:
        run_behaviour(args.interval, args.jitter)
    else:
        print(__doc__.split("OURS, NOT")[0].strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
