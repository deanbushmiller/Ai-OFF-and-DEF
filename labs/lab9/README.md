# Lab 9 — Defending the model supply chain

**Time:** 12–15 minutes · You write no code.

The first **defend** lab. It pairs with lab 1, where you built a model file that ran a
command when it loaded. This time you build the control that stops it.

Lines marked 🅱️ in [`LAB.md`](LAB.md) are the **core defence commands**. Beginner mode runs
only those. Expert mode runs the whole list.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have already done lab 1, you are ready — nothing new to install, and the download is
**about 28 KB**. Lab 9 reuses lab 1's model and libraries down to the byte, so there is
almost nothing left to fetch. From a clean machine the image is about **191 MB on Apple
Silicon and 247 MB on Intel**. Both figures measured on the published image, 2026-09-19.

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
  finishes it is copied out to `lab9-results.txt`, next to the setup script you ran. If
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
powershell -ExecutionPolicy Bypass -File .\labs\lab9\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab9/setup/setup.sh
```

This lab serves nothing and opens no port. It is also the first lab the setup script starts
with **`--network none`**, so the container has no way to reach anything at all. That is not
housekeeping — it is the lab's subject. One of the files you load tries to open a connection,
and you are meant to see that the container it is running in has nowhere to send it.

When it finishes, the script copies `lab9-results.txt` out of the container and puts it next
to the setup script. That is your transcript and your evidence.

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Nine commands: three through
the gate, three through the sandbox, then quarantine and tune.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also adds the steps beginner skips:
editing the gate's policy in `rules.json` with `nano` instead of letting a script do it,
reading `blocklist.json` and the raw `sandbox-log.jsonl` yourself, and running
`python check.py` at the end — a self-check that tells you whether your defence actually
holds together, without walking you through it.

You can re-run the lab to switch modes.

---

## What you are building

Four small pieces, and the lab is the argument for why you need all four.

A **gate** that hashes an artifact, scans it, and applies rules of your own before it is
allowed into a build. A **sandbox** that loads the artifact on purpose, in a separate process
with no network, and writes down every import, every command and every attempted connection.
A **quarantine** that moves a bad artifact aside and records its hash with the evidence. And
a **tuning** step where you take an indicator your own sandbox produced and add it to your
own rules, so the gate catches it earlier next time.

Scan, sandbox, quarantine, tune. The scan is cheap and it is not enough — it reads the file
but cannot tell you what the file *does*, and its list of dangerous things is somebody else's
list, kept up to date by somebody else. The sandbox costs more and tells you what actually
happened. The quarantine and the rule are how an organisation remembers. Whether you buy the
first, build the second, or decide the whole class of artifact is not allowed through the
door, that is a decision about appetite, not about tooling — and somebody above you makes it
before you write a line of the gate.

---

## Safety

Nothing here is real malware and nothing leaves your machine. One payload runs an `echo`.
The other opens a socket to `203.0.113.10`, an address reserved for documentation that
routes nowhere — and the lab refuses the call before it is made, inside a container that has
no network in the first place.
