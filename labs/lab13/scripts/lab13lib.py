"""The broker, the policy file and the audit log. This is the whole control.

Lab 5 put the authorization check INSIDE the tool, where the model could reach the
variable it consulted. Lab 5's own fix (--mediate) moved that check onto a value
fixed at launch. Both are about IDENTITY: who is this session.

This lab is about something identity cannot answer. The broker sits OUTSIDE every
tool and asks a different question before any call runs:

    what is this run FOR, and is this call part of that?

OWASP LLM03:2026 prevention 7 calls it "an independent pre-execution policy
decision point between the tool and the downstream system", and the sentence that
follows is the one worth memorising:

    "Such policies can help manage cases where an agent's nominally-permitted
     action is contextually unsafe."

THREE GATES, IN THIS ORDER, AND THE ORDER IS THE TEACHING
---------------------------------------------------------
  1. ALLOW-LIST   is this tool on this purpose's list?
                  The coarse gate. "The firewall allows the traffic."
  2. CREDENTIAL   is the scoped credential covering this exact action active?
                  The gate every organisation already has.
  3. PURPOSE      is this action within what the run is FOR?
                  The gate almost nobody has. Identity is not intent.

The shipped policy passes gates 1 and 2 for the privileged call and stops it at
gate 3. That is deliberate: the student sees the attack defeated by the ONLY check
that could have defeated it, with a valid credential in hand.

Measured on the published lab 5 image, 2026-09-19, 3 runs per case, all identical:
the injection lands, the model escalates to admin, and the admin box is not read.
"""
import json
import os
import pathlib
import time

WORK = pathlib.Path("/labs/lab13")
POLICY = WORK / "policy.json"
POLICY_DEFAULT = WORK / "policy.default.json"
LOG = WORK / "audit-log.jsonl"
NOTES = WORK / "notes"

# Every gate's verdict line, in one place, so audit.py, evidence.py and check.py
# all agree on the wording and no assertion has to guess.
# An ALLOW passed all three gates; only a DENY stopped AT one. Labelling an
# allowed call "gate 3" reads as though it barely scraped through, and puts the
# word "gate" next to a verdict it did not stop at - which is exactly the kind of
# thing a student quotes back at you in the debrief.
RULES = {
    "not_on_allowlist":   "gate 1  allow-list",
    "credential_revoked": "gate 2  scoped credential",
    "outside_purpose":    "gate 3  declared purpose",
    "within_purpose":     "passed all three gates",
    "no_such_tool":       "gate 1  allow-list",
}


# --------------------------------------------------------------------------
# policy
# --------------------------------------------------------------------------
def load_policy(path=POLICY):
    """Read the policy, and fail loudly rather than fall open.

    A broker that cannot read its policy must DENY, never allow. Returning an
    empty dict here would make every call fail gate 1 for the wrong reason and
    the lab would look like it worked.
    """
    try:
        text = pathlib.Path(path).read_text()
    except OSError as e:
        raise SystemExit(f"LAB ERROR: cannot read the policy file {path}: {e}")
    if not text.strip():
        raise SystemExit(f"LAB ERROR: the policy file {path} is empty. "
                         "A broker with no policy is not a broker.")
    try:
        pol = json.loads(text)
    except ValueError as e:
        raise SystemExit(f"LAB ERROR: {path} is not valid JSON: {e}")
    for key in ("purpose", "allow", "credentials", "purpose_scope"):
        if key not in pol:
            raise SystemExit(f"LAB ERROR: {path} has no {key!r} section.")
    return pol


def save_policy(pol, path=POLICY):
    pathlib.Path(path).write_text(json.dumps(pol, indent=2) + "\n")


# --------------------------------------------------------------------------
# the broker
# --------------------------------------------------------------------------
def action_of(tool, args):
    """The tool:argument pair the policy talks about.

    This is the single most important line in the file. `read_notes` appears
    TWICE in one hijacked run with opposite verdicts, and the tool name alone
    cannot tell those two calls apart. A policy written against tool names is a
    policy that cannot express "read the public box but not the admin box" -
    which is OWASP's Common Example of Risk 4, excessive permissions, in one
    sentence.
    """
    if tool == "read_notes":
        return "read_notes:" + (str(args.get("box", "")).strip().lower() or "?")
    if tool == "set_role":
        return "set_role:" + (str(args.get("role", "")).strip().lower() or "?")
    return tool + ":*"


def in_scope(action, scope):
    """`read_notes:public` matches itself, or a `read_notes:*` wildcard."""
    tool = action.split(":", 1)[0]
    return action in scope or (tool + ":*") in scope


class Broker:
    """The policy decision point. Nothing calls a tool without passing through."""

    def __init__(self, policy, run_id, logpath=LOG):
        self.policy = policy
        self.run_id = run_id
        self.logpath = pathlib.Path(logpath)
        self.records = []

    def check(self, tool, args):
        """Return (allowed, reason). Logs a record either way."""
        purpose = self.policy["purpose"]
        action = action_of(tool, args)
        allow = self.policy["allow"].get(purpose, [])
        scope = self.policy["purpose_scope"].get(purpose, [])

        # GATE 1 - the allow-list, by tool name.
        if tool not in allow:
            return self._log(tool, args, action, "DENY", "not_on_allowlist",
                             f"{tool!r} is not on the allow-list for purpose "
                             f"{purpose!r}")

        # GATE 2 - the scoped credential for this exact action.
        for name, cred in self.policy["credentials"].items():
            if cred.get("scope") == action:
                if not cred.get("active", False):
                    return self._log(tool, args, action, "DENY",
                                     "credential_revoked",
                                     f"credential {name!r}, scoped to {action}, "
                                     f"is revoked")
                break

        # GATE 3 - the purpose of the run. This is the one that is usually missing.
        if not in_scope(action, scope):
            return self._log(tool, args, action, "DENY", "outside_purpose",
                             f"{action} is not within the declared purpose "
                             f"{purpose!r}")

        return self._log(tool, args, action, "ALLOW", "within_purpose",
                         f"{action} is within purpose {purpose!r}")

    def _log(self, tool, args, action, verdict, rule, reason):
        """One JSONL record per ATTEMPTED call - allowed and denied alike.

        NOTE WHAT IS NOT HERE: the tool's RESULT. The log records what was asked
        for and what was decided, never what came back. That is how a real tool
        audit log is written (the result may be anything, including the contents
        of the admin box) and it is why this lab can assert that the fake
        password appears nowhere in any file the student sends the instructor.
        """
        rec = {"ts": round(time.time(), 3), "run": self.run_id,
               "purpose": self.policy["purpose"], "tool": tool, "args": args,
               "action": action, "verdict": verdict, "rule": rule,
               "reason": reason}
        self.records.append(rec)
        with self.logpath.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        return verdict == "ALLOW", reason


# --------------------------------------------------------------------------
# the log
# --------------------------------------------------------------------------
def read_log(path=LOG):
    path = pathlib.Path(path)
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def next_run_id(path=LOG):
    recs = read_log(path)
    return (max((r.get("run", 0) for r in recs), default=0)) + 1


def replay(records, policy):
    """Re-decide already-logged calls under a DIFFERENT policy.

    This is the regression check, and it costs no model time at all. It is also
    what a real change-control process does before shipping a rule: take
    yesterday's traffic, run it against the proposed policy, and look at what
    would have changed.

    Returns a list of (record, new_verdict, new_rule).
    """
    broker = Broker(policy, run_id=0, logpath=os.devnull)
    out = []
    for rec in records:
        broker.records = []
        broker.check(rec["tool"], rec.get("args") or {})
        new = broker.records[-1]
        out.append((rec, new["verdict"], new["rule"]))
    return out
