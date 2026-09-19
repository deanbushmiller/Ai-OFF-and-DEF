# Lab 10 — Defending RAG ingestion

The second defend lab. It pairs with lab 2, where one document changed what the assistant
believed about who invented the telephone. This time you stand up the control that refuses it,
watch something get through anyway, and tune what you have.

**Defends:** lab 2 — RAG and semantic ingestion attacks
**OWASP:** LLM09:2026 Vector and Embedding Weaknesses (risk 3; preventions 2, 4, 5, 6) ·
LLM07:2026 Misinformation
**ATLAS:** defends `AML.T0066` → `AML.T0068` → `AML.T0070`, with `AML.M0020` Generative AI
Guardrails, `AML.M0024` AI Telemetry Logging, `AML.M0033` Input and Output Validation

---

## The architecture

```
   a document from somewhere you do not control
                     |
                     v
        +------------------------------+
        |  validate.py     PREVENT     |  rule 1  invisible text
        |                              |  rule 2  provenance tag
        |                              |  rule 3  topic claim count
        +------------------------------+
             |                    |
         passes                refused
             |
             v
        +------------------------------+
        |  rag.py build / ingest       |  every chunk carries its
        |                              |  provenance tag
        +------------------------------+
             |
             v
        +------------------------------+
        |  canary.py       DETECT      |  one known question,
        |  retrieval-log.jsonl         |  one known answer,
        |                              |  asked after every ingest
        +------------------------------+
             |                    |
         holds               CHANGED
                                  |
                                  v
        +------------------------------+
        |  purge.py        RECOVER     |  delete by provenance tag
        |  tune.py                     |  verify, then add a rule
        +------------------------------+
                                  |
                                  +---> the validator now catches it at the door
```

## The vulnerable configuration and the defended one

| | Vulnerable (lab 2) | Defended (this lab) |
|---|---|---|
| Ingest | any document, no review | three rules before anything is embedded |
| Chunks | filename only | filename **plus a provenance tag** |
| After an ingest | nothing is checked | the canary is asked, and logged |
| Retrieval | nothing recorded | every chunk, tag and score written down |
| A poisoned document | stays in the index | purged by tag, verified, and the indicator added to your rules |
| The prompt | retrieved text pasted in unlabelled | **unchanged — still unlabelled.** That is lab 12 |

---

## The steps

The wording below is what the runner prints, word for word.

**1 — validate the clean corpus.** PREVENT. The validator is what stands between a document
and your index. Three rules: refuse ink a human cannot read, refuse a document with no
recorded origin, refuse one that claims to answer too many different questions. Start with the
15 documents you already trust. Expect: all pass.

> ^ Fifteen documents, fifteen passes, and every one of them covers exactly one topic. That is
> your baseline, and it is the half of the evidence people forget to collect.

**2 — build the poisoned document.** Build the poisoned document from lab 2. Same script, same
payload. A human opening it sees an IT onboarding checklist.

**3 — validate the poisoned document.** Now run the same validator against it. Read WHICH
rules fire, and read what rule 1 says it found — that is the text a reviewer opening this file
cannot see.

> ^ Three rules fired. Rule 1 is the one that matters most: the payload is drawn in white on a
> white page at 6pt, so a human reviewer approves a clean-looking checklist while the extractor
> reads every word. Review is not a control against invisible text.

**4 — index the clean corpus.** Index the 15 documents you trust. Each chunk carries the
provenance tag of the document it came from.

**5 — ask the canary.** DETECT. The canary: one question whose correct answer you already
know, asked after every ingest. Ask it now, on the clean index, so you know what right looks
like.

> ^ Alexander Graham Bell, from `bell.txt`, score 0.723. Written to `canary-log.jsonl`.
> Nothing clever happened here and nothing was supposed to.

**6 — ingest the poison, over your own refusal.** Now poison the index — and note what you
have to do to manage it. Your own validator already refused this document, so the pipeline will
not take it without `--force`. Type the `--force`. It is the most honest line in the lab.

> ^ Eleven chunks went in, all UNTAGGED, over a refusal you overrode yourself. Somebody does
> this in every organisation, usually to unblock a demo, usually on a Friday.

**7 — ask the canary again.** Ask the canary again. Same question, same pipeline, same model.
One document entered the index.

> ^ The answer changed and nothing broke. No error, no exception, no alert anywhere else in
> the system — it retrieved a document and answered from it, exactly as designed. Without the
> canary you would find out when a user did.

**8 — read the retrieval log.** The retrieval log. This is the question a detector has to be
able to answer: WHICH document drove that answer?

> ^ 0.772 against `bell.txt`'s 0.723. The poisoned chunk did not break the ranking — it won
> it, by 0.049. Note the tag beside it: UNTAGGED. You are about to spend that.

**9 — purge by tag.** RECOVER. You do not need to know which document was poisoned. You need
to know which documents you can account for. Purge everything with no provenance tag.

> ^ Eleven chunks gone, by tag, without anyone identifying the attack. That option only exists
> because rule 2 wrote a tag on the way in. Without it the only safe recovery is rebuilding the
> whole index — instant here, days on a real corpus.

**10 — verify the recovery.** Re-ask the canary and confirm the answer is restored. A purge
you have not verified is a hope, not a recovery.

> ^ Bell is back, from `bell.txt`, at exactly the score it had before. Detected, contained,
> verified — and you can prove all three from the logs rather than from memory.

**11 — tune.** TUNE. The index is clean, and exactly as easy to poison as it was ten minutes
ago. This step re-issues the same payload under a name nobody would question, then adds YOUR
indicator to `rules.json`.

> ^ Rules 1–3 were somebody else's judgement, written before your incident. The canary caught
> it only after it was already answering your users. Your rule catches it at the door, and it
> exists because your own detector produced it.

---

## The command list

Expert runs all of it. Beginner mode runs only the lines marked 🅱️.

```
cd /labs/lab10

🅱️ python validate.py corpus/
🅱️ python make_poison.py
🅱️ python validate.py poisoned_handbook.pdf
🅱️ python rag.py build
🅱️ python canary.py ask
🅱️ python rag.py ingest poisoned_handbook.pdf --force
🅱️ python canary.py ask
🅱️ python rag.py log
🅱️ python purge.py --untagged
🅱️ python canary.py check
🅱️ python tune.py --add invisible-text

   python rag.py ingest poisoned_handbook.pdf        (no --force: watch it refuse)
   python canary.py second                          BEFORE the purge, then AFTER
   python purge.py --source poisoned_handbook.pdf
   cat canary-log.jsonl
   cat retrieval-log.jsonl
   cat purge-log.json
   nano rules.json
   python check.py
```

Expert mode edits `rules.json` by hand with `nano` instead of running `tune.py`. Add
`"invisible-text"` to `blocked_indicators`, and look hard at `canary_similarity` while you are
in there. Then `python check.py` tells you whether the defence holds together.

**Run `python canary.py second` twice — once before the purge and once after.** It asks a
question from the same corpus, poisoned by the same document, that your canary was never
configured to watch. Before the purge: both are wrong, one alert. After: both are correct,
because you purged the *document* by tag rather than correcting an *answer*. That pair is the
strongest argument in the lab for provenance over monitoring, and it is the one beginner mode
only gets told about.

---

## Reading the code

Five files, none of them long. Read them before you trust them.

| File | What it is |
|---|---|
| `validate.py` | the three rules. Rule 1 walks the PDF content stream; that is the interesting one |
| `canary.py` | one question, one known answer, and a log |
| `purge.py` | delete by provenance tag, and write down what went |
| `rag.py` | lab 2's pipeline, plus tags, a retrieval log, and validated ingest |
| `rules.json` | your policy. Four settings matter and you edit one of them |

---

## The threshold, and why it is 0.60

Rule 3 refuses a document that answers **2 or more** canary questions above a similarity of
**0.60**. Those numbers were measured, not chosen:

| similarity threshold | widest clean document | the poisoned PDF |
|---|---|---|
| 0.50 | **2** topics | 5 topics |
| 0.55 | 1 topic | 5 topics |
| **0.60** | **1 topic** | **5 topics** |
| 0.65 | 1 topic | 5 topics |

0.55, 0.60 and 0.65 all behave identically, so 0.60 is the middle of a plateau rather than an
edge. At 0.50 a legitimate document reaches 2 and would be refused — a false positive you can
reproduce in expert mode by editing `canary_similarity` and re-running the validator over
`corpus/`.

**Counted per chunk instead of per document, this rule does not work at all.** Every poisoned
chunk scores above threshold for exactly one question — and so does every relevant clean
document. Each poisoned sentence imitates one reference document, because that is what it is
pretending to be. The tell is not any single chunk. It is one document pretending to be five.

---

## What this lab does not prove

**A canary only ever proves the questions you thought of.** Yours covered the telephone. The
same document also claimed the light bulb, the Mona Lisa, penicillin and the World Wide Web.
Had your one canary been about any other subject in that corpus, it would have held —
correctly — while four other answers were wrong. Expert mode lets you see this rather than
take it on trust: `python canary.py second`, before the purge and after.

**A content filter tuned for malicious instructions would not have seen this document at all.**
The payload contains no commands. It simply states things that are false, and the pipeline
treats whatever it retrieves as true. That is why detection leads here and why the canary is
the core of the lab rather than the validator.

**The prompt boundary is untouched.** Look at `build_prompt()` in `rag.py`: retrieved text
still goes in unlabelled, with no marker saying where it came from, exactly as in lab 2.
Defending ingestion does not defend the prompt. That is lab 12.

A production pipeline runs content inspection on ingest **and** on retrieved context — **Azure
AI Content Safety** is the named tool for that — carries signed provenance rather than a JSON
file, runs a canary suite in CI, and reconciles deletions by audit. Every one of those costs
money, latency, or a dependency off-site. A bought control is still yours to run, monitor and
recover.

---

## Evidence to submit

Paste **two** things into the class chat:

1. the **canary pair** — the answer before the poison and the answer after
2. the **retrieval-log line** naming `poisoned_handbook.pdf` as the source, with its score and
   its UNTAGGED provenance

The pair is the proof: something was caught, and something was recorded about why.

Your full transcript is saved to `lab10-results.txt` and copied out to the course folder when
the lab exits.
