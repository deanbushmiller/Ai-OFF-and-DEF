# Instructor Demo 7: RAG Poisoning

**OWASP mapping:** LLM04, LLM08, LLM09, ML02, and ML10. See the [course crosswalk](../../../docs/owasp-threat-mapping.md#lab-crosswalk).

## Demonstrate

Give a local model two conflicting retrieved documents. One has an owner and review date. The other is anonymous and false.

## Run

1. Run: docker compose -f compose.instructor.yaml run --rm demo 07
2. Compare the baseline and guarded answers.
3. Ask students to identify the provenance data that changed the answer.
4. Define the admission gate for a future uploaded document.

## Observe

The baseline can accept the false document because it receives no trust signal. The guarded model should prefer the named policy and escalate a conflict. Similarity search alone does not establish trust.

## Advanced

Add retrieval metadata to three more synthetic documents. Create a trust score and test the score with current and expired policies.
