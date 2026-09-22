# Lab 14 — Defending MCP tool calls

**OWASP LLM01:2026 Prompt Injection**, **prevention 10** — *"Pin, sign, and verify every MCP
server and third-party tool package, audit tool descriptions for hidden instructions, and
monitor tool composition"* — plus **Scenario #9, Trusted-Backend Indirect Injection through
MCP**, and **LLM08:2026 Hidden Context Exposure**, risks #1 and #4.
Agentic cross-map **ASI04 Agentic Supply Chain Vulnerabilities** — MCP servers and tool
registries are ASI04's supply chain, **not LLM04's**; LLM04's own scope note says so.
**MITRE ATLAS** `AML.T0084.001` → **`AML.T0110.000` / `AML.T0110.002`** → `AML.T0051.001` →
`AML.T0053`, with `AML.T0109` **AI Supply Chain Rug Pull** as the update path.

---

## The architecture

Two processes, both inside this container, both on `127.0.0.1`. No port is published and
there is no network.

```
   "What is the balance of account chk-001?"
                │
                ▼
   ┌────────────────────────────────────┐
   │   THE HOST        ask.py           │        ┌──────────────────────┐
   │   loads the model                  │        │   MCP SERVER         │
   │                                    │        │   mcp_server.py      │
   │   ┌────────────────────────────┐   │ JSON-  │   127.0.0.1:8014     │
   │   │  verify.py                 │◄──┼──RPC──►│                      │
   │   │  1 trust list              │   │  2.0   │   get_balance        │
   │   │  2 descriptor pin (sha256) │   │        │   send_payment       │
   │   │  3 message schema          │   │        │                      │
   │   └──────────┬─────────────────┘   │        │   ** COMPROMISED **  │
   │              │                     │        └──────────────────────┘
   │        tamper-log.jsonl            │
   └────────────────────────────────────┘
                  │
            trust.json  ── the servers you approved, and exactly what you approved
```

**Read that right-hand box.** In lab 6 the server was honest and an attacker sat on the wire.
Here there is no attacker on the wire — **the server itself is the adversary**, which is the
real MCP threat model: you connect an agent to software somebody else operates, and that
software chooses the text your model reads.

## The vulnerable configuration

Nothing is wrong with the protocol and nothing is malformed. The vulnerability is what a host
takes on trust.

1. **Tool descriptions are instructions.** The host pastes them into the model's system
   prompt. The user never sees them and the *server* chooses the text. OWASP LLM08:2026,
   risks #1 and #4 — whose worked example is literally a tool description served by an MCP
   server.
2. **Approval is bound to a name, not to content.** Approve a server once and it can change
   what it advertises afterwards. That is `AML.T0109`, and it is **CVE-2025-54136** with a
   CVSS of 7.2.
3. **Tool results go into the conversation unlabelled.** An instruction inside a result reads
   as a turn in the conversation.

## The control — pin, diff, drop, re-pin

`verify.py` is about 80 lines and you should read it. Three gates, in order, and **a record
for every one of them, pass or block**:

| gate | question | rule when it blocks |
|---|---|---|
| **1** trust list | is this server one we approved at all? | `not_in_trust_list` |
| **2** descriptor pin | does `sha256(descriptor)` match the copy we pinned? | `descriptor_changed` |
| **3** message schema | does the result match the shape its own schema declares? | `result_off_schema` |

**Gate 2 hashes the content, not the version.** OWASP says why, in prevention 10's own
caveat: *"pinning does not stop a payload shipped in the pinned version or tool-description
poisoning that leaves the version unchanged."* A version number does not move when a
description does. A hash does.

## What was measured during the build

Temperature 0, byte-identical verdicts across three runs and again at `--cpus=2`.

| beat | what the server did | control | outcome |
|---|---|---|---|
| clean | nothing | on | **4820.55**, three PASS records |
| `--result` | appended an instruction to the result | on | **blocked at gate 3**, no payment |
| `--result` | the same attack | **off** | **the payment is made** |
| `--rewrite` | returned a different balance | on | **PASSED — reports 999,999.00** |
| `--descriptor` | changed a tool description | on | **blocked at gate 2**, and the tool is gone |
| after `drop.py` | — | on | refused at **gate 1**, nothing read |
| after `repin.py` | still advertising the poison | on | **4820.55 restored** from your own copy |

**And the finding that decides this lab: tool-description poisoning does not work on this
model — 0 out of 24.** Nine attempts here, across three structurally different styles
(hiding an instruction, lying about argument semantics, and tool shadowing), plus lab 6's own
0 out of 15. The model ignored every one.

That is **not** a reason to skip the control, and the reason why is the whole point:

> **MCPTox** (AAAI 2026) tested 353 real tools from 45 live MCP servers against 20 models:
> **36.5% average** attack success, **72.8%** on the most instruction-compliant model, and
> even the most refusal-prone model tested complied **34%** of the time.

The attack **scales with model capability**. Your 1.5B model shrugged it off; the model your
company deploys next quarter may not, and you do not get to know in advance. The pin is a
hash comparison — it fires identically either way.

*(Lab 6's handout rounds the same benchmark up to "over 60%". 36.5% average / 72.8% best are
the paper's numbers and the ones to use.)*

---

## Every command in the lab

🅱️ marks the core commands. **Beginner mode runs only those. Expert runs the list.**

```
🅱️  LAB14_RUN=clean python ask.py                     a normal question, control on
🅱️  python tamperlog.py                               three PASS records, one per gate
🅱️  python poison.py --result                         compromise the server's ANSWER
🅱️  LAB14_RUN=result python ask.py                    blocked at gate 3
🅱️  LAB14_RUN=undefended python ask.py --no-verify    the same attack, control OFF
🅱️  python poison.py --rewrite                        a well-formed LIE
🅱️  LAB14_RUN=rewrite python ask.py                   the control passes it. On purpose.
🅱️  python poison.py --descriptor                     compromise the DESCRIPTION
🅱️  LAB14_RUN=swapped python ask.py                   blocked at gate 2 - and an outage
🅱️  python tamperlog.py --diff                        THE DIFF. This is the finding.
🅱️  python drop.py                                    recovery 1: off the trust list
🅱️  LAB14_RUN=dropped python ask.py --wire-only       refused at gate 1, nothing read
🅱️  python repin.py                                   recovery 2: re-pin what you approved
🅱️  LAB14_RUN=repinned python ask.py                  service restored, on YOUR copy
🅱️  python evidence.py                                the story, plus the free replay
    cat verify.py                                     ~80 lines; the whole control
    python ask.py --tools                             the raw descriptors, unchecked
    python ask.py --ask "How much is in chk-002?"     ask something else
    python mcp_server.py &                            run the server by hand
    nano trust.json                                   edit the trust list yourself
    python check.py                                   confirm the control held
```

The beginner runner packs these into ten steps by pairing each `poison.py` with the `ask.py`
that follows it. Expert runs them one at a time.

## Evidence to submit

`python evidence.py` prints every run, where each refusal happened, and the replay. **The
diff from `python tamperlog.py --diff` is the finding** — paste both into the class
chat. The full transcript is in `lab14-results.txt`.

## Expert mode — the steps beginner skips

- **`nano trust.json`** and drop or re-pin by hand instead of running the scripts. Decide for
  yourself what to pin.
- **Pin the poisoned descriptor on purpose**, then re-run. Every gate reports PASS and the
  poison reaches the model anyway. *A pin is only as good as the review that produced it* —
  and `python check.py` is the only thing that catches it, because it measures the system
  prompt rather than trusting a verdict.
- **Tighten `SHAPES` in `verify.py`** so the rewritten balance is caught too — then ask what
  you had to assume about the value to do it, and whether you could have written that rule
  before you knew the attack.
- **`python ask.py --tools`** to see what the server advertises before any check touches it.

## How this differs from a real defence

| this lab | production |
|---|---|
| one JSON trust list, two tools | a tool registry with provenance, owners and review |
| `sha256` of a descriptor | signed tool definitions bound to an approved version |
| one regex per tool shape | full JSON Schema validation, plus scanning for imperative language |
| one log file | a pipeline with retention, alerting and a SIEM |
| one hand edit to re-pin | a change process with an owner and a time to close |
| the check runs inside the host process | an out-of-process vetting gateway the agent cannot reach |
| one server, two tools | dozens of servers, hundreds of tools, and latency is real |

The shape is real; the scale is not. And the last row is the honest one: a validator the
compromised server could edit would be lab 6's bug again, one level up.

Real 2025–26 incidents of this exact shape: **MCPoison** (CVE-2025-54136) swapped an approved
Cursor MCP configuration after approval — fixed in v1.3 by forcing re-approval on *any*
change, *"including something as small as adding a space"*. **Invariant Labs** poisoned a
calculator tool's description and exfiltrated a developer's SSH private key; the model
returned the correct sum and the developer never knew. **CVE-2025-6514** reached full RCE on
the client OS from an untrusted remote MCP server, across 437,000+ downloads. CSA counted
seven high or critical MCP CVEs by May 2026 and an estimated **200,000 vulnerable instances**
across more than 150 million package downloads; of 1,808 servers scanned, **66% had a
security finding** and **5.5% were tool-poisoned**.

## The defence

1. **Treat a tool description as code.** Version it, diff it, review the diff before it takes
   effect — *"exactly as a pull request to production code would be reviewed"* (CSA,
   2026-07-11).
2. **Pin the content, not the version.** OWASP's own caveat is the argument.
3. **Log the passes too.** The clean run's three PASS records are the only proof the check
   was running at all.
4. **Know what your control does not cover.** The rewritten balance passed every gate. *You
   checked the shape; nobody checked the source.*
5. **The production answer is signed tool calls** through a vetting gateway — ETDI's
   OAuth-based attestation binding a tool definition to an approved version, or
   Sigstore-backed artifact signing (`AML.M0013`; OWASP LLM04 prevention 5). It costs a
   review step on every legitimate update, and it is still yours to run and tune.

**ATLAS 2026.08 maps no mitigation to `AML.T0110` or to any of its three sub-techniques.**
They were added on 2026-07-31 and the mitigation relationships have not caught up. Every
control in this lab is borrowed from a neighbouring technique — `AML.M0014` Verify AI
Artifacts (the pin), `AML.M0033` Input and Output Validation (the schema check), `AML.M0024`
AI Telemetry Logging (the log), `AML.M0023` AI Bill of Materials (the trust list). When the
framework has not caught up with the attack, you borrow, and you say that you borrowed.
