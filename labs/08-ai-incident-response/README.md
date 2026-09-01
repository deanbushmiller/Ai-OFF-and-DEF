# Lab 8: AI-Native Incident Response

**Time:** 40 minutes  
**Company:** Summit Logistics  
**Evidence:** A completed [incident record](../../templates/incident-record.md)

## Scenario

Summit Logistics operates an AI dispatch assistant. Monitoring shows a burst of retrieval requests, several tool requests outside normal hours, and an attempted dispatch change. The logs are synthetic. The incident commander needs an evidence-backed containment plan.

## Safe to share with an LLM

```text
09:10 user=planner-17 action=retrieve_docs count=4 result=success
09:12 user=planner-17 action=retrieve_docs count=93 result=success
09:14 user=planner-17 action=tool_request tool=change_dispatch result=approval_required
09:15 user=planner-17 action=tool_request tool=change_dispatch result=denied
09:16 system action=policy_alert rule=unusual_retrieval_volume severity=high
09:19 manager action=confirm user=planner-17 status=on_leave
```

## Learning outcomes

1. Triage AI-specific signals with normal incident-response discipline.
2. Use an LLM to organize evidence without delegating the decision.
3. Define containment, recovery, and follow-up controls.

## Steps

1. Build a timeline from the log entries.
2. Separate facts, assumptions, and unanswered questions.
3. Ask the LLM to propose hypotheses and evidence gaps.
4. Choose a containment action that preserves evidence and limits further tool use.
5. Define recovery checks before restoring access.
6. Document an after-action control for detection or prevention.

### ChatGPT prompt

```text
Act as an incident-analysis assistant. Analyze only this synthetic log. Separate observed facts from hypotheses. Suggest evidence-preserving containment options and questions for the incident commander. Do not make the final decision.
```

### Claude prompt

```text
Help an incident commander triage this synthetic AI-assistant alert. Produce a timeline, facts, hypotheses, evidence gaps, and reversible containment options. Do not state that an attacker is confirmed.
```

## Expected evidence

Your record notes the account holder was on leave and that the attempted change was denied. It proposes a reversible account or session containment step, preserves logs, and requires credential and authorization review before restoration.

## Advanced challenge

Write a playbook trigger for unusual retrieval volume. Include baseline, threshold, severity, owner, automatic action, human review, and rollback conditions.

## Instructor notes

The exercise teaches evidence discipline. Do not accept “the LLM says it is an attack” as a conclusion. The denial event lowers impact but does not close the investigation.
