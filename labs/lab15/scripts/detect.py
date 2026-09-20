"""The detector. Four orthogonal limbs, one score, one threshold you choose.

    python detect.py --baseline            what you have today: D1, and lab 7's D3
    python detect.py --score               the four limbs, per channel
    python detect.py --sweep               the precision curve
    python detect.py --sweep --set 4       ... and write the threshold you pick
    python detect.py --window channel      widen the matching window and re-run
    python detect.py --rarity-only         the trap. Expert mode

OURS, NOT A PRODUCT
-------------------
Every limb here was written for this lab. Nothing is tuned against a named EDR,
NDR or IDS and no real product's rules are reproduced. This is a deliberately
crude version of the idea behind RITA's beacon score, which scores on interval
consistency AND data-size uniformity AND dispersion over real PCAP. Read RITA
if you want the real thing: https://github.com/activecm/rita

WHY THIS IS NOT LAB 7's DETECTOR, AND THE ONE LINE THAT CHANGED
---------------------------------------------------------------
Lab 7 shipped `volume > 24 OR cv < 0.35` and it was the right detector for lab
7, which had ONE channel and knew it was malicious. Measured on this estate:

    TRUE POSITIVES 1      FALSE POSITIVES 144      precision 0.0069

Every EDR agent, every monitoring agent, every backup client and every browsing
channel trips it. The monitoring agent - 1441 check-ins a day, cv 0.011 - is
behaviourally indistinguishable from the beacon at 1440 and cv 0.000, because
both of them are a timer talking to a server. One is your fleet.

And you cannot tune your way out. Sweeping lab 7's volume threshold down until
it catches a slow-and-low channel never gets precision above 0.0127, and past
the catch point tightening makes it worse. Measured, see --sweep.

Two changes fix it, and only one of them is a number:

  1. SCORE, don't switch. Four limbs, weighted, one threshold. Booleans fail
     in both directions here - `rarity AND regularity` is 1 TP / 0 FP and is
     beaten by FREE jitter; `rarity AND (regularity OR volume)` catches the
     jittered beacon and brings back 72 browsing false positives.
  2. ASK A DIFFERENT CADENCE QUESTION. Lab 7 asked `cv < 0.35` - is this a
     timer - which 95% jitter beats at no cost to throughput. Ask `cv < 1.0` -
     is this NOT a person - and it holds: a beacon at 95% jitter is cv 0.543,
     human browsing is cv 4.482.

THERE IS NO --tune FLAG AND THERE MUST NEVER BE ONE
---------------------------------------------------
Same rule as lab 7, pointed the other way. A loop that searches detector
settings against a known-malicious channel until it passes is a model-evasion
tool wearing a defender's badge, and it also teaches the wrong habit: you do not
get labels in production. The student reads a table and picks a number.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab15lib as L

RUN = None          # set from the environment by runner.py, for the log


def need_estate():
    if not L.ESTATE.exists():
        print("No estate yet. Build it first:")
        print("    python estate.py --build")
        sys.exit(1)
    return L.load_estate()


def need_inbox():
    if not L.collector_entries():
        print("Nothing has arrived at the collector yet. Run:")
        print("    python inbox.py")
        sys.exit(1)


# ---------------------------------------------------------------------------
# --baseline : what you have today
# ---------------------------------------------------------------------------
def run_baseline():
    need_inbox()
    chans = need_estate()
    cfg = L.load_detector()
    vals = L.field_values()

    print(L.BAR)
    print(" WHAT YOU HAVE TODAY, PART 1:  THE SIGNATURE RULE")
    print(L.BAR)
    print()
    print(f"   The entire rule:   '{L.MARKER}'.lower() in body.lower()")
    print()
    print(f"   {'variant':<10} {'source':<8} verdict")
    caught = 0
    for e in L.collector_entries():
        hit = L.signature_limb(e["body"])
        caught += hit
        print(f"   {e['variant']:<10} {e['source']:<8} "
              f"{'CAUGHT' if hit else '  miss  <--'}")
    total = len(L.collector_entries())
    print()
    print(f"   D1 caught {caught} of {total}.")
    print()
    print("   The two that got through are base64 and hex - the two the model")
    print("   could NOT write. The evasion that worked came from two lines of")
    print("   standard library and it is free. Eight renderings of AI output")
    print("   bought the attacker nothing against this rule.")
    L.log(run=RUN or "baseline", kind="detector", detector="signature",
          rule="signature_match", caught=caught, total=total)

    # ---- and now the same question asked of an estate ----
    print()
    print(L.BAR)
    print(" WHAT YOU HAVE TODAY, PART 2:  LAB 7's BEHAVIOURAL DETECTOR")
    print(L.BAR)
    print()
    print("   Copied from lab 7 unchanged:")
    print("       volume > 24 check-ins / 24 h   OR   regularity  cv < 0.35")
    print()
    print("   Lab 7 ran it against ONE channel it already knew was malicious.")
    print("   Here it is against your estate.")
    print()

    def lab7(c):
        cv = L.cadence(c["times"], 12)
        return len(c["times"]) > 24 or (cv is not None and cv < 0.35)

    by_sw, counts = {}, L.dest_host_counts(chans)
    for c in chans:
        d = by_sw.setdefault(c["software"], {"n": 0, "flag": 0, "ex": c})
        d["n"] += 1
        d["flag"] += lab7(c)
    print(f"   {'software':<16} {'channels':>8} {'flagged':>8}  "
          f"{'events/24h':>10} {'cv':>8}")
    for sw, d in by_sw.items():
        c = d["ex"]
        cv = L.cadence(c["times"], 12)
        cvs = f"{cv:.3f}" if cv is not None else "n/a"
        print(f"   {sw:<16} {d['n']:>8} {d['flag']:>8}  "
              f"{len(c['times']):>10} {cvs:>8}")

    tp = sum(1 for c in chans if c["malicious"] and lab7(c))
    fp = sum(1 for c in chans if not c["malicious"] and lab7(c))
    print()
    print(f"   TRUE POSITIVES  {tp}")
    print(f"   FALSE POSITIVES {fp}")
    print(f"   PRECISION       {L.precision(tp, fp):.4f}"
          f"   -> {fp} alerts a day to find {tp}")
    print()
    print("   It found the beacon. It also found your entire monitoring fleet,")
    print("   every EDR agent, every backup client and everyone's browser.")
    print()
    print("   100% recall and 0.7% precision. A SOC handed this stops reading")
    print("   it inside a week, and then the recall is zero too. That is not a")
    print("   tuning problem, it is a design problem, and the next two")
    print("   commands are the design.")
    L.log(run=RUN or "baseline", kind="detector", detector="lab7",
          rule="lab7_behaviour", tp=tp, fp=fp,
          precision=round(L.precision(tp, fp), 4))
    print()
    return tp, fp


# ---------------------------------------------------------------------------
# --score : the four limbs
# ---------------------------------------------------------------------------
def limb_table(chans, counts, cfg):
    by_sw = {}
    for c in chans:
        l = L.limbs(c, counts, cfg, L.payload_for(c))
        s = L.score(l, cfg)
        d = by_sw.setdefault(c["software"], {"n": 0, "ex": (c, l, s)})
        d["n"] += 1
    print(f"   {'software':<16} {'chans':>6}  {'rare':>5} {'cadence':>8} "
          f"{'volume':>7} {'record':>7}  {'score':>6}")
    for sw, d in by_sw.items():
        c, l, s = d["ex"]
        y = lambda b: "Y" if b else "."          # noqa: E731
        print(f"   {sw:<16} {d['n']:>6}  {y(l['rare_dest']):>5} "
              f"{y(l['machine_cadence']):>8} {y(l['high_volume']):>7} "
              f"{y(l['record_values']):>7}  {s:>6}")


def run_score(quiet=False):
    need_inbox()
    chans = need_estate()
    cfg = L.load_detector()
    counts = L.dest_host_counts(chans)
    w = cfg["weights"]
    lim = cfg["limits"]

    if not quiet:
        print(L.BAR)
        print(" THE DETECTOR - FOUR ORTHOGONAL LIMBS")
        print(L.BAR)
        print()
        print("   Not one of these can be turned off by rewording a payload.")
        print()
        print(f"   {'limb':<18} {'weight':>6}  what it asks")
        print(f"   {'rare_dest':<18} {w['rare_dest']:>6}  is this destination "
              f"contacted by <= {lim['rare_max_hosts']} hosts?")
        print(f"   {'machine_cadence':<18} {w['machine_cadence']:>6}  "
              f"cv < {lim['burst_cv_max']} - a machine, not a person")
        print(f"   {'high_volume':<18} {w['high_volume']:>6}  more than "
              f"{lim['volume_max']} check-ins / 24 h")
        print(f"   {'record_values':<18} {w['record_values']:>6}  do >= "
              f"{lim['min_fields']} of the record's 6 values survive?")
        print()
        print(f"   window: per {cfg['window']}        "
              f"threshold: score >= {cfg['threshold']}")
        print()

    limb_table(chans, counts, cfg)

    tp, fp, fn, rows = L.confusion(chans, counts, cfg, L.payload_for)
    print()
    print(f"   at threshold {cfg['threshold']}:   TP {tp}   FP {fp}   "
          f"precision {L.precision(tp, fp):.4f}")
    print()

    if not quiet:
        print("   Read the beacon's row. It is the only channel in the estate")
        print("   that trips all four, and it trips the content limb because")
        print("   the record is the thing it NEEDED to send. It cannot drop")
        print("   that and still be doing its job.")
        print()
        print("   Now read user-browsing. Rare, high volume, and completely")
        print("   innocent. That row is why 'just alert on rare destinations'")
        print("   is not the answer, and why the threshold is a real decision")
        print("   rather than a formality.")
        print()
        print(f"   The shipped threshold is {cfg['threshold']} - alert if ANY")
        print("   limb fires. That is the instinct lab 7 leaves you with and")
        print("   it is wrong. Find out by how much:")
        print("       python detect.py --sweep")
        print()

    L.log(run=RUN or "score", kind="detector", detector="score",
          rule="above_threshold" if tp else "below_threshold",
          threshold=cfg["threshold"], window=cfg["window"],
          tp=tp, fp=fp, precision=round(L.precision(tp, fp), 4))
    return tp, fp


# ---------------------------------------------------------------------------
# --sweep : the precision curve
# ---------------------------------------------------------------------------
def run_sweep(set_to=None):
    need_inbox()
    chans = need_estate()
    cfg = L.load_detector()
    counts = L.dest_host_counts(chans)

    print(L.BAR)
    print(" THE THRESHOLD SWEEP - WHERE DO YOU PUT THE LINE?")
    print(L.BAR)
    print()
    print("   Every threshold, scored against the whole estate. TP is the one")
    print("   beacon. FP is how many colleagues you wake up.")
    print()
    print(f"   {'threshold':>9} {'TP':>4} {'FP':>5} {'precision':>11}   note")
    best = None
    for thr in range(1, sum(cfg["weights"].values()) + 1):
        probe = dict(cfg, threshold=thr)
        tp, fp, fn, _ = L.confusion(chans, counts, probe, L.payload_for)
        note = ""
        if tp >= 1 and fp == 0 and best is None:
            best = thr
            note = "<-- the beacon, and nobody else"
        elif tp == 0:
            note = "the beacon is now missed too"
        print(f"   {thr:>9} {tp:>4} {fp:>5} "
              f"{L.precision(tp, fp):>11.4f}   {note}")
    print()
    print("   That is the whole job. Not 'is the detector on' - where is the")
    print("   line, and what does each side of it cost you.")
    print()

    # The contrast that makes the point: lab 7's dial, swept the same way, and
    # swept for a REASON - there is a slow channel it misses and you want it.
    # Without the "catches slow" column this table is just a list of numbers
    # going down; with it, it is the argument.
    slow = L.schedule_times(14400, 0.90, seed=7742)     # 4 h, 90% - see evade.py
    print("   And for comparison, lab 7's detector. Suppose you already know")
    print("   it misses a slow channel, and you turn its volume threshold down")
    print("   until it does not:")
    print()
    print(f"   {'volume max':>10} {'catches slow':>13} {'TP':>4} {'FP':>5} "
          f"{'precision':>11}")
    for vmax in (24, 12, 8, 6, 4, 2, 1):
        def lab7(times, v=vmax):
            cv = L.cadence(times, 12)
            return len(times) > v or (cv is not None and cv < 0.35)
        gets_slow = lab7(slow)
        tp = sum(1 for c in chans if c["malicious"] and lab7(c["times"]))
        tp += gets_slow
        fp = sum(1 for c in chans if not c["malicious"] and lab7(c["times"]))
        print(f"   {vmax:>10} {('YES' if gets_slow else 'no'):>13} {tp:>4} "
              f"{fp:>5} {L.precision(tp, fp):>11.4f}")
    print()
    print("   You have to go all the way to 4 check-ins a DAY to catch it, and")
    print("   precision never gets above 0.013 - it peaks there and then falls")
    print("   again. A dial on one dimension cannot buy precision at any")
    print("   setting. Orthogonal limbs can, and that is the whole difference")
    print("   between the two tables on this screen.")
    print()

    if set_to is not None:
        cfg["threshold"] = set_to
        L.save_detector(cfg)
        print(f"   threshold set to {set_to} in detector.json.")
        print()
        tp, fp, fn, _ = L.confusion(chans, counts, cfg, L.payload_for)
        print(f"   TP {tp}   FP {fp}   precision {L.precision(tp, fp):.4f}")
        print()
        if fp == 0 and tp >= 1:
            print("   One alert. It is the right one. You did not buy that by")
            print("   turning anything up - you bought it by asking four")
            print("   independent questions and requiring more than one 'yes'.")
        print()
        L.log(run=RUN or "sweep", kind="tune", rule="above_threshold",
              threshold=set_to, window=cfg["window"], tp=tp, fp=fp,
              precision=round(L.precision(tp, fp), 4))
    else:
        print(f"   Pick one and set it:")
        print(f"       python detect.py --sweep --set {best}")
        print("   or edit detector.json by hand.")
        print()
    return best


# ---------------------------------------------------------------------------
# --window : the recovery move
# ---------------------------------------------------------------------------
def run_window(window):
    need_inbox()
    chans = need_estate()
    cfg = L.load_detector()
    counts = L.dest_host_counts(chans)

    before_tp, before_fp, _, _ = L.confusion(chans, counts, cfg, L.payload_for)
    old = cfg["window"]
    cfg["window"] = window
    L.save_detector(cfg)
    tp, fp, fn, rows = L.confusion(chans, counts, cfg, L.payload_for)

    print(L.BAR)
    print(" THE TUNE - AND IT IS NOT A NUMBER")
    print(L.BAR)
    print()
    print(f"   matching window:  per {old}  ->  per {window}")
    print()
    if window == "channel":
        print("   The evasive channel beat the content limb by SPLITTING: two")
        print("   of the record's six values per check-in, so no single message")
        print("   ever reaches the 4-field threshold. You already know from")
        print("   --sweep that lowering the threshold cannot recover it - it")
        print("   only brings the false positives back.")
        print()
        print("   So do not match a message. Reassemble everything the channel")
        print("   sent in the day, and then match.")
        print()
        payloads = L.payload_for({"dest": L.BEACON_DEST})
        per_msg = max((L.content_hits(p)[0] for p in payloads), default=0)
        per_chan = L.content_hits("\n".join(payloads))[0]
        print(f"   best single message   {per_msg}/6 values  -> "
              f"{'CAUGHT' if per_msg >= cfg['limits']['min_fields'] else 'miss'}")
        print(f"   whole channel-day     {per_chan}/6 values  -> "
              f"{'CAUGHT' if per_chan >= cfg['limits']['min_fields'] else 'miss'}")
        print()
        print("   This is lab 7's own advice - 'normalise before you match' -")
        print("   extended from FORMAT to TIME. Decode, unescape, flatten,")
        print("   and now also reassemble, THEN apply the rule.")
        print()

    def prec(a, b):
        # No alerts at all is not precision 0.0 - it is undefined, and printing
        # 0.0000 next to "MISSED" reads as if the detector were wrong twice.
        return f"{L.precision(a, b):.4f}" if (a + b) else "no alerts"

    print(f"   {'':<22} {'TP':>4} {'FP':>5} {'precision':>11}")
    print(f"   {'before (per ' + old + ')':<22} {before_tp:>4} {before_fp:>5} "
          f"{prec(before_tp, before_fp):>11}")
    print(f"   {'after  (per ' + window + ')':<22} {tp:>4} {fp:>5} "
          f"{prec(tp, fp):>11}")
    print()
    if window == "channel" and fp == before_fp:
        print("   The wider window cost NOTHING. Not one extra false positive,")
        print("   because no legitimate channel in the estate carries the")
        print("   record's values at all. The window was never what made the")
        print("   detector noisy - the missing limbs were.")
        print()
    L.log(run=RUN or "window", kind="tune",
          rule=f"window_per_{window}", threshold=cfg["threshold"],
          window=window, tp=tp, fp=fp,
          precision=round(L.precision(tp, fp), 4))
    return tp, fp


# ---------------------------------------------------------------------------
# --rarity-only : the trap, for expert mode
# ---------------------------------------------------------------------------
def run_rarity_only():
    chans = need_estate()
    cfg = L.load_detector()
    counts = L.dest_host_counts(chans)

    print(L.BAR)
    print(" THE TRAP - 'JUST ALERT ON RARE DESTINATIONS'")
    print(L.BAR)
    print()
    print("   It is the right instinct and it is not a detector. Every schema")
    print("   below was tried; only one of them works, and it is not a boolean.")
    print()

    def rare(c):
        return counts[c["dest"]] <= cfg["limits"]["rare_max_hosts"]

    def regular(c):
        cv = L.cadence(c["times"], 12)
        return cv is not None and cv < 0.35

    def volume(c):
        return len(c["times"]) > cfg["limits"]["volume_max"]

    schemes = {
        "lab 7:  volume OR regularity": lambda c: volume(c) or regular(c),
        "rarity alone": rare,
        "rarity AND regularity": lambda c: rare(c) and regular(c),
        "rarity AND (regularity OR volume)":
            lambda c: rare(c) and (regular(c) or volume(c)),
    }
    print(f"   {'scheme':<38} {'TP':>4} {'FP':>5} {'precision':>11}")
    for name, fn in schemes.items():
        tp = sum(1 for c in chans if c["malicious"] and fn(c))
        fp = sum(1 for c in chans if not c["malicious"] and fn(c))
        print(f"   {name:<38} {tp:>4} {fp:>5} {L.precision(tp, fp):>11.4f}")
    print()
    print("   'rarity AND regularity' looks perfect. Now watch it lose to the")
    print("   move lab 7 measured as FREE - jitter, which costs the attacker")
    print("   nothing at all in throughput:")
    print()
    print(f"   {'attacker setting':<26} {'events':>7} {'cv':>8} "
          f"{'rare':>5} {'regular(0.35)':>14} {'AND':>8}")
    for iv, jit, label in ((60, 0.00, "60 s, no jitter"),
                           (60, 0.60, "60 s, 60% jitter"),
                           (60, 0.95, "60 s, 95% jitter")):
        t = L.schedule_times(iv, jit, seed=7742)
        cv = L.cadence(t, 12)
        r, rg = True, (cv is not None and cv < 0.35)
        print(f"   {label:<26} {len(t):>7} {cv:>8.3f} {'yes':>5} "
              f"{('yes' if rg else 'NO'):>14} "
              f"{('flag' if (r and rg) else 'MISS'):>8}")
    print()
    print("   That is why limb 2 asks cv < 1.0 instead of cv < 0.35. At 95%")
    print("   jitter the beacon is 0.543. Human browsing is 4.482. Bounded")
    print("   jitter is still bounded, and a beacon cannot become a person.")
    print()
    print("   And it is why the detector scores instead of switching: no")
    print("   boolean over these limbs is both precise and hard to evade.")
    print()
    return 0


def main():
    global RUN
    import os
    RUN = os.environ.get("LAB15_RUN")

    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--set", type=int, default=None, dest="set_to")
    ap.add_argument("--window", choices=("message", "channel"), default=None)
    ap.add_argument("--rarity-only", action="store_true")
    args = ap.parse_args()

    if args.set_to is not None and not 1 <= args.set_to <= 6:
        print("threshold must be between 1 and 6 (the weights sum to 6)")
        return 2

    if args.baseline:
        run_baseline()
    elif args.score:
        run_score()
    elif args.sweep:
        run_sweep(args.set_to)
    elif args.window:
        run_window(args.window)
    elif args.rarity_only:
        run_rarity_only()
    else:
        print(__doc__.split("OURS, NOT")[0].strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
