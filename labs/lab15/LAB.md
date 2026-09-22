# Lab 15 — Defending against AI-scaled attacks

**Time:** 12–15 minutes · You write no code.

Lines marked 🅱️ are the **core commands**. Beginner mode runs only those.
Expert mode runs the whole list.

---

## The question

In lab 7 you were the attacker. You asked a model for five renderings of one record,
watched a signature rule catch all five, and got past it with two lines of Python that
needed no AI at all. Then a behavioural detector caught you anyway and you paid 80× in
throughput to go clean.

That detector had **one channel** to look at and already knew it was malicious.

**How many colleagues do you wake up to catch one beacon?**

---

## Architecture

```
  estate.py --build              24 workstations, 193 host->destination channels,
      |                          one day of check-ins. A FLOW LOG: who talked to
      |                          whom and how often. No payloads.
      v
  estate.json  <----------------+ the cadence limbs read this
                                |
  variants.json                 |   lab 7's TEN measured renderings of one record,
      |                         |   shipped as evidence. You do not regenerate them.
      |   inbox.py              |
      v                         |
  collector.py  127.0.0.1:8015  |   the mock endpoint. Appends to collector.log.
      |                         |   Not published. The container has no network.
      v                         |
  collector.log  <--------------+ the content limb reads this
      |
      +--> detect.py --baseline   the signature rule, and lab 7's detector
      +--> detect.py --score      four orthogonal limbs, one score
      +--> detect.py --sweep      where do you put the line, and what does it cost
      +--> detect.py --window     the recovery move
      |
  limit.py --cap N                the prevent stub, in the real request path
  evade.py                        the operator's next day
  evidence.py                     both bills
```

**Two files on purpose.** A SOC does not replay a day of packets — it reads flow records
and whatever payload inspection it has, separately. The cadence limbs read `estate.json`
and the content limb reads `collector.log`, and that split is the realistic asymmetry: a
defender never gets the attacker's working files, only what arrived.

Nothing executes. Nothing persists. Nothing connects out. The container is run with
`--network none` and the collector binds loopback only.

---

## The estate is synthetic, and that matters

The lab generates the estate from fixed seeds. Read this before you quote any number from
it:

- **The shape is real.** A monitoring agent's heartbeat genuinely is indistinguishable
  from a beacon on cadence alone. User browsing genuinely does produce a long tail of
  destinations only one host ever contacts. The intervals are real agent defaults — EDR
  telemetry at 300 s, monitoring at 60 s, backup at an hour.
- **The exact numbers are this generator's.** "144 false positives" is a property of
  `estate.py`, not a measurement of anybody's network. Your estate will be different.
- **The method transfers. The constants do not.** Take away how you priced a threshold,
  not the threshold.

---

## The vulnerable configuration

The vulnerability here is not in a model or in an application. It is in a **detection
strategy**, and there are two of them, both common:

```python
# Strategy 1: match the wording.
if "LAB-BEACON-7742".lower() in body.lower():
    alert()

# Strategy 2: match the behaviour, on one dimension.
if events_per_day > 24 or cv_of_gaps < 0.35:
    alert()
```

Strategy 1 loses to a format converter. **Strategy 2 is lab 7's detector, and on a real
estate it produces 144 false alarms a day to find one beacon.** Both are 100 % recall.
Neither is a control.

---

## Mapping

**OWASP GenAI LLM Top 10 (2026)**

| | |
|---|---|
| **`LLM10:2026` Improper Output Handling**, scenario #2 | *"the LLM can **encode** the sensitive data and send it, without any output validation or filtering, to an attacker-controlled server."* Prevention 7 asks for detection of *unusual patterns* — patterns, not strings. |
| **`LLM02:2026` Sensitive Information Disclosure** | via OWASP's own ATLAS cross-map: *"Cross-lingual, **Base64, and hex encodings defeat regex and blocklist data-loss filters**."* Step 3 measures it: 8 of 10. |
| **`LLM06:2026` Unbounded Consumption** | **cited for its CONTROLS, not for its risk.** Prevention 1 is the rate limit; prevention 8 is *"establish baselines of normal tool behavior in order to detect if a particular tool is deviating"*, which is the estate model. Its **risk** points the other way — cost asymmetry against your own inference bill — and this lab is about traffic leaving. The mismatch is stated rather than fudged. |

**MITRE ATLAS (v2026.08, the course baseline, plus one v2026.09 addition: `AML.M0039`)** — this
lab is a *counter* to:

| Stage | Tactic | Technique |
|---|---|---|
| 1 | `AML.TA0003` Resource Development | `AML.T0016.002` Obtain Capabilities: Generative AI |
| 2 | `AML.TA0001` AI Attack Adaptation | `AML.T0043.003` Craft Adversarial Data: Manual Modification |
| 3 | `AML.TA0007` Defense Evasion | **`AML.T0015` Evade AI Model** ← the one you are countering |

**Controls, and one of them warns you about itself:**

| | |
|---|---|
| **`AML.M0004`** Limit AI Service Query Volume and Rate | the prevent stub — and ATLAS's own text says *"Query limits may not protect against attacks that require few requests."* Step 7 measures exactly that. |
| **`AML.M0024`** AI Telemetry Logging | `detect-log.jsonl` |
| **`AML.M0006`** Predictive AI Ensembles | orthogonality in ATLAS's voice: *"prevent an adversarial example that evades one model from controlling the system's predictions"* |
| **`AML.M0039`** AI Honeypots *(added in v2026.09, after the course's v2026.08 baseline)* | named, not built. *"any interaction with them is a high-confidence indicator of unauthorized activity"* — the one signal no amount of variation can touch |
| **`AML.M0035`** AI Red Team | step 6, and all of lab 16 |

### The framework gap — say it out loud

**Five of the seven mitigations ATLAS maps to `AML.T0015` begin with the word
"Predictive":** Predictive AI Model Hardening, Predictive AI Ensembles, Predictive AI
Multi-Sensor Fusion, Predictive AI Input Restoration, Predictive AI Adversarial Input
Detection. The other two are Deepfake Detection and AI Red Team.

Every one of the five assumes **you own the model being evaded** and tells you to harden it.
Not one of them is *"detect on a behavioural invariant outside the model."* If the thing
being evaded is your **signature set** rather than your classifier, the framework has no
entry for you. That is what this lab fills, and it is worth knowing that the gap is real
rather than assuming you missed the right control.

**Two case studies, both real:**

- **`AML.CS0000`** — Palo Alto Networks' ML detector for malware C2 traffic, evaded by
  *removing header fields not used for C2*. **The crafted packets were identified as benign
  with over 80 % confidence.** Note what was evaded: a model that read **content**.
- **`AML.CS0032`** — attackers modified brand logos, evaded the visual-similarity model,
  and **the other components of the ensemble caught the phishing sites anyway.** That is
  step 5 in one sentence, from the field.

---

## The commands

🅱️ = core, run by both modes. Unmarked = expert only.

```bash
# --- expert only: get into the lab folder ---
cd /labs/lab15
cat record.txt
cat detector.json
sed -n '/^def limbs/,/^def score/p' lab15lib.py     # the four limbs, 20 lines

# --- the estate and the evidence ---
🅱️ python estate.py --build
🅱️ python inbox.py
   python inbox.py --show
   python estate.py --show

# --- what you have today ---
🅱️ python detect.py --baseline

# --- the detector you are building ---
🅱️ python detect.py --score
🅱️ python detect.py --sweep --set 4
   python detect.py --rarity-only          # the trap. Four booleans, none of them work

# --- red-team your own control ---
🅱️ python variants.py --live json
   python variants.py --live yaml
   python variants.py --formats

# --- the prevent stub ---
🅱️ python limit.py --cap 6
   python limit.py --cap 1

# --- the miss, and the recovery ---
🅱️ python evade.py
   python evade.py --split 1
🅱️ python detect.py --window channel

# --- expert only: tune the WEIGHTS, not just the threshold ---
   nano detector.json
   python detect.py --score

# --- the evidence ---
🅱️ python check.py && python evidence.py
```

---

## The steps

### 1 · Build the estate — 🅱️

`python estate.py --build`

Twenty-four workstations, one day, 193 host→destination channels. Read the table.

> **^** The **monitoring agent** checks in **1441** times a day at **cv 0.011**. The
> **beacon** checks in **1440** times at **cv 0.000**. On cadence they are the same
> traffic.
>
> **^** One of them is your fleet. The only column that separates them is the one lab 7
> never had, because lab 7 had one host and nothing to compare it to.

### 2 · Read the collector's inbox — 🅱️

`python inbox.py`

The ten renderings lab 7 measured, replayed into the collector so the detector has a log
to read. **You are not generating these.** You are receiving them.

> **^** The detector reads `collector.log` and `estate.json`. It never sees
> `variants.json`. That asymmetry is real: a defender does not get the attacker's working
> files, only what arrived.

### 3 · What you have today — 🅱️

`python detect.py --baseline`

The signature rule first, then lab 7's behavioural detector pointed at the estate.

> **^** The signature rule caught **8 of 10**. The two it missed were `base64` and `hex` —
> the two the model **could not write**. The evasion that worked was free and needed no AI.
>
> **^** Lab 7's detector: **1 true positive, 144 false positives, precision 0.0069.** It
> found the beacon. It also found every EDR agent, every monitoring agent, every backup
> client and everyone's browser.
>
> **^** It is not broken. It is **100 % recall**, and on an estate that is the same thing
> as useless: nobody reads 144 alerts a day twice. That is not a tuning problem, it is a
> design problem.

### 4 · Four limbs instead of two — 🅱️

`python detect.py --score`

Rarity, cadence, volume, and whether the record's values survive the rendering. Weighted,
summed, thresholded.

> **^** The beacon is the only channel that trips all four. It trips the content limb
> because **the record is the thing it needed to send** — it cannot drop that and still be
> doing its job.
>
> **^** Now read `user-browsing`: rare, high-volume, and completely innocent. That row is
> why *"just alert on rare destinations"* is not the answer.
>
> **^** One limb changed from lab 7 and it is load-bearing. Lab 7 asked `cv < 0.35` — *is
> this a timer* — which 95 % jitter beats **for free**. This asks `cv < 1.0` — *is this not
> a person* — and it holds, because bounded jitter is still bounded: a beacon at 95 %
> jitter is **0.543**, human browsing is **4.482**.

### 5 · Where do you put the line — 🅱️

`python detect.py --sweep --set 4`

Every threshold, priced against the whole estate. Then set it.

> **^** **0 false positives at threshold 4**, down from 144. You did not turn anything up.
> You asked four independent questions and required more than one answer.
>
> **^** Read the second table. Lab 7's dial, swept down to catch a slow channel, **peaks at
> 0.0127 and then gets worse**. A threshold on one dimension cannot buy precision at any
> setting.
>
> **^** That is the difference between tuning and design, and it is the thing to remember
> the next time somebody says "just turn the detector up".

### 6 · Red-team your own control — 🅱️

`python variants.py --live json`

Generate a variant that did not exist when your detector was written, in wording nobody
predicted, and see whether a limb nobody updated still catches it. **This is the only model
call in the lab.**

> **^** Caught. The limb was not updated. The record is what the attacker **needed** to
> send, so the record is what survives every rendering — including ones nobody has thought
> of yet.
>
> **^** Read the prompt that was sent. It is a format converter. No jailbreak, no roleplay,
> nothing a safety filter would refuse and nothing a prompt scanner would flag. **A
> detector keyed on wording loses to this. Yours is not.**
>
> **^** Note what the lab just checked: the **field count** and the verdict, never the
> model's sentence. Lab 13 measured this model confidently stating it had verified
> something it never did. Assert on structure.
>
> **^** And note what this command *is*: attacking your own control with an input it has
> never seen. ATLAS calls that `AML.M0035`, AI Red Team. It is lab 16 in one command.

### 7 · The prevent stub, and its bill — 🅱️

`python limit.py --cap 6`

A real rate limiter in a real request path. Watch all three numbers, then watch the last
one.

> **^** The cap stopped **1296 of 1440** check-ins. It stopped **none** of the slow
> version. And it cost **120 legitimate channels** their traffic to do it.
>
> **^** **All 6 of the record's values reached the collector anyway.** A control that
> throttles 90 % of the traffic looks like it is working, and the thing it exists to
> protect left the building.
>
> **^** That is why prevention is the stub and detection leads. Not an opinion: ATLAS
> `AML.M0004` says *"query limits may not protect against attacks that require few
> requests"* and OWASP LLM06 says *"traditional request-rate limiting alone is no longer
> sufficient."* You just measured both.

### 8 · The operator's next day — 🅱️

`python evade.py`

Same host, same record. Three changes: slower, jittered, split across check-ins.
**This one is supposed to get past you.**

> **^** Score **2**, threshold **4**, missed. Three limbs went dark and the fourth is not
> worth 4 on its own — deliberately, because 72 innocent browsing channels are also rare.
>
> **^** **Do not reach for the threshold.** You measured that already in step 5: threshold
> 3 is 72 false positives. Knowing that *before* you touch the dial is what step 5 was for.
>
> **^** Look at the five messages instead. Every value of the record is in there. Not in
> any **one** of them — **across** them.

### 9 · Recovery — 🅱️

`python detect.py --window channel`

Reassemble everything the channel sent in the day, then match.

> **^** Caught, and still **0 false positives**. The wider window cost nothing, because no
> legitimate channel carries the record's values at all. The window was never what made the
> detector noisy — the missing limbs were.
>
> **^** The tune was **not a number**. It was where you looked. Lab 7 told you to
> *normalise before you match* — decode, unescape, flatten. This is that advice extended
> from **format** to **time**.

### 10 · Both bills — 🅱️

`python check.py && python evidence.py`

What the control saw, what it cost you, and what evasion cost them.

> **^** **864× slower.** Moving 500 records went from 0.35 days to 300 days.
>
> **^** And they bought nothing with it, because the window tune catches the slow version
> too. The bill was paid for a miss that lasted as long as it took you to read the log.

---

## How this differs from a real defence

| This lab | Production |
|---|---|
| 193 channels, one synthetic day, fixed seed | millions of flows, continuously, over months of baseline |
| the estate is generated by the lab | the estate is the estate, and nobody labelled it |
| one channel is malicious **and you were told** | nothing is labelled; precision is estimated from triage |
| four limbs, hand-weighted | RITA-class scoring plus EDR plus DNS plus identity |
| the tune is one edit | a change ticket, an owner, a target time to close |
| 0 false positives | there is no such thing. There is a **budget**, and somebody owns it |

**There is no detector-search loop in this lab, and there never will be.** A program that
scores configurations against a channel it knows is malicious until one passes is a
model-evasion tool wearing a defender's badge — and it also teaches the wrong habit,
because you do not get labels in production. You read a table and pick a number.

### Why there is no remote endpoint

A real endpoint on a domain the instructor controls was proposed and reconsidered four
times across labs 3 to 7, and closed permanently. Lab 7 is the case that closed it: a
security professional's work laptop running a "hacking lab" that then makes periodic timed
check-ins to an unfamiliar external domain is the textbook EDR detection. It would file
incident tickets at students' employers by design — in the lab about detecting exactly
that. So step 2 prints what a real operator's endpoint *would* have received and stops
there.

---

## The defence

1. **Recall without precision is not a control.** 144 alerts a day to find one beacon is a
   detector that gets switched off by March, and then you have neither.
2. **Key on what the attacker cannot drop.** Wording is free to vary. The record is the
   thing they needed to send. That is why a limb written before a variant existed still
   catches it.
3. **Orthogonal beats tight.** One dimension turned up never got past 0.0127 precision.
   Four independent questions got to 1.0000.
4. **Ask the right question of each dimension.** *"Is this a timer"* loses to free jitter.
   *"Is this not a person"* does not.
5. **When you miss something, change the control, not the dial.** The dial was already
   measured and it costs 72 colleagues.
6. **Price your detector in both currencies** — what it costs them (864×) and what it costs
   you (how many alerts). A defender who can only quote the first one loses the budget
   meeting.

---

## The good news, and it is measured

Unit 42, *The State of AI-Enabled Malware*, **August 2026**: FunkSec ransomware shipped
**seven distinct variants in six days**, a pace their analysts attribute to LLM-assisted
development. Every one was caught.

> *"Existing behavioral detection, cloud-based sandboxing and endpoint analytics catch
> these threats using the same mechanisms that stop conventional malware. **The AI
> component does not evade detection.**"*

Cheap variation is real — Recorded Future's H1 2026 data has AsyncRAT at 59,507 hashes
across **43,549 unique C2 configurations**, 73 % diversity, and none of that needed AI
either. And it loses to defenders who key on behaviour. You just built the small version
of why.

---

## Notes on the toolchain, for the curious

- **The professional version of your detector** is [RITA](https://github.com/activecm/rita)
  (ActiveCM, GPL), which scores beaconing on interval consistency, data-size uniformity and
  dispersion over real PCAP. ActiveCM's free
  [beacon threat-hunting lab](https://activecm.github.io/threat-hunting-labs/beacons/) is
  this exercise done properly. Recommended follow-up.
- **Our marker is an EICAR.** NVIDIA's [garak](https://github.com/NVIDIA/garak) has an
  `av_spam_scanning` probe that checks whether a model will emit EICAR, GTUBE and GTPHISH —
  the industry-standard *harmless* test signatures that exist so a detector can be proven to
  fire without anyone handling real malware. `LAB-BEACON-7742` is the same idea.
- **Formats measured to FAIL on this model**, so you do not waste time: `ini` returns bare
  `[section]` headers and drops every value (0/6, identically on three runs); `syslog` keeps
  the fields but produces no syslog framing; `base64` and `hex` do not work at all — the
  model loops for 49 seconds and returns `SGVsbG8gd29ybGQ=`, which is base64 for *"Hello
  world"*, a memorised string rather than the input. A model is a **paraphraser, not a
  computer**.

---

## Submit

Paste the three numbers from `evidence.py` into the class chat: lab 7's detector on a real
estate, yours after tuning, and what evasion cost the attacker.

The full transcript is saved to `lab15-results.txt`.
