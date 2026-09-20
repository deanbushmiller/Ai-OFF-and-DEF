"""Shared vocabulary for lab 14. Every script reads the rules from HERE.

Lab 13 learned this the expensive way: a verdict label lived in four files and
changing it was a four-file edit. One module, one set of names.

    TRUST      the trust list and the pinned descriptor fingerprints
    RULES      the verdict vocabulary, in gate order
    fingerprint()  sha256 over a tool descriptor, serialised canonically
    log()      append one record to the tamper log
"""
import hashlib
import json
import pathlib
import time

WORK = pathlib.Path("/labs/lab14")
TRUST = WORK / "trust.json"
TRUST_DEFAULT = WORK / "trust.default.json"
TAMPER_LOG = WORK / "tamper-log.jsonl"
SERVER_STATE = WORK / "server-state.json"

SERVER = "velocity-finance-tools"
PORT = 8014                      # 127.0.0.1 only. See the README.

# The three gates, in the order they run. A record's `rule` is always one of
# these, and the `gate` number is what makes "denied EARLIER" visible when the
# student drops the server.
RULES = {
    "not_in_trust_list":  (1, "gate 1  trust list"),
    "descriptor_changed": (2, "gate 2  descriptor pin"),
    "not_pinned":         (2, "gate 2  descriptor pin"),
    "result_off_schema":  (3, "gate 3  message schema"),
    # the pass labels
    "server_trusted":     (1, "gate 1  trust list"),
    "matches_pin":        (2, "gate 2  descriptor pin"),
    "matches_declared_shape": (3, "gate 3  message schema"),
    # the recovery label
    "served_pinned_copy": (0, "recovered  re-pinned"),
}


def gate_of(rule):
    return RULES.get(rule, (0, "?"))[0]


def label_of(rule):
    return RULES.get(rule, (0, rule))[1]


def fingerprint(tool):
    """sha256 over the descriptor, keys sorted so formatting cannot move it.

    This is the whole integrity check. OWASP LLM01:2026 prevention 10 asks for
    a PIN; a version number does not move when a description does, and a hash
    does. That is the entry's own caveat - "pinning does not stop ...
    tool-description poisoning that leaves the version unchanged" - answered.
    """
    return hashlib.sha256(json.dumps(tool, sort_keys=True).encode()).hexdigest()


def load_trust():
    return json.loads(TRUST.read_text())


def save_trust(t):
    TRUST.write_text(json.dumps(t, indent=2) + "\n")


def reset_trust():
    """Restore the shipped trust list. The runner calls this at every start.

    Without it a second run would begin with the server already dropped and the
    lab would silently skip its own lesson.
    """
    TRUST.write_text(TRUST_DEFAULT.read_text())


def log(**rec):
    rec.setdefault("ts", round(time.time(), 3))
    rec.setdefault("server", SERVER)
    with TAMPER_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def read_log():
    if not TAMPER_LOG.exists():
        return []
    return [json.loads(l) for l in TAMPER_LOG.read_text().splitlines() if l.strip()]


def poison_mode():
    """Which poison poison.py has armed. Read by the SERVER, not the client."""
    if not SERVER_STATE.exists():
        return "none"
    try:
        return json.loads(SERVER_STATE.read_text()).get("poison", "none")
    except ValueError:
        return "none"


def set_poison(mode):
    SERVER_STATE.write_text(json.dumps({"poison": mode}, indent=2) + "\n")


# ---------------------------------------------------------------- presentation
BAR = "-" * 70


def verdict_line(rec):
    """One log record as one readable line. Used by tamperlog.py and evidence.py."""
    mark = {"PASS": "  ok  ", "BLOCK": "BLOCK ", "REPIN": "REPIN "}.get(rec["verdict"], "      ")
    return "  %s %-10s %-13s %-26s %s" % (
        mark, rec["kind"], rec.get("tool", "-"), label_of(rec["rule"]), rec["rule"])
