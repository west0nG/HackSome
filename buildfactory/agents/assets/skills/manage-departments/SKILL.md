---
name: manage-departments
description: Let the CEO inspect public Department options and create a needed Department.
---

# Department organization

List the available fixed options:

```bash
python3 -m orchestration.control_client list_department_options
```

The result intentionally contains only option ID, public name, and description.
Choose based on the recurring responsibility the company needs; do not ask for
or infer template internals.

Create one Department with its first Objective:

```bash
python3 -m orchestration.control_client create_department \
  --json '{"option_id":"researcher","initial_objective":"the long-lived ownership outcome"}' \
  --request-id 'create-department-researcher'
```

The Objective is independently verified before any Department container exists.
Each of `strategist`, `researcher`, `builder`, and `growth` can exist at most
once. V7 has no retire, delete, merge, recreate, or draining operation.

`inspect` is deliberately not a default heartbeat ritual. Use it only for a
fact conflict, abnormal state, consequential trade-off, or explicit need to
verify orchestration facts:

```bash
python3 -m orchestration.control_client inspect
python3 -m orchestration.control_client inspect --json '{"department_id":"builder"}'
python3 -m orchestration.control_client inspect --json '{"goal_id":"goal-..."}'
```
