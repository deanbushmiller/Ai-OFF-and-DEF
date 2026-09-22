# Lab 10 — Defending RAG ingestion

**Time:** 12–15 minutes · You write no code.

The second **defend** lab. It pairs with lab 2, where one document changed what the assistant
believed about who invented the telephone. This time you build the control that refuses it —
and then watch something get through anyway.

Lines marked 🅱️ in [`LAB.md`](LAB.md) are the **core defence commands**. Beginner mode runs
only those. Expert mode runs the whole list.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have already done lab 2, you are ready — nothing new to install, and almost nothing
new to download. This lab reuses lab 2's dependencies and both of lab 2's models down to the
byte, so the pull is **about 34 KB** and takes a second. From a clean machine it is about
572 MB on Apple Silicon and 628 MB on Intel. Measured on the published image, both
architectures.

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
  finishes it is copied out to `lab10-results.txt`, next to the setup script you ran. If
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
powershell -ExecutionPolicy Bypass -File .\labs\lab10\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab10/setup/setup.sh
```

This lab serves nothing and opens no port. Like lab 9, the setup script starts it with
**`--network none`**, so the container cannot reach anything at all. Here that is not the
lab's subject — it is the lab's *control group*. Everything you are about to watch happen,
happens with no network: the answer changes because of a file on your own disk, not because
of anything fetched from outside.

When it finishes, the script copies `lab10-results.txt` out of the container and puts it next
to the setup script. That is your transcript and your evidence.

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Eleven commands: three through
the validator, five through the canary and the log, then purge, verify and tune.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also adds the steps beginner skips:
editing the validator's policy in `rules.json` with `nano` instead of letting a script do it
— including dropping the similarity threshold until a *legitimate* document starts failing,
so you see what a tighter rule costs — reading `canary-log.jsonl`, `retrieval-log.jsonl` and
`purge-log.json` yourself, purging by document instead of by tag, and running
`python check.py` at the end.

You can re-run the lab to switch modes.

---

## What you are building

Five small pieces, and the lab is the argument for why you need all of them.

A **validator** that refuses a document before it is embedded: no text a human cannot read,
no document without a recorded origin, no document claiming to be the authority on half your
corpus. A **provenance tag** on every chunk, saying where it came from and who is accountable
for it. A **canary** — one question whose correct answer you already know, asked after every
ingest. A **retrieval log** that records which chunk drove every answer and what it scored. A
**purge** that removes vectors by tag and a **tuning** step where you add the indicator your
own detector produced to your own rules.

Validate, canary, log, purge, tune. The validator is cheap and it is not enough — you will
override it yourself, on purpose, because that is what happens in real organisations on a
Friday afternoon. The canary is what catches the document that got past it, and it is the
deterministic heart of the lab. The log is how you answer "which document did that?" — a
question that has no answer at all if nobody wrote it down. The tag is what makes the purge
surgical instead of a full rebuild. And whether your company lets anyone contribute documents
at all, or only a named team, is a decision about appetite rather than tooling — and somebody
above you makes it before you write a line of the validator.

---

## Safety

Nothing here is malware and nothing leaves your machine. The payload is the same one from
lab 2: five sentences, drawn in white on a white page, that simply state things which are
false. No commands, no code, no network. That is the point — a content filter looking for
malicious instructions would not see this document at all.

---

## Want to see the poisoned file yourself?

You cannot open a PDF inside the container — there is no viewer, and `cat` shows you
compressed binary. Copy it out to your own machine instead, from a **second terminal** while
the lab is still running:

```
docker cp seclm-lab10-run:/labs/lab10/poisoned_handbook.pdf ~/Desktop/
```

Open it. You will see four dull lines about laptops and multi-factor authentication, and
nothing else. That is the whole point: the five lines that change the assistant's answer are
drawn in white on a white page at 6pt, and **you will not find them by looking.**

To see what the machine reads instead, back in the container:

```
python -c "
from pypdf import PdfReader
for p in PdfReader('poisoned_handbook.pdf').pages:
    print(p.extract_text())
"
```

Eleven lines instead of four. Same file. `python validate.py poisoned_handbook.pdf` goes one
better and tells you *why* five of them are hidden — the fill colour and the font size each
one was drawn at.

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
