---
name: manage-objectives
description: Let the CEO propose Company or Department Objective revisions for independent review.
---

# Objectives

An Objective is a durable direction and ownership boundary, not a small task.
Every Company and Department Objective revision must pass an independent
Verifier before it becomes the wake-time Objective.

## Company Objective

Write one coherent direction, grounded in facts already under `/company` or in
traceable external evidence. Make the load-bearing case explicit:

- the concrete buyer or user and the situation that triggers the need;
- what they do today, including manual work, competitors, free alternatives,
  or doing nothing;
- costly behavior showing that the problem matters, rather than interest,
  trends, or the company's ability to build;
- the unresolved gap, why this offer could be chosen, and how the company can
  reach its first real users;
- the smallest real delivery and an observable result that could strengthen,
  weaken, or overturn the direction.

Separate facts, assumptions, and unknowns. One Objective may contain the full
reasoning needed to judge it, but it must still name one direction rather than a
portfolio of unrelated bets. A heartbeat, empty Goal queue, finished Goal, or
new idea is not by itself a reason to revise an active Company Objective.

## Department Objective

A Department Objective defines a durable ownership outcome under the Company
Objective. It must have one direction, fit the Department's recurring function,
be sized for this company, and make observable progress possible within weeks.
It is not a Goal list, a one-off deliverable, or permission to wait. Departments
choose and create their own concrete Goals beneath it.

```bash
python3 -m orchestration.control_client propose_company_objective \
  --json '{"objective":"durable company direction"}' \
  --request-id 'company-objective-<revision-purpose>'

python3 -m orchestration.control_client propose_department_objective \
  --json '{"department_id":"builder","objective":"durable ownership outcome"}' \
  --request-id 'builder-objective-<revision-purpose>'
```

Do not edit an Objective projection directly. A rejected proposal leaves the
currently active Objective unchanged. Do not approve your own proposal; the
global ephemeral Verifier pool performs the independent review.
