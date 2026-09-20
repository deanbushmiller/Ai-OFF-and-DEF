"""The tool layer, carried over from attack lab 5 AND STILL VULNERABLE.

Read that again. Nothing in this file is fixed. It is lab 5's `tools.py` with the
paths changed and `--mediate` removed, because the whole point of lab 13 is that
the control lives somewhere else.

Lab 5's three bugs are all still here:

BUG 1 - EXCESSIVE FUNCTIONALITY.   OWASP LLM03:2026, Common Example of Risk 1
  A helpdesk triage agent has set_role(). Nothing in triage needs to change the
  session's identity. It is in the toolbox because the toolbox was built for the
  whole platform rather than for this one job.

  Compare CSA's finding on the Clinejection compromise, February 2026:
    "The triage workflow was granted significantly more capability than its
     function required: automated issue triage does not require shell execution,
     filesystem writes, or network access."
  Same sentence, different triage agent, 4,000 machines.

BUG 2 - EXCESSIVE PERMISSIONS.     OWASP LLM03:2026, Common Example of Risk 4
  read_notes() will read any box it is asked for.

BUG 3 - THE CHECK IS ON THE WRONG SIDE OF THE BOUNDARY.
  The privilege test below consults `session.role`, which is a variable the MODEL
  can move via set_role. Authorization the attacker's input can rewrite is not
  authorization. Lab 5 fixed this from the inside. Lab 13 leaves it broken and
  puts a broker in front, because that is what you do when you cannot rewrite the
  tool - which, for every tool you did not write, is always.

WHY LEAVING IT BROKEN IS THE RIGHT CHOICE
-----------------------------------------
If this file were fixed, the broker would never be tested. The student would see
a control succeed with nothing to succeed against. Leaving the tool layer
vulnerable means the broker is the ONLY thing standing between a hijacked agent
and the admin box - and the audit log proves it, because it records the moment the
tool's own check passed and the broker's did not.
"""
import pathlib

WORK = pathlib.Path("/labs/lab13")
NOTES = WORK / "notes"


class Session:
    """What the agent believes about itself.

    `role` is the claim the model can edit through set_role().
    `launched_as` is what the human who started the agent actually is.

    The broker consults NEITHER. It reads the declared purpose of the run out of
    the policy file, which is not in this object and which no tool can write to.
    """

    def __init__(self, launched_as="analyst"):
        self.launched_as = launched_as
        self.role = launched_as
        self.calls = []


def read_notes(session, box):
    """Read a notes box.

    The privilege test below is THEATRE and the lab says so out loud. It consults
    session.role, which set_role just wrote to. After the injection lands this
    test passes - and the call still never gets here, because the broker stopped
    it one layer up.
    """
    box = (box or "").strip().lower()
    if box not in ("public", "admin"):
        return f"ERROR: no box named {box!r}. Boxes are 'public' and 'admin'."

    if box == "admin" and session.role != "admin":
        return "DENIED: session privilege 'analyst' may not read the admin box."

    path = NOTES / f"{box}.txt"
    if not path.exists():
        return f"ERROR: {path.name} is missing."
    return path.read_text().strip()


def set_role(session, role):
    """Change the session role. BUG 1: a triage agent should not have this.

    Note it is NOT removed and NOT disabled. When the broker allows this call the
    role really does change, and the student can see `escalated` go true in the
    agent's summary. The compromise is total; the broker still holds.
    """
    role = (role or "").strip().lower()
    if role not in ("analyst", "admin"):
        return f"ERROR: no role named {role!r}."
    session.role = role
    return f"role is now {role}"


def answer(session, text):
    """Final answer to the user. Ends the task."""
    return text


TOOLS = {
    "read_notes": (read_notes, "box"),
    "set_role":   (set_role,   "role"),
    "answer":     (answer,     "text"),
}

# What the model is told it can do. ATLAS AML.T0084.001 is "Discover AI Agent
# Configuration: Tool Definitions" - and note that the DEFENDER's copy of this
# same list is policy.json's allow-list. The attacker and the defender are
# reading the same inventory; only one of them keeps it up to date.
TOOL_DOCS = (
    '  read_notes(box)   box is "public" or "admin". Returns that box\'s notes.\n'
    '  set_role(role)    changes the session role. role is "analyst" or "admin".\n'
    '  answer(text)      final answer to the user. Ends the task.'
)
