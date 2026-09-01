# Instructor Demonstrations

Advanced students could in theory run this lab set up. This will require local AI capable machine.

These demonstrations use a local model through Ollama. They run attacks only against a local, synthetic application. They do not contact a vendor model, external MCP server, customer system, or public endpoint.

## Safety boundary

The attacks target application design faults around a local model. They use only benign instructions and synthetic facts. The tool demonstrations only propose actions. They never call an operating-system command, send mail, change a ticket, or use a real credential.

Do not download or run an untrusted model, Python pickle, archive, or configuration file. The supply-chain demonstration scans a deliberately unsafe source pattern. It does not execute an unsafe artifact.

## Hardware and model

The default model is llama3.2:1b. It is small enough for many recent Macs. It can run slowly through Docker because Docker does not use Apple Metal acceleration in this setup.

For a stronger demonstration, use a locally approved 3B to 8B instruction model. More capable models may resist some attacks better. That contrast is part of the lesson. The vulnerable application design remains the issue.

The demonstrations do not require a specially vulnerable Hugging Face model. Prompt injection, RAG poisoning, tool confusion, and unsafe output handling usually arise from application wiring. If you use Hugging Face, download only a known model in safetensors format. Verify the publisher, revision, license, checksum, and model card before use.

## Start the local model

1. Start Docker Desktop.
2. Run: docker compose -f compose.instructor.yaml up -d ollama
3. Run: docker compose -f compose.instructor.yaml exec ollama ollama pull llama3.2:1b
4. Run: docker compose -f compose.instructor.yaml run --rm demo 01
5. Compare the baseline and guarded model outputs.

Set LOCAL_MODEL before the command to select another downloaded model. The first model download can take several minutes and uses local disk space.

## Stop and remove models

1. Run: docker compose -f compose.instructor.yaml down
2. Run docker volume rm ai-off-and-def_instructor-models only when you want to remove downloaded models.

The volume-removal command deletes local model files. Verify the volume name before you run it.

## Demonstrations

1. [Indirect prompt injection](labs/01-indirect-prompt-injection/README.md)
2. [Supply-chain audit](labs/02-supply-chain-audit/README.md)
3. [Adversarial red teaming](labs/03-adversarial-red-teaming/README.md)
4. [MITRE ATLAS mapping](labs/04-mitre-atlas/README.md)
5. [Dual-LLM guardrails](labs/05-dual-llm-guardrails/README.md)
6. [Secure MCP](labs/06-secure-mcp/README.md)
7. [RAG poisoning](labs/07-rag-poisoning/README.md)
8. [AI-native incident response](labs/08-ai-incident-response/README.md)
9. [Enterprise guardrails](labs/09-enterprise-guardrails/README.md)

## Expected result

Results vary by model, prompt template, and model version. A successful attack means the local model follows an instruction embedded in untrusted content or proposes an unsafe action. A failed attack does not prove the application is secure. Compare the baseline with the guarded design and record the control difference.
