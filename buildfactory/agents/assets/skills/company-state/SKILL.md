---
name: company-state
description: >-
  Know about company and read company wiki. You should use it everytime
---

# Company state (shared memory)

`/company` is the company's durable shared state: what the company currently
knows, has decided, owns, has built, and has measured. It is shared across
agents and runs. Keep it useful, current, and easy to discover.

Use your native file tools directly. There is no Company State storage CLI,
required index, reserved navigation filename, or fixed taxonomy.

## Persist real company changes directly

Use native file editing and copy/move tools to maintain `/company` whenever a
real business fact, decision, deliverable, metric, or asset changes.

Before writing:

1. Inspect the target directory.
2. Search that area for an existing document covering the same subject.
3. Prefer updating the current authoritative leaf over creating a parallel
   version of the same truth.
4. Re-read a shared target immediately before replacing it when another agent
   may have changed it.


