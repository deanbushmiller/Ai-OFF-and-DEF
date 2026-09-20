"""Replay what actually arrived at the collector from the compromised host.

    python inbox.py            deliver the day's check-ins
    python inbox.py --show     print what is already in collector.log

YOU ARE NOT THE ATTACKER IN THIS LAB
------------------------------------
Lab 7 made you generate these ten renderings and watch three detectors try to
catch them. That work is done, and this lab does not repeat it. What arrives
here is EVIDENCE - the ten bodies lab 7 measured, replayed into a collector so
the detector has a log to read instead of the attacker's working files.

That asymmetry is the whole reason the collector exists. A defender never sees
`variants.json`. They see what landed.

The ten bodies are in variants.json and every one of them was recorded
byte-identical across three runs at temperature 0 on Qwen2.5-1.5B-Instruct
Q4_K_M - see lab-research/lab7/probe-transcripts/q1.out. Eight came from the
model. Two - base64 and hex - came from two lines of Python, because the model
cannot perform an exact transform on data it has not memorised. Those two are
the ones that beat the signature rule, and they needed no AI at all.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab15lib as L

CHANNEL = f"{L.BEACON_HOST}->{L.BEACON_DEST}"


def real_endpoint_note(count, total_bytes):
    """The parked-decision answer: say what egress WOULD have looked like.

    Decided 2026-09-13 and closed permanently. The lab shows the shape of the
    request a real operator's endpoint would have logged, and stops there.
    """
    print()
    print(L.BAR)
    print(" WHAT A REAL OPERATOR'S ENDPOINT WOULD HAVE RECEIVED")
    print(L.BAR)
    print()
    print("   POST /api/v2/telemetry HTTP/1.1")
    print("   Host: <a domain the operator registered last week>")
    print("   User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    print("   Content-Type: application/json")
    print(f"   Content-Length: <one of {count} shapes, {total_bytes} bytes total>")
    print()
    print(f"   {count} check-ins, from one workstation, to one host that")
    print("   nothing else in the estate has ever contacted.")
    print()
    print("   This lab stops here on purpose. Nothing leaves your machine, and")
    print("   the reason is not squeamishness: a work laptop that runs a")
    print("   hacking lab and then beacons on a timer to an unfamiliar domain")
    print("   is the textbook EDR detection. Doing it for real would page")
    print("   your SOC - and this is the lab about detecting exactly that.")
    print()


def show():
    entries = L.collector_entries()
    if not entries:
        print("collector.log is empty. Run:  python inbox.py")
        return 1
    print(f"   {'variant':<10} {'source':<8} {'bytes':>6}  body (first 60 chars)")
    for e in entries:
        body = e["body"].replace("\n", " ")[:60]
        print(f"   {e['variant']:<10} {e['source']:<8} {e['bytes']:>6}  {body}")
    print()
    print(f"   {len(entries)} entries in collector.log.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    if args.show:
        return show()

    variants = L.load_variants()

    # A fresh log per delivery, so a re-run cannot double-count.
    if L.COLLECTOR_LOG.exists():
        L.COLLECTOR_LOG.unlink()

    print(L.BAR)
    print(" THE COLLECTOR'S INBOX")
    print(L.BAR)
    print()
    print(f"   One workstation - {L.BEACON_HOST} - has been checking in to")
    print(f"   {L.BEACON_DEST} all day. Here is what landed.")
    print()

    proc, reused = L.start_collector()
    if proc is None and not reused:
        print("   The collector did not come up on 127.0.0.1:8015.")
        print("   Nothing is broken on your machine - this is inside the")
        print("   container. Tell the instructor and send lab15-results.txt.")
        return 1
    if reused:
        print("   a collector is ALREADY listening on 127.0.0.1:8015")
        print("   using it rather than starting a second one, and leaving it")
        print("   running when this finishes - it is yours, not mine.")
        print()

    total = 0
    try:
        print(f"   {'code':>4}  {'source':<7}  {'variant':<8} {'bytes':>5}")
        for i, (name, v) in enumerate(variants.items()):
            code = L.post(v["text"], CHANNEL, name, v["source"], hour=i % 24)
            if code != 200:
                L.stop_collector(proc)
                print(f"   could not deliver {name}: HTTP {code}")
                return 1
            n = len(v["text"].encode())
            total += n
            tag = {"model": "MODEL", "python": "python"}.get(v["source"], " -- ")
            print(f"   {code:>4}  {tag:<7}  {name:<8} {n:>5}")
    finally:
        # Only stop a collector we started. An expert's own process is theirs.
        L.stop_collector(proc)

    entries = L.collector_entries()
    print()
    print(f"   collector.log now has {len(entries)} entries, {total} bytes "
          f"of body.")
    print()
    print("   Eight of those ten came out of a language model in about 48")
    print("   seconds. Two came out of base64.b64encode and .hex() instantly,")
    print("   and they are the two that are about to matter most.")
    real_endpoint_note(len(entries), total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
