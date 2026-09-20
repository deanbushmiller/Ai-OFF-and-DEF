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

## Safety

Nothing here is malware and nothing leaves your machine — there is nowhere for it to go, as
the container runs with no network at all. The attacker's payload is one plain English sentence
appended to a notes file: no commands, no code, nothing hidden. The agent's tools are fake and
local — two text files — and no tool in this lab runs a shell command, sends a message or
touches a network. The "admin notes" and the password in them are **fake** and exist only
inside the container.

The broker's log records what was *asked for* and what was *decided*, never what a tool
returned — which is how a real tool audit log is written, and it means the fake password
cannot reach the file you send your instructor. `python check.py` asserts exactly that.

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
