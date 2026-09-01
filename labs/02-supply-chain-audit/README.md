# Lab 2: AI Supply-Chain Audit

**Time:** 40 minutes  
**Company:** Harbor Claims  
**Evidence:** A completed [finding record](../../templates/finding-record.md)

## Scenario

Harbor Claims plans to deploy a third-party document classifier. The vendor bundle includes a model file, a Python loader, a dependency list, and a model card. The release owner cannot show a checksum, signed provenance, or a software bill of materials.

## Learning outcomes

1. Inventory AI artifacts and dependencies.
2. Run a local scanner against a harmless example.
3. Decide whether a release meets a deployment gate.

## Safe to share with an LLM

```text
Release evidence:
- model.bin: downloaded from an unverified mirror
- loader.py: uses pickle.load(model_file)
- requirements.txt: requests==2.19.0
- model-card.md: author and training data are not listed
- release notes: no checksum, signature, SBOM, or security contact
```

## Steps

1. Inventory the model, code, package, metadata, and release source.
2. Run the included local scanner command: `docker compose run --rm scanner`.
3. Read each scanner finding and confirm it against the supplied source file.
4. Classify each issue as provenance, code safety, dependency, or governance.
5. Set a release decision: approve, approve with conditions, or block.
6. Write the minimum evidence required before release.

### ChatGPT prompt

```text
Act as a software supply-chain reviewer. Analyze this synthetic release evidence. Do not suggest executing model files. Create a release-gate table with risk, evidence, decision, and required remediation.
```

### Claude prompt

```text
Review this synthetic AI vendor bundle as a release approver. Do not execute any artifact. Separate provenance, dependency, unsafe loading, and documentation gaps. Recommend a release decision with required proof.
```

## Expected evidence

Your finding identifies unsafe deserialization as a code risk. It blocks release until the team verifies source, hash, signature, SBOM, dependency status, and model documentation.

## Advanced challenge

Draft an intake questionnaire for a model vendor. Include artifact source, signing, training-data claims, vulnerability response, license, and update policy.

## Instructor notes

The scanner supports discovery. It does not prove a file is safe. Students must confirm scanner output against source and define an approval gate.
