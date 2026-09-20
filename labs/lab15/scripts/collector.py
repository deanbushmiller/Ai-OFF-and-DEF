"""The mock collector - the endpoint the compromised workstation checks in to.

    python collector.py                run it in the foreground (expert mode)
    python collector.py --cap N        run it with a volume cap, N per hour

It binds 127.0.0.1:8015 INSIDE this container and the port is not published to
your machine. The container is run with no network at all.

WHAT IT IS NOT
--------------
It is not command and control. It accepts a POST, writes the body to
collector.log with a timestamp and a length, and answers 200 - or 429 when the
cap is in force. There is no command channel, no task queue, no session, no
encryption and no protocol. It would not function as C2 for anything.

It exists for two reasons. First, the detector has to read a LOG rather than the
attacker's own files: a defender never sees the variant generator, only what
arrived. Second - and this is lab 15's reason rather than lab 7's - a rate limit
that is not in a request path is not a rate limit. The prevent stub has to sit
somewhere real or its measured cost is fiction.

THE CAP, AND WHY IT BUCKETS ON A HEADER
---------------------------------------
Real limiters bucket on wall-clock time. This one buckets on X-Lab-Hour, the
simulated hour of the day the check-in belongs to, because the lab compresses a
24-hour schedule into about a second of loopback traffic. The arithmetic is
identical and the honest alternative - waiting 24 hours - is not a lab.

WHY THERE IS NO REMOTE ENDPOINT, AND THERE NEVER WILL BE
--------------------------------------------------------
Closed permanently 2026-09-13, and lab 7 is the case that closed it: a security
professional's work laptop running a "hacking lab" that then makes periodic
timed check-ins to an unfamiliar external domain is the textbook EDR detection.
We would be filing incident tickets at students' employers by design.

So the lab prints what a real operator's endpoint WOULD have received and stops
there. See inbox.py.
"""
import argparse
import datetime
import http.server
import json
import os
import pathlib
import sys

# See the note on WORK in lab15lib.py. LAB15_WORK is never set in the container.
WORK = pathlib.Path(os.environ.get("LAB15_WORK", "/labs/lab15"))
LOG = WORK / "collector.log"
HOST, PORT = "127.0.0.1", 8015      # loopback only, never 0.0.0.0

CAP = None                          # None = no limit
_seen = {}                          # simulated hour -> count delivered
_throttled = 0


class Collector(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        global _throttled
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace")
        hour = self.headers.get("X-Lab-Hour", "0")

        if CAP is not None:
            got = _seen.get(hour, 0)
            if got >= CAP:
                _throttled += 1
                self._reply(429, f"throttled {_throttled}\n")
                return
            _seen[hour] = got + 1

        entry = {
            "received": datetime.datetime.now(datetime.timezone.utc)
                                .isoformat(timespec="seconds"),
            "channel": self.headers.get("X-Lab-Channel", "unknown"),
            "variant": self.headers.get("X-Lab-Variant", "unknown"),
            "source": self.headers.get("X-Lab-Source", "unknown"),
            "hour": hour,
            "bytes": n,
            "body": body,
        }
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
        self._reply(200, "ok\n")

    def do_GET(self):
        self._reply(200, "collector up\n")

    def _reply(self, code, text):
        payload = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):
        """Silence the default stderr access log; collector.log is the record."""
        return


def main():
    global CAP
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=None,
                    help="max check-ins per simulated hour, per channel")
    args = ap.parse_args()
    CAP = args.cap

    srv = http.server.ThreadingHTTPServer((HOST, PORT), Collector)
    print(f"collector listening on http://{HOST}:{PORT}  (loopback only)")
    print(f"writing to {LOG}")
    if CAP is not None:
        print(f"volume cap: {CAP} check-ins per hour")
    print("Ctrl-C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        srv.server_close()


if __name__ == "__main__":
    sys.exit(main())
