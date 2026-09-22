# Lab 5 — Exploiting AI agents and excessive agency

**Time:** 12–15 minutes · You write no code.

Lines marked 🅱️ are the **core attack commands**. Beginner mode runs only those.
Expert mode runs the whole list.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have already done labs 1 to 4, you are ready — nothing new to install. This lab adds
**no new software at all**: it reuses the same language model labs 3 and 4 already put on
your machine.

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
  finishes it is copied out to `lab5-results.txt`, next to the setup script you ran. If
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
powershell -ExecutionPolicy Bypass -File .\labs\lab5\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab5/setup/setup.sh
```

This lab serves nothing and opens no port. Once the image is on your machine it runs with no
network at all.

When it finishes, the script copies your transcript out to `lab5-results.txt`, next to the
setup script. That file is your evidence.

### Three steps take about a minute each

Three of the six commands run a language model on your own CPU. Each takes roughly a minute,
and up to two on an older laptop. **That is the lab working, not the lab hanging.** There is
nothing to watch while it thinks.

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Six commands.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also adds the steps beginner skips:
reading `tools.py` and finding the three bugs before the comments name them, editing
`payload.txt` with `nano` to write **your own** instruction and re-planting it, and running
the second defence for real with `python agent.py --minimal` so you can decide which of the
two you would actually ship. Finish with `python check.py`, which confirms your evidence is
real without walking you through it.

To go straight to expert mode, add `--expert` to the command above.

**If it fails**, the script tells you why in plain English. Send that message to the
instructor via email or post to class Q&A.

---

## The question this lab answers

Your agent can call tools. **What decides whether it is allowed to — your code, or the text
it just read?**

---

## Architecture

```
   "Summarise today's public notes for me."
                │
                ▼
        ┌───────────────┐   picks one tool, as JSON
        │     model     │──────────────────────────┐
        │ Qwen2.5-1.5B  │                          ▼
        └───────────────┘                 ┌────────────────────┐
                ▲                         │    TOOL LAYER      │
                │  the tool's result      │    tools.py        │
                └─────────────────────────│                    │
                                          │  read_notes(box) ──┼──► notes/public.txt
                                          │  set_role(role)  ──┼──► notes/admin.txt
                                          │  answer(text)      │      (analyst may
                                          └────────────────────┘       not read this)
                                                   ▲
                                     THE PRIVILEGE CHECK READS A
                                     VARIABLE THE MODEL CAN WRITE TO
```

The attacker never touches the model, the code, or the system prompt. They append **one
line** to `notes/public.txt` — a file the agent is *supposed* to read.

---

## The vulnerable configuration

Three bugs, all of them in `tools.py`, all of them in ordinary Python written by the person
who wired the agent up. They compound.

1. **Excessive functionality** — OWASP risk #1. A helpdesk triage agent was handed
   `set_role`. Nothing about summarising notes needs the power to change who you are. It is
   in the toolbox because the toolbox was built for the whole platform rather than for this
   one job, which is the most common way this bug reaches production.
2. **Excessive permissions** — OWASP risk #4. `read_notes` will read any box it is asked
   for. The only thing guarding the admin box is *a sentence in the system prompt* asking
   the model nicely. A sentence in a prompt is not an access control.
3. **The check is on the wrong side of the trust boundary.** The privilege test reads
   `session.role` — the same variable `set_role` writes to. Authorization that the
   attacker's input can rewrite is not authorization.

Bug 3 is what makes 1 and 2 exploitable, and it is the one the defence fixes.

---

## Your evidence

**OWASP LLM03:2026 Excessive Agency**, Common Examples of Risk **#1** and **#4**, triggered
by **LLM01:2026** indirect prompt injection.

> Note the number. Excessive Agency was **LLM06 in the 2025 list** and moved to **LLM03 in
> 2026** — the biggest climb on the list. `LLM06:2026` is now Unbounded Consumption.

The defence is the entry's own **prevention #7, complete mediation**:

> Implement authorization in logic rather than relying on an LLM to decide if an action is
> allowed or not.

**MITRE ATLAS** (v2026.08):
`AML.T0084.001` Tool Definitions → `AML.T0065` LLM Prompt Crafting →
`AML.T0051.001` Prompt Injection: Indirect → **`AML.T0053` AI Agent Tool Invocation**
(tactic **`AML.TA0012` Privilege Escalation**) → `AML.T0085.001` Data from AI Agent Tools.

`AML.T0053` is the only technique in ATLAS that carries the Privilege Escalation tactic for
an agent, and its own description is this exercise:

> AI agents may be configured to have access to tools that are not directly accessible by
> users. Adversaries may abuse this to gain access to tools they otherwise wouldn't be able
> to use.

---

## Every step in the lab

🅱️ marks the core commands. Beginner mode runs only those.

```
🅱️  python agent.py --tools               what powers does this agent have?
🅱️  python agent.py                       the honest baseline
    cat tools.py                          find the three bugs yourself
🅱️  python plant.py                       append the payload to the public notes
🅱️  python agent.py                       the same agent, now escalating
🅱️  python agent.py --mediate             the check moves into the tool layer
🅱️  python evidence.py                    the three tool-call logs, side by side
    nano payload.txt                      write your OWN instruction
    python plant.py --reset               restore the notes
    python plant.py                       plant yours instead
    python agent.py                       does the agent obey you too?
    python agent.py --minimal             the other defence: delete set_role
    python check.py                       confirm the evidence is real
```

---

## Submit

`python evidence.py` prints three tool-call chains. **Paste all three** into the class
chat — the escalation proves nothing without the clean run above it and the
mediated run below it. The full transcript is in `lab5-results.txt`.

---

## What makes this lab different from labs 3 and 4

All three involve injected text, and by now that should feel familiar. The difference is
what happens next.

| | Lab 3 | Lab 4 | **Lab 5** |
|---|---|---|---|
| how the payload arrives | HTML the scraper reads | pixels the OCR reads | a line in a notes file |
| hidden from humans by | `display:none` | 1.2 % contrast | **nothing — it is in plain sight** |
| what the model does | emits a token | reverses a decision | **calls two more tools** |
| the consequence | text on screen | text on screen | **data the session could not reach** |

**The payload being unhidden is the point.** Labs 3 and 4 spent their effort on concealment
because they were talking a model past its own judgment. Here there is no judgment to talk
past — the tool layer does whatever it is asked. Four different payload styles were tried
while building this lab, including a polite lowercase request, and all four worked.

When the authorization is missing, payload craft stops mattering.

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
