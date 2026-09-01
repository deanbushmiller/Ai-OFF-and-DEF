# OWASP Threat Mapping

This course maps each student lab and instructor demonstration to the [OWASP GenAI LLM Top 10 2026](https://genai.owasp.org/initiatives/top-10-for-llm-and-genai/) and the [OWASP Machine Learning Security Top Ten 2023](https://owasp.org/www-project-machine-learning-security-top-10/). Lab 6 also uses the [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/).

This is a teaching crosswalk. It is not an official OWASP mapping. The LLM list is current as of 2026-09-01. The ML list remains a draft that OWASP may change.

## OWASP GenAI LLM Top 10 2026

| ID | Threat |
| --- | --- |
| LLM01 | Prompt Injection |
| LLM02 | Sensitive Information Disclosure |
| LLM03 | Supply Chain Vulnerabilities |
| LLM04 | Data and Model Poisoning |
| LLM05 | Improper Output Handling |
| LLM06 | Excessive Agency |
| LLM07 | System Prompt Leakage |
| LLM08 | Vector and Embedding Weaknesses |
| LLM09 | Misinformation |
| LLM10 | Unbounded Consumption |

## OWASP Machine Learning Security Top Ten 2023

| ID | Threat |
| --- | --- |
| ML01 | Input Manipulation Attack |
| ML02 | Data Poisoning Attack |
| ML03 | Model Inversion Attack |
| ML04 | Membership Inference Attack |
| ML05 | Model Theft |
| ML06 | AI Supply Chain Attacks |
| ML07 | Transfer Learning Attack |
| ML08 | Model Skewing |
| ML09 | Output Integrity Attack |
| ML10 | Model Poisoning |

## Lab crosswalk

| Lab | Student exercise | Instructor demonstration | Primary LLM threats | Primary ML threats |
| --- | --- | --- | --- | --- |
| 1 | Identify an indirect injection | Compare a permissive and guarded local travel assistant | LLM01, LLM06, LLM07 | ML01, ML09 |
| 2 | Scan and gate a model bundle | Scan unsafe loading code and ask a local model for a release decision | LLM03, LLM05 | ML06, ML10 |
| 3 | Plan bounded tests | Run safe misinformation, disclosure, and action-boundary tests against a local model | LLM01, LLM02, LLM06, LLM09 | ML01, ML09 |
| 4 | Map threats to ATLAS | Map outputs from local demonstrations to an ATLAS attack path | LLM01, LLM04, LLM06, LLM08 | ML01, ML02, ML09 |
| 5 | Design a dual-LLM review | Compare a local application-model draft with an independent reviewer-model decision | LLM02, LLM05, LLM06, LLM07 | ML09 |
| 6 | Secure MCP tools | Show a local model proposing an unsafe mock tool action, then constrain it | LLM01, LLM05, LLM06 | ML01, ML09 |
| 7 | Defend a RAG corpus | Compare an unverified RAG answer with a source-aware answer | LLM04, LLM08, LLM09 | ML02, ML10 |
| 8 | Triage an AI incident | Show a local model ingesting an instruction planted in synthetic logs | LLM01, LLM05, LLM10 | ML01, ML09 |
| 9 | Design enterprise guardrails | Compare permissive and layered local-agent policies | LLM01, LLM02, LLM03, LLM04, LLM05, LLM06, LLM08, LLM09, LLM10 | ML06, ML09 |

## Lab 6 MCP crosswalk

Lab 6 also maps to MCP02 Privilege Escalation via Scope Creep, MCP03 Tool Poisoning, MCP06 Intent Flow Subversion, MCP07 Insufficient Authentication and Authorization, MCP08 Lack of Audit and Telemetry, and MCP10 Context Injection and Over-Sharing.

## How to use the mapping

1. Start each student lab with its mapping line.
2. Name the relevant threat before the exercise.
3. Run the instructor demonstration to show the failure mode.
4. Return to the mapping during the mitigation discussion.
5. Ask students which control changes the mapped risk.
