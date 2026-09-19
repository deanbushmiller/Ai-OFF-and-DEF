"""The locked-down child process. Never run this directly - sandboxed_load.py
starts it.

Everything here happens BEFORE the model is trusted:

  1. install a Python audit hook (PEP 578) - it sees every import, every
     command execution and every socket call the process attempts
  2. import torch AND load a throwaway clean file. That is the BASELINE:
     hundreds of modules, none of them interesting. The throwaway load
     matters - torch imports part of its deserializer lazily, on the first
     load, and without this warm-up those modules would show up as if the
     artifact had pulled them in.
  3. switch to recording, then load the artifact with weights_only=False -
     the careless setting, deliberately, because that is the failure we are
     defending against
  4. anything the hook sees from that moment on belongs to the ARTIFACT, not
     to torch

Egress is refused: the hook raises when the artifact tries to resolve or
reach an address, so connect() is never called. The connection is not
attempted and then failed - it never reaches the kernel.

WHAT THIS IS NOT. An audit hook is telemetry, not a boundary. Code that is
already running inside this process has already won; a determined payload
could work around what it reports. The boundary is the container, this being
a separate process, and --network none. The hook tells you what happened. The
container is what stops it.
"""
import json
import os
import resource
import sys
import tempfile

ARTIFACT = sys.argv[1]
LOGPATH = sys.argv[2]

# Cheap belt and braces. Not a sandbox on their own, but a runaway payload
# hits a wall instead of the student's laptop.
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024 * 1024, 64 * 1024 * 1024))

LOG = open(LOGPATH, "w", encoding="utf-8")

# NOTE: 'exec' is deliberately NOT watched. CPython raises it for every
# module-level code object, so every import would show up twice - once as an
# import, once as an exec - and the signal would drown. Command execution is
# caught by the events below, which is what actually matters.
EXEC_EVENTS = {"os.system", "subprocess.Popen", "os.exec", "os.posix_spawn", "os.fork"}
EGRESS_EVENTS = {"socket.connect", "socket.getaddrinfo", "socket.bind", "urllib.Request"}
WATCHED = EXEC_EVENTS | EGRESS_EVENTS | {"import"}

state = {"phase": "baseline"}
baseline_imports = set()
findings = []


def write(record):
    LOG.write(json.dumps(record) + "\n")
    LOG.flush()


def hook(event, args):
    # No imports, no file opens and nothing clever in here - the hook must
    # not trigger the events it is watching.
    if event not in WATCHED:
        return

    if state["phase"] == "baseline":
        if event == "import":
            baseline_imports.add(args[0])
        return

    if event == "import":
        name = args[0]
        if name not in baseline_imports:
            rec = {"event": "import", "detail": name, "verdict": "new"}
            findings.append(rec)
            write(rec)
        return

    detail = str(args)[:200]

    if event in EGRESS_EVENTS:
        rec = {"event": event, "detail": detail, "verdict": "BLOCKED"}
        findings.append(rec)
        write(rec)
        raise RuntimeError("egress refused by the sandbox policy: " + event + " " + detail)

    rec = {"event": event, "detail": detail, "verdict": "EXECUTED"}
    findings.append(rec)
    write(rec)


sys.addaudithook(hook)

# --- baseline -------------------------------------------------------------
import torch  # noqa: E402  - deliberately after the hook

# Warm up the deserializer on a file we built ourselves, so its lazy imports
# land in the baseline instead of being blamed on the artifact.
_warm = os.path.join(tempfile.gettempdir(), "_sandbox_warmup.pt")
torch.save({"warmup": torch.zeros(1)}, _warm)
torch.load(_warm, weights_only=False)
os.unlink(_warm)

write({"event": "baseline",
       "detail": str(len(baseline_imports)) + " modules imported by torch and the warm-up load",
       "verdict": "info"})

# --- the artifact ---------------------------------------------------------
state["phase"] = "load"
status = "clean"
error = ""
try:
    # weights_only=False on purpose. Since torch 2.6 the default is True and
    # this payload would never fire. We are standing in for the careless or
    # legacy loader that turns the safety off.
    torch.load(ARTIFACT, weights_only=False)
except Exception as exc:                                  # noqa: BLE001
    status = "load-failed"
    error = type(exc).__name__ + ": " + str(exc)[:300]

state["phase"] = "done"

executed = [f for f in findings if f["verdict"] == "EXECUTED"]
blocked = [f for f in findings if f["verdict"] == "BLOCKED"]
new_imports = [f for f in findings if f["verdict"] == "new"]

write({"event": "summary", "detail": json.dumps({
    "artifact": os.path.basename(ARTIFACT),
    "baseline_modules": len(baseline_imports),
    "new_imports": [f["detail"] for f in new_imports],
    "executed": len(executed),
    "blocked": len(blocked),
    "load_status": status,
    "load_error": error,
}), "verdict": "info"})
LOG.close()

# 0 = nothing to report. 2 = the artifact did something.
sys.exit(2 if (executed or blocked) else 0)
