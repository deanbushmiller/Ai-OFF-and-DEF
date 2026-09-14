"""The mock collector - this lab's stand-in for a C2 server.

    python collector.py          run it in the foreground (expert mode)

It binds 127.0.0.1:8007 INSIDE this container and the port is not published to
your machine. Nothing reaches the network, and the container is run with no
network at all.

WHAT IT IS NOT
--------------
It is not command and control. It accepts a POST, writes the body to
collector.log with a timestamp and a length, and answers 200. There is no
command channel, no task queue, no session, no encryption and no protocol. It
would not function as C2 for anything.

It exists because the detector has to read a LOG rather than read the attacker's
own files. That is the realistic asymmetry: a defender never sees the variant
generator, only what arrived.

WHY THERE IS NO REMOTE ENDPOINT, AND THERE NEVER WILL BE
--------------------------------------------------------
A real endpoint on a domain the instructor controls was proposed at lab 3 and
considered again at labs 5, 6 and here. CLOSED PERMANENTLY 2026-09-13, and this
lab is the clearest case: it is about beaconing on a timer to a collector. A
security professional's work laptop running a "hacking lab" that then makes
periodic timed check-ins to an unfamiliar external domain is not something EDR
might flag - it is the textbook detection, and beat 6 would be tuning the
interval of a real one. We would be filing incident tickets at students'
employers by design.

So the lab prints what a real attacker's endpoint WOULD have received instead.
Same lesson, nobody's SOC paged. See beacon.py.
"""
import datetime
import http.server
import json
import pathlib
import sys

WORK = pathlib.Path("/labs/lab7")
LOG = WORK / "collector.log"
HOST, PORT = "127.0.0.1", 8007      # loopback only, never 0.0.0.0


class Collector(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace")
        entry = {
            "received": datetime.datetime.now(datetime.timezone.utc)
                                 .isoformat(timespec="seconds"),
            "variant": self.headers.get("X-Lab-Variant", "unknown"),
            "source": self.headers.get("X-Lab-Source", "unknown"),
            "bytes": n,
            "body": body,
        }
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok\n")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"collector up\n")

    def log_message(self, *a):
        """Silence the default stderr access log; collector.log is the record."""
        return


def main():
    srv = http.server.HTTPServer((HOST, PORT), Collector)
    print(f"collector listening on http://{HOST}:{PORT}  (loopback only)")
    print(f"writing to {LOG}")
    print("Ctrl-C to stop.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        srv.server_close()


if __name__ == "__main__":
    sys.exit(main())
