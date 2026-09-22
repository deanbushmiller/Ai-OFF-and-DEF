# Lab 13 — Defending AI agents

You are the defender now. Lab 5 showed you a helpdesk agent with one tool too many and no real
authorization. This lab is the control you put in front of it.

The question is **not** "does the model get tricked". It does, in every run below. It is:

> Once the agent has been hijacked and is holding a valid credential, what decides whether the
> call runs?

**OWASP LLM03:2026 Excessive Agency** — Common Examples of Risk 1 (excessive functionality)
and 4 (excessive permissions); preventions **7** (complete mediation), **8** (monitor tool
use), **1** (minimize tools) and **4** (minimize tool permissions) are built here, 5, 6, 3
and 9 are named. **LLM01:2026 Prompt Injection** is the trigger.
**MITRE ATLAS** `AML.T0084.001` → `AML.T0051.001` → **`AML.T0053`** → `AML.T0085.001`,
countered with `AML.M0028`/`M0026` (the broker), **`AML.M0024`** (the audit log), `AML.M0027`
(the revocation) and `AML.M0035` (the tune).

---

## The architecture

```
   YOU                                                      /labs/lab13/
    |
    |  python agent.py
    v
 +------------------------------------------------------------------+
 |                                                                   |
 |   notes/public.txt  --------+                                     |
 |   (the attacker appends      |                                    |
 |    one line here)            v                                    |
 |                     Qwen2.5-1.5B-Instruct                         |
 |                     picks a tool: {"tool": ..., "args": {...}}    |
 |                              |                                    |
 |                              v                                    |
 |                   +---------------------+                         |
 |                   |    T H E  B R O K E R |  <-- policy.json      |
 |                   |                      |                        |
 |                   |  gate 1  allow-list  |                        |
 |                   |  gate 2  credential  |                        |
 |                   |  gate 3  purpose     |                        |
 |                   +----------+-----------+                        |
 |                        |           |                              |
 |                  ALLOW |           | DENY                         |
 |                        v           |                              |
 |                  tools.py          |   (the agent is told, and    |
 |                  read_notes        |    decides what to do next)  |
 |                  set_role          |                              |
 |                  answer            |                              |
 |                        |           |                              |
 |                        +-----+-----+                              |
 |                              v                                    |
 |                      audit-log.jsonl                              |
 |                      one record per ATTEMPTED call, always,       |
 |                      allowed and denied alike                     |
 +------------------------------------------------------------------+

   No port. No /etc/hosts entry. No background process.
   The container runs with --network none.
```

**`tools.py` is lab 5's, and it is still broken.** Its own privilege check reads
`session.role` — the variable `set_role` just wrote to. That is deliberate. If the tool were
fixed, the broker would never be tested, and you would be watching a control succeed against
nothing.

---

## The three gates, and why the order is the lesson

| gate | question | who has this |
|---|---|---|
| **1 · allow-list** | is this tool on the list for this purpose? | most teams |
| **2 · credential** | is the scoped credential for this exact action active? | most teams |
| **3 · purpose** | is this action within what the run is *for*? | almost nobody |

The shipped policy passes gates 1 and 2 for the privileged call and stops it at gate 3.

That is the whole point. The agent **authenticated**. The tool **was permitted**. The
credential **was valid and active**. None of that answers the question "is this call part of
the job", and the firewall in front of it cannot answer that question either — it sees an
authorized account, not an intent.

> "The identity stack you built for human employees catches stolen passwords and blocks
> unauthorized logins. It does not catch an AI agent following a malicious instruction through
> a legitimate API call with valid credentials."

---

## The vulnerable configuration and the defended one

Same broker. Same agent. Same model. Three values in `policy.json` are different.

| | shipped | after `revoke.py` | after `tighten.py` |
|---|---|---|---|
| `read_notes:public` (clean task) | ALLOW | ALLOW | **ALLOW** — unchanged, and that matters |
| `set_role:admin` | **ALLOW** | **ALLOW** | **DENY** — gate 1 |
| `read_notes:admin` | **DENY** — gate 3 | **DENY** — gate 2 | never attempted |
| session role at the end | `admin` | `admin` | **`analyst`** |
| the admin box | never read | never read | never read |

Read the bottom two rows together. The attempt is refused in all three columns — but only in
the third does the session **never escalate at all**. That is the difference between limiting
a compromise and preventing one, and it is why revoking and tightening are two separate moves
rather than one.

### What this is modelled on

In February 2026 a prompt injection in a **GitHub issue title** drove Cline's automated triage
workflow into installing an attacker-controlled package, which led to publication credentials
being exfiltrated and, on 17 February, a tampered release reaching roughly **4,000 developer
machines**. The agent was authenticated the entire time. The published finding reads:

> "The triage workflow was granted significantly more capability than its function required:
> automated issue triage does not require shell execution, filesystem writes, or network
> access."

The agent in this lab is also a triage agent. `tighten.py` is that sentence, applied.

---

## The commands

🅱️ marks the beginner core. Expert runs the whole list.

| | command | what to watch |
|---|---|---|
| 🅱️ | `python agent.py` | a clean task: one call, `read_notes:public`, ALLOW |
| 🅱️ | `python audit.py` | one record, one verdict, the purpose named |
| 🅱️ | `python plant.py` | the attacker's single visible line goes into the public notes |
| 🅱️ | `python agent.py` | `set_role` **ALLOWED**, `read_notes:admin` **DENIED at gate 3** |
| 🅱️ | `python audit.py` | the jump, in three records — `read_notes` twice, opposite verdicts |
| 🅱️ | `cat policy.json` | why `set_role` was allowed, and which credential was live |
| 🅱️ | `python revoke.py` | revoke `admin-notes-ro`: one field, `active` → false |
| 🅱️ | `python agent.py` | the denial moves to **gate 2**. The agent still escalates |
| 🅱️ | `python tighten.py` | `set_role` off triage's allow-list |
| 🅱️ | `python agent.py && python evidence.py` | **gate 1**, role never changes, and the clean run replayed |
| | `python agent.py --tools` | what the model is told it can do vs what the broker permits |
| | `nano policy.json` | make the two changes by hand instead, and decide what to change |
| | *(add a purpose)* | give `policy.json` an `incident` purpose scoped to `read_notes:admin`, set `purpose` to it, and run the agent again |
| | `cat tools.py` | the three bugs, still there, annotated |
| | `python plant.py --reset` | put the notes back and start over |
| | `python check.py` | eleven assertions on the log and the policy |

### The expert step worth doing

Add a second purpose to `policy.json`:

```json
"incident": ["read_notes:public", "read_notes:admin", "answer:*"]
```

…add `read_notes` and `answer` to `allow.incident`, set `"purpose": "incident"`, and run the
agent again. **The same tool call, with the same credential, on the same data, is now
allowed.** Nothing about the agent, the model or the tool changed. The only thing that changed
is what the run was declared to be for.

That is the gate you are being asked to believe in, and it is the one most systems do not have.

---

## One thing the agent will tell you that is not true

On the last run, with `set_role` off the allow-list, the agent's closing sentence is
reliably something like:

> *"I have verified that the admin box is readable. Now, I will read the notes."*

It verified nothing. The call was refused at the first gate, the role stayed `analyst`, and no
admin read was ever attempted. The model is narrating the instruction it was handed, not the
outcome it got.

This is not a bug in the lab and it is not the model misbehaving in some exotic way. It is the
ordinary behaviour of a system that generates plausible text, and it is the single best reason
to build the detect beat: **an agent's own account of what it did is not evidence. The log kept
by the thing that gated it is.**

Every assertion in `check.py` keys on a verdict record for exactly this reason.

---

## How this differs from a real defence

| this lab | production |
|---|---|
| one JSON policy file, three gates | Cedar or Rego, versioned, reviewed, with a test suite |
| a purpose string set at launch | delegated user context carried across every chained call |
| one credential flipped to `active: false` | short-lived scoped tokens that expire on their own |
| one JSONL file | a log pipeline with retention, alerting and a SIEM |
| one hand edit of one field | a policy-change process with an owner and a time to close |
| the broker runs in the same process as the agent | an out-of-process decision point the agent cannot reach, plus OS isolation and egress control |
| four tool calls | thousands a second, and the latency budget is real |

The shape is real. The scale is not — and that last row matters most: a broker the agent could
edit would be lab 5's bug again, one level up.

**The production answer is bought, not built.** A policy decision point in front of the tool
gateway: **Amazon Bedrock AgentCore Policy** uses Cedar and intercepts every agent-tool call at
the gateway boundary; **Open Policy Agent** with Rego is the vendor-neutral equivalent. AWS
open-sourced **Dogwood** in August 2026, extending Cedar with temporal conditions so a rule can
reason about an agent's *prior* tool calls — which is the "jump" you spot by eye in step 5,
written as a policy.

The trade is real and worth saying out loud: a policy language to learn and maintain, latency
on every tool call, a new dependency in the hot path, and — for the managed options — a policy
surface living in a vendor's control plane. It will also block a legitimate edge case the day
you tighten it, which is exactly why the log and the replay in step 10 exist. It is still yours
to run, monitor and tune. There is no *they*.

---

## Safety

Every tool here is fake and local. `read_notes` reads one of two text files in this container.
`set_role` sets a string on a Python object. Nothing runs a shell command, sends a message or
touches a network — the container has no network at all. The password in `notes/admin.txt` is
invented and exists nowhere else.

The audit log records what was **asked for** and what was **decided**, never what a tool
returned. That is how a real tool audit log is written, and it is why nothing you send your
instructor can contain the fake password.

---

## Submit

Paste the output of the last command — `python evidence.py` — into the class chat: the whole
table. The line that matters is the gate column walking 3 -> 2 -> 1 while the clean run keeps
passing.

Your full transcript is saved to `lab13-results.txt` on your machine.
