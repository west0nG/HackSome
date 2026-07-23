---
name: submit-work
description: Declare the current one-Goal Worker's real work complete so an independent Verifier can inspect and judge the actual outcome.
---

# Declare Worker completion

Complete only the Goal in your turn. When you believe the real work is done,
declare completion without supplying a summary, evidence list, path, URL, or
other result content:

```bash
python3 -m orchestration.control_client submit_result \
  --request-id 'result-<goal-id>-<meaningful-revision>'
```

When a Verifier FAIL resumes you, correct the real work and declare completion again.

