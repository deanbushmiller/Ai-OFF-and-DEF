"""RECOVER, beat 1: revoke the scoped credential the blocked call tried to use.

    python revoke.py

This is the move every organisation believes it can make and very few have ever
rehearsed. One field, from true to false, in a file the agent cannot write to.

ATLAS AML.M0027, Single-User AI Agent Permissions Configuration, names it:
    "Lifecycle management involves establishing identity, protocols for access
     management, and DECOMMISSIONING of the agent when its role is no longer
     needed."

And CSA's Clinejection remediation is the production form:
    "Publication credentials ... should be provisioned as short-lived OIDC tokens
     scoped to specific packages and environments rather than long-lived personal
     access tokens."

Note what this does NOT do: it does not stop the escalation. set_role is still on
the allow-list, the agent will still change its own role, and the privileged call
will still be attempted. It just dies one gate earlier. That is the point of doing
this move on its own - a credential revocation limits the blast radius of a
compromise it does not prevent.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from lab13lib import load_policy, read_log, save_policy        # noqa: E402

W = 68
TARGET = "admin-notes-ro"


def main():
    pol = load_policy()
    creds = pol["credentials"]

    if TARGET not in creds:
        sys.exit(f"LAB ERROR: policy.json has no credential {TARGET!r}.")

    # Which credential did the denied call actually need? Read it from the log
    # rather than assuming, so the student sees the evidence drive the change.
    denied = [r for r in read_log() if r["verdict"] == "DENY"]
    wanted = denied[-1]["action"] if denied else None

    print("=" * W)
    print(" CREDENTIAL REVOCATION")
    print("=" * W)
    print()
    if wanted:
        print(f"  The audit log's last denial was for:  {wanted}")
        holder = [n for n, c in creds.items() if c.get("scope") == wanted]
        if holder:
            print(f"  The credential scoped to that action: {holder[0]!r}")
        print()

    if not creds[TARGET].get("active", False):
        print(f"  {TARGET!r} is already revoked. Nothing to do.")
        print("=" * W)
        return

    print(f"  BEFORE   {TARGET}: scope={creds[TARGET]['scope']}  active=true")
    creds[TARGET]["active"] = False
    creds[TARGET]["revoked"] = "by the on-call engineer, after reading the log"
    save_policy(pol)
    print(f"  AFTER    {TARGET}: scope={creds[TARGET]['scope']}  active=false")
    print()
    print("  One field. The agent cannot write to this file, and nothing in")
    print("  the conversation can change it back.")
    print()
    print("  What this does NOT do: set_role is still on triage's allow-list,")
    print("  so the agent will still escalate. Re-run it and watch WHERE the")
    print("  denial happens now.")
    print("=" * W)


if __name__ == "__main__":
    main()
