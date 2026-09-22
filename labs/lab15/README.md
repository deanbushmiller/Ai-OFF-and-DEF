# Lab 15 — Defending against AI-scaled attacks

**Time:** 12–15 minutes · You write no code.

The seventh **defend** lab, and the last one you download. It pairs with lab 7, where you
were the attacker: you asked a model for five renderings of one record, a signature rule
caught all five, and you got past it with two lines of Python that needed no AI at all. Then
a behavioural detector caught you anyway and you paid 80× in throughput to go clean.

**That detector had one channel to look at, and already knew it was malicious.** This time
you point it at an estate of 24 workstations where almost everything is legitimate software
that also beacons — EDR agents, monitoring, backup clients — and the question stops being
*"does behavioural detection work"* and becomes **"how many colleagues do you wake up to
catch one beacon?"**

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

If you have already done labs 3 to 8 or 12 to 14, you are ready — nothing new to install,
and the download is small. This lab runs the same local language model as those labs and
buys no model, no system package and no Python package of its own, so the pull is the lab's
own source files and nothing else. The big model layer is already on your disk and is not
fetched again. From a clean machine, expect about **1.2 GB** — the language model itself,
the one-time cost that labs 3 to 8, 12 to 14 and this lab all share.

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
  finishes it is copied out to `lab15-results.txt`, next to the setup script you ran. If
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
powershell -ExecutionPolicy Bypass -File .\labs\lab15\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab15/setup/setup.sh
```

This lab runs a mock collector on `127.0.0.1:8015` **inside** the container, started and
stopped by the lab itself. No port is published and none is needed — there is nothing to
open in a browser. The setup script starts the container with **`--network none`**: a lab
about spotting traffic leaving a network should be given no network to leave.

A local language model runs **once**, for about 20 seconds on two cores. Everything else is
plain Python and runs in well under a second, so the machine is not what makes this lab take
15 minutes — the reading is.

When it finishes, the script copies three things out of the container and puts them next to
the setup script: `lab15-results.txt`, your transcript; `lab15-detect-log.jsonl`, the
detector's log; and `lab15-detector.json`, the detector configuration as you left it.
**The log is the evidence.** It is worth opening on its own — the field to follow is
`precision`.

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Ten commands: build the
estate, read what arrived at the collector, run the two detectors you already have, score
the four new limbs, sweep the threshold and set it, generate a variant your detector has
never seen, apply a rate limit and read its bill, watch a changed beacon slip past you, fix
it by changing the matching window rather than the number, and check your work.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also adds the steps beginner skips:
`python detect.py --rarity-only`, which walks four boolean detectors over the same limbs and
shows that the one with perfect precision is beaten by jitter that costs the attacker
nothing; editing `detector.json` with `nano` to change the **weights** rather than just the
threshold; `python evade.py --split 1`, one value per check-in; reading every body the
collector holds; and running `python check.py` at the end.

You can re-run the lab to switch modes.

---

## The question this lab answers

The question is **not** "does behavioural detection work". It is:

**How many colleagues do you wake up to catch one beacon?**

---

## What you will find

- **Lab 7's detector finds the beacon, and 144 other things.** 1 true positive, 144 false
  positives, precision 0.0069. It is not broken; nobody reads 144 alerts a day twice.
- **Four independent questions take that to 0 false positives.** You did not turn anything
  up. A threshold on one dimension cannot buy precision at any setting.
- **A variant nobody predicted is still caught.** The record is what the attacker needed to
  send, so the record is what survives every rendering.
- **The rate limit throttles 90% of the traffic, and the record leaves anyway.** All 6 of its
  values reach the collector, and 120 legitimate channels pay for it.
- **The fix for the slow beacon is not a number, it is where you look.** Reassemble the
  channel's whole day before matching: caught, still 0 false positives, and the attacker paid
  864× in throughput for nothing.

---

## Your evidence

**The log is the evidence.** The setup script copies out **`lab15-detect-log.jsonl`**, the
detector's log — the field to follow is `precision` — **`lab15-results.txt`**, your
transcript, and **`lab15-detector.json`**, the detector configuration as you left it.

| | |
|---|---|
| **Defends** | lab 7 — AI-powered attack orchestration |
| **OWASP** | LLM10:2026 Improper Output Handling, scenario #2, prevention 7 · LLM02:2026 Sensitive Information Disclosure · LLM06:2026 Unbounded Consumption — cited for its controls, not its risk |
| **ATLAS techniques** | `AML.T0016.002` → `AML.T0043.003` → **`AML.T0015` Evade AI Model**, the one you are countering |
| **ATLAS mitigations** | `AML.M0004` the prevent stub · `AML.M0024` `detect-log.jsonl` · `AML.M0006` Predictive AI Ensembles · `AML.M0039` AI Honeypots, named not built · `AML.M0035` AI Red Team |

Five of the seven mitigations ATLAS maps to `AML.T0015` assume you own the model being evaded.
If the thing being evaded is your signature set, the framework has no entry for you. That gap
is explained in [`LAB.md`](LAB.md).

---

## Every step in the lab

🅱️ marks the core steps. Beginner mode runs only those. The full walkthrough of each step is
in [`LAB.md`](LAB.md).

```
    cd /labs/lab15                          expert: start here
    cat record.txt
    cat detector.json
    sed -n '/^def limbs/,/^def score/p' lab15lib.py     the four limbs, 20 lines
🅱️  python estate.py --build                build the estate
🅱️  python inbox.py                         read the collector's inbox
    python inbox.py --show
    python estate.py --show
🅱️  python detect.py --baseline             what you have today
🅱️  python detect.py --score                four limbs instead of two
🅱️  python detect.py --sweep --set 4        where do you put the line
    python detect.py --rarity-only          the trap. Four booleans, none of them work
🅱️  python variants.py --live json          red-team your own control
    python variants.py --live yaml
    python variants.py --formats
🅱️  python limit.py --cap 6                 the prevent stub, and its bill
    python limit.py --cap 1
🅱️  python evade.py                         the operator's next day
    python evade.py --split 1
🅱️  python detect.py --window channel       recovery
    nano detector.json                      expert: tune the WEIGHTS, not just the threshold
    python detect.py --score
🅱️  python check.py && python evidence.py   both bills
```

---

## Submit

Paste the three numbers from `evidence.py` into the class chat: lab 7's detector on a real
estate, yours after tuning, and what evasion cost the attacker.

---

## What you are building

**Limit, detect on behaviour, log, tune, measure the cost.** Five words, and the lab is the
argument for why the order matters.

A **rate and volume cap** goes in front of the collector — and the lab measures what it
actually buys, which is less than it looks: it throttles the loud beacon and the monitoring
fleet equally, never touches a slow one, and the record leaves anyway. That is why
prevention is the small half here.

A **behavioural detector** does the work, keyed on four things a rewrite cannot change: how
rare the destination is, whether the timing looks like a machine rather than a person, how
much traffic there is, and whether the record's own values survive the rendering. Each one is
weighted; the scores are summed; you choose the threshold by reading what each setting costs
in false alarms.

A **log** records every verdict, so the tune is a change you can point at afterwards rather
than a number somebody remembers editing.

Then you **tune** — and the interesting part is that the fix is not the threshold. You will
already have measured that turning it down costs 72 false positives and still misses. The
change that works is *where you look*: reassemble what a channel sent across the whole day
before matching it, instead of judging each message alone.

Finally you **measure the cost** — in both directions. What evasion cost the attacker (864×
slower), and what your own wrong answer would have cost you (144 alerts a day). A defender
who can only quote the first number loses the budget meeting.

---

## Safety

Nothing here is malware and nothing leaves your machine — there is nowhere for it to go, as
the container runs with no network at all. The "beacon" is one line of inert text with a
harmless marker in it, the same convention as EICAR. The ten renderings of it were generated
once, during lab 7, and ship as a data file; **this lab does not generate attack variants
and does not contain a loop that searches for one that evades**. The estate is synthetic
telemetry the lab writes itself. The collector binds `127.0.0.1:8015` inside the container,
accepts a POST, appends it to a file and answers 200 — there is no command channel, no
session and no protocol.

The one model call sends a prompt that asks for a record to be re-encoded into JSON. That is
all it asks, no content filter would refuse it, and lifting it out of this image gets you a
format converter. **That is the lesson rather than an oversight:** a detector keyed on
wording loses to a format converter, so the one you build is not keyed on wording.

The detector log records limb verdicts, scores and counts. `python check.py` asserts that
the record's values actually reaching the collector are **measured at the collector's own
store** rather than inferred from any verdict — because a detector that alerts on everything
scores perfect recall and protects nothing, and that is exactly the failure worth catching.

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
