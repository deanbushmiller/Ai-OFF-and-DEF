# Instructor Guide

## Before class

1. Confirm that students received the repository link.
2. Ask students to install Docker Desktop before class.
3. Ask students to sign in to ChatGPT or Claude before class.
4. Run the Docker smoke test on one Mac and one Windows computer.
5. Tell students that completion matters more than LLM output style.

## Opening script

State that the labs simulate enterprise AI risks with local, synthetic assets. State that students may not test real systems. State that the LLM helps analyze evidence but does not make security decisions.

## Instructor demonstration flow

Use the local-model demonstration before each matching student lab when time and hardware permit. The demonstration replaces the scenario introduction. It does not add time to the student lab.

1. Name the mapped OWASP threat.
2. Run the baseline local-model demonstration.
3. Run the guarded local-model demonstration.
4. Ask students what changed at the application boundary.
5. Start the matching student lab.

See [instructor demonstrations](../instructor-demos/README.md) and the [OWASP threat mapping](owasp-threat-mapping.md). Do not run a demonstration against a vendor model, an external tool server, or a real data source.

## Facilitation pattern

For each lab, use this pattern:

1. Present the company scenario and business impact.
2. Give students the core time box.
3. Ask students to inspect local evidence before opening an LLM chat.
4. Ask students to save a short finding record.
5. Debrief the mitigation and deployment tradeoff.

## Provider differences

ChatGPT and Claude may refuse, format, or reason differently. Accept any answer that cites the scenario, follows the safety policy, and produces a sound mitigation. Do not require identical wording.

## Completion check

A student completes a lab when the student saves the listed evidence and can explain a mitigation. Do not assign a numeric grade. Use the [completion checklist](../templates/completion-checklist.md).

## Common issues

| Issue | Instructor response |
| --- | --- |
| Docker does not start | Let the student use the Markdown-only path. |
| LLM refuses a prompt | Ask the student to use the safer alternative prompt. |
| Student uses a real artifact | Stop the work and replace it with the supplied file. |
| Student finishes early | Assign the advanced challenge. |
| Student gets a false LLM claim | Ask for a local source citation. |

## Debrief questions

1. What evidence changed your decision?
2. Which control reduces risk at the lowest operational cost?
3. Where could the guardrail fail?
4. What needs a human approval step?
