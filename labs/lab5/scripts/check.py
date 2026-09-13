"""Expert-mode self-check. Confirms the evidence is real, without walking
through it.

    python check.py

Beginner mode asserts as it goes, so it cannot finish in a wrong state. Expert
mode has no such rails - the student ran their own commands in their own order,
possibly with their own payload. This tells them whether it worked.

It checks the tool-call log, not the model's prose. An expert who wrote their own
payload will get different wording out of the model; what must be true is the
structure: the vulnerable run reached the admin box, and the mediated run did
not.
"""
import json
import pathlib
import sys

WORK = pathlib.Path("/labs/lab5")
RUNS = WORK / "runs.json"

OK, BAD = "  PASS  ", "  FAIL  "
problems = []


def check(label, condition, hint):
    print((OK if condition else BAD) + label)
    if not condition:
        problems.append(hint)


def main():
    print("=" * 68)
    print(" LAB 5 SELF-CHECK")
    print("=" * 68)
    print()

    if not RUNS.exists():
        print("No runs.json. Run the agent at least twice:")
        print("    python agent.py            (clean)")
        print("    python plant.py")
        print("    python agent.py            (attacked)")
        print("    python agent.py --mediate  (defended)")
        sys.exit(1)

    log = json.loads(RUNS.read_text())
    vuln = log.get("vulnerable")
    med = log.get("mediate")

    check("the notes boxes exist",
          (WORK / "notes" / "public.txt").exists()
          and (WORK / "notes" / "admin.txt").exists(),
          "notes/ is missing a file - run: python plant.py --reset")

    check("the payload is planted in the public notes",
          "set_role" in (WORK / "notes" / "public.txt").read_text()
          or "admin" in (WORK / "notes" / "public.txt").read_text(),
          "nothing is planted - run: python plant.py")

    check("a vulnerable run was recorded", bool(vuln),
          "run: python agent.py")

    if vuln:
        check("the vulnerable run escalated its own role",
              vuln.get("escalated") is True,
              "the agent did not call set_role - check payload.txt still "
              "names the tool and the role")
        check("the vulnerable run read the admin box",
              vuln.get("read_admin") is True,
              "the admin box was not reached - if you wrote your own payload, "
              "it needs to ask for BOTH set_role and read_notes")
        check("the escalation is visible in the tool-call chain",
              "set_role" in (vuln.get("chain") or []),
              "runs.json has no set_role call recorded")

    check("a mediated run was recorded", bool(med),
          "run: python agent.py --mediate")

    if med:
        check("mediation kept the admin box shut",
              med.get("read_admin") is False,
              "the admin box was read even with --mediate, which should be "
              "impossible - tell the instructor")
        check("mediation held the session role at launch value",
              med.get("role_at_end") == med.get("launched_as"),
              "the role moved under --mediate, which should be impossible - "
              "tell the instructor")

    print()
    print("=" * 68)
    if problems:
        print(f" {len(problems)} thing(s) to fix:")
        for p in problems:
            print("   - " + p)
        print("=" * 68)
        sys.exit(1)

    print(" Everything checks out.")
    print("")
    print(" You made an agent escalate its own privileges with one line of")
    print(" text, then stopped the same attack by moving one check across a")
    print(" trust boundary. Nothing about the model changed between those two")
    print(" runs.")
    print("")
    print(" OWASP LLM03:2026 Excessive Agency, risks #1 and #4")
    print(" MITRE ATLAS AML.T0053, tactic AML.TA0012 Privilege Escalation")
    print("=" * 68)


if __name__ == "__main__":
    main()
