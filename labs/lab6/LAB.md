# Lab 6 — MCP and interface hijacking

**OWASP LLM01:2026 Prompt Injection**, **Scenario #9 — Trusted-Backend Indirect Injection
through MCP**, plus **LLM08:2026 Hidden Context Exposure**, risks #1 and #4.
**MITRE ATLAS** `AML.T0084.001` → **`AML.T0110` AI Agent Tool Poisoning** →
`AML.T0051.001` → `AML.T0053`.

---

## The architecture

Three processes, all inside this container, all on `127.0.0.1`. No port is published and
there is no network.

```
   "What is the balance of account chk-001?"
                │
                ▼
   ┌────────────────────┐   JSON-RPC 2.0 over HTTP
   │   MCP CLIENT       │───────────────┐
   │   mcp_client.py    │               ▼
   │   loads the model  │      ┌──────────────────┐      ┌────────────────────┐
   └────────────────────┘      │   THE PROXY      │      │   MCP SERVER       │
              ▲                │   proxy.py       │─────►│   mcp_server.py    │
              │                │   127.0.0.1:8006 │◄─────│   127.0.0.1:8007   │
              └────────────────│                  │      │   get_balance      │
                  tool result  │  reads and EDITS │      │   send_payment     │
                               │  both directions │      └────────────────────┘
                               └──────────────────┘
                                        │
                                    wire.log
```

The client believes it is talking to the server. The server believes it is answering the
client. **Neither can tell the proxy exists, and neither checks.**

## The vulnerable configuration

Nothing is wrong with the server, and nothing is wrong with the client. Both behave
correctly. The vulnerability is in what they take on trust.

1. **Nothing authenticates the channel.** Plain JSON-RPC over HTTP: no signature, no
   checksum, nothing tying an answer to the server that sent it. Anything on the wire speaks
   with the server's authority.
2. **The client pastes tool DESCRIPTIONS into the model's instructions.** Those descriptions
   are hidden context — the user never sees them, and the *server* chooses the text.
   OWASP LLM08:2026, risks #1 and #4.
3. **The client pastes tool RESULTS into the conversation unlabelled.** Nothing marks them
   as data rather than instruction. OWASP lists "an MCP server's output" among its untrusted
   surfaces for exactly this reason.

## What was measured during the build

Temperature 0, byte-identical output across three fresh containers.

| beat | payment made | answer mentions it |
|---|---|---|
| clean wire | no | — |
| `--rewrite-arg chk-002` | no | reports **your** account with **another's** balance |
| `--inject` | **yes** | **no** |
| `--inject --verify` | **no** — refused in transit | — |
| `--rewrite-arg --verify` | no | **still wrong.** The signature was valid. |

**Tool-description poisoning — the famous MCP attack — was tried and does not work on this
model: 0 out of 15**, across four phrasings and two presentations. It works well on larger
models: the MCPTox benchmark measures over 60% success across 45+ real-world MCP servers,
best model 72.8%. **This attack scales with model capability**, which is the opposite of
reassuring. Ask your instructor for the demo.

---

## Every command in the lab

🅱️ marks the core commands. **Beginner mode runs only those. Expert runs the list.**

```
🅱️  python mitm.py --tools                                    what the server advertises
🅱️  python mitm.py --beat control                             a normal question
🅱️  python mitm.py --rewrite-arg chk-002 --beat arg           edit the REQUEST
🅱️  python mitm.py --inject --beat inject                     edit the RESPONSE
🅱️  python mitm.py --inject --verify --beat defended          the defence
🅱️  python mitm.py --rewrite-arg chk-002 --verify --wire-only where the defence fails
🅱️  python evidence.py                                        the evidence
    python mitm.py --rewrite-result 999999.00                 the beat the guided path skips
    cat proxy.py                                              ~120 lines; the whole attack
    python mcp_server.py &                                    run the three by hand
    python proxy.py --inject &
    python mcp_client.py
    nano payload.txt                                          write your OWN instruction
    python check.py                                           confirm the evidence is real
```

## Evidence to submit

`python evidence.py` prints the wire log next to what the assistant told you. **The
disagreement between those two is the finding** — paste both into the class chat. The full
transcript is in `lab6-results.txt`.

## How this differs from a real attack

| this lab | a real attack |
|---|---|
| you are handed the proxy | the position is bought with a poisoned server or package |
| a `--rewrite` flag | persistent, hidden tampering |
| two stub tools | real payments, files, repositories |
| the payment is a printed string | money actually leaves |
| the wire log is printed for you | nobody is reading the log |

Three real 2025 incidents took the shape of the injection beat: a poisoned GitHub issue that
exfiltrated private repos, a Supabase MCP server that dumped a production database, and the
`postmark-mcp` package that BCC'd email from an estimated 300 organisations.

## The defence

1. **Authenticate the channel in both directions.** You watched signing the response stop
   two attacks and miss the third, because the server honestly signed an honest answer to
   the wrong question. *You signed the answer; nobody signed the question.*
2. **Treat tool output as data, never instruction.** Render it quoted and labelled so an
   instruction inside a result cannot read as a turn in the conversation.
3. **Do not trust tool descriptions either.** Server-controlled hidden context, pasted
   straight into the system prompt.
4. **Pinning is necessary and not sufficient** — OWASP says so in the entry itself: it does
   not stop "a payload shipped in the pinned version or tool-description poisoning that
   leaves the version unchanged". Diff what the server advertises, every run.
5. **Keep the privileged action behind a check the channel cannot reach.** That is lab 5's
   lesson, and it is what would have stopped the payment.
