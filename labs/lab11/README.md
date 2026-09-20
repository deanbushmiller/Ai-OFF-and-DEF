# Lab 11 — Defending multimodal input

**Time:** 12–15 minutes · You write no code.

The third **defend** lab. It pairs with lab 4, where a pipeline read an instruction out of an
invoice that no person could see, and a classifier was flipped by a change of 7 in 255. This
time you build the controls that stand in front of both.

Lines marked 🅱️ in [`LAB.md`](LAB.md) are the **core defence commands**. Beginner mode runs
only those. Expert mode runs the whole list.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have already done lab 4, you are ready — nothing new to install, and the OCR engine
this lab uses is already on your disk from lab 4, down to the byte. No language model runs
here, so this is the smallest image in the course.

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
  finishes it is copied out to `lab11-results.txt`, next to the setup script you ran. If
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
powershell -ExecutionPolicy Bypass -File .\labs\lab11\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab11/setup/setup.sh
```

This lab serves nothing and opens no port. Like labs 9 and 10, the setup script starts it with
**`--network none`**. Nothing here needs a network, and running without one proves the point:
the hidden text is in a file on your own disk, not fetched from anywhere.

When it finishes, the script copies three things out of the container and puts them next to
the setup script: `lab11-results.txt`, your transcript; a `lab11-invoices/` folder with the
clean invoice and the stamps; and a `lab11-review-queue/` folder with the doctored invoice,
the held stamp, and the record written for each. **Open `invoice-clean.png` and the queued
`invoice-attack.png` side by side.** That is the part of this lab worth two minutes of your
own eyes.

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Ten commands: two through the
OCR, two through the content check, the comparison and its log, the stamp gate, then route,
tune and the gate again.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also adds the steps beginner skips:
editing the policy in `rules.json` with `nano` instead of letting a script do it — including
moving the visible-contrast threshold until the hidden line counts as visible at one end and
the print itself vanishes at the other — writing your own hidden instruction with `nano
payload.txt` and `python craft.py` and rewording it until the rule check passes it while the
comparison still catches it, running the clean stamp through the tightened gate, reading the
log and the queue records yourself, and running `python check.py` at the end.

You can re-run the lab to switch modes.

---

## What you are building

Five small pieces, and the lab is the argument for why you need all of them.

A **content check** on the text the OCR produced, before anything acts on it: four patterns
and a length limit that flag text which reads like an instruction rather than like data. A
**comparison** between what the machine read and what a person would see — the same OCR run
twice, once on the image as it is and once with every faint mark erased — that logs any line
the model read and a reviewer could not have. A **mismatch log** that records every decision
in order, so "which document said that?" has an answer. A **review queue** that a flagged
document is moved into, with the evidence and its hash, so a person decides instead of a
score. And a **tuning** step where you tighten the classifier's auto-accept threshold and add
the indicator your own comparison produced to a rule list that is yours.

OCR, check, compare, route, tune. The content check is cheap and it is not enough — reword the
payload and it misses, which OWASP says in the same sentence that recommends it. The
comparison is what catches the line without reading it, and it is the deterministic heart of
the lab. The log is how you answer "which document did that?" The queue is what turns a
detection into a decision by a person. And whether your company lets a model act on anything
it reads out of a picture at all, or only suggest, is a decision about appetite rather than
tooling — and somebody above you makes it before you write a line of the check.

---

## Safety

Nothing here is malware and nothing leaves your machine. The doctored invoice is lab 4's: one
line of plain English drawn at 1.2% contrast, asking for an approval. The perturbed stamp is
lab 4's too: a change of 7 in 255. No commands, no code, no network, and no language model —
every result is arithmetic on pixels and text, identical on every machine.
