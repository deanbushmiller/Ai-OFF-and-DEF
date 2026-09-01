# Instructor Demo 6: Secure MCP

**OWASP mapping:** LLM01, LLM05, LLM06, ML01, ML09, MCP02, MCP03, MCP06, MCP07, MCP08, and MCP10. See the [MCP crosswalk](../../../docs/owasp-threat-mapping.md#lab-6-mcp-crosswalk).

## Demonstrate

Show a local model proposing a mock tool action after it reads a poisoned ticket note. The runner does not execute the proposed action. It prints the model’s proposed action for review.

## Run

1. Run: docker compose -f compose.instructor.yaml run --rm demo 06
2. Compare the proposed action from the baseline and guarded prompts.
3. Explain why an application must validate the user, tool, argument schema, scope, approval, and audit record before a tool call.

## Observe

The baseline may propose update_ticket even though the user requested a read. The guarded version should propose only a validated read. This is a real local model response within a simulated tool boundary.

## Advanced

Connect an MCP Inspector to a local, read-only MCP server. Keep update tools disabled. Use the inspector to show tool schemas, authorization metadata, and audit fields before enabling any write tool.
