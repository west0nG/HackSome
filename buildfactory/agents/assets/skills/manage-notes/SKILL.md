---
name: manage-notes
description: Read or replace this resident Agent's private lightweight cross-wake note.
---

# Notes

Your current Note is injected into each wake. It is private to this resident
Agent and is not Company State.

```bash
python3 -m orchestration.control_client read_notes
python3 -m orchestration.control_client write_notes \
  --json '{"text":"short context for my next wake"}' \
  --request-id 'notes-<stable-purpose-id>'
```

Use Notes only for lightweight continuity. Facts, decisions, evidence, and
deliverables that the company must retain belong under `/company`.
