# OWASP threat mapping

How each lab maps to the **OWASP GenAI LLM Top 10 (2026)** and to **MITRE ATLAS**.

Source: <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
ATLAS: **[the ATLAS matrix](https://atlas.mitre.org/matrices/ATLAS-matrix)** ·
data: <https://github.com/mitre-atlas/atlas-data>

Every technique below links to its page on <https://atlas.mitre.org>. Each lab's chain is
also printed in that lab's own runner, so what you saw on screen and what you read here are
the same identifiers.

> **This course cites ATLAS v2026.08.** It was first built on v5.6.0; on 2026-09-22 every lab
> moved to v2026.08. The changes that touch the course: `AML.T0058 Publish Poisoned Models`
> was retired and replaced by
> **[`AML.T0115` Publish Poisoned AI Artifacts](https://atlas.mitre.org/techniques/AML.T0115)**
> (lab 1 now prints `AML.T0115`); tactic `AML.TA0001` was renamed from *AI Attack Staging* to
> **AI Attack Adaptation**; seven mitigations gained a "Predictive AI" prefix; and
> `AML.M0035` AI Red Team was added. The other 19 technique IDs are unchanged. Lab 15 also
> names one v2026.09 addition, `AML.M0039` AI Honeypots.

---

## ⚠️ The numbering changed between editions

If you are working from older material, or comparing notes with someone who is, the entry
numbers moved between the 2025 (2.0) and 2026 (v1.0) editions. The two that matter most for
this course:

| 2025 (2.0) | 2026 (v1.0) |
|---|---|
| LLM03:2025 Supply Chain | **LLM04:2026 Supply Chain** |
| LLM04:2025 Data and Model Poisoning | **LLM05:2026 Data and Model Poisoning** |

**This course cites the 2026 edition.** Say which edition you mean when you map a finding,
or two people will describe the same risk with different numbers.

### The 2026 list, for reference

| # | Entry |
|---|---|
| LLM01:2026 | Prompt Injection |
| LLM02:2026 | Sensitive Information Disclosure |
| LLM03:2026 | Excessive Agency |
| LLM04:2026 | Supply Chain |
| LLM05:2026 | Data and Model Poisoning |
| LLM06:2026 | Unbounded Consumption |
| LLM07:2026 | Misinformation |
| LLM08:2026 | Hidden Context Exposure |
| LLM09:2026 | Vector and Embedding Weaknesses |
| LLM10:2026 | Improper Output Handling |

---

## Lab 1 — Data and model supply chain poisoning

**Primary: LLM04:2026 Supply Chain**, item #4 *Weak Provenance and Unsigned Model Artifacts*.
**Also: LLM05:2026 Data and Model Poisoning** — the mechanism. The 2025 text names it
directly: *"malicious pickling, which can execute harmful code when the model is loaded."*

**2026 Scenario #7 under LLM04 is this lab, verbatim:** a developer loads a third-party
model using unsafe serialization, embedded code executes during loading, host compromise
follows.

### ATLAS

```
AML.T0115          →  AML.T0018.000  →  AML.T0010.003   →  AML.T0011.000
Publish Poisoned      Poison AI          AI Supply Chain    User Execution:
AI Artifacts          Model              Compromise: Model  Unsafe AI Artifacts
(Resource Dev)        (Persistence)      (Initial Access)   (Execution)
```

**Look these up:**

- [AML.T0115](https://atlas.mitre.org/techniques/AML.T0115) — Publish Poisoned AI Artifacts (replaced the retired `AML.T0058`)
- [AML.T0018.000](https://atlas.mitre.org/techniques/AML.T0018.000) — Manipulate AI Model: Poison AI Model
- [AML.T0010.003](https://atlas.mitre.org/techniques/AML.T0010.003) — AI Supply Chain Compromise: Model
- [AML.T0011.000](https://atlas.mitre.org/techniques/AML.T0011.000) — User Execution: Unsafe AI Artifacts

`AML.T0011.000 Unsafe AI Artifacts` is the closest ID in ATLAS to what the lab shows:
nobody runs an exploit, a developer calls `torch.load()`.

> ATLAS renamed these. "ML Supply Chain Compromise" is now **AI** Supply Chain Compromise,
> and "Backdoor ML Model" is now **Manipulate AI Model**.

---

## Lab 2 — RAG and semantic ingestion attacks

**Primary: LLM01:2026 Prompt Injection** — indirect, through retrieved content. Its own risk
list names it: *"attacker instructions ride in a RAG passage, web page, document, or email."*
**Also: LLM07:2026 Misinformation** — the pipeline confidently returns a false fact. The
model is not broken; it faithfully reports a poisoned corpus.
**Touches LLM09:2026 Vector and Embedding Weaknesses** at the retrieval step only.

**Not LLM05:2026.** OWASP scopes that entry to *training-time* poisoning and says so
explicitly inside LLM09's text:

> "Indirect prompt injection through retrieved content is covered in LLM01:2026 Prompt
> Injection, training-time poisoning of the embedding model in LLM05:2026 Data and Model
> Poisoning, serialization flaws in vector-store libraries in LLM04:2026 Supply Chain."

Nothing in lab 2 retrains anything. The distinction is the difference between poisoning the
model and poisoning what the model reads.

### ATLAS

```
AML.T0064  →  AML.T0066   →  AML.T0068   →  AML.T0051.001  →  AML.T0070
Gather RAG    Retrieval      LLM Prompt     LLM Prompt        RAG
Indexed       Content        Obfuscation    Injection:        Poisoning
Targets       Crafting                      Indirect
(Recon)       (Resource      (Defense       (Execution)       (Impact)
              Development)   Evasion)
```

**Look these up:**

- [AML.T0064](https://atlas.mitre.org/techniques/AML.T0064) — Gather RAG-Indexed Targets
- [AML.T0066](https://atlas.mitre.org/techniques/AML.T0066) — Retrieval Content Crafting
- [AML.T0068](https://atlas.mitre.org/techniques/AML.T0068) — LLM Prompt Obfuscation
- [AML.T0051.001](https://atlas.mitre.org/techniques/AML.T0051.001) — LLM Prompt Injection: Indirect
- [AML.T0070](https://atlas.mitre.org/techniques/AML.T0070) — RAG Poisoning

`AML.T0066 Retrieval Content Crafting` — *"writing content designed to be retrieved by user
queries to influence system users"* — is the skill students actually practise, and the one
most people have never heard of.

---

## Lab 3 — Advanced prompt injection

**Primary: LLM01:2026 Prompt Injection**, risk item #2 — *"attacker instructions ride in a
RAG passage, web page, document, or email and run when the content enters the context."*

Lab 2 poisoned what the model *knew*. This one hides instructions in a page the assistant is
asked to summarise, so the injection arrives as a side effect of an ordinary request.

### ATLAS

```
AML.T0066          →  AML.T0068          →  AML.T0051.001  →  AML.T0051.002
Retrieval Content     LLM Prompt            LLM Prompt        LLM Prompt
Crafting              Obfuscation           Injection:        Injection:
(Resource Dev)        (Defense Evasion)     Indirect          Triggered
                                            (Execution)       (Execution)
```

**Look these up:**

- [AML.T0066](https://atlas.mitre.org/techniques/AML.T0066) — Retrieval Content Crafting
- [AML.T0068](https://atlas.mitre.org/techniques/AML.T0068) — LLM Prompt Obfuscation
- [AML.T0051.001](https://atlas.mitre.org/techniques/AML.T0051.001) — LLM Prompt Injection: Indirect
- [AML.T0051.002](https://atlas.mitre.org/techniques/AML.T0051.002) — LLM Prompt Injection: Triggered

The lab prints `.001 / .002` together on purpose. The payload is delivered indirectly *and*
fires on a user action, so both fit — and arguing about which is primary is a better use of
two minutes than being told.

---

## Lab 4 — Multimodal and vision-based exploits

**Primary: LLM01:2026 Prompt Injection**, risk item #4 — *"Multimodal and steganographic
injection: sub-perceptual perturbations in images, audio, or video are extracted by the
encoder."*
**Also: LLM02:2026 Sensitive Information Disclosure** — what the hijacked pipeline gives up.

This lab runs **two independent attacks** on the same document pipeline, which is why it has
two chains rather than one.

### ATLAS

**Stage 1 — evading the stamp classifier (FGSM):**

```
AML.T0043.000        →  AML.T0015
Craft Adversarial       Evade AI Model
Data: White-Box         (Initial Access)
Optimization
(AI Attack Adaptation)
```

**Stage 2 — the OCR injection:**

```
AML.T0065       →  AML.T0043.003        →  AML.T0068          →  AML.T0051.001
LLM Prompt         Craft Adversarial       LLM Prompt            LLM Prompt
Crafting           Data: Manual            Obfuscation           Injection:
(Resource Dev)     Modification            (Defense Evasion)     Indirect
                   (AI Attack Adaptation)                           (Execution)
```

**Look these up:**

- [AML.T0043.000](https://atlas.mitre.org/techniques/AML.T0043.000) — Craft Adversarial Data: White-Box Optimization
- [AML.T0015](https://atlas.mitre.org/techniques/AML.T0015) — Evade AI Model
- [AML.T0065](https://atlas.mitre.org/techniques/AML.T0065) — LLM Prompt Crafting
- [AML.T0043.003](https://atlas.mitre.org/techniques/AML.T0043.003) — Craft Adversarial Data: Manual Modification
- [AML.T0068](https://atlas.mitre.org/techniques/AML.T0068) — LLM Prompt Obfuscation
- [AML.T0051.001](https://atlas.mitre.org/techniques/AML.T0051.001) — LLM Prompt Injection: Indirect

`AML.T0068`'s own text names this lab's mechanism: *"malicious instructions could be hidden
in the data itself (e.g. in the pixels of an image)."*

---

## Lab 5 — Exploiting AI agents and excessive agency

**Primary: LLM03:2026 Excessive Agency**, risks #1 and #4 — an agent with tools it does not
need, and tool permissions beyond the intended operation. *(It was LLM06 in the 2025 list.)*
**LLM01:2026 is the trigger**, not the finding: injection gets in, excessive agency is what
makes it matter.

### ATLAS

```
AML.T0084.001      →  AML.T0065       →  AML.T0051.001  →  AML.T0053
Discover AI Agent     LLM Prompt         LLM Prompt        AI Agent Tool
Configuration:        Crafting           Injection:        Invocation
Tool Definitions      (Resource Dev)     Indirect          (Execution,
(Discovery)                              (Execution)        Priv Esc)
      ↓
AML.T0085.001
Data from AI
Services: AI Agent
Tools
(Collection)
```

**Look these up:**

- [AML.T0084.001](https://atlas.mitre.org/techniques/AML.T0084.001) — Discover AI Agent Configuration: Tool Definitions
- [AML.T0065](https://atlas.mitre.org/techniques/AML.T0065) — LLM Prompt Crafting
- [AML.T0051.001](https://atlas.mitre.org/techniques/AML.T0051.001) — LLM Prompt Injection: Indirect
- [AML.T0053](https://atlas.mitre.org/techniques/AML.T0053) — AI Agent Tool Invocation
- [AML.T0085.001](https://atlas.mitre.org/techniques/AML.T0085.001) — Data from AI Services: AI Agent Tools

**`AML.T0053` is the one to remember.** It is the only technique in ATLAS carrying the
Privilege Escalation tactic for an agent, and its description is the lab verbatim: *"AI
agents may be configured to have access to tools that are not directly accessible by users.
Adversaries may abuse this to gain access to tools they otherwise wouldn't be able to use."*

---

## Lab 6 — MCP and interface hijacking

**Primary: LLM01:2026 Prompt Injection**, **Scenario #9** — *Trusted-Backend Indirect
Injection through MCP.* The most incident-backed scenario in the entry: a poisoned GitHub
issue that exfiltrated private repos, a Supabase MCP server that dumped a production
database, and the `postmark-mcp` package that BCC'd mail from ~300 organisations. All 2025.
**Also: LLM08:2026 Hidden Context Exposure**, risks #1 and #4 — tool descriptions and
schemas are context the model reads and the user never sees.

The control this lab teaches is the entry's own **prevention #10**, which undercuts the
obvious fix: *"Pinning does not stop a payload shipped in the pinned version or
tool-description poisoning that leaves the version unchanged."*

### ATLAS

```
AML.T0084.001      →  AML.T0110      →  AML.T0051.001  →  AML.T0053
Discover AI Agent     AI Agent Tool     LLM Prompt        AI Agent Tool
Configuration:        Poisoning         Injection:        Invocation
Tool Definitions      (Persistence)     Indirect          (Execution)
(Discovery)                             (Execution)
```

**Look these up:**

- [AML.T0084.001](https://atlas.mitre.org/techniques/AML.T0084.001) — Discover AI Agent Configuration: Tool Definitions
- [AML.T0110](https://atlas.mitre.org/techniques/AML.T0110) — AI Agent Tool Poisoning
- [AML.T0051.001](https://atlas.mitre.org/techniques/AML.T0051.001) — LLM Prompt Injection: Indirect
- [AML.T0053](https://atlas.mitre.org/techniques/AML.T0053) — AI Agent Tool Invocation

`AML.T0110` names the protocol and both of the lab's attacks: *"modifying parameters or
descriptions, injecting hidden logic, or redirecting outputs."*

---

## Lab 7 — AI-powered attack orchestration

**ATLAS leads this one and OWASP comes second**, which is a deliberate break from labs 1–6.
The Top 10 describes risks in software *you build*; an attacker using an LLM to help them
work is a fact about the threat landscape, not a vulnerability in your application. This is
the one lab whose topic sits outside the list, and saying so is better teaching than forcing
a fit.

**Primary: LLM10:2026 Improper Output Handling**, Scenario #2 — *"the LLM can **encode** the
sensitive data and send it, without any output validation or filtering, to an
attacker-controlled server."*
**Also: LLM02:2026 Sensitive Information Disclosure**, via OWASP's own ATLAS cross-map:
*"Base64 and hex encodings defeat regex and blocklist data-loss filters."*
**LLM06:2026 Unbounded Consumption is cited as the mirror, not a mapping** — LLM06 is cost
asymmetry pointed at the defender; this lab measures it pointed back at the attacker.

### ATLAS

```
AML.T0016.002   →  AML.T0043.003        →  AML.T0015         →  AML.T0096
Obtain             Craft Adversarial       Evade AI Model       AI Service API
Capabilities:      Data: Manual            (Defense Evasion)    (Command and Control)
Generative AI      Modification                                 cited, not built
(Resource Dev)     (AI Attack Adaptation)
```

**Look these up:**

- [AML.T0016.002](https://atlas.mitre.org/techniques/AML.T0016.002) — Obtain Capabilities: Generative AI
- [AML.T0043.003](https://atlas.mitre.org/techniques/AML.T0043.003) — Craft Adversarial Data: Manual Modification
- [AML.T0015](https://atlas.mitre.org/techniques/AML.T0015) — Evade AI Model
- [AML.T0096](https://atlas.mitre.org/techniques/AML.T0096) — AI Service API

**Two real case studies, not hypotheticals:**

- **[AML.CS0000](https://atlas.mitre.org/studies/AML.CS0000)** — Palo Alto Networks evaded a
  deep-learning detector for malware C2 traffic by varying header fields. The crafted packets
  were called **benign with over 80 % confidence**.
- **[AML.CS0044](https://atlas.mitre.org/studies/AML.CS0044)** — **LAMEHUG** (APT28, 2025,
  CERT-UA#16039) called a **Qwen 2.5 Coder 32B** model to generate its commands. Students run
  the same model family, three sizes down.

---

## Lab 8 — Offensive recap and transition to defense

No new mapping. This lab **is** the mapping: students place their own seven attacks on the
matrix and export an
**[ATLAS Navigator](https://atlas.mitre.org/navigator)** layer file.

**Coverage across labs 1–7:** 20 distinct techniques, **13 of the 16 ATLAS tactics**, and 8
of the 10 OWASP 2026 entries.

**The spine:** [`AML.T0051.001`](https://atlas.mitre.org/techniques/AML.T0051.001) LLM Prompt
Injection: Indirect appears in **five of the seven labs**. Twelve of the twenty techniques
appear in exactly one. Seven attacks that felt completely different shared one delivery
mechanism.

**The three tactics never touched** — AI Model Access, Credential Access and **Exfiltration**.
(Lateral Movement is lit on v2026.08, which also files `AML.T0053` under it.) The first two
are out of scope by design. Exfiltration was a safety
decision taken four times: no lab gets an external endpoint, because a work laptop that runs
a hacking lab and then beacons to an unfamiliar domain is the textbook EDR detection.

**The defensive half**, from ATLAS's own mitigations:

- [AML.M0035](https://atlas.mitre.org/mitigations/AML.M0035) — AI Red Team — **7 of 7 labs**
- [AML.M0020](https://atlas.mitre.org/mitigations/AML.M0020) — Generative AI Guardrails — **6 of 7 labs**
- [AML.M0024](https://atlas.mitre.org/mitigations/AML.M0024) — AI Telemetry Logging — **5 of 7 labs**
- [AML.M0033](https://atlas.mitre.org/mitigations/AML.M0033) — Input and Output Validation for AI Agent Components — **5 of 7 labs**

And the finding the lab ends on: **only 2 of those 20 techniques have no published ATLAS
mitigation** — [`AML.T0065`](https://atlas.mitre.org/techniques/AML.T0065) LLM Prompt
Crafting and [`AML.T0110`](https://atlas.mitre.org/techniques/AML.T0110) AI Agent Tool
Poisoning, lab 6's core. On v5.6.0 it was 9. The standard caught up fast, mostly with broad
controls — and covered is not the same as solved. The gap that is left is the agent's tool
layer.

### ATLAS

Lab 8 has no chain of its own — it is the chains from labs 1–7, placed on the matrix.

```
labs 1-7  ──►  20 techniques  ──►  13 of 16 tactics  ──►  atlas-layer.json
                    │                                     (an ATLAS Navigator
                    └──►  2 with NO published mitigation    layer file)
```

**Look these up:**

- [The ATLAS matrix](https://atlas.mitre.org/matrices/ATLAS-matrix) — where the coverage lands
- [ATLAS Navigator](https://atlas.mitre.org/navigator) — where the exported layer file loads
- [AML.T0051.001](https://atlas.mitre.org/techniques/AML.T0051.001) — the spine, in 5 of 7 labs
- [AML.M0035](https://atlas.mitre.org/mitigations/AML.M0035) — AI Red Team
- [AML.M0024](https://atlas.mitre.org/mitigations/AML.M0024) — AI Telemetry Logging
- [AML.M0033](https://atlas.mitre.org/mitigations/AML.M0033) — Input and Output Validation for AI Agent Components
- [AML.T0110](https://atlas.mitre.org/techniques/AML.T0110) — AI Agent Tool Poisoning, still unmitigated

---

## A caution on scanners

Labs 1 and 2 both end by showing a control that catches the attack. Neither is a guarantee,
and OWASP 2026 is explicit that scanners and safe-loader flags are defence in depth rather
than assurance. Documented bypasses worth knowing:

- **nullifAI** — models on Hugging Face using broken or compression-wrapped pickle streams
  that execute before a scanner reaches the malformed byte (Zanki, 2025)
- **picklescan zero-days** (Cohen, 2025)
- **`torch.load` `weights_only` bypass** — CVE-2025-32434
- **ShadowLogic** — a backdoor in the computation graph of a "safe" format like ONNX, with
  no executable code for a serialization scanner to find (Wickens et al., 2024)

Lab payloads are built to be caught. Real ones are built to survive the tool you just ran.
