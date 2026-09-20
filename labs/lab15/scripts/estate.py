"""Build one day of check-in telemetry for a 24-workstation estate.

    python estate.py --build      generate it and show the fleet
    python estate.py --show       print what exists

This is the file the cadence limbs read. It is what a NetFlow collector or a
Zeek conn.log gives you: who talked to whom, when, and how much. No payloads -
those arrive separately, at the collector, which is the realistic asymmetry.

IT IS SYNTHETIC, AND THE LAB SAYS SO OUT LOUD
---------------------------------------------
The estate is generated here, by this file, from fixed seeds. The SHAPE is real
and citable - a monitoring agent's heartbeat genuinely is indistinguishable from
a beacon on cadence alone, and user browsing genuinely does produce a long tail
of destinations only one host ever contacts. The exact number of false positives
is a property of this generator, not a measurement of anybody's network. A
student who assumes otherwise has learned the wrong thing, so LAB.md says this
too.

THE INTERVALS ARE REAL AGENT DEFAULTS, NOT NUMBERS CHOSEN TO MAKE A POINT
-------------------------------------------------------------------------
    EDR telemetry     300 s, tight jitter    CrowdStrike/Defender-class heartbeat
    monitoring         60 s, very tight      node-exporter / Zabbix-class
    backup client     3600 s
    update check     21600 s  (6 h)
    licence check    43200 s  (12 h)

That matters. If the fleet's beaconing software were invented to lose, the lab
would be cheating. It is not: the monitoring agent trips both of lab 7's limbs
because it is a timer talking to a server, which is exactly what it is.
"""
import argparse
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab15lib as L

# name              interval  jitter   destination
FLEET = [
    ("edr-telemetry",      300,  0.05, "edr.velocity.internal"),
    ("monitoring",          60,  0.02, "metrics.velocity.internal"),
    ("backup-client",     3600,  0.10, "backup.velocity.internal"),
    ("update-check",     21600,  0.25, "updates.velocity.internal"),
    ("licence-check",    43200,  0.15, "lic.vendor-a.example"),
]
BROWSE_DESTS_PER_HOST = 3

# The compromised channel: WKSTN-14, the workstation from lab 7, checking in to
# one address nothing else in the estate has ever contacted.
BEACON_INTERVAL = 60
BEACON_JITTER = 0.0


def browse_times(seed, hours=L.HOURS):
    """Bursty human browsing: clustered requests, long idle gaps.

    This channel is the reason `rarity alone` is not the answer. Every browsing
    destination is contacted by exactly one host, so a rarity-only detector
    flags all 72 of them. Measured: 72 false positives. A student who reaches
    for rarity first - and they should, it is the right instinct - needs this
    in the data or the lesson is a lecture instead of a result.
    """
    rng = random.Random(seed)
    t, out = 0.0, []
    while t < hours * 3600:
        for _ in range(rng.randint(4, 30)):
            out.append(t)
            t += rng.uniform(0.5, 12.0)
            if t >= hours * 3600:
                break
        t += rng.uniform(300, 5400)
    return out


def build():
    chans = []
    for host in range(1, L.HOSTS + 1):
        hname = f"WKSTN-{host:02d}"
        for i, (name, iv, jit, dest) in enumerate(FLEET):
            chans.append({
                "host": hname, "dest": dest, "software": name,
                "interval": iv, "jitter": jit,
                "times": L.schedule_times(iv, jit, seed=1000 + host * 10 + i),
                "malicious": False})
        for k in range(BROWSE_DESTS_PER_HOST):
            chans.append({
                "host": hname, "dest": f"cdn-{host:02d}-{k}.example",
                "software": "user-browsing", "interval": None, "jitter": None,
                "times": browse_times(seed=5000 + host * 10 + k),
                "malicious": False})
    chans.append({
        "host": L.BEACON_HOST, "dest": L.BEACON_DEST, "software": "beacon",
        "interval": BEACON_INTERVAL, "jitter": BEACON_JITTER,
        "times": L.schedule_times(BEACON_INTERVAL, BEACON_JITTER, seed=7742),
        "malicious": True})
    return chans


def summarise(chans):
    counts = L.dest_host_counts(chans)
    cfg = L.load_detector()
    by_sw = {}
    for c in chans:
        d = by_sw.setdefault(c["software"], {"n": 0, "ex": c})
        d["n"] += 1

    print(L.BAR)
    print(" THE ESTATE - ONE DAY OF CHECK-IN TELEMETRY")
    print(L.BAR)
    print()
    print(f"   {L.HOSTS} workstations, {len(chans)} host->destination channels, "
          f"{L.HOURS} h.")
    print("   This is a flow log. It has no payloads in it - who talked to")
    print("   whom, when, and how often. That is what a defender actually gets.")
    print()
    print(f"   {'software':<16} {'channels':>8} {'events/24h':>11} {'cv':>8} "
          f"{'dest':<28} {'hosts':>5}")
    for sw, d in by_sw.items():
        c = d["ex"]
        cv = L.cadence(c["times"], cfg["limits"]["min_events"])
        cvs = f"{cv:.3f}" if cv is not None else "n/a"
        dest = c["dest"] if sw != "user-browsing" else "cdn-NN-K.example"
        print(f"   {sw:<16} {d['n']:>8} {len(c['times']):>11} {cvs:>8} "
              f"{dest:<28} {counts[c['dest']]:>5}")
    print()
    print("   Read the last two columns of the first two rows again.")
    print()
    # cadence() returns None below min_events, and formatting None with :.3f is
    # a TypeError. In the shipped estate the monitoring agent always has 1441
    # events so this can never fire - which is exactly why it has to be guarded.
    # Found 2026-09-20 by sabotaging the fleet for a negative test: the line
    # crashed instead of the verifier firing, which would have sent the next
    # person hunting the wrong bug. A display helper must never be able to stop
    # the lab.
    def cv_str(c):
        cv = L.cadence(c["times"], 12)
        return f"{cv:.3f}" if cv is not None else "  n/a"

    b = next(c for c in chans if c["malicious"])
    m = next((c for c in chans if c["software"] == "monitoring"), None)
    if m is not None:
        print(f"     monitoring   {len(m['times']):>5} check-ins   "
              f"cv {cv_str(m)}   "
              f"{counts[m['dest']]} hosts talk to it")
    print(f"     beacon       {len(b['times']):>5} check-ins   "
          f"cv {cv_str(b)}   "
          f"{counts[b['dest']]} host talks to it")
    print()
    print("   On CADENCE they are the same thing. One is your monitoring")
    print("   fleet and one is an intruder, and the only column that tells")
    print("   them apart is the one lab 7 never had, because lab 7 had one")
    print("   host and nothing to compare it to.")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    if args.build:
        chans = build()
        L.ESTATE.write_text(json.dumps(chans))
        summarise(chans)
        print(f"   Written to estate.json "
              f"({L.ESTATE.stat().st_size // 1024} KB). Fixed seeds, so this")
        print("   is the same estate on every machine in the class.")
        print()
        return 0

    if args.show:
        if not L.ESTATE.exists():
            print("No estate yet. Run:  python estate.py --build")
            return 1
        summarise(L.load_estate())
        return 0

    print(__doc__.split("IT IS SYNTHETIC")[0].strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
