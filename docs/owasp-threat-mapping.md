# OWASP threat mapping

How each lab maps to the **OWASP GenAI LLM Top 10 (2026)** and to **MITRE ATLAS**.

Source: <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
ATLAS: <https://github.com/mitre-atlas/atlas-navigator-data>

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
AML.T0058          →  AML.T0018.000  →  AML.T0010.003   →  AML.T0011.000
Publish Poisoned      Poison AI          AI Supply Chain    User Execution:
Models                Model              Compromise: Model  Unsafe AI Artifacts
(Resource Dev)        (Persistence)      (Initial Access)   (Execution)
```

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

`AML.T0066 Retrieval Content Crafting` — *"writing content designed to be retrieved by user
queries to influence system users"* — is the skill students actually practise, and the one
most people have never heard of.

---

## Labs 3–8

Mappings will be added as each lab is built and its OWASP and ATLAS entries confirmed
against the current sources rather than assumed.

| # | Lab | Expected |
|---|---|---|
| 3 | Advanced prompt injection | LLM01:2026 |
| 4 | Multimodal and vision-based exploits | LLM01:2026 (multimodal delivery) |
| 5 | Exploiting AI agents and excessive agency | LLM03:2026 (risks #1 excessive functionality, #4 excessive permissions; LLM01:2026 is the trigger) |
| 6 | MCP and interface hijacking | LLM01:2026, LLM03:2026 |
| 7 | AI-powered attack orchestration | tbc |
| 8 | Offensive recap and transition to defense | all of the above |

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
