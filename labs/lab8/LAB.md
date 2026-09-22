# Lab 8 — Offensive recap and transition to defense

**Time:** 12–15 minutes · You write no code. **There is no attack in this lab.**

Lines marked 🅱️ are the **core steps**. Beginner mode runs only those.
Expert mode runs the whole list.

---

## The question

You have attacked seven things. **What does that add up to?**

This lab takes the seven attacks you ran yourself and turns them into a defender's map:
an ATLAS coverage picture, the controls MITRE names for them, and an honest account of
where the published guidance still runs out.

**This is the first half of a two-part course.** Part 2 is seven defender labs covering the
same ground from the other side. So this lab *names* the controls and stops there. It is an
introduction — and anything more would feel like enough when it is not.

---

## Architecture

No model. No network. No port. Two JSON files and seven scripts.

```
  /opt/lab-assets/atlas/atlas.json     MITRE ATLAS v2026.08, distilled at build
                                       time and checked by sha256. 197 techniques,
                                       39 mitigations, 16 tactics.
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

**ATLAS coverage across labs 1–7** (ATLAS v2026.08): 20 distinct techniques, **13 of the
16 tactics**.

| covered | not covered |
|---|---|
| Reconnaissance, Resource Development, AI Attack Adaptation, Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Discovery, Lateral Movement, Collection, Command and Control, Impact | AI Model Access, Credential Access, **Exfiltration** |

Lateral Movement is lit only because v2026.08 also files `AML.T0053` AI Agent Tool
Invocation (labs 5 and 6) under it. Every lab was still one container on your machine.

**The three empty ones are answers, not omissions** — and Exfiltration is the one to read
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

20 techniques, 13 of 16 tactics, laid out in the matrix's own column order.

> **^** That is a coverage map, and you built it from attacks you ran rather than from a
> vendor's slide. 13 of 16 tactics is a lot of ground for eight hours.

## Step 4 · The three tactics you never touched — 🅱️

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

> **^** The controls that cover the most labs are the broadest ones. `AML.M0035` **AI Red
> Team** touches all seven — it is what you just spent eight hours doing. `AML.M0020`
> Generative AI Guardrails touches six. Then the unglamorous pair, five each: **log what the
> model and its tools did** (`AML.M0024`), and **validate what crosses every boundary**
> (`AML.M0033`). Not a product. The two things that have defended every other kind of
> system for thirty years.

Each lab also shows which part-2 lab teaches its control properly. One line each, on
purpose.

## Step 7 · Where the guidance runs out — 🅱️

`python defend.py --gaps`

And the honest part.

> **^** Two of your twenty techniques have **no published mitigation at all**. When this
> lab was first built, on ATLAS 5.6.0, it was nine — and in v2026.08 seven of those nine
> gained one. ATLAS is a living standard, and a coverage map is a snapshot with a release
> number on it.
>
> **^** But look at *what* closed those gaps: mostly broad controls — Generative AI
> Guardrails, Limit Public Release of Information, and the new AI Red Team. A broad
> mitigation mapped to a technique tells you where to start, not what specifically stops
> the attack.
>
> **^** And look at which gap is left. `AML.T0110` **AI Agent Tool Poisoning** — lab 6's
> core, the agent's tool layer — has no published control at all, not even a broad one. (The
> other, `AML.T0065` LLM Prompt Crafting, is a supporting step in labs 4 and 5.) That is the
> edge of the field right now, and it is why part 2 exists.

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

MITRE now names a control for 18 of your 20 techniques — mostly broad ones. The specific
answer to most of it is still: *log what happened, and validate what crosses a boundary.*
Part 2 is where you build it.

---

## Part 2 — seven defender labs

**Labs 9 to 15, in the order part 2 is taught.** Each one pairs with one attack you ran:

| | part 2 | pairs with |
|---|---|---|
| lab 9 | Defending the model supply chain | your lab 1 |
| lab 10 | Defending RAG ingestion | your lab 2 |
| lab 11 | Defending multimodal input | your lab 4 |
| lab 12 | Defending against prompt injection | your lab 3 |
| lab 13 | Defending AI agents | your lab 5 |
| lab 14 | Defending MCP tool calls | your lab 6 |
| lab 15 | Defending against AI-scaled attacks | your lab 7 |

The order follows yours except in one place: multimodal input (your lab 4) is taught before
prompt injection (your lab 3).

Where MITRE has a control, those labs build it. Where MITRE has nothing yet — lab 14,
against the tool poisoning you did in lab 6 — they build something anyway and say honestly
that it is ahead of the standard.

---

## Submit

Nothing - You have the atlas-layer.json. Review it and prepare to ask questions. The full
transcript is in `lab8-results.txt`.

**And check you have submitted evidence for labs 1–7** — the setup script lists them when
the lab exits.
