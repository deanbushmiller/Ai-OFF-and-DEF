# Instructor Demo 4: MITRE ATLAS Mapping

**OWASP mapping:** LLM01, LLM04, LLM06, LLM08, ML01, ML02, and ML09. See the [course crosswalk](../../../docs/owasp-threat-mapping.md#lab-crosswalk).

## Demonstrate

Use a local model to draft an attack-path explanation. Then verify all terminology against the official MITRE ATLAS matrix.

## Run

1. Run: docker compose -f compose.instructor.yaml run --rm demo 04
2. Copy only the model’s technique names into the ATLAS worksheet.
3. Check every name against the [MITRE ATLAS matrix](https://atlas.mitre.org/).
4. Draw the final path from retrieval content to tool impact.

## Observe

The guarded prompt asks the model to state uncertainty. The model must not create technique identifiers from memory. The instructor makes the final mapping decision.

## Advanced

Map the actual result from Demos 1, 6, and 7. Add an owner, detection source, and prevention control for each path stage.
