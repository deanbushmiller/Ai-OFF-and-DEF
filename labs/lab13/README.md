# Lab 13 — Defending AI agents

**Time:** 12–15 minutes · You write no code.

The fifth **defend** lab. It pairs with lab 5, where a helpdesk agent with one tool too many
read a line of text in a notes file, changed its own role, and handed over the admin box. This
time you put a **broker** in front of the agent's tools — and then you watch it stop a call
that had a valid credential and a permitted tool behind it.

The model still gets tricked here. Every single run. That is not the lab's failure, it is the
lab's premise: the question is what the agent is *allowed to do* once it has been.

Lines marked 🅱️ in [`LAB.md`](LAB.md) are the **core defence commands**. Beginner mode runs
only those. Expert mode runs the whole list.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have already done labs 3 to 8 or lab 12, you are ready — nothing new to install, and
the download is small. This lab runs the same local language model as those labs and buys no
model, no system package and no Python package of its own, so the pull is the lab's own source
files and nothing else. From a clean machine, expect about **1.2 GB** — the language model
itself, the one-time cost that labs 3 to 8, 12 and this lab all share.

<!-- DOWNLOAD FIGURE: written 2026-09-20 in the course-wide pass, from one
     verify-sharing.py run against the published registry. Figures are rounded;
     the exact byte counts are in the instructor pack. Any rebuild invalidates
     them, so re-run the pass after a base-digest bump. -->

---

## How the lab works — read this once

Every step is a small experiment, and it always has the same three beats:

**1. Why** — one or two lines telling you what you are about to do and what to watch for.

**2. The command** — you type or paste it. The lab checks what you typed before it runs
anything. Get it wrong and it shows you the right command; get it wrong twice and it runs
the correct one for you.

**3. What it meant** — lines beginning with `^` underneath the output, on the steps where
something just changed.

> **The `^` lines are the point of the lab.** The output shows you *what happened*; the `^`
> lines tell you *why it matters*. If you read one thing, read those.

### The output will run off your screen. Nothing is lost.

Some steps print more than a screenful. That is expected, and there are three reasons not
to worry about it:

- **The lab never moves on by itself.** It waits at every step until you type something.
  Read first, type second. The 12–15 minutes assumes you are reading.
- **You can scroll back at any time.** The mouse wheel works everywhere. macOS Terminal and
  most Linux terminals also take `Shift`+`PageUp`; Windows Terminal takes
  `Ctrl`+`Shift`+`PageUp`. Scrolling does not interrupt the lab.
- **The whole transcript is saved to a file**, including every `^` line. When the lab
  finishes it is copied out to `lab13-results.txt`, next to the setup script you ran. If
  something scrolled past, open that file afterwards rather than hunting for it in the
  terminal — and it is the same file you use as evidence.

---

## Run the lab

Open a terminal **in the course folder** — the `Ai-OFF-and-DEF` folder you cloned, wherever
you put it. Not sure you are in it? `dir` on Windows, `ls` on macOS and Linux: you should
see a `labs` folder.

**Windows** — PowerShell, opened **as Administrator** (Start menu → type `powershell` →
right-click → **Run as administrator**):

```bash
cd $HOME\Documents\Ai-OFF-and-DEF
```

```bash
powershell -ExecutionPolicy Bypass -File .\labs\lab13\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab13/setup/setup.sh
```

This lab publishes no port and needs none. The setup script starts the container with
**`--network none`** — a lab whose own subject includes keeping an agent away from things it
was never meant to reach should run that way itself. The agent, its tools, the policy file,
the model and the log are all inside the container.

When it finishes, the script copies three things out of the container and puts them next to
the setup script: `lab13-results.txt`, your transcript; `lab13-audit-log.jsonl`, the broker's
tool-call log; and `lab13-policy.json`, the policy as you left it. **The log is the
evidence.** It is worth opening on its own.

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Ten commands: a clean task, the
log, the attacker's line, the attack, the log again, the policy, the credential revocation,
the re-run, the allow-list change, and the final re-run with the evidence.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also adds the steps beginner skips:
editing `policy.json` with `nano` and deciding for yourself what to change rather than letting
a script do it, adding a second purpose that *is* entitled to the admin box so you can watch
the same tool call allowed for one purpose and denied for another, comparing what the model is
told it can do against what the broker will actually permit, and running `python check.py` at
the end.

You can re-run the lab to switch modes.

---

## The question this lab answers

The question is **not** "does the model get tricked". It does, in every run below. It is:

**Once the agent has been hijacked and is holding a valid credential, what decides whether
the call runs?**

---

## Your evidence

**The log is the evidence.** The setup script copies out **`lab13-audit-log.jsonl`**, the
broker's record of every attempted call and the verdict on each, **`lab13-results.txt`**, your
transcript, and **`lab13-policy.json`**, the policy as you left it.

| | |
|---|---|
| **Defends** | lab 5 — exploiting AI agents and excessive agency |
| **OWASP** | LLM03:2026 Excessive Agency — Common Examples of Risk 1 and 4; preventions 7, 8, 1 and 4 built, 5, 6, 3 and 9 named · LLM01:2026 Prompt Injection is the trigger |
| **ATLAS techniques** | `AML.T0084.001` → `AML.T0051.001` → `AML.T0053` → `AML.T0085.001` |
| **ATLAS mitigations** | `AML.M0028`/`M0026` the broker · `AML.M0024` the audit log · `AML.M0027` the revocation · `AML.M0035` the tune |

---

## Every step in the lab

🅱️ marks the core steps. Beginner mode runs only those. The full walkthrough of each step is
in [`LAB.md`](LAB.md).

```
🅱️  python agent.py                           a clean task: read_notes:public, ALLOW
🅱️  python audit.py                           one record, one verdict, the purpose named
🅱️  python plant.py                           the attacker's line goes into the public notes
🅱️  python agent.py                           set_role ALLOWED, read_notes:admin DENIED at gate 3
🅱️  python audit.py                           the jump, in three records
🅱️  cat policy.json                           why set_role was allowed, which credential was live
🅱️  python revoke.py                          revoke admin-notes-ro
🅱️  python agent.py                           the denial moves to gate 2; the agent still escalates
🅱️  python tighten.py                         set_role off triage's allow-list
🅱️  python agent.py && python evidence.py     gate 1, role never changes, clean run replayed
    python agent.py --tools                   expert: what the model is told vs what the broker permits
    nano policy.json                          expert: make the two changes by hand instead
    (add a purpose)                           expert: an incident purpose scoped to read_notes:admin
    cat tools.py                              the three bugs, still there, annotated
    python plant.py --reset                   put the notes back and start over
    python check.py                           eleven assertions on the log and the policy
```

---

## Submit

Paste the output of the last command — `python evidence.py` — into the class chat: the whole
table. The line that matters is the gate column walking 3 -> 2 -> 1 while the clean run keeps
passing.

Your full transcript is saved to `lab13-results.txt` on your machine.

---

## What you are building

**Broker, allow-list, audit, revoke, tighten.** Five words, and the lab is the argument for
why you need all five.

A **broker** sits between the agent and every one of its tools: nothing runs without passing
through it first. It asks three questions in order — is this tool on the **allow-list** for
what this run is for; is the scoped credential covering this exact action still active; and is
this action actually within the run's declared **purpose**. An **audit log** records every
attempted call and the verdict on each — *including the ones it allowed*, which turns out to
be the record this whole lab depends on. Then, when the log shows you a privileged call that
had to be stopped, you **revoke** the credential it tried to use and **tighten** the allow-list
so the escalation is refused by name, and you confirm the denial now lands earlier without
breaking anything that was working.

The first two gates are the ones most organisations already have, and the lab shows the attack
walking straight through both of them: the agent authenticated, the tool was permitted, the
credential was valid and active. Only the third gate — *what is this run for?* — stops it.
That gap has a name, **confused deputy**, and in 2026 it cost a coding assistant's users about
four thousand compromised machines. Whether your company lets an agent act with its
credentials at all, and who owns the allow-list afterwards, is a decision about appetite rather
than tooling — and somebody above you makes it before you write a line of the broker.

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
