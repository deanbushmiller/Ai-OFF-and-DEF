# Lab 14 — Defending MCP tool calls

**Time:** 12–15 minutes · You write no code.

The sixth **defend** lab. It pairs with lab 6, where an attacker sat on the wire between an
honest MCP client and an honest MCP server and rewrote the messages going past. This time
there is no attacker on the wire. **The server itself is the adversary** — which is the real
MCP threat model, because you connect an agent to software somebody else operates, and that
software chooses the text your model reads.

You put an integrity layer in the host: pin every tool descriptor, diff it on every
connection, drop a server that changed, and re-pin the copy you actually approved.

One beat of this lab is designed to **fail**. That is not a mistake in the lab; it is the
most useful five minutes in it.

Lines marked 🅱️ in [`LAB.md`](LAB.md) are the **core defence commands**. Beginner mode runs
only those. Expert mode runs the whole list.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have already done labs 3 to 8, 12 or 13, you are ready — nothing new to install, and
the download is small. This lab runs the same local language model as those labs and buys no
model, no system package and no Python package of its own, so the pull is the lab's own
source files and nothing else. The big model layer is already on your disk and is not
fetched again. From a clean machine, expect about **1.2 GB** — the language model itself,
the one-time cost that labs 3 to 8, 12, 13 and this lab all share.

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
  finishes it is copied out to `lab14-results.txt`, next to the setup script you ran. If
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
powershell -ExecutionPolicy Bypass -File .\labs\lab14\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab14/setup/setup.sh
```

This lab runs a mock MCP server on `127.0.0.1:8014` **inside** the container, started and
stopped by the lab itself. No port is published and none is needed — there is nothing to
open in a browser. The setup script starts the container with **`--network none`**: a lab
about what you accept from a third-party server should run with no route to any of them.

When it finishes, the script copies three things out of the container and puts them next to
the setup script: `lab14-results.txt`, your transcript; `lab14-tamper-log.jsonl`, the
integrity layer's log; and `lab14-trust.json`, the trust list as you left it. **The log is
the evidence.** It is worth opening on its own.

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Ten commands: a clean run, the
log, a poisoned tool result, the same attack with the control off, a well-formed lie, a
poisoned tool description, the diff, dropping the server, re-pinning it, and the evidence.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also adds the steps beginner skips:
editing `trust.json` with `nano` and deciding for yourself what to pin, **pinning the
poisoned descriptor on purpose** to see every gate report success while the poison reaches
the model anyway, tightening the shape rules so the well-formed lie is caught too, reading
the raw descriptors before any check touches them, and running `python check.py` at the end.

You can re-run the lab to switch modes.

---

## What you are building

**Validate, pin, diff, drop, re-pin.** Five words, and the lab is the argument for why you
need all five.

A tool description is not documentation. It is **instructions your model reads and your user
never sees**, and on an MCP server it is text a third party controls. So the host **pins**
the `sha256` of every descriptor it approved, **diffs** what the server advertises against
that pin on every connection, and **validates** every tool result against the shape its own
schema declares. Every check writes a record either way — including the ones that passed,
which turns out to be the only proof the check was running at all. When the log shows a
descriptor that changed since approval, you **drop** the server from the trust list and
**re-pin** the copy you reviewed, then confirm legitimate traffic still works.

Pinning the *content* rather than the version is the whole trick, and OWASP says why in its
own caveat: pinning "does not stop tool-description poisoning that leaves the version
unchanged". A version number does not move when a description does. A hash does.

**One beat fails on purpose.** The server returns a different balance — nothing appended,
nothing malformed, simply false — and every gate waves it through, because it matches the
declared shape perfectly. You checked the shape; nobody checked the source. Knowing exactly
what your control does not cover is worth more than believing it covers everything, and the
production answer to that gap is a *signed* tool call rather than a better regex.

Whether your company connects agents to third-party MCP servers at all, and who reviews the
diff when one changes, is a decision about appetite rather than tooling — and somebody above
you makes it before you write a line of the validator.

---

## Safety

Nothing here is malware and nothing leaves your machine — there is nowhere for it to go, as
the container runs with no network at all. The "compromised" MCP server is a local Python
file you can read; its payload is one plain English sentence added to a tool description. The
accounts are two lines of fake data, and the "payment" is an entry appended to a list in
memory — no shell command, no message, no network call anywhere in this lab. The MCP server
binds `127.0.0.1:8014` inside the container and is started and stopped by the lab itself.

The tamper log records descriptor hashes, verdicts and the diff. `python check.py` asserts
that the poisoned text never reached the model on any run where the control was on — and it
measures that in the system prompt itself rather than trusting the verdicts, because a
control that logs a block and leaks anyway is exactly the failure worth catching.

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
