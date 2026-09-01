# Lab 4: MITRE ATLAS Mapping

**Time:** 30 minutes  
**Company:** Northstar Travel  
**Evidence:** An ATLAS mapping worksheet and one visual
**OWASP mapping:** [LLM01, LLM04, LLM06, LLM08, ML01, ML02, and ML09](../../docs/owasp-threat-mapping.md#lab-crosswalk)

## Scenario

Northstar Travel found three issues during its assistant review: untrusted retrieved content tried to redirect the assistant, a knowledge-base entry gave a false travel rule, and a tool could send an email without confirmation.

## Learning outcomes

1. Map AI threats to MITRE ATLAS techniques.
2. Show an attack path for technical and business stakeholders.
3. Connect each technique to a mitigation owner.

## Steps

1. Open the [MITRE ATLAS matrix](https://atlas.mitre.org/).
2. Find techniques that match LLM prompt injection, RAG poisoning, and AI agent tool invocation.
3. Create a table with the local scenario, ATLAS technique, tactic, control, owner, and status.
4. Create a simple visual from the table.
5. Explain which control breaks the path earliest.

## Worksheet

| Scenario event | ATLAS technique | Tactic | Control | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| Untrusted travel note redirects model | LLM Prompt Injection | Execution | Treat retrieval as data | AI engineering | Planned |
| False travel rule enters knowledge base | RAG Poisoning | Persistence | Provenance and review | Knowledge owner | Planned |
| Tool sends email without confirmation | AI Agent Tool Invocation | Execution | Human approval gate | Platform team | Planned |

## Visual format

```text
Untrusted content → LLM Prompt Injection → Tool request → Email impact
                    ↓
             retrieval boundary
                    ↓
               approval gate
```

## Safe to share with an LLM

```text
Map these synthetic scenario events to MITRE ATLAS. Use the official ATLAS terminology when possible. Do not invent technique identifiers. Return a concise table and an ASCII attack-path visual.
```

## Expected evidence

Your mapping uses the official matrix as the source of truth. Your visual shows the sequence from content to model to tool to impact. Your controls include a technical owner.

## Advanced challenge

Add maturity and detection columns. Mark each technique as prevented, detected, or unaddressed. Propose one security telemetry source for each detection.

## Instructor notes

ATLAS changes over time. Accept current official terminology. Ask students to link to the matrix and avoid relying on memory.
