# Instructor Demo 1: Indirect Prompt Injection

**OWASP mapping:** LLM01, LLM06, LLM07, ML01, and ML09. See the [course crosswalk](../../../docs/owasp-threat-mapping.md#lab-crosswalk).

## Demonstrate

Run the same synthetic visa question through a permissive local assistant and a guarded local assistant. The partner note tries to alter the assistant intent.

## Run

1. Start and load the local model from the [instructor setup](../../README.md).
2. Run: docker compose -f compose.instructor.yaml run --rm demo 01
3. Read both model outputs aloud.
4. Ask students which instruction boundary changed.

## Observe

The baseline may claim approval or repeat the embedded instruction. The guarded version should state only the passport rule. Model behavior varies. Treat an unsafe baseline response as a real local failure. Treat a safe response as one data point, not a pass.

## Advanced

Repeat with a second local model. Keep the application prompt unchanged. Compare model behavior with the same vulnerable and guarded boundaries.
