"""RECOVER, beat 2: tighten the allow-list so the escalation is denied BY NAME.

    python tighten.py

OWASP LLM03:2026 prevention 1, "Minimize tools":
    "Limit the tools that LLM agents are allowed to call to only the minimum
     necessary."

CSA on Clinejection, February 2026, which is the same sentence with a victim:
    "automated issue triage does not require shell execution, filesystem writes,
     or network access."

Beat 1 revoked a credential and the privileged call still got as far as gate 2.
This beat removes set_role from what a triage run may call at all, so the attempt
dies at gate 1 - before the session role is ever changed. That is the difference
between limiting a compromise and preventing one, and the audit log shows it as a
shorter chain.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from lab13lib import load_policy, save_policy                  # noqa: E402

W = 68
DROP_TOOL = "set_role"
DROP_SCOPE = "set_role:*"


def main():
    pol = load_policy()
    purpose = pol["purpose"]
    allow = pol["allow"].setdefault(purpose, [])
    scope = pol["purpose_scope"].setdefault(purpose, [])

    print("=" * W)
    print(" ALLOW-LIST CHANGE")
    print("=" * W)
    print()

    if DROP_TOOL not in allow and DROP_SCOPE not in scope:
        print(f"  {DROP_TOOL!r} is already off the allow-list for {purpose!r}.")
        print("=" * W)
        return

    print(f"  BEFORE   allow[{purpose}]        = {allow}")
    print(f"           purpose_scope[{purpose}] = {scope}")
    if DROP_TOOL in allow:
        allow.remove(DROP_TOOL)
    if DROP_SCOPE in scope:
        scope.remove(DROP_SCOPE)
    save_policy(pol)
    print()
    print(f"  AFTER    allow[{purpose}]        = {allow}")
    print(f"           purpose_scope[{purpose}] = {scope}")
    print()
    print("  Denied by name, at the first gate. A triage run now cannot change")
    print("  its own role at all - not because the tool was deleted, but")
    print("  because this purpose was never entitled to it.")
    print()
    print("  Re-run the agent. Watch the chain get SHORTER and the session")
    print("  role stay 'analyst'.")
    print("=" * W)


if __name__ == "__main__":
    main()
