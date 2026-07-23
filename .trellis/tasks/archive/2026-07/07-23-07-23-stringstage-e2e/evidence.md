# StringStage E2E Evidence

## Inputs

- Team: `stringstage-e2e`
- Challenge: `challenge.md` in this task
- Initializer: user-supplied StringStage Idea Card
- Initial `/project`: exactly
  `reference/challenge.md` and `reference/initial-idea-card.md`

No credential values are recorded here.

## Runtime path

1. Hub, resident Lead, Worker Manager, and Verifier Manager started successfully.
2. E2E exposed that the original Lead Prompt explicitly permitted direct product
   work. The Lead was stopped, the Prompt was corrected to preserve broad
   permissions while assigning all substantive execution to Workers, and the
   Team state was reinitialized from the two references.
3. Corrected Lead created Goal `goal-3e6b1d51bce004bb`; `worker-1` claimed it.
4. Worker built a real local StringStage React/Vite application in `/project`,
   including multilingual sample data, four synthetic UI surfaces, deterministic
   LQA, import/export, focused tests, a production build, README, and browser
   verification.
5. Reducing heartbeat to 60 seconds exposed a second issue: Lead woke while the
   Goal was active and added three queued Goals. Those pre-gate Goals were
   explicitly cancelled by the operator.
6. Runtime wake gating was added. With the Goal still `running`, the resident
   Lead logged `wake suppressed by gate`; no Lead model process ran and no new
   Goal was created.
7. Worker submitted
   `result-goal-3e6b1d51bce004bb-complete-slice-v1`.
8. Fresh read-only `verifier-1-1` reviewed
   `review-dcd6e0c8f0cdfbaf` and submitted `PASS`.
9. Goal became `done`, Worker and Verifier containers were removed, and the
   empty batch immediately woke Lead through `goal_batch_drained`.

## Independent verifier evidence

The Verifier reported:

- all 11 focused LQA/import/export tests passed;
- the production build passed;
- the production bundle loaded without console errors or external requests;
- five named language contexts and all four required preview types were visible;
- the German broken-placeholder/overflow scenario produced three grounded
  findings and recomputed to zero after the observed fix;
- manual surface override, dismissal, valid CSV import, malformed JSON handling,
  corrected-string export, and unresolved-clarification export worked;
- the README contained install, development, test, build, preview, offline, and
  3–5 minute walkthrough instructions;
- both reference files remained present.

## Wake invariant verified

```text
any non-terminal Goal
  -> heartbeat checks state
  -> Lead model wake is suppressed

all Goals done/cancelled
  -> goal_batch_drained
  -> Lead model wakes immediately
```

The 60-second heartbeat is now only an empty-queue fallback; it does not run
Lead while a Worker or Verifier owns unfinished work.
