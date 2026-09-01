# Instructor Demo 8: AI-Native Incident Response

**OWASP mapping:** LLM01, LLM05, LLM10, ML01, and ML09. See the [course crosswalk](../../../docs/owasp-threat-mapping.md#lab-crosswalk).

## Demonstrate

Put a harmless instruction inside synthetic incident logs. Compare a permissive analyst-model response with a model that treats logs as evidence, not instructions.

## Run

1. Run: docker compose -f compose.instructor.yaml run --rm demo 08
2. Ask students to extract the timeline from both outputs.
3. Separate observed facts from hypotheses.
4. Select a reversible containment action.

## Observe

The embedded instruction asks the model to close the alert. The guarded prompt should ignore it and preserve the relevant evidence. An LLM must not close incidents or make containment decisions without an approved workflow.

## Advanced

Add a second benign alert to the log. Define correlation rules that distinguish a confirmed incident from a suspicious event.
