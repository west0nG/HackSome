# e2e findings — info-product find-opportunity method (2026-07-02)

Ran `CEO_HEARTBEAT_SECS=45 PUMP_COMPANY=e2e-infoprod docker compose up -d --build`
(empty throwaway company, cold-start, fresh CEO session), watched `docker logs
foundagent-ceo` + the goal ledger, then `docker compose down` + removed the company dir.

## What passed
- **Materialization ✓** — CEO loadout line: `skills=['send-goal', 'find-opportunity', 'decide-direction']`. The new `references/*.md` reach the container via the `./agents:/opt/foundagent-orch/agents:ro` bind mount (no rebuild needed). Also confirmed offline by loadout unit tests (11 passed).
- **Cold-start trigger ✓** — empty company (`companies/e2e-infoprod`, MAP.md auto-created). CEO first heartbeat: `start heartbeat=45s session=(new)` → `woke … ok` → dispatched a research goal. It did NOT say "nothing to do" — recognized "no direction → find-opportunity". (The earlier `295a11d` charter fix holds.)
- **Business-form aware, info-product ✓** — CEO turn: *"We are evaluating whether to build an **info product** (guide, template, or ebook) for freelancers and solopreneurs."*
- **Signal-first, no fabrication ✓** — dispatched a research Goal FIRST (`84db48cf`), stating it would find recurring pains with payment evidence and generate 2-3 candidates for `decide-direction` once the corpus returns.
- **⭐ Read and followed the NEW father method ✓ (the core incremental claim)** — the dispatched Goal precisely mirrors `finding-info-product-opportunities.md`, with details unique to the new file (absent from the skeleton and from the prior find-idea run's goal `bf5806cb`):
  - **Step 1 readability gate:** *"confirm it is publicly readable without a login. If fewer than 2 are active AND publicly readable, say so and stop — we cannot observe this market."*
  - **Step 2 verbatim harvest:** *"collect 40-60 VERBATIM quotes … exact words, source URL, and the community … Do NOT summarize or interpret — the raw words are the deliverable."*
  - **Step 3 trigger words:** *"'I hate', 'I wish', 'finally', 'annoying', 'I always have to', 'why is there no', 'is there a tool for'"*.

## What was not reached live (and why it's fine)
- **Platform child files (steps 4–5, marketplace payment on Gumroad/KDP/Etsy)** were not exercised. They sit later in the pipeline — the CEO correctly front-loads signal-gathering (steps 1–3) and only proves payment / picks a platform *after* the corpus returns. In this test the `researcher` never returns a corpus (its web research times out in this environment — the ledger shows prior researcher goals `timed out (no progress before deadline)`), so the CEO stays at "research goal still in flight — nothing to act on" across subsequent wakes. This is a `researcher`/environment limitation, not a skill defect. Platform-file reading is logically gated on step 4, which is gated on researcher completion.

## Verdict
AC8 substantially verified: the new father reference is read and drives correct, method-faithful behavior on a cold-start empty company. The platform-child branch is verified by structure/routing (AC9) and by the father's explicit routing (step 4 → "open that platform's file"); exercising it live would require a `researcher` that completes real web research — track as a separate live-loop check when the researcher path is hardened.

## Cleanup
Stack down, `companies/e2e-infoprod` removed, no containers left running. The test goal `84db48cf` remains in the shared ledger/inbox (consistent with prior e2e runs that left goals like `bf5806cb`); shared-state hand-editing was avoided to not disturb the hub state machine.
