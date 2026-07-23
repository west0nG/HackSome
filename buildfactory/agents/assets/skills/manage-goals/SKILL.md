---
name: manage-goals
description: Let a Department create, inspect, and cancel its own concrete V7 Goals.
---

# Department Goals

A Goal is a small result that must be achieved and can be independently
verified. It is not a plan, a vague research direction, or a waiting state.

```bash
python3 -m orchestration.control_client create_goal \
  --json '{"intent":"the concrete result","acceptance":"optional private verifier context"}' \
  --request-id 'goal-<stable-purpose-id>'

python3 -m orchestration.control_client list_my_goals

python3 -m orchestration.control_client cancel_goal \
  --json '{"goal_id":"goal-...","reason":"why this work is intentionally withdrawn"}' \
  --request-id 'cancel-<goal-id>'
```

Workers execute Goals. Up to five Worker lifecycles run globally in strict FIFO
order. A started Goal keeps one absolute time limit through all verifier
feedback. There is no blocked/waiting status, attempt limit, supersede, or
replacement relation. If direction changes, explicitly cancel and create an
ordinary new Goal.

Waiting on one avenue is never the Department's only work. Use independent
Goals to advance another useful product, evidence, distribution, or delivery
line when appropriate.
