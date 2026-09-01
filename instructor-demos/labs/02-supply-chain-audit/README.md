# Instructor Demo 2: Supply-Chain Audit

**OWASP mapping:** LLM03, LLM05, ML06, and ML10. See the [course crosswalk](../../../docs/owasp-threat-mapping.md#lab-crosswalk).

## Demonstrate

Run a local scanner against the included unsafe loader. Then show how a permissive model might approve a useful-looking bundle without supply-chain evidence.

## Run

1. Run: docker compose run --rm scanner
2. Confirm that the scanner flags pickle.load in the supplied sample.
3. Run: docker compose -f compose.instructor.yaml run --rm demo 02
4. Compare the baseline and guarded release decisions.

## Observe

The scanner finding identifies unsafe deserialization. The release gate also needs provenance, signatures, hashes, dependency review, an SBOM, and a model card. Do not execute the sample loader or any downloaded model artifact.

## Advanced

Create a CycloneDX SBOM for a trusted local demonstration project. Compare its evidence to the missing evidence in the scenario.
