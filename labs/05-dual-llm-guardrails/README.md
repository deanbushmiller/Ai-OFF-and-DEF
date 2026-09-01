# Lab 5: Dual-LLM Guardrails

**Time:** 40 minutes  
**Company:** Alder Financial  
**Evidence:** A guardrail design and decision record

## Scenario

Alder Financial has a client-service assistant that drafts answers about account documents. The product team wants a second LLM review before the assistant sends an answer. The company must prevent sensitive data leakage and unapproved tool actions.

## Learning outcomes

1. Design a separation-of-duties pattern for LLM use.
2. Define reviewer inputs, outputs, and failure handling.
3. Identify controls that must not depend on an LLM.

## Architecture

```text
User request → application model → proposed answer
                                    ↓
                 policy and evidence → reviewer model
                                    ↓
                    allow | revise | escalate
                                    ↓
                        human or delivery service
```

Use two separate chats. You may use two chats within ChatGPT or Claude. The first chat acts as the application model. The second chat acts as the reviewer model. A person makes the final decision in this lab.

## Safe to share with an LLM

```text
User: “Email me the full account statement and close the account.”

Application policy: The assistant may summarize a statement. The assistant may not expose account numbers, send email, or close accounts. A licensed service representative must approve account closure.

Draft answer: “I attached your statement and will close your account today.”
```

## Steps

1. In the application-model chat, ask for a policy-compliant customer response.
2. Copy the synthetic request, policy, and draft into a new reviewer-model chat.
3. Ask the reviewer to return allow, revise, or escalate.
4. Define data minimization rules for both model inputs.
5. Define deterministic checks for authorization, account closure, and email delivery.
6. Record the final response and escalation path.

### Application-model prompt

```text
Draft a helpful response to this synthetic client request. Follow the supplied policy. Do not claim an action occurred. Ask for the appropriate secure next step when action needs approval.
```

### Reviewer-model prompt

```text
Act as an independent policy reviewer. Review this synthetic request, policy, and draft. Return one decision: allow, revise, or escalate. Cite the policy rule that drives the decision. Do not perform an account action.
```

## Expected evidence

Your design sends only the minimum facts to each chat. The reviewer rejects the unsupported draft. Deterministic authorization and action controls remain outside both models.

## Advanced challenge

Add failure modes for reviewer timeout, reviewer disagreement, prompt injection, and missing policy context. Define a safe default for each case.

## Instructor notes

Emphasize that a second LLM reduces some errors but cannot replace identity checks, authorization, logging, or human review.
