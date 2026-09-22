# Lab 12 — Defending against prompt injection

**Time:** 12–15 minutes · You write no code.

The fourth **defend** lab, and the flagship control of the defend half. It pairs with lab 3,
where a web page you did not write took over an assistant by hiding an instruction in a div no
browser paints. This time you put a firewall in front of the model and behind it — and then
you find out what the firewall missed.

Lines marked 🅱️ in [`LAB.md`](LAB.md) are the **core defence commands**. Beginner mode runs
only those. Expert mode runs the whole list.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have already done labs 3 to 8, you are ready — nothing new to install, and the
download is **about 30 KB**, on both Apple Silicon and Intel, measured on
the published image. This lab runs the same local language model as those labs and buys no
model, no system package and no Python package of its own, so the pull is the lab's own source
files and nothing else. From a clean machine, expect about **1.2 GB** — the language model
itself, the one-time cost labs 3 to 8 all share.

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
  finishes it is copied out to `lab12-results.txt`, next to the setup script you ran. If
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
powershell -ExecutionPolicy Bypass -File .\labs\lab12\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab12/setup/setup.sh
```

This lab runs a small website, but it runs it **inside the container, on loopback there
only**. No port is published to your machine, and the setup script starts the container with
**`--network none`** — a lab about a content boundary should run under one. You read the
pages the way the assistant reads them, with `curl`, from inside the lab. That is also the
only view that shows you a payload a browser is built to hide.

When it finishes, the script copies two things out of the container and puts them next to the
setup script: `lab12-results.txt`, your transcript, and `lab12-firewall-log.jsonl`, the
firewall's own request log. **The log is the evidence.** It is worth opening on its own.

### Choose a mode

**Beginner** — the default, and the right choice if you are not sure. The lab shows each
command with a short explanation of what it does and why. You type or paste it, and the lab
checks it before anything runs. Get it wrong and it tells you what the command should have
been; get it wrong twice and it runs the correct one for you. Ten commands: the rule file, a
clean page through the firewall, the log, the obvious attack, the quiet attack, the log again,
the fix, the re-test, the clean page once more, and the evidence.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md). Expert also adds the steps beginner skips:
editing `rules.json` with `nano` and deciding for yourself what to change rather than letting
a script do it, fetching the page whose payload is hidden with invisible Unicode characters
instead of CSS, writing your own wording into a page and watching a phrase rule miss a
rephrasing it was never written for, and running `python check.py` at the end.

You can re-run the lab to switch modes.

---

## The question this lab answers

The question is **not** "does the firewall work". It is:

**When the firewall sees the attack and lets it through anyway, how do you find out?**

---

## Architecture

```
   YOU                                                      /labs/lab12/
    |
    |  python firewall.py <url>
    v
 +------------------------------------------------------------------+
 |  fetch  ->  to_text()  ->  [ INBOUND SCAN ]  -> gate              |
 |               ^                    |                              |
 |        the naive scraper           | families -> severity         |
 |        keeps display:none          | block if >= rules.json       |
 |        and comment text            |            block_at          |
 |                                    v                              |
 |                           Qwen2.5-1.5B-Instruct                   |
 |                           system prompt holds a FAKE support key  |
 |                                    |                              |
 |                                    v                              |
 |                            [ OUTBOUND SCAN ]                      |
 |                            marker found -> suppress the answer    |
 |                                    |                              |
 |                                    v                              |
 |                        firewall-log.jsonl                         |
 |                        one record per direction, always           |
 +------------------------------------------------------------------+

   site/ served by serve.py on 127.0.0.1:8012 INSIDE the container ONLY.
   No port is published. The container runs with --network none.
   http://news.acme.com:8012/... resolves locally via /etc/hosts.
```

**Four pages, and they look identical in a browser. That is the point.**

| page | what is in it | families | severity |
|---|---|---|---|
| `article.html` | an ordinary business article | — | NONE |
| `article-poisoned.html` | lab 3's payload: hidden div, "ignore the text above", "reply with exactly" | `override`, `authority`, `exfil`, `concealment` | **CRITICAL** |
| `memo-leak.html` | a quiet one: a format demand, hidden in a div. No "ignore", no fake system header | `exfil`, `concealment` | **HIGH** |
| `memo-smuggled.html` | the same demand, concealed with invisible Unicode instead of CSS *(expert)* | `exfil`, `concealment` | **HIGH** |

---

## Your evidence

**The log is the evidence.** The setup script copies out **`lab12-firewall-log.jsonl`**, the
firewall's own request log, and **`lab12-results.txt`**, your transcript. `python evidence.py`
turns the story into one table.

| | |
|---|---|
| **Defends** | lab 3 — advanced prompt injection |
| **OWASP** | LLM01:2026 Prompt Injection — Common Example 2, Scenario #2; preventions 3, 5 and 11 built, 1, 2 and 6 named · LLM02:2026 Sensitive Information Disclosure — Tier 1 preventions 4 and 5 |
| **ATLAS techniques** | `AML.T0066` → `AML.T0068` → `AML.T0051.001`/`.002` → `AML.T0057` |
| **ATLAS mitigations** | `AML.M0020` / `AML.M0033` the two-sided scan · `AML.M0024` the log · `AML.M0035` the tune |

`AML.M0021` Generative AI Guidelines and `AML.M0022` Model Alignment are real ATLAS
mitigations for prompt injection, and lab 3 measured a 3/3 hijack with both of them in place.
They are not a firewall.

---

## Every step in the lab

🅱️ marks the core steps. Beginner mode runs only those. The full walkthrough of each step is
in [`LAB.md`](LAB.md).

```
🅱️  cat rules.json                                 look at the control before you use it
🅱️  python firewall.py http://news.acme.com:8012/article.html
                                                   the baseline: a clean page through the firewall
🅱️  python log.py                                  every request, both directions
🅱️  python firewall.py http://news.acme.com:8012/article-poisoned.html
                                                   the obvious attack
🅱️  python firewall.py http://news.acme.com:8012/memo-leak.html
                                                   the quiet one
🅱️  python log.py                                  find the request that was allowed anyway
🅱️  python tune.py                                 close the gap
    nano rules.json                                expert: instead of tune.py, decide what to change
🅱️  python firewall.py http://news.acme.com:8012/memo-leak.html
                                                   the same page, the same command
🅱️  python firewall.py http://news.acme.com:8012/article.html
                                                   re-check the clean page
🅱️  python evidence.py                             the whole story in one table
    curl -s http://news.acme.com:8012/memo-smuggled.html | tail -8
                                                   expert: the invisible-character page
    python firewall.py http://news.acme.com:8012/memo-smuggled.html
    python check.py                                confirm it all holds together
```

---

## Submit

The table from **`python evidence.py`** — the whole story in one table. This is what you
submit.

Your full transcript is saved to `lab12-results.txt` and copied out next to the setup script
when the lab exits.

---

## What you are building

**Scan in, scan out, log, tune.** Four pieces, and the lab is the argument for why you need
all four.

An **inbound scan** on the text fetched from a page, before it reaches the model: four
detector families — an order to ignore the page, text impersonating a system message, a
demand for something out of the model's own configuration, and any attempt to hide the
payload from a human reader. An **outbound scan** on the model's answer, matching the shape of
a credential before the answer reaches you. A **request log** that records every request in
both directions with the verdict on each — *including the ones it decided to allow*, which is
the record everything else in this lab depends on. And a **tuning** step where the log tells
you the gate was set too loose, you tighten it, and you re-test against the attack **and**
against ordinary traffic.

The inbound scan is cheap and it is not enough — reword the payload and it misses, which OWASP
says in the same sentence that recommends it. The outbound scan is a regex, and OWASP says
plainly that regex alone fails on encoded output. Neither is the point. **The log is the
point:** it is the only reason you can discover, after the fact, that a control you were
relying on had been quietly waving an attack through. Whether your company lets a model read
the open web at all, and who owns the threshold once it does, is a decision about appetite
rather than tooling — and somebody above you makes it before you write a line of the scanner.

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
