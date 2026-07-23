# Local Agent Workflow Contracts

## Scenario: Codex stage execution, artifact publication, and resume

### 1. Scope / Trigger

Use these contracts whenever a stage, review loop, CLI option, artifact type, or
Codex invocation is added or changed. They cover the boundary from the CLI to
`UsefulIdeaWorkflow`, from a workflow task to `CodexRunner`, and from staged
model output to durable run state.

The controller owns routing. Model prose may explain a decision, but only
validated JSON fields or YAML front matter may change the next stage. Candidate
collections are quality-gated sets: do not add Top-K selection, semantic
deduplication, or direction quotas.

### 2. Signatures

Public CLI commands:

```text
hacksome run [CHALLENGE_FILE] [--prompt TEXT] [runtime options]
hacksome resume RUN_DIR [runtime overrides]
hacksome status RUN_DIR [--json]
hacksome validate RUN_DIR
hacksome doctor [--json]
```

Core Python boundaries:

```python
UsefulIdeaWorkflow.create(
    prompt: str,
    runs_dir: str | Path,
    *,
    settings: WorkflowSettings | None = None,
    codex_config: CodexConfig | None = None,
    runner: CodexRunner | None = None,
    prompt_renderer: PromptRenderer | None = None,
    run_id: str | None = None,
) -> UsefulIdeaWorkflow

await UsefulIdeaWorkflow.execute() -> Path  # idea-report.md
await CodexRunner.run(task: CodexTask) -> CodexResult
ArtifactStore.promote(request: PromotionRequest) -> PublishedArtifact
ArtifactStore.promote_many(
    requests: Iterable[PromotionRequest],
) -> tuple[PublishedArtifact, ...]
StateStore.save(state: RunState) -> RunState
validate_run(run_dir: str | Path) -> list[str]

# Internal S4 -> S5 provenance projection
UsefulIdeaWorkflow._derive_problem_evidence_refs(
    *,
    problem_ref: str,
    audience_id: str,
    research_refs: Sequence[str],
    verification_refs: Sequence[str],
) -> tuple[str, ...]

# Durable workflow-owned run data
RunState.data["workflow_topology_version"]: Literal[1, 2]
RunState.data["draft_screen_policy_version"]: Literal[1, 2, 3]
```

`CodexTask.resume=True` requires the exact `session_id`; never implement an
implicit "resume last session" path.

### 3. Contracts

#### Run directory

Every run persists:

```text
challenge.md               immutable raw input
state.json                  atomic current state with state_revision
events.jsonl                append-only, idempotent operational events
decisions.jsonl             append-only, idempotent product decisions
.staging/<task-id>/          isolated task inputs, output, and logs
revisions/...               immutable Living Document snapshots
idea-report.md              deterministic S11 output
```

`state.json` must bind `challenge.md`, `idea-report.md`, copied context, and
completed task outputs by SHA-256. A completed task is skippable only after its
saved identity, canonical path, metadata, structured projection, and content
hash validate.

New runs persist `workflow_topology_version: 2`. When loading older state
without this field, infer and persist v1 if any S7, S8, S9, or S10 task exists
in any status; infer v2 only when no such task exists. An explicit valid value
never changes. Invalid values, including booleans and floats, fail before
orchestration. This keeps old partial runs on their original topology while an
S0-S6-only run can safely adopt the early draft screen.

New topology-v2 runs also persist `draft_screen_policy_version: 3`. A
topology-v2 run missing this field infers and persists the newest supported
policy for which any draft-screen task, artifact, or final reference already
exists in any status; otherwise it adopts current policy 3. Explicit policy
selection wins over inference, while null, booleans, floats, strings, and
unsupported integers fail before orchestration. Moving an interrupted run to a
newer policy is an explicit migration performed only after the old orchestrator
stops: completed older-policy tasks and artifacts remain immutable historical
records, incomplete obsolete draft-screen tasks become `cancelled` with no
`next_action`, and every Idea receives a new independent current-policy task,
session, context, and output file. Historical validation accepts all supported
policies, but current routing, `final_ideas`, and S11 must use the run-selected
policy.

#### Codex task

`CodexTask` requires a non-empty prompt, a safe stable task ID, an isolated
working directory, and an output schema. `web_search=True` is allowed only for
the research stages configured by the workflow. Subprocess arguments must be
passed as an array and prompt text over stdin. Stage sessions disable project
instructions, hooks, apps, goals, nested agents, browser/computer tools, and
unneeded web access. They also pass `--disable plugins` and
`skills.include_instructions=false`; `project_doc_max_bytes=0` alone does not
remove plugin- or skill-injected context. Because Codex still loads a non-empty
`AGENTS.override.md` or `AGENTS.md` from the effective `CODEX_HOME`, the runner
must reject that ambient state before spawn. It must not silently switch homes
or copy file-backed authentication credentials. Saved or injected Codex
configurations that omit any mandatory disabled feature, config override, or
isolation control also fail preflight; legacy state is never silently resumed
with a weaker execution boundary.

Codex `--output-schema` accepts only the server/model structured-output subset,
not arbitrary JSON Schema. Packaged schemas must not use known rejected
keywords such as `uniqueItems`. The runner parses and checks a schema before
spawning Codex, validates the schema itself as Draft 2020-12, and validates the
returned JSON instance locally before accepting a successful process exit.
Semantic constraints omitted from the wire schema (for example unique S1
aliases and unique completion paths) remain controller-side validation.

Infrastructure retry may resume the same explicit session once. New research,
verification, writer, Gateway, Red Team, or feasibility work starts a new
logical task and therefore a new session.

A transient JSONL `error` such as a reconnect notice is not the final task
result when the same attempt later emits `turn.completed`. The completed turn
is authoritative unless a later terminal failure event occurs. Invalid request,
invalid schema, unsupported parameter, and context-length failures are
non-retryable because resuming the same session cannot repair the request.

#### Artifact publication

Long outputs are Markdown with unique YAML keys and a stage-specific fixed
heading schema. `PromotionRequest.expected_metadata` is mandatory and must
fully bind the task identity. `source_refs` must be allow-listed, safe relative
paths inside the run, and consistent with routing metadata.

Agents write only to their task staging directory. The controller validates
and atomically promotes output. Immutable canonical artifacts cannot be
overwritten. A Living Document replacement must increment its revision,
preserve stable lineage fields, and snapshot the previous revision first.

Before promotion the task journal records the staged paths, exact content
hashes, routing metadata, session, and `publication_prepared=true`. On resume,
if canonical output is missing but every staged byte still matches that journal,
the controller revalidates and replays publication without another model call.
If canonical output already matches, it only finishes the task state. Changed,
missing, or invalid staged bytes must never be replayed.

Deterministic JSON or artifact validation failures consume the configured
format-correction budget durably. Before another same-session correction, the
task stores the consumed count, prior validation error, session id, and attempt
usage. Resume continues the remaining budget and correction context; it never
grants a fresh budget or loses already consumed attempts. Prepared-publication
recovery clears that transient correction state without counting attempts twice.

Topology-v2 `draft_screen` S9 front matter additionally binds
`reviewed_idea_revision` (a positive integer) and `reviewed_idea_sha256` (a
lowercase SHA-256). These fields are forbidden on later S9 modes. Before S7,
on every resume, during S11, and in `validate_run`, the controller resolves the
binding to the exact S6 Idea bytes: the current canonical file before S8, or
the immutable `revisions/.../revision-NNNN.md` snapshot after S8 advances the
Living Document. Missing or changed bytes are integrity failures, not product
decisions. Its versioned `red_team_id`, output filename, stable task identity,
and routing manifest must all encode the same selected policy; a new policy
cannot reuse an earlier task, session, result, or review context.

S4 and S6 fan-out may publish a same-directory batch atomically; independent
agents must not concurrently edit one canonical file.

#### Workflow behavior

- Keep all ready candidates in the fan-out, but acquire the same persisted
  `CodexConfig.max_concurrency` slot before copying task context or mutating task
  state. Hold it through the concrete Codex call, then release it before the
  branch's next stage. This bounds preparation, state serialization, and model
  execution without capping candidates or wrapping an entire S7-S10 branch.
- Keep every candidate that passes the same absolute gate, including similar
  candidates; zero candidates is valid and still produces a report.
- S1 treats the full `DiscoveryView`, including `explicit_audiences`, as clues,
  not mandatory outputs. It emits only natural groups with an independently
  explained direct tie to the challenge theme or `problem_domains`; roles named
  only as participants, judges, organizers, submission or Q&A actors, Sponsors,
  evidence authors, or public-data sources are excluded. When a named person
  also has a genuine domain role, S1 names that role instead. This remains a
  prompt contract: the controller adds no keyword filter, quota, Top-K, or
  forced-diversity rule.
- S5 permits at most one targeted evidence loop and one blind confirmation of
  a rejection. Its T1 check also reads `DiscoveryView` and rejects a Problem
  outside the challenge theme/problem domains; this is relevance validation,
  not Sponsor-technology or submission compliance.
- The S4 Problem body's `Evidence` and `Counterevidence and Uncertainty`
  sections, not front-matter `source_refs` alone, define S5's evidence packet.
  Every cited item binds a canonical Research path, local Evidence id, and one
  or more canonical Verification paths. The controller accepts only full files
  from the current same-Audience allowlist that are also present in the
  Problem's `source_refs`; copied context, staging, excerpt, unknown,
  cross-Audience, and unpaired paths fail instead of widening to the full
  corpus. Within one citation line, pair Verification files to cited Research
  items by each Verification's canonical `research_ref`, not by token order;
  coalesce repeated mentions of the same Research/local-id pair. Every cited
  Research/local-id still needs a matching Verification on that line, and a
  Verification that matches none of the line's Research refs is invalid. If
  verifier-001 requested blind recheck of a cited id, the citation must include
  verifier-002 and its `Evidence Checks` must cover that id. The subset is
  recomputed after every S4 revision, shared unchanged by primary and blind
  Gateways, and persisted as `PassedProblem.evidence_refs` for all downstream
  stages. This projection changes context size, never candidate count: it adds
  no ranking, quota, deduplication, or forced diversity.
- A completed S5 stage is a durable checkpoint. Resume reconstructs passed
  Problems from completed, hash-bound Gateway task outputs and their historical
  `source_refs`, while also requiring every current Problem to have exactly one
  terminal pass or S5 elimination. It does not reinterpret already-decided
  Problems with a newer body-citation parser. The strict citation projection
  still applies to every new or incomplete S5 decision. Only `pass` from a
  primary `initial` or `post_evidence` Gateway is terminal; a pass from
  `blind_rejection_confirmation` means the reviewers disagreed. Replayed S5
  eliminations must have their exact stable identity, occur once, match the
  append-only decision ledger, and cite completed hash-bound Gateways for the
  same Problem.
- In S3, `routing.assigned_recheck_evidence_ids` is blind-review input scope.
  Artifact front matter `recheck_evidence_ids` is the verifier's output
  decision. Never manifest-bind the output field to the input list: a first
  verifier may derive a non-empty list, while the blind second verifier must
  output `needs_second_verifier: false` and `recheck_evidence_ids: []`.
- In topology v2, every S6 Idea first receives one independent S9
  `draft_screen` task at
  `idea-reviews/<idea-lineage>/draft-screen-<policy>.md`, currently
  `draft-screen-003.md` for new runs.
  It reads only the exact S6 revision, passed Problem/Gateway, and necessary
  verified evidence. It checks felt value, a complete real User Flow, causal
  delivery without hidden humans/fake data/magic, and Problem fidelity.
  The Idea's own claims about inputs, integrations, permissions, state changes,
  or outputs are hypotheses to attack, not proof. The reviewer must distinguish
  producing an artifact from delivering the passed Problem's user value: a
  ticket, report, request, alert, export, or post is insufficient when relief
  still depends on an uncontrolled third party. Productizing an observed
  workaround is not automatically Problem fidelity, and naming an API,
  internal manifest, hook, rollback, or state mutation does not prove access or
  authority. Missing control over a core dependency is product-invalid; it is
  `repairable` only when one bounded local correction preserves the core
  trigger, output, mechanism, felt-value moment, target user, and Problem.
  Authorized enterprise/customer-owned inputs and first-party capabilities may
  be legitimate; this screen must not import a separate public-data or
  challenge-compliance judgment.
  Policy 3 additionally derives the target user's primary blocked state from
  the passed Problem, then compares it with the immediate state change produced
  by the Idea's declared Trigger -> primary output/action -> felt-value moment.
  Observed consequences may make the same native judgment/action concrete, but
  Current Workarounds, optional fields, secondary audiences, and reviewer-
  invented uses cannot redefine it. Under the no-handoff counterfactual, if no
  uncontrolled third party ever reads, responds, or acts, the primary output
  must still materially advance that same blocked state. Reformatting facts the
  user already supplied or handing them to another actor is not by itself such
  a state change. Partial solutions remain valid when they immediately advance
  the same native outcome; useful downstream/reporting tools that change the
  outcome are invalid for that Problem branch.
  Adoption/alternatives is explicitly deferred until S7 evidence exists;
  similarity is never a failure. Only `invalid` records
  `draft-product-invalid` and stops that Idea before S7. Both `pass` and
  `repairable` continue without editing the Idea or consuming the later product
  repair budget. A failed execution leaves the run resumable and never creates
  an elimination.
- Later S7 -> S8 -> full fresh S9 behavior is unchanged. Later S8/S9 contexts
  never include the draft-screen review. Full S9 keeps `red-team-001.md` and
  later numbering, its one product-repair budget, and independent sessions.
  S10 permits at most one scope reduction, followed by fresh S9 and S10
  sessions.
- Compliance context may shape S8, but there is no separate compliance gate.
- S11 is deterministic rendering and hard-field validation, not another model
  session. `FinalIdea.draft_screen_ref` is required for topology v2 and null for
  topology v1; report review refs contain the draft screen when present, the
  final passed full S9 review, and S10.

### 4. Validation & Error Matrix

| Condition | Required result |
|---|---|
| Empty challenge or invalid runtime limits | Reject before creating/running a task |
| Missing Codex executable or authentication | `doctor` is unhealthy; task is not started |
| Effective `CODEX_HOME` contains non-empty global AGENTS instructions | `doctor` is unhealthy and tasks fail preflight before spawn |
| Saved Codex config omits a mandatory feature disable, config override, or isolation control | `doctor` is unhealthy and resume fails before task spawn |
| Task timeout | Terminate the process group; record `timed_out`; allow only the configured infrastructure retry |
| Output schema contains a known unsupported keyword | Reject in runner preflight before spawning Codex |
| Output schema is invalid Draft 2020-12, or the returned last message does not satisfy it | Reject locally; never accept process exit alone as success |
| Codex returns `invalid_request_error`, `invalid_json_schema`, unsupported parameter, or context-length failure | Mark non-retryable; do not resume the session |
| A transient reconnect error is followed by `turn.completed` | Accept the completed attempt and do not issue a runner retry |
| Invalid JSON/completion envelope | One same-session format correction across the run's entire restart history, then fail that branch |
| Unsafe path, symlink escape, unknown source ref, or metadata mismatch | Reject publication; canonical artifacts remain unchanged |
| Prepared canonical output is missing but staged bytes and metadata still match the journal | Revalidate, promote from staging, and complete without calling Codex |
| Prepared staged bytes are missing, changed, or invalid | Refuse journal replay and return to the bounded task recovery path |
| Missing topology version and at least one S7-S10 task exists | Persist topology v1 once and resume the legacy path without creating a draft screen |
| Missing topology version and no S7-S10 task exists | Persist topology v2 once; every S6 Idea must pass through `draft_screen` before S7 |
| Topology version is a boolean, float, or unsupported integer | Reject run loading before orchestration |
| Topology v2 is missing a draft-screen policy and has historical draft-screen work | Persist the newest supported policy represented by that work; do not silently upgrade or reinterpret it |
| Topology v2 is missing a draft-screen policy and has no historical draft-screen work | Persist current policy 3 once |
| Draft-screen policy is null, a boolean, float, string, or unsupported integer | Reject run loading before orchestration |
| An explicitly migrated run still has incomplete obsolete draft tasks | Cancel only those obsolete draft-screen tasks with a superseded-policy reason and no next action; preserve every completed historical review and unrelated task |
| A current route/final/report references a historical draft-screen policy | Fail selected-policy validation; never reuse the old review as the new decision |
| Draft screen omits/changes its assigned S6 revision, SHA-256, or copied context bytes | Reject publication or resume validation; do not route or eliminate the Idea |
| S8 advanced the Idea but the reviewed S6 snapshot/hash no longer resolves | Fail integrity validation and leave the run recoverable |
| Draft screen returns `invalid` | Record `draft-product-invalid` pointing to the draft screen; create no S7/S8/S10 task for that Idea |
| Draft screen returns `pass` or `repairable` | Continue to S7 unchanged; retain the complete later S9 product-repair budget |
| Draft-screen execution fails | Continue independent branches, leave the run resumable, and never translate failure into an elimination |
| A real Problem concerns hackathon participation, judging, submission mechanics, or a public-data author but the challenge domain is game publishing | Fail S5 T1 for challenge irrelevance; do not treat a name mentioned in the prompt as a target user |
| Problem body cites an unknown, copied-context, excerpt, cross-Audience, or front-matter-only evidence path | Fail deterministic S4-to-S5 routing for that branch; never fall back to all same-Audience evidence |
| Cited Research/local id is missing its paired Verification, or the Verification points to another Research | Fail deterministic S4-to-S5 routing before any Gateway session starts |
| Cited local id appears in verifier-001 `recheck_evidence_ids`, but cited verifier-002 is absent or does not cover that id | Fail deterministic S4-to-S5 routing; do not treat verifier-001 uncertainty as resolved |
| Resume reaches a completed S5 checkpoint after citation rules changed | Replay validated historical Gateway packets; do not rerun the Gateway or silently drop a formerly passed Problem |
| Completed S5 checkpoint has a missing, conflicting, unknown, or integrity-invalid terminal outcome | Fail the resume; do not infer a new decision from current Problem text |
| Blind rejection-confirmation Gateway returns `pass` | Treat it as disagreement, never as terminal Problem acceptance; replay follows the recorded elimination outcome |
| S5 elimination is malformed, duplicated, absent from the decision ledger, or cites an unbound Gateway | Fail checkpoint replay; do not let an untrusted state entry suppress a Problem |
| Existing immutable artifact has different bytes | Raise an artifact conflict; never overwrite it |
| Living Document revision/lineage mismatch | Reject replacement and keep the current revision |
| State revision changed during save | Raise `StateConflictError`; reload/reconcile before retrying |
| Saved output, challenge, or report hash mismatch | `validate` fails and `resume` refuses completed-state reuse |
| One candidate branch has an infrastructure failure | Record warning/failure and continue other independent branches |
| No candidate passes | Complete successfully with a zero-result `idea-report.md` and trace |

### 5. Good / Base / Bad Cases

- Good: ten ideas independently clear S9 and S10; the report retains all ten,
  even when several are similar.
- Good: two materially similar S6 Ideas independently pass their draft screens;
  both enter S7 because the screen applies an absolute product floor, not
  ranking, deduplication, or diversity pressure.
- Base: a draft screen returns `repairable`; S7 and S8 continue without an
  early edit, then the full S9 may still use its one `product_repair` cycle.
- Base: after S8 replaces revision 1 with revision 2, the draft screen's stored
  revision/hash resolves to `revisions/.../revision-0001.md`, while every later
  reviewer sees only the current Idea and never the early review.
- Base: if the draft-screen output must be re-executed after S8, its task copies
  the hash-bound S6 snapshot into the original logical `idea_ref` context slot;
  it never substitutes the current S8 canonical bytes.
- Base: an interrupted policy-2 run is explicitly moved to policy 3 after its
  old process stops; completed `draft-screen-002` reviews remain valid history,
  incomplete obsolete tasks are cancelled, and fresh `draft-screen-003` tasks
  use new sessions without seeing the old reviews.
- Base: one problem needs more evidence; exactly one targeted S2/S3 retry
  produces S4 revision 2, which returns to a fresh Gateway.
- Base: a run stops after several parallel tasks; `resume` skips only validated
  completed task IDs and continues incomplete work without duplicate events.
- Base: S3 first review derives `E-002` and `E-004`; the second task receives
  them as `assigned_recheck_evidence_ids` but publishes an exhausted-budget
  output with `needs_second_verifier: false` and empty `recheck_evidence_ids`.
- Good: a Problem cites two positive items and one counterexample from three
  paired Research/Verification files; both Gateways and S6 receive exactly
  those full canonical files, while other same-Audience research stays absent.
- Base: a completed legacy S5 pass has an artifact-valid Problem body that a
  newer citation parser rejects; resume validates and reuses the historical
  Gateway packet with zero Codex calls, and S6 retains that passed branch.
- Bad: `stage_statuses.S5` says `completed`, but a current Problem has neither a
  validated pass Gateway nor an S5 elimination. Resume must fail closed instead
  of shrinking the candidate set.
- Base: the first Gateway rejects and its blind confirmation passes; the live
  state machine records unresolved disagreement, and replay preserves that
  elimination instead of promoting the blind review to a pass.
- Bad: a fabricated S5 elimination contains only a stage and candidate path.
  It cannot satisfy a terminal checkpoint without its stable id, complete
  decision, ledger entry, and bound Gateway refs.
- Base: S4 revision 2 drops an old citation and adds a newly verified targeted
  result; the post-evidence Gateway and `PassedProblem.evidence_refs` use the
  newly derived subset, including a counterevidence-only subset when that is
  what the body cites.
- Good: a process stops after journaling a valid staged artifact but before its
  canonical rename; resume publishes the hash-matching staged file with zero
  additional Codex calls.
- Bad: a model writes `status: passed` but omits required user-flow headings or
  points to an unprovided source. Publication must fail regardless of prose.
- Bad: a first S3 result is required to match the empty input recheck list; this
  rejects exactly the ambiguous evidence that should trigger blind review.
- Bad: evidence proves that hackathon participants struggle with pitch decks,
  but the challenge asks to transform game publishing. S5 must reject it as a
  true yet out-of-domain Problem.
- Bad: the Problem front matter lists every Audience research file, so the
  controller passes all of them to S5 without checking body citations. This
  hides provenance mistakes and lets the Gateway invent support the Writer did
  not actually use.
- Bad: `idea-report.md` is edited after completion. `validate` and `resume` must
  report an integrity error rather than accepting the edit.

### 6. Tests Required

For every contract change, add focused assertions for the affected boundary
and keep the full suite green:

```bash
python3 -m compileall -q src tests
python3 -m unittest discover -s tests -v
git diff --check
```

Required assertion points:

- command array, stdin prompt, search policy, exact-session retry, timeout
  process-group cleanup, plugin/skill isolation flags, schema preflight,
  terminal-event precedence, non-retryable request errors, and JSONL capture
  for `CodexRunner`;
- path/symlink rejection, metadata and source binding, immutable conflict,
  Living Document snapshots, and atomic batch behavior for `ArtifactStore`;
- state compare-and-swap, JSONL idempotence, task reconciliation, content hash
  validation, and completed-run idempotence;
- dynamic parallel fan-out, zero-result output, S5 evidence/rejection limits,
  S5 `DiscoveryView` routing and challenge relevance, S3 derived recheck IDs
  plus blind-review input scoping, body-derived S5 evidence routing (including
  counterevidence-only citations, invalid paths/pairs, verifier-002 coverage,
  multi-Research and repeated-mention line pairing, identical primary/blind
  packets, revision recomputation, downstream refs, and resume reuse),
  prepared-publication replay with zero runner calls, topology
  inference/persistence, draft-screen policy inference, explicit migration,
  obsolete-task cancellation, historical-policy preservation, selected-policy
  final/report enforcement, early S9 invalid/pass/repairable routing,
  draft-screen execution recovery, exact S6 revision/hash/context-copy snapshot
  resolution, early/full S9 session and path separation, later-context
  exclusion, anti-self-evidence/causal-control prompt rules, report refs,
  similar-Idea preservation, and fresh-session full S9/S10 repair loops.

A live paid Codex run is explicit and is not part of the default test suite.

### 7. Wrong vs Correct

#### Wrong

```python
# Conflates the blind review's assigned input with the verifier's output.
routing["recheck_evidence_ids"] = assigned_ids
expected_metadata["recheck_evidence_ids"] = assigned_ids
```

#### Correct

```python
# Input scope is controller-owned; the output decision remains verifier-owned.
routing["assigned_recheck_evidence_ids"] = assigned_ids
expected_metadata.pop("recheck_evidence_ids", None)

# Before any crash-boundary replay, require the journaled staged hash.
assert sha256(staged_output) == task.data["output_hashes"][expected_path]
artifacts.promote_many([validated_request])
```

#### Wrong

```python
# Front matter is only an allowlist; it does not prove which evidence the
# Problem actually used.
gateway_refs = current_research + current_verifications
```

#### Correct

```python
gateway_refs = self._derive_problem_evidence_refs(
    problem_ref=problem_ref,
    audience_id=audience_id,
    research_refs=current_research,
    verification_refs=current_verifications,
)
# Reuse this exact tuple for a blind Gateway and PassedProblem.
```

#### Wrong

```python
# A draft review points only at a mutable canonical Idea path, then consumes
# the sole product repair before competition evidence exists.
if early_review.status == "repairable":
    await revise_idea(mode="product_repair")
```

#### Correct

```python
# The immutable reviewed bytes and copied context are controller-bound; only
# invalid stops early.
assert resolve_idea_revision_and_copy(
    early_review.reviewed_idea_revision,
    early_review.reviewed_idea_sha256,
)
if early_review.status == "invalid":
    eliminate(rule="draft-product-invalid")
else:
    await run_s7_without_editing_the_s6_draft()
```

The real implementation uses the atomic state and publication helpers; the
example highlights the required order and bindings.
