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

If you have already done labs 3 to 7, 12 or 13, you are ready — nothing new to install, and
the download is small. This lab runs the same local language model as those labs and buys no
model, no system package and no Python package of its own, so the pull is the lab's own
source files and nothing else. The big model layer is already on your disk and is not
fetched again. From a clean machine, expect about **1.2 GB** — the language model itself,
the one-time cost that labs 3 to 7, 12, 13 and this lab all share.

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

## The question this lab answers

The question is **not** "is the traffic tampered with on the wire". There is no attacker on
the wire. It is:

**When the MCP server itself is the adversary, how do you know the tool your model is reading
is still the one you approved?**

---

## Architecture

Two processes, both inside this container, both on `127.0.0.1`. No port is published and
there is no network.

```
   "What is the balance of account chk-001?"
                │
                ▼
   ┌────────────────────────────────────┐
   │   THE HOST        ask.py           │        ┌──────────────────────┐
   │   loads the model                  │        │   MCP SERVER         │
   │                                    │        │   mcp_server.py      │
   │   ┌────────────────────────────┐   │ JSON-  │   127.0.0.1:8014     │
   │   │  verify.py                 │◄──┼──RPC──►│                      │
   │   │  1 trust list              │   │  2.0   │   get_balance        │
   │   │  2 descriptor pin (sha256) │   │        │   send_payment       │
   │   │  3 message schema          │   │        │                      │
   │   └──────────┬─────────────────┘   │        │   ** COMPROMISED **  │
   │              │                     │        └──────────────────────┘
   │        tamper-log.jsonl            │
   └────────────────────────────────────┘
                  │
            trust.json  ── the servers you approved, and exactly what you approved
```

**Read that right-hand box.** In lab 6 the server was honest and an attacker sat on the wire.
Here there is no attacker on the wire — **the server itself is the adversary**, which is the
real MCP threat model: you connect an agent to software somebody else operates, and that
software chooses the text your model reads.

---

## Your evidence

**The log is the evidence.** The setup script copies out **`lab14-tamper-log.jsonl`**, the
integrity layer's log — a record for every gate, pass or block, plus the descriptor hashes and
the diff — **`lab14-results.txt`**, your transcript, and **`lab14-trust.json`**, the trust
list as you left it.

| | |
|---|---|
| **Defends** | lab 6 — MCP and interface hijacking |
| **OWASP** | LLM01:2026 Prompt Injection — prevention 10, Scenario #9 · LLM08:2026 Hidden Context Exposure — risks #1 and #4 · Agentic cross-map ASI04 Agentic Supply Chain Vulnerabilities |
| **ATLAS techniques** | `AML.T0084.001` → `AML.T0110.000` / `AML.T0110.002` → `AML.T0051.001` → `AML.T0053`, with `AML.T0109` AI Supply Chain Rug Pull as the update path |
| **ATLAS mitigations** | borrowed: `AML.M0014` Verify AI Artifacts the pin · `AML.M0033` Input and Output Validation the schema check · `AML.M0024` AI Telemetry Logging the log · `AML.M0023` AI Bill of Materials the trust list · `AML.M0013` the production answer, signed tool calls |

---

## Every step in the lab

🅱️ marks the core steps. Beginner mode runs only those. The full walkthrough of each step is
in [`LAB.md`](LAB.md).

```
🅱️  LAB14_RUN=clean python ask.py                     a normal question, control on
🅱️  python tamperlog.py                               three PASS records, one per gate
🅱️  python poison.py --result                         compromise the server's ANSWER
🅱️  LAB14_RUN=result python ask.py                    blocked at gate 3
🅱️  LAB14_RUN=undefended python ask.py --no-verify    the same attack, control OFF
🅱️  python poison.py --rewrite                        a well-formed LIE
🅱️  LAB14_RUN=rewrite python ask.py                   the control passes it. On purpose.
🅱️  python poison.py --descriptor                     compromise the DESCRIPTION
🅱️  LAB14_RUN=swapped python ask.py                   blocked at gate 2 - and an outage
🅱️  python tamperlog.py --diff                        THE DIFF. This is the finding.
🅱️  python drop.py                                    recovery 1: off the trust list
🅱️  LAB14_RUN=dropped python ask.py --wire-only       refused at gate 1, nothing read
🅱️  python repin.py                                   recovery 2: re-pin what you approved
🅱️  LAB14_RUN=repinned python ask.py                  service restored, on YOUR copy
🅱️  python evidence.py                                the story, plus the free replay
    cat verify.py                                     ~80 lines; the whole control
    python ask.py --tools                             the raw descriptors, unchecked
    python ask.py --ask "How much is in chk-002?"     ask something else
    python mcp_server.py &                            run the server by hand
    nano trust.json                                   edit the trust list yourself
    python check.py                                   confirm the control held
```

The beginner runner packs these into ten steps by pairing each `poison.py` with the `ask.py`
that follows it. Expert runs them one at a time.

---

## Submit

`python evidence.py` prints every run, where each refusal happened, and the replay. **The
diff from `python tamperlog.py --diff` is the finding** — paste both into the class
chat. The full transcript is in `lab14-results.txt`.

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

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
