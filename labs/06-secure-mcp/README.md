# Lab 6: Secure MCP

**Time:** 35 minutes  
**Company:** CityWorks Support  
**Evidence:** An MCP control checklist and finding record
**OWASP mapping:** [LLM01, LLM05, LLM06, ML01, ML09, and MCP02/MCP03/MCP06/MCP07/MCP08/MCP10](../../docs/owasp-threat-mapping.md#lab-6-mcp-crosswalk)

## Scenario

CityWorks connects an assistant to an MCP helpdesk server. The server exposes `search_ticket`, `read_ticket`, and `update_ticket` tools. The first design gives every user access to every tool and accepts a free-text ticket identifier.

## Learning outcomes

1. Identify security boundaries for MCP tools.
2. Apply least privilege and explicit approval.
3. Define audit records for an AI tool call.

## Safe to share with an LLM

```text
Tools:
- search_ticket(query): read-only search of synthetic tickets
- read_ticket(ticket_id): reads one synthetic ticket
- update_ticket(ticket_id, status): changes a synthetic ticket

Current rules:
- Any authenticated user may call every tool.
- The assistant selects tool arguments from free text.
- update_ticket has no human approval.
- Logs record only “tool succeeded.”
```

## Steps

1. Draw trust boundaries among user, assistant, MCP client, server, and ticket system.
2. Assign an allowed role and data scope to each tool.
3. Require schema validation for every tool argument.
4. Add explicit human approval for `update_ticket`.
5. Define an audit event with user, tool, argument summary, authorization decision, approval, result, and trace ID.
6. Record the highest-risk design flaw.

### ChatGPT prompt

```text
Act as an MCP security architect. Review this synthetic tool server. Produce a least-privilege table with role, allowed tool, parameter constraints, approval need, and audit fields. Do not provide exploitation steps.
```

### Claude prompt

```text
Review this synthetic MCP server for secure tool use. Focus on authorization, input validation, human approval, and logs. Return a control checklist and identify the highest-risk missing control.
```

## Expected evidence

Your control list separates read and update capabilities. It rejects free-form identifiers when a structured ticket ID is required. It requires approval before an update and records a full audit event.

## Advanced challenge

Define an approval policy for a bulk update. Include a maximum change count, a dry-run preview, an approver role, and a rollback record.

## Instructor notes

MCP is a protocol boundary, not a security boundary by itself. Tool servers need normal application security controls plus AI-specific context and approval controls.
