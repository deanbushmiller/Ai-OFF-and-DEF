# Lab 11 — Defending multimodal input

The third defend lab. It pairs with lab 4, where a pipeline read an instruction out of an
invoice that no person could see, and a classifier was flipped by a change of 7 in 255. This
time you build the controls that stand in front of both: a check on the extracted text, a
comparison between what the machine read and what a person would see, a log of every gap, a
human path for anything flagged, and a threshold you tighten yourself.

**Defends:** lab 4 — multimodal and vision-based exploits
**OWASP:** LLM01:2026 Prompt Injection — risk 4, Scenario 6; preventions 3 and 7 built,
2 and 4 named · LLM02:2026 Sensitive Information Disclosure, risk 4 · LLM06:2026 prevention 7
adjacent
**ATLAS:** defends `AML.T0068` → `AML.T0051.001` and `AML.T0043` → `AML.T0015`, with
`AML.M0020` Generative AI Guardrails, `AML.M0033` Input and Output Validation, `AML.M0024` AI
Telemetry Logging, `AML.M0015` Adversarial Input Detection

No language model runs in this lab. Every result is arithmetic on pixels and text, and it is
the same on every machine, every time.

---

## The architecture

```
   a scanned document from somewhere you do not control
                     |
                     v
        +------------------------------+
        |  ocr.py                      |  lab 4's OCR, unchanged:
        |  (tesseract, adaptive, psm 4)|  adaptive threshold, --psm 4
        +------------------------------+
             |                    |
             v                    v
   +---------------------+  +-----------------------------+
   | inspect.py  PREVENT |  | compare.py         DETECT   |
   | four patterns,      |  | the same OCR on the image   |
   | a length limit,     |  | with every faint mark       |
   | your indicators     |  | erased - what a person sees |
   +---------------------+  | any extra line = MISMATCH   |
             |              +-----------------------------+
             |                    |
             +--------+-----------+
                      v
        +------------------------------+
        |  mismatch-log.jsonl          |  every decision, in order
        +------------------------------+
                      |
                      v
        +------------------------------+
        |  route.py         RECOVER    |  flagged -> review-queue/
        |  tune.py                     |  tighten, add YOUR rule
        +------------------------------+

   and, beside it, lab 4's stamp gate with two additions:

        +------------------------------+
        |  gate.py                     |  label + confidence
        |  + random-noise control      |  same change, 30 random ways
        |  + auto-accept threshold     |  below it -> HELD for a person
        +------------------------------+
```

## The vulnerable configuration and the defended one

| | Vulnerable (lab 4) | Defended (this lab) |
|---|---|---|
| After the OCR | text pasted straight into the prompt | **checked** for instruction-like content before anything acts on it |
| What a person would see | never computed | **computed and compared** against what the model reads; every gap logged |
| The stamp classifier | its label is the decision | its label **plus a confidence threshold**; below it, a person decides |
| "Is this an attack or a fragile model?" | not asked | the **random-noise control** answers it every time: 0 of 30 |
| A flagged document | keeps flowing | **moved out of the inbox** into `review-queue/` with the evidence and a hash |
| The policy | constants in code | `rules.json`, which you edit |
| The spend limit in code (lab 4's `--strict`) | already taught | not repeated — that beat is done |

---

## The steps

The wording below is what the runner prints, word for word.

**1 — OCR the clean invoice.** Start where lab 4's pipeline starts: the picture becomes text.
This is the honest invoice, through the pipeline's own OCR. Count the lines. You will need the
number in a moment.

**2 — check the clean text.** PREVENT. The content check: after the OCR, before anything acts
on the text. Four patterns and a length limit, all in `rules.json`. Expect: pass. A control
with no clean baseline is a guess.

**3 — OCR the doctored invoice.** Now the doctored invoice — the one lab 4 built. To your eye
it is the same document. Same OCR. Count the lines again.

> ^ Twelve lines. The twelfth is printed at 1.2% contrast — grey 252 on white 255 — and the
> OCR read it as cleanly as the total. Nobody scrolling an invoice queue would ever see it.

**4 — check the doctored text.** The same content check on the doctored text. Read WHICH
rules fire. Every one of them is looking at the words.

> ^ Caught — by rules somebody wrote before this invoice existed. Reword the payload and they
> miss. OWASP says so in the same sentence that recommends them. That is why the next step
> does not read the words at all.

**5 — compare what a person sees with what the model reads.** DETECT. Two renderings of each
image through the SAME OCR: the image as it is, and the image with every mark fainter than 15%
contrast erased — what a person sees. Any line the model reads that a person would not see is
a mismatch, whatever it says.

> ^ Clean: 11 and 11, match. Doctored: 11 and 12, one line the model read that no reviewer
> could have. This check never looked at what the line said. It cannot be rephrased past.

**6 — read the mismatch log.** The mismatch log. Every decision so far, in order, in one
file. This is the question a detector must be able to answer later: WHICH document said that,
and what exactly did it say?

**7 — the stamp gate, with its control.** The other half of lab 4: the DUPLICATE-stamp gate,
and the stamp that was nudged 7/255 to flip it. Two things are new. A random-noise control:
the same size of change, thirty random directions. And an auto-accept confidence threshold,
shipped at 0.50.

> ^ ORIGINAL at about 0.61, and it went to payment. The control is the honest part: thirty
> random changes of the same size flipped the gate 0 times. This is not a fragile model. It is
> a model pushed along its own gradient — and 0.61 is not confidence, it is a coin that landed.
> At 0.50, the gate paid it anyway.

**8 — route to a person.** RECOVER, part one. Nothing flagged should sit in the pipeline's
inbox. Route it to a person, with the evidence and the file hash.

> ^ Out of `invoices/`, into `review-queue/`, with a record naming the hidden line and the
> file's hash. A flagged document does not get a worse score. It gets a person.

**9 — tune.** RECOVER, part two. Tune with what your own log just taught you: raise the
auto-accept threshold, and add the first words of the line your comparison caught to a rule
list that is yours.

> ^ Four patterns, one comparison, and now one rule of your own. The verdict did not change.
> What changed is that one of the reasons for it came from your incident instead of a
> textbook.

**10 — the gate again.** Same stamp, same gate, same score. One number in `rules.json` moved.

> ^ Held. 0.61 did not change; what it is allowed to do did. And the clean duplicate still
> scores 1.000 and is still blocked — the tighter threshold cost nothing on the case that was
> already right. That trade is the one you should be able to explain.

---

## The command list

Expert runs all of it. Beginner mode runs only the lines marked 🅱️.

```
cd /labs/lab11

🅱️ python ocr.py invoices/invoice-clean.png
🅱️ python inspect.py invoices/invoice-clean.png
🅱️ python ocr.py invoices/invoice-attack.png
🅱️ python inspect.py invoices/invoice-attack.png
🅱️ python compare.py invoices/invoice-clean.png invoices/invoice-attack.png
🅱️ python log.py
🅱️ python gate.py invoices/stamp-attack.png
🅱️ python route.py
🅱️ python tune.py
🅱️ python gate.py invoices/stamp-attack.png

   nano rules.json                                  instead of tune.py - see below
   python compare.py invoices/invoice-clean.png     after moving visible_contrast_percent
   python gate.py invoices/stamp.png                the clean duplicate through the tightened gate
   nano payload.txt                                 write your own hidden instruction
   python craft.py                                  render it into invoices/invoice-attack.png
   python inspect.py invoices/invoice-attack.png    does the rule check catch YOUR wording?
   python compare.py invoices/invoice-attack.png    the comparison does, whatever you wrote
   cat mismatch-log.jsonl
   cat review-queue/*.json
   python check.py
```

Expert mode edits `rules.json` by hand with `nano` instead of running `tune.py`: raise
`auto_accept_confidence`, add a phrase to `your_indicators`. Then `python check.py` tells you
whether the defence holds together.

**Two expert experiments worth the time.** First, move `visible_contrast_percent` and re-run
`compare.py` on *both* invoices: below 1.2 the hidden line counts as visible and the mismatch
disappears; past 70 the print itself starts to vanish from the visible view and the *clean*
invoice mismatches. Second, write your own payload with `nano payload.txt` and `python
craft.py`, then reword it until `inspect.py` passes it. `compare.py` will still catch it. That
pair is the whole argument for why detection leads.

---

## Reading the code

Nine files, none of them long. Read them before you trust them.

| File | What it is |
|---|---|
| `ocr.py` | lab 4's OCR call, and nothing else. The thing the controls stand in front of |
| `inspect.py` | the content check: four regular expressions, a length limit, your indicators. PREVENT |
| `compare.py` | two renderings, one OCR, a diff. DETECT — the heart of the lab |
| `lab11lib.py` | `visible_render()` is eleven lines; that is the whole "what a person sees" |
| `gate.py` | lab 4's classifier plus the noise control and the threshold |
| `route.py` | move a flagged file, write a record with its hash |
| `tune.py` | two edits to `rules.json`, before-and-after |
| `rules.json` | your policy. Three numbers and two lists |
| `stamp_gate.py`, `make_invoices.py`, `craft.py`, `payload.txt` | lab 4's, unchanged |

---

## The threshold, and why it is 15%

`compare.py` erases every mark fainter than **15%** of the brightness range before the
visible-view OCR. The number was measured, not chosen:

| contrast threshold | clean invoice | doctored invoice |
|---|---|---|
| 0.5% | match | **match — the hidden line counts as visible. False negative.** |
| 1% | match | OCR noise on a half-erased line |
| **1.2% to 60%** | **match** | **1 hidden line — MISMATCH, identical at every value** |
| 70% | **6 lines differ — the print is being erased. False positive.** | 7 |
| 95% | nothing visible at all | nothing |

The print on this invoice sits at 92% contrast and the hidden line at 1.2%. Between them is a
plateau nearly sixty points wide, and 15% is in the middle of it. That is unusually
comfortable. Real scans are faded, photographed and stamped, and the plateau is narrower —
which is why a production pipeline scores per-field confidence on *your* documents rather than
shipping one number.

## The other threshold, and why it is 0.90

The gate ships with `auto_accept_confidence` at **0.50** — the vulnerable configuration. The
clean stamp scores DUPLICATE at **1.000**; the perturbed stamp scores ORIGINAL at **0.607**.
Anything between 0.61 and 0.99 holds the attack and still blocks the duplicate. 0.90 is in the
middle of that range, and it is the number `tune.py` writes. The random-noise control is
printed every time: the same 7/255 in thirty random directions flips the gate **0 of 30**
times. That is what lets you say "attack" rather than "fragile".

---

## What this lab does not prove

**The OCR was never unsure.** Ask tesseract how confident it was in the hidden line and it
says about 90% — the same as the printed total. A pipeline that holds anything the OCR is
unsure about holds nothing here. There is nothing wrong with the text. The only thing wrong
with it is that a person cannot see it. The comparison is the control on the OCR side; the
confidence threshold belongs on the classifier side, where 0.61 really is a coin landing.

**The comparison ran on the file you were sent.** A real pipeline resizes the image before the
model sees it, and an attacker who knows that can hide text that appears only *after* the
resize (Trail of Bits demonstrated exactly this against production systems in 2025). Compare at
the resolution and preprocessing the model actually sees, not the file you received.

**Four patterns are not a content filter.** They caught this payload. Reword it and they will
not — expert mode lets you prove that in two commands. A production pipeline runs content
inspection on every extracted field — **Azure AI Content Safety** is the named tool — and a
document-intelligence service that scores extraction confidence per field, calibrated on your
own documents. Every one of those costs money, latency, or a dependency off-site. A bought
control is still yours to run, monitor and recover.

**The spend limit in code is not repeated.** Lab 4's `--strict` already showed that a numeric
check in application code holds against every payload tried. That is OWASP LLM01 prevention 4
and it is the strongest control in the pair. This lab is the two in front of it.

---

## Evidence to submit

Paste **two** things into the class chat:

1. the **MISMATCH block** from step 5 — the line the model read that a person would not see
2. the **HELD block** from step 10 — the same 0.607 that was paid at step 7, held at step 10

Your full transcript is saved to `lab11-results.txt`, and the `invoices/` and `review-queue/`
folders are copied out next to it when the lab exits. Open `invoice-clean.png` and
`review-queue/invoice-attack.png` side by side. That is worth two minutes of your own eyes.
