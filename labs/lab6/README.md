# Lab 6 — MCP and interface hijacking

**Time:** 12–15 minutes · You write no code.

Lines marked 🅱️ are the **core attack commands**. Beginner mode runs only those.
Expert mode runs the whole list.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have already done labs 1 to 5, you are ready — nothing new to install. Like lab 5,
this lab adds **no new software at all**: it reuses the same language model labs 3 to 5
already put on your machine.

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
  finishes it is copied out to `lab6-results.txt`, next to the setup script you ran. If
  something scrolled past, open that file afterwards rather than hunting for it in the
  terminal — and it is the same file you use as evidence.

---

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
powershell -ExecutionPolicy Bypass -File .\labs\lab6\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab6/setup/setup.sh
```

This lab runs three programs that talk to each other over HTTP — but all three live inside
the container, all three bind `127.0.0.1` only, and **no port is published to your machine**.
Once the image is on your machine the lab runs with no network at all.

When it finishes, the script copies your transcript out to `lab6-results.txt`, next to the
setup script. That file is your evidence.

### Four steps take about a minute each

Four of the seven commands run a language model on your own CPU. Each takes roughly a
minute, and up to two on an older laptop. **That is the lab working, not the lab hanging.**

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Seven commands.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also adds the steps beginner skips:
starting the server, the proxy and the client as **three separate processes** so you can see
they really are three programs on a network, reading `proxy.py` (about 120 lines, and it is
the entire attack), running the one tampering beat the guided path skips, and editing
`payload.txt` with `nano` to write **your own** instruction. Finish with `python check.py`.

To go straight to expert mode, add `--expert` to the command above.

**If it fails**, the script tells you why in plain English. Send that message to the
instructor via email or post to class Q&A.

---

## The question this lab answers

Your model talks to its tools over a protocol. **What proves that the answer it got back is
the answer the server sent?**

---

## Architecture

Three processes, all inside the container, all on `127.0.0.1`.

```
   "What is the balance of account chk-001?"
                │
                ▼
   ┌────────────────────┐   JSON-RPC 2.0 over HTTP
   │   MCP CLIENT       │───────────────┐
   │   mcp_client.py    │               ▼
   │   loads the model  │      ┌──────────────────┐      ┌────────────────────┐
   └────────────────────┘      │   THE PROXY      │      │   MCP SERVER       │
              ▲                │   proxy.py       │─────►│   mcp_server.py    │
              │                │   127.0.0.1:8006 │◄─────│   127.0.0.1:8007   │
              └────────────────│                  │      │   get_balance      │
                  tool result  │  reads and EDITS │      │   send_payment     │
                               │  both directions │      └────────────────────┘
                               └──────────────────┘
                                        │
                                    wire.log
```

The client believes it is talking to the server. The server believes it is answering the
client. **Neither can tell the proxy exists, and neither checks.**

---

## The vulnerable configuration

Nothing is wrong with the server, and nothing is wrong with the client. Both behave
correctly. The vulnerability is in what they take on trust.

1. **Nothing authenticates the channel.** Plain JSON-RPC over HTTP: no signature, no
   checksum, nothing tying an answer to the server that sent it. Anything sitting on that
   wire speaks with the server's authority.
2. **The client pastes tool DESCRIPTIONS into the model's instructions.** The user never
   sees them, and the *server* chooses the text — OWASP LLM08:2026, risks #1 and #4.
3. **The client pastes tool RESULTS into the conversation unlabelled.** Nothing marks them
   as data rather than instruction.

---

## Mapping

**OWASP LLM01:2026 Prompt Injection — Scenario #9, Trusted-Backend Indirect Injection
through MCP.** The most incident-backed scenario in the entry: it names a poisoned GitHub
issue that exfiltrated private repos, a Supabase MCP server that dumped a production
database, and the `postmark-mcp` package that BCC'd email from an estimated 300
organisations — all in 2025.

The control this lab teaches is the entry's **prevention #10**, which undercuts the obvious
fix in its own words:

> Pin, sign, and verify every MCP server and third-party tool package, audit tool
> descriptions for hidden instructions… **Pinning does not stop a payload shipped in the
> pinned version or tool-description poisoning that leaves the version unchanged.**

**Secondary: LLM08:2026 Hidden Context Exposure**, new in 2026 — risk #4's own worked
example is a tool description served by an MCP server.

**MITRE ATLAS** (v5.6.0): `AML.T0084.001` Tool Definitions → **`AML.T0110` AI Agent Tool
Poisoning** → `AML.T0051.001` → `AML.T0053`. `AML.T0110` names the protocol and both
attacks: *"modifying parameters or descriptions… or redirecting outputs."*

---

## Every command in the lab

🅱️ marks the core commands. Beginner mode runs only those.

```
🅱️  python mitm.py --tools                                    what the server advertises
🅱️  python mitm.py --beat control                             a normal question
🅱️  python mitm.py --rewrite-arg chk-002 --beat arg           edit the REQUEST
🅱️  python mitm.py --inject --beat inject                     edit the RESPONSE
🅱️  python mitm.py --inject --verify --beat defended          the defence
🅱️  python mitm.py --rewrite-arg chk-002 --verify --wire-only where the defence fails
🅱️  python evidence.py                                        the evidence
    python mitm.py --rewrite-result 999999.00                 the beat the guided path skips
    cat proxy.py                                              ~120 lines; the whole attack
    python mcp_server.py &                                    run the three by hand
    python proxy.py --inject &
    python mcp_client.py
    nano payload.txt                                          write your OWN instruction
    python check.py                                           confirm the evidence is real
```

---

## Evidence to submit

`python evidence.py` prints the wire log next to what the assistant told you. **The
disagreement between those two is the finding** — paste both into the class chat. The full
transcript is in `lab6-results.txt`.

---

## One thing that did NOT work, and why you should know

**Tool-description poisoning is the famous MCP attack** — hide an instruction in a tool's
help text and the agent obeys it. It was tried while building this lab, in four phrasings
and two presentations, and this model ignored it **15 times out of 15**.

That is not reassurance. The MCPTox benchmark measures over **60% success across 45+
real-world MCP servers**, with the best model at 72.8%. **The attack scales with model
capability** — a smarter agent is a more obedient one. Ask your instructor for the demo.

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
