# Lab 8 — Offensive recap and transition to defense

**Time:** 12–15 minutes · You write no code. **There is no attack in this lab.**

Lines marked 🅱️ are the **core steps**. Beginner mode runs only those.
Expert mode runs the whole list.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have done labs 1 to 7, you are ready — and this one is the lightest of the lot. It
runs **no model at all**, so there is nothing to download beyond a few hundred kilobytes
and nothing to wait for once it starts.

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
  finishes it is copied out to `lab8-results.txt`, next to the setup script you ran. If
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
powershell -ExecutionPolicy Bypass -File .\labs\lab8\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab8/setup/setup.sh
```

This lab opens no port, starts no server, and loads no model. It reads two JSON files.

When it finishes, the script copies your transcript out to `lab8-results.txt`, next to the
setup script.

### Nothing in this lab takes time

Every step is instant. The 12–15 minutes is **reading time**, and that is the whole design:
this is the lab where you stop doing and start thinking about what you did.

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Eight steps.

One of those steps asks you seven questions — for each earlier lab, which ATLAS technique
*is* that lab. It shows you the full chain to pick from, tells you when you are wrong, and
fills the answer in after a second miss.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also does the mapping **without
multiple choice**: `python mapping.py --worksheet` writes a blank worksheet, you fill it in with
`nano worksheet.txt`, and `python mapping.py --grade` scores it. Expert also reads `course.json`
(this lab's answer key, which was *generated* from labs 1–7 rather than typed) and the
distilled ATLAS data at `/opt/lab-assets/atlas/atlas.json`. Finish with `python check.py`.

To go straight to expert mode, add `--expert` to the command above.

**If it fails**, the script tells you why in plain English. Send that message to the
instructor through GitHub.

---

## The question this lab answers

You have attacked seven things. **What does that add up to?**

**This is the first half of a two-part course.** Part 2 is seven defender labs covering the
same ground from the other side, so this lab *names* the controls and stops there. It is an
introduction — anything more would feel like enough when it is not.

---

## What you will find

- **20 ATLAS techniques across 12 of the 16 tactics**, from seven labs.
- **One technique in five of the seven labs** — indirect prompt injection is not one attack
  among many, it is how most of the others were *delivered*.
- **Two controls covering five of the seven labs**, and they are the least glamorous two in
  security: log what happened, validate what crosses a boundary.
- **Nine techniques with no published mitigation at all** — every one added to ATLAS
  between March 2025 and March 2026. The defensive literature is about a year behind the
  offensive literature, and the lab shows you the dates.
- **Four tactics you never touched**, including Exfiltration — which was a deliberate
  safety decision taken four separate times, not an oversight.

---

## Your evidence: an ATLAS Navigator layer

The last step writes **`atlas-layer.json`**. It is not a file only this course can read —
it is a standard **ATLAS Navigator layer**, the same format security teams use for their own
coverage maps.

**To see your own course on the real matrix:**

1. Open the **[MITRE ATLAS Navigator](https://atlas.mitre.org/navigator)**.
2. Choose **Open Existing Layer** → **Upload from local**.
3. Drop in `atlas-layer.json`, which the setup script copied out next to
   `lab8-results.txt`.

Your seven labs appear on the live matrix, coloured by how many labs used each technique,
with the ATLAS mitigations — or the absence of them — in each technique's comment.

Useful links while you are there:

- **[MITRE ATLAS](https://atlas.mitre.org)** — the matrix itself, with every technique's
  full description and case studies.
- **[ATLAS Navigator](https://atlas.mitre.org/navigator)** — where your layer file loads.
- **[atlas-data](https://github.com/mitre-atlas/atlas-data)** — the raw data this lab
  bundles, if you want to build your own tooling on it.
- **[OWASP GenAI LLM Top 10 (2026)](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)**
  — the other framework this course maps against.

---

## Every step in the lab

🅱️ marks the core steps. Beginner mode runs only those.

```
🅱️  python recap.py                      the seven attacks, one line each
🅱️  python mapping.py                        name the technique that IS each lab
🅱️  python coverage.py                   the matrix, with your labs on it
🅱️  python coverage.py --gaps            the four tactics you never touched
🅱️  python coverage.py --spine           the one technique in 5 of 7 labs
🅱️  python defend.py                     the controls MITRE names
🅱️  python defend.py --gaps              where the published guidance runs out
🅱️  python export.py                     your ATLAS Navigator layer
    cd /labs/lab8                        expert: start here
    python mapping.py --worksheet            expert: no multiple choice
    nano worksheet.txt
    python mapping.py --grade
    cat course.json                      the answer key, generated from labs 1-7
    python check.py                      confirm it all holds together
```

---

## Submit

`atlas-layer.json`, or a screenshot of it loaded in the Navigator, through the class chat
or GitHub.

**And check you have submitted evidence for all eight labs.** The setup script lists them
when the lab exits — if one is missing, the lab is still on your machine and still
repeatable.

---

## That is the end of part 1

Eight labs. You have attacked a model supply chain, a RAG corpus, a web-reading assistant,
an OCR pipeline, an agent's tool layer, an MCP channel, and a detector — and then mapped
the lot.

Part 2 is the other half — seven defender labs, starting with semantic firewalls and RAG
validation and ending with automated red teaming. Same ground, from the other side.

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
