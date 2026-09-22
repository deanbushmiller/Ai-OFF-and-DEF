# Lab 8 — Offensive recap and transition to defense

**Time:** 12–15 minutes · You write no code. **There is no attack in this lab.**

Lines marked 🅱️ are the **core steps**. Beginner mode runs only those.
Expert mode runs the whole list.

---

## The question

You have attacked seven things. **What does that add up to?**

This lab takes the seven attacks you ran yourself and turns them into a defender's map:
an ATLAS coverage picture, the controls MITRE names for them, and an honest account of
where the published guidance runs out.

**This is the first half of a two-part course.** Part 2 is seven defender labs covering the
same ground from the other side. So this lab *names* the controls and stops there. It is an
introduction — and anything more would feel like enough when it is not.

---

## Architecture

No model. No network. No port. Two JSON files and seven scripts.

```
  /opt/lab-assets/atlas/atlas.json     MITRE ATLAS, distilled at build time.
                                       170 techniques, 35 mitigations, 16 tactics.
                                       NOT ours - this is MITRE's data.
        │
        │         course.json          What THIS COURSE taught: the chain each of
        │              │               labs 1-7 used, and the one technique that IS
        │              │               each lab. GENERATED from labs 1-7, not typed.
        ▼              ▼
  ┌─────────────────────────────────────────────────────────┐
  │  recap.py      the seven attacks, one line each          │
  │  mapping.py    you name the core technique for each      │
  │  coverage.py   the matrix, the gaps, the spine           │
  │  defend.py     the controls, and where they run out      │
  │  export.py     an ATLAS Navigator layer file             │
  └─────────────────────────────────────────────────────────┘
        │
        ▼
  atlas-layer.json   ── loads at https://atlas.mitre.org/navigator
```

**`course.json` is generated, not written.** A script reads every student-facing file of
labs 1 to 7 — the runner, `LAB.md`, the README — and refuses to produce an answer key
containing any technique your own labs never showed you. That matters: a recap lab that
marks a correct answer wrong is worse than no recap lab.

---

## The vulnerable configuration

There isn't one. This is the only lab in the course with no adversary in it.

What it does have is the *method*: a coverage map is how a security team decides where it
is exposed and what it can see. You are building one from attacks you personally ran,
which is the only way to build one you actually believe.

---

## Mapping

This lab does not add a mapping. It **is** the mapping.

**ATLAS coverage across labs 1–7:** 20 distinct techniques, **12 of the 16 tactics**.

| covered | not covered |
|---|---|
| Reconnaissance, Resource Development, Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Discovery, Collection, AI Attack Staging, Command and Control, Impact | AI Model Access, Credential Access, Lateral Movement, **Exfiltration** |

**The four empty ones are answers, not omissions** — and Exfiltration is the one to read
twice. An external endpoint was proposed at lab 3, reconsidered at labs 5 and 6, and closed
permanently at lab 7. You are security professionals on work laptops; a machine that runs a
hacking lab and then beacons to an unfamiliar domain is the textbook EDR detection, and
lab 7 would have had you tuning the interval of a real one.

**OWASP 2026 coverage:** 8 of the 10 entries. `LLM01 Prompt Injection` appears in **five of
the seven labs**.

**The spine:** `AML.T0051.001` — LLM Prompt Injection: Indirect — is in **5 of 7 labs**.
Twelve of the twenty techniques appear in exactly one. If you remember one identifier from
this whole course, that is the one.

---

## The steps

🅱️ = core, run by both modes. Unmarked = expert only.

```bash
# --- expert only: get into the lab folder and look at the inputs ---
cd /labs/lab8
cat course.json
python -c "import json;print(json.load(open('/opt/lab-assets/atlas/atlas.json'))['source'])"

# --- the recap ---
🅱️ python recap.py

# --- the mapping ---
🅱️ python mapping.py                        seven questions, checked as you go
   python mapping.py --worksheet             expert: a blank worksheet, no multiple choice
   nano worksheet.txt
   python mapping.py --grade

# --- the coverage picture ---
🅱️ python coverage.py
🅱️ python coverage.py --gaps
🅱️ python coverage.py --spine

# --- the introduction to defense ---
🅱️ python defend.py
🅱️ python defend.py --gaps

# --- the evidence ---
🅱️ python export.py
   python check.py
```

---

## Step 1 · The seven attacks — 🅱️

`python recap.py`

Eight hours of work, on one screen. Read it before you map it — the point of this lab is
seeing seven separate labs as one thing.

> **^** Seven labs, seven ways in, and not one of them was theory. Hold that list in your
> head for the next seven minutes.

## Step 2 · Map them onto ATLAS — 🅱️

`python mapping.py`

The only typing in this lab. For each of the seven, name the **one** ATLAS technique that
*is* that lab — the one that, if you took it away, the attack stops being that attack. The
full chain is shown; pick from it.

> **^** The number you get right matters less than the vocabulary. *"We did a lab about
> MCP"* is a story. **`AML.T0110`, AI Agent Tool Poisoning** is something your detection
> team can actually search for.

Expert mode does this without multiple choice: `python mapping.py --worksheet`, fill it in with
`nano worksheet.txt`, then `python mapping.py --grade`.

## Step 3 · The coverage map — 🅱️

`python coverage.py`

20 techniques, 12 of 16 tactics, laid out in the matrix's own column order.

> **^** That is a coverage map, and you built it from attacks you ran rather than from a
> vendor's slide. 12 of 16 tactics is a lot of ground for eight hours.

## Step 4 · The four tactics you never touched — 🅱️

`python coverage.py --gaps`

An empty column on a coverage map is a question, not a verdict. Here are the answers.

> **^** Read the Exfiltration one again. Nothing in this course ever sent data to an
> external endpoint, and that was decided four separate times, on purpose. **Designing a
> safe lab means choosing what you will NOT demonstrate — and saying why.**

## Step 5 · The spine — 🅱️

`python coverage.py --spine`

Seven labs that felt completely different. Here is how much they actually had in common.

> **^** Five of seven. Indirect prompt injection is not one attack among many; it is how
> most of the others were *delivered*. The payload changed every time. The way it arrived
> did not.

## Step 6 · The controls MITRE names — 🅱️

`python defend.py`

Switch sides. These are real ATLAS mitigation IDs read out of MITRE's own data — not our
advice.

> **^** Two controls cover five of your seven labs, and notice how unglamorous they are:
> **log what the model and its tools did**, and **validate what crosses every boundary**.
> Not a product. Not a filter. The two things that have defended every other kind of system
> for thirty years.

Each lab also shows which part-2 lab teaches its control properly. One line each, on
purpose.

## Step 7 · Where the guidance runs out — 🅱️

`python defend.py --gaps`

And the honest part.

> **^** Nine of your twenty techniques have **no published mitigation at all**, and the
> date column shows why: every one of them was added to ATLAS between March 2025 and March
> 2026. The ones that *do* have controls are the older, classical machine-learning attacks.
>
> **^** The defensive literature is roughly a year behind the offensive literature, and you
> can see the gap by reading the dates. That is not a criticism of MITRE — it is what the
> field looks like right now, and it is why part 2 exists.

## Step 8 · Your evidence — 🅱️

`python export.py`

Writes `atlas-layer.json`, an **ATLAS Navigator layer file**.

> **^** That file loads into the real ATLAS Navigator at
> <https://atlas.mitre.org/navigator>. It is a professional artifact, it is yours, and it
> took eight hours of attacking to earn it.

---

## How this differs from real practice

| This lab | A real coverage map |
|---|---|
| seven lab exercises | your estate's actual systems |
| techniques you were taught | techniques found by threat intel |
| MITRE's published controls | the controls *you* have deployed |
| scored by lab count | scored by detection confidence |

The method is the same and it is the part worth keeping. The inputs are the part you go and
get on Monday.

---

## What part 1 adds up to

1. **The model believes what it reads.** Labs 2, 3 and 4 were three different delivery
   routes for one idea.
2. **The model does what it is *permitted* to do, not what you intended.** Labs 5 and 6.
3. **Nothing on the wire between a model and its tools is authenticated** unless you
   authenticate it. Lab 6.
4. **An attacker with an LLM is good at exactly the part defenders stopped keying on years
   ago.** Lab 7.
5. **And the supply chain was already a solved problem that nobody solved.** Lab 1.

The defensive answer to most of that, today, is: *log what happened, and validate what
crosses a boundary.* Part 2 is where you build it.

---

## Part 2 — seven defender labs

**In the order part 2 is taught:**

| | part 2 | closest to |
|---|---|---|
| 1 | Semantic firewalls and RAG validation | your lab 2 |
| 2 | Implementing guardrail frameworks — part 1 | your lab 3 |
| 3 | Implementing guardrail frameworks — part 2 | your lab 4 |
| 4 | Architectural hardening and data segregation | your lab 1 |
| 5 | Securing AI agents | your lab 5 |
| 6 | AI-native incident response and monitoring | your lab 6 |
| 7 | Automated red teaming | your lab 7 |

**The right-hand column is the nearest counterpart, not a day-for-day pairing.** Part 2 is
taught in its own order and some of it draws on more than one of the attacks you ran — your
lab 2 is where it starts, and your lab 1 is not picked up until its fourth day.

Where MITRE has a control, those labs build it. Where MITRE has nothing yet, they build
something anyway and say honestly that it is ahead of the standard.

---

## Submit

Nothing - You have the atlas-layer.json. Review it and prepare to ask questions. The full
transcript is in `lab8-results.txt`.

**And check you have submitted evidence for labs 1–7** — the setup script lists them when
the lab exits.
