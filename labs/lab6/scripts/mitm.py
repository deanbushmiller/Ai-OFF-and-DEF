"""Run one exchange end to end: MCP server, proxy, client. One command per beat.

    python mitm.py                                  watch only, change nothing
    python mitm.py --tools                          print what the server advertises
    python mitm.py --rewrite-arg chk-002            edit the REQUEST in flight
    python mitm.py --rewrite-result 999999.00       edit the RESPONSE in flight
    python mitm.py --inject                         append payload.txt to a result
    python mitm.py --inject --verify                the defence, against injection
    python mitm.py --rewrite-arg chk-002 --verify   the defence, against arg tampering

Why this wrapper exists: the interesting part of each beat is the FLAG, not the
plumbing. Starting three processes by hand is expert-mode work (LAB.md covers it);
for the guided path, one command whose flags read as the attack is clearer and
keeps the beginner path inside its ten-command cap.

--verify turns on the defence: the server signs each response and the proxy
checks the signature. Note what that does and does not cover - see beat 6.

--wire-only skips the model entirely and does one raw tools/call. Used for the
beats whose point is the protocol rather than the assistant, which keeps three
model generations out of the lab's time budget.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request

WORK = pathlib.Path("/labs/lab6")
PY = sys.executable


def wait_for_port(port, timeout=20):
    """A fixed sleep is a flake waiting to happen on a loaded laptop."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}",
                data=json.dumps({"jsonrpc": "2.0", "id": 0, "method": "ping"}).encode(),
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=2).read()
            return True
        except urllib.error.HTTPError:
            return True          # it answered, which is all we needed
        except Exception:
            time.sleep(0.3)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", action="store_true")
    ap.add_argument("--rewrite-arg", metavar="ACCOUNT")
    ap.add_argument("--rewrite-result", metavar="AMOUNT")
    ap.add_argument("--inject", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--wire-only", action="store_true",
                    help="one raw tools/call, no model")
    ap.add_argument("--beat", default=None, help="key to record in runs.json")
    args = ap.parse_args()

    server_cmd = [PY, str(WORK / "mcp_server.py")] + (["--sign"] if args.verify else [])
    proxy_cmd = [PY, str(WORK / "proxy.py")]
    if args.rewrite_arg:
        proxy_cmd += ["--rewrite-arg", args.rewrite_arg]
    if args.rewrite_result:
        proxy_cmd += ["--rewrite-result", args.rewrite_result]
    if args.inject:
        proxy_cmd += ["--inject"]
    if args.verify:
        proxy_cmd += ["--verify"]

    srv = subprocess.Popen(server_cmd, stdout=subprocess.DEVNULL,
                           stderr=subprocess.STDOUT)
    if not wait_for_port(8007):
        srv.terminate()
        print("The MCP server did not come up on 127.0.0.1:8007.")
        sys.exit(1)

    print("--- the wire, as the proxy sees it " + "-" * 33)
    pxy = subprocess.Popen(proxy_cmd)
    if not wait_for_port(8006):
        pxy.terminate(); srv.terminate()
        print("The proxy did not come up on 127.0.0.1:8006.")
        sys.exit(1)

    rc = 0
    try:
        if args.wire_only:
            # The protocol, with no model in the way.
            def rpc(method, params=None, _id=[0]):
                _id[0] += 1
                body = {"jsonrpc": "2.0", "id": _id[0], "method": method}
                if params is not None:
                    body["params"] = params
                r = urllib.request.Request(
                    "http://127.0.0.1:8006", data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(r, timeout=30) as resp:
                    return json.loads(resp.read())

            rpc("initialize", {"protocolVersion": "2024-11-05"})
            out = rpc("tools/call", {"name": "get_balance",
                                     "arguments": {"account": "chk-001"}})
            print("-" * 68)
            if "error" in out:
                print("\nThe client asked for chk-001 and got:")
                print(f"  REFUSED: {out['error']['message']}")
            else:
                print("\nThe client asked for chk-001 and got:")
                print(f"  {out['result']['content'][0]['text']}")
        else:
            client = [PY, str(WORK / "mcp_client.py")]
            if args.tools:
                client.append("--tools")
            env = dict(os.environ)
            if args.beat:
                env["LAB6_BEAT"] = args.beat
            print("-" * 68)
            print()
            rc = subprocess.call(client, env=env)
    finally:
        pxy.terminate(); srv.terminate()
        try:
            pxy.wait(timeout=5); srv.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pxy.kill(); srv.kill()

    sys.exit(rc)


if __name__ == "__main__":
    main()
