# Lab 12 — Defending against prompt injection

You are the defender now. Lab 3 showed you that a web page can hijack an assistant. This lab
is the control you put around it.

The question is **not** "does the firewall work". It is:

> When the firewall sees the attack and lets it through anyway, how do you find out?

---

## The architecture

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

## The vulnerable configuration and the defended one

They are the same firewall. One field is different.

| | shipped (`block_at: CRITICAL`) | tuned (`block_at: HIGH`) |
|---|---|---|
| `article.html` | ALLOW | **ALLOW** — unchanged, and that matters |
| `article-poisoned.html` | BLOCK | BLOCK |
| `memo-leak.html` | **ALLOW — the model runs and leaks** | **BLOCK — the model is never called** |
| `memo-smuggled.html` | ALLOW | BLOCK |

The shipped threshold is copied from a real product. **CVE-2026-60086** (PraisonAI < 4.6.78,
July 2026, CVSS 6.9) blocked only what it rated CRITICAL, and its own advisory says CRITICAL
"required three or more detector families to match simultaneously", so "single or double-vector
prompt injections … classified as HIGH … pass through unblocked to reach the model."

Two families is HIGH. `memo-leak.html` has two.

---

## Mapping

**OWASP LLM01:2026 Prompt Injection** — Common Example 2, and Scenario #2 is this lab word for
word: *"A user asks an assistant to summarize a web page containing hidden instructions."*

Built here: **prevention 3** (filter at the boundary — *"Semantic filters are evadable by
rephrasing or encoding"*), **prevention 5** (strip tag-block, variation-selector and zero-width
characters at every ingest boundary), **prevention 11** (test against adaptive attackers).
Named, not built: preventions 1, 2 and 6.

The sentence that explains why the *log* is the core of this lab and the scanner is only a stub:

> "no reliable prevention mechanism exists today … Defense is therefore architectural rather
> than interceptive."

**OWASP LLM02:2026 Sensitive Information Disclosure** — the way out. Tier 1 prevention 4 says
*"never store secrets, credentials, or regulated data in system prompts"*, and this assistant
does exactly that on purpose. Tier 1 prevention 5 is the honest limit of what you build here:
*"Sanitize with classifiers, not regex alone … because regex fails on encoded and cross-lingual
output."* Your outbound scan is a regex.

**MITRE ATLAS** — defends `AML.T0066` → `AML.T0068` → `AML.T0051.001`/`.002` → `AML.T0057`,
with `AML.M0020` / `AML.M0033` (the two-sided scan), `AML.M0024` (the log) and `AML.M0035`
(the tune). `AML.M0035` against `AML.T0057` describes the seeded key exactly: *"Place synthetic
secrets or canary records in representative data sources and attempt extraction … improve
filtering and exfiltration detection."*

`AML.M0021` Generative AI Guidelines and `AML.M0022` Model Alignment are real ATLAS mitigations
for prompt injection, and lab 3 measured a 3/3 hijack with both of them in place. They are not
a firewall.

---

## The commands

🅱️ marks the beginner core. Expert runs the whole list.

**Look at the control before you use it**

🅱️ `cat rules.json`

**The baseline: a clean page through the firewall**

🅱️ `python firewall.py http://news.acme.com:8012/article.html`

> A clean page, through the firewall. Nothing matches, so the request reaches the model and the
> answer comes back. This is the baseline: the control not interfering.

🅱️ `python log.py`

> Every request is logged in both directions, whatever the verdict. A firewall that only records
> what it blocked cannot tell you what it missed.

**The obvious attack**

🅱️ `python firewall.py http://news.acme.com:8012/article-poisoned.html`

> Now the injected page from lab 3. A hidden div, an order to ignore the article, and a demand to
> reply with a fixed string. Three separate families fire, plus the concealment check.

**The quiet one**

🅱️ `python firewall.py http://news.acme.com:8012/memo-leak.html`

> A different page. Same kind of attack, quieter: no 'ignore', no fake system header. Just a
> format demand, hidden in a div. Watch the severity, and watch what the firewall does about it.

🅱️ `python log.py`

> Read the log again. One of these requests matched a rule and was allowed through anyway.
> Find it.

The reason is one field in `rules.json`, which you read at the start: the gate blocks at
CRITICAL, which needs three families. The page that got through scored two. This is
CVE-2026-60086, and it shipped in a real product.

**Close the gap**

🅱️ `python tune.py`

> Close the gap. One field, from CRITICAL to HIGH. Nothing else about the firewall changes.

*Expert: skip `tune.py` and edit the file yourself —* `nano rules.json` *— and decide for
yourself what to change. Lowering `block_at` is one answer. Adding the phrase to a family is
another. They are not equivalent; work out why.*

🅱️ `python firewall.py http://news.acme.com:8012/memo-leak.html`

> The same page, the same command, the same model. The only thing that changed is the rule file.

🅱️ `python firewall.py http://news.acme.com:8012/article.html`

> The half people skip. A tighter rule that breaks real traffic is not a fix — it is the reason
> the next person sets the threshold too loose. Re-check the clean page.

**Evidence**

🅱️ `python evidence.py`

> The whole story in one table. This is what you submit.

---

## Expert only

**The invisible-character page.** Same demand, no CSS:

```
curl -s http://news.acme.com:8012/memo-smuggled.html | tail -8
python firewall.py http://news.acme.com:8012/memo-smuggled.html
```

The payload is split by `U+E0020` TAG SPACE — a character that renders as nothing in every
browser and is read as content by a tokenizer. Microsoft measured a phishing campaign doing
exactly this in 2026: 21,000 messages on 8 February, over 1.3 million the next day, peaking at
2.3 million on the 11th, from ~150 sender domains with 92% of the volume out of a single /24.
Their four-word rule is the one `lab12lib.normalize()` implements: **"normalize before you
match."**

There is a subtlety in `lab12lib.scan_inbound()` worth reading the code for. Concealment is
scored on the **raw** HTML, *before* normalising, because normalising strips the invisible
characters and therefore destroys the evidence that anything was concealed. Sanitise first and
the page drops from HIGH to MEDIUM. *Normalize before you match* is about matching; it is not
about scoring.

**Write your own payload.** Edit a page, invent a phrasing no rule in `rules.json` covers, and
watch `exfil` miss it. That is OWASP prevention 3's own caveat — *"semantic filters are evadable
by rephrasing"* — and it is why detect leads and prevent is a stub.

**Check your work:**

```
python check.py
```

---

## How this differs from a real defence

| this lab | production |
|---|---|
| four regex families in one JSON file | a maintained classifier, inline, retrained against live attacks |
| severity = how many families matched | scoring calibrated per surface and per tenant |
| one regex for one known marker | classifiers plus NER — regex fails on encoded and cross-lingual output |
| one log file | a pipeline with retention, alerting and a SIEM |
| one hand edit | a rule-change process with an owner and a time to close |
| three requests | thousands a second, and the latency budget is real |

The shape is real. The scale is not.

**The production answer to the prevent half is bought, not built.** Azure AI Content Safety
**Prompt Shields** is a unified API that scans a user prompt and up to five documents in one
call and returns `attackDetected` for each, covering both direct attacks and what Microsoft
calls *document attacks* — hidden instructions in third-party content. Its own annotations
return `detected` and `filtered` as two separate booleans, which is where this lab's log schema
comes from, and its documentation tells you to *"adjust from block to annotate mode to log
without filtering"* while you tune. Its *Spotlighting* feature is OWASP prevention 6 shipped —
it base64-tags a document as lower-trust — and it is in preview and off by default.

**The trade:** it costs money per call, adds 100–300 ms per request in synchronous mode, and
your content leaves your boundary to be inspected. It is still yours to run, monitor and tune.

There is no *they*. There is only us.

---

## Safety

The support key in this lab is **fake** and exists only inside this container. It is a canary.
It is never printed when the outbound scan fires, it is written to the log redacted, and it is
never sent anywhere — there is nowhere to send it, because the container runs with
`--network none`.

Note what `rules.json` holds: a **pattern**, `ACME-SUPPORT-[A-Z0-9]{4}-[A-Z0-9]{4}`, not the
key. That is how a real DLP rule is written, and for a practical reason — a rule file gets
read, diffed and pasted into tickets, so a secret stored in one has just moved somewhere
quieter. It is also why `python check.py` asserts that nothing matching the pattern appears in
your log or your transcript: those are the two files you are asked to hand over.
