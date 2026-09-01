# Instructor Demo 5: Dual-LLM Guardrails

**OWASP mapping:** LLM02, LLM05, LLM06, LLM07, and ML09. See the [course crosswalk](../../../docs/owasp-threat-mapping.md#lab-crosswalk).

## Demonstrate

Run an application-model draft through a separate reviewer-model call. Both calls use a real local model, but they use separate contexts and duties.

## Run

1. Run: docker compose -f compose.instructor.yaml run --rm demo 05
2. Read the application-model draft.
3. Read the reviewer-model decision.
4. Identify the required deterministic controls outside both models.

## Observe

The reviewer should reject or escalate the request. Account closure, authorization, email delivery, and logging remain normal application controls. A second model is not a replacement for those controls.

## Advanced

Run the application and reviewer calls with different locally approved models. Record disagreement cases and set a safe default for a reviewer outage.
