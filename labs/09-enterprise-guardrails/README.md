# Lab 9: Enterprise Guardrails

**Time:** 40 minutes  
**Company:** Redwood Retail Group  
**Evidence:** A completed [guardrail policy](../../templates/guardrail-policy.md)
**OWASP mapping:** [LLM01–LLM10, ML06, and ML09](../../docs/owasp-threat-mapping.md#lab-crosswalk)

## Scenario

Redwood plans to release a customer-support assistant in three regions. The assistant retrieves product policies, drafts replies, and can request refunds through a service tool. Leadership wants a deployment design that reduces risk without blocking routine support work.

## Learning outcomes

1. Design layered guardrails for an enterprise AI service.
2. Assign owners and measurable release gates.
3. Balance user value, control strength, and operational cost.

## Guardrail layers

| Layer | Design question |
| --- | --- |
| Identity | Who can use the assistant and the tool? |
| Data | Which data classes may enter prompts and retrieval? |
| Prompt and model | Which instructions and output rules apply? |
| Retrieval | Which sources qualify as authoritative? |
| Tool | Which actions require scope limits or approval? |
| Monitoring | Which events need logs, alerts, and review? |
| Response | Who contains, investigates, and restores service? |
| Release | Which tests must pass before deployment? |

## Safe to share with an LLM

```text
Assistant scope: answer product-policy questions and request refunds.
Constraints: Refunds over $100 need a manager approval. The assistant must cite policy. It must not handle payment-card data. It must log all tool requests. It must block unverified documents from retrieval.

Deployment condition: Three regions, shared platform team, and a 24-hour incident response target.
```

## Steps

1. Complete the guardrail policy template.
2. Select a control for every layer in the table.
3. Define a release gate with evidence, owner, and pass condition.
4. Define a refund-tool policy with amount limits, approval, and rollback.
5. Define two monitoring alerts and an incident owner.
6. Explain one tradeoff between friction and risk reduction.

### ChatGPT prompt

```text
Act as an enterprise AI security architect. Turn this synthetic deployment scope into a layered guardrail plan. Include identity, data, retrieval, tool approval, monitoring, incident response, and release gates. State assumptions clearly.
```

### Claude prompt

```text
Design a practical guardrail policy for this synthetic customer-support assistant. Use layered controls with owners and measurable release gates. Keep refund approvals and payment-card exclusions explicit.
```

## Expected evidence

Your policy places payment-card handling outside the assistant. It cites authorized policies, limits refunds, requires manager approval above the threshold, logs tools, and blocks release until tests pass.

## Advanced challenge

Create a 90-day rollout plan. Divide it into pilot, limited release, and broad release. Add one metric and one exit condition for each phase.

## Instructor notes

Ask students to avoid a single “AI firewall” solution. Effective guardrails span identity, data, retrieval, tools, observability, response, and governance.
