"""DETECT - load a model file where it cannot hurt you, and write down
everything it does.

    python sandboxed_load.py <artifact.pt>

The gate you just ran reads the file. This RUNS it, on purpose, somewhere it
cannot reach anything: a separate process, with no network, with a Python
audit hook watching every import, every command and every socket call.

  clean file      nothing to report
  poisoned file   the command it ran, with its arguments
  beacon file     the address it tried to reach, refused before the connect

Exit code 0 means nothing to report. 1 means the artifact acted.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHILD = os.path.join(HERE, "_sandbox_child.py")
LOGPATH = os.path.join(os.getcwd(), "sandbox-log.jsonl")
WIDTH = 64


def network_facts():
    """Does this container have a way out?

    /sys/class/net is not the place to ask - it lists kernel tunnel stubs
    that exist whether or not this container is connected to anything, and
    under Docker Desktop it can show the VM's devices too. /proc/net/route
    is namespace-aware and answers the only question that matters: is there
    a route off this container? With --network none it holds nothing but
    its header line.
    """
    routes, nics = 0, []
    try:
        with open("/proc/net/route", encoding="utf-8") as fh:
            routes = max(0, len(fh.read().strip().split("\n")) - 1)
    except OSError:
        routes = -1
    try:
        with open("/proc/net/dev", encoding="utf-8") as fh:
            for line in fh.read().split("\n")[2:]:
                name = line.split(":")[0].strip()
                if name and name != "lo":
                    nics.append(name)
    except OSError:
        pass
    # These exist in every fresh namespace and carry no traffic.
    stubs = {"tunl0", "gre0", "gretap0", "erspan0", "ip_vti0", "ip6_vti0",
             "sit0", "ip6tnl0", "ip6gre0", "bonding_masters"}
    return routes, [n for n in nics if n not in stubs]


def main():
    if len(sys.argv) != 2:
        print("usage: python sandboxed_load.py <artifact.pt>")
        return 64
    artifact = sys.argv[1]
    if not os.path.exists(artifact):
        print("No such file: " + artifact)
        return 66

    routes, nics = network_facts()
    print("=" * WIDTH)
    print(" SANDBOXED LOAD  " + os.path.basename(artifact))
    print("=" * WIDTH)
    print()
    if routes == 0 and not nics:
        print("  routes off this container: 0. No network interface but loopback.")
        print("  There is nowhere for a payload to go, and the hook below means")
        print("  it does not even get to try. Two controls, not one.")
    else:
        print("  ! This container HAS a network: " + (", ".join(nics) or "a default route"))
        print("    The lab is meant to run with --network none. The hook below")
        print("    still refuses the connection, but you are now relying on one")
        print("    control instead of two.")
    print()
    print("  Loading in a child process with an audit hook attached.")
    print("  torch.load(weights_only=False) - the careless setting, on purpose.")
    print()

    proc = subprocess.run(
        [sys.executable, CHILD, os.path.abspath(artifact), LOGPATH],
        capture_output=True, text=True, timeout=300,
    )

    payload_output = (proc.stdout or "").strip()

    records = []
    if os.path.exists(LOGPATH):
        with open(LOGPATH, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    summary = next((json.loads(r["detail"]) for r in records if r["event"] == "summary"), None)
    if summary is None:
        print("  LAB ERROR - the sandbox produced no summary.")
        print("  " + (proc.stderr or "").strip()[:500])
        return 1

    print("-" * WIDTH)
    print(" WHAT THE ARTIFACT DID")
    print("-" * WIDTH)
    print()

    acted = False
    for rec in records:
        if rec["verdict"] == "EXECUTED":
            acted = True
            print("  EXECUTED  " + rec["event"])
            print("            " + rec["detail"])
        elif rec["verdict"] == "BLOCKED":
            acted = True
            print("  BLOCKED   " + rec["event"])
            print("            " + rec["detail"])
            print("            refused by the hook - connect() was never called")
    if summary["new_imports"]:
        print("  IMPORTED  " + ", ".join(summary["new_imports"]))
        print("            modules torch had not already loaded")
    if not acted and not summary["new_imports"]:
        print("  nothing. No commands, no sockets, no new imports.")
    print()

    if payload_output:
        print("  the payload's own output:")
        for line in payload_output.split("\n"):
            print("      " + line)
        print()

    if summary["load_status"] == "load-failed":
        print("  the load did not complete: " + summary["load_error"])
        print("  (expected when the sandbox refuses something mid-load)")
        print()

    print("  full log: sandbox-log.jsonl")
    print()
    print("=" * WIDTH)
    if acted:
        print(" VERDICT: this artifact acted on load. Do not ship it.")
        print("=" * WIDTH)
        return 1
    print(" VERDICT: nothing to report.")
    print("=" * WIDTH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
