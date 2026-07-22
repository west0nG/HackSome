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
StateStore.save(state: RunState) -> RunState
validate_run(run_dir: str | Path) -> list[str]
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

#### Codex task

`CodexTask` requires a non-empty prompt, a safe stable task ID, an isolated
working directory, and an output schema. `web_search=True` is allowed only for
the research stages configured by the workflow. Subprocess arguments must be
passed as an array and prompt text over stdin. Stage sessions disable project
instructions, hooks, apps, goals, nested agents, browser/computer tools, and
unneeded web access.

Infrastructure retry may resume the same explicit session once. New research,
verification, writer, Gateway, Red Team, or feasibility work starts a new
logical task and therefore a new session.

#### Artifact publication

Long outputs are Markdown with unique YAML keys and a stage-specific fixed
heading schema. `PromotionRequest.expected_metadata` is mandatory and must
fully bind the task identity. `source_refs` must be allow-listed, safe relative
paths inside the run, and consistent with routing metadata.

Agents write only to their task staging directory. The controller validates
and atomically promotes output. Immutable canonical artifacts cannot be
overwritten. A Living Document replacement must increment its revision,
preserve stable lineage fields, and snapshot the previous revision first.

S4 and S6 fan-out may publish a same-directory batch atomically; independent
agents must not concurrently edit one canonical file.

#### Workflow behavior

- Fan out all ready tasks globally and let `CodexRunner` enforce the configured
  concurrency bound.
- Keep every candidate that passes the same absolute gate, including similar
  candidates; zero candidates is valid and still produces a report.
- S5 permits at most one targeted evidence loop and one blind confirmation of
  a rejection.
- S9 permits at most one product repair. S10 permits at most one scope
  reduction, followed by fresh S9 and S10 sessions.
- Compliance context may shape S8, but there is no separate compliance gate.
- S11 is deterministic rendering and hard-field validation, not another model
  session.

### 4. Validation & Error Matrix

| Condition | Required result |
|---|---|
| Empty challenge or invalid runtime limits | Reject before creating/running a task |
| Missing Codex executable or authentication | `doctor` is unhealthy; task is not started |
| Task timeout | Terminate the process group; record `timed_out`; allow only the configured infrastructure retry |
| Invalid JSON/completion envelope | One same-session format correction, then fail that branch |
| Unsafe path, symlink escape, unknown source ref, or metadata mismatch | Reject publication; canonical artifacts remain unchanged |
| Existing immutable artifact has different bytes | Raise an artifact conflict; never overwrite it |
| Living Document revision/lineage mismatch | Reject replacement and keep the current revision |
| State revision changed during save | Raise `StateConflictError`; reload/reconcile before retrying |
| Saved output, challenge, or report hash mismatch | `validate` fails and `resume` refuses completed-state reuse |
| One candidate branch has an infrastructure failure | Record warning/failure and continue other independent branches |
| No candidate passes | Complete successfully with a zero-result `idea-report.md` and trace |

### 5. Good / Base / Bad Cases

- Good: ten ideas independently clear S9 and S10; the report retains all ten,
  even when several are similar.
- Base: one problem needs more evidence; exactly one targeted S2/S3 retry
  produces S4 revision 2, which returns to a fresh Gateway.
- Base: a run stops after several parallel tasks; `resume` skips only validated
  completed task IDs and continues incomplete work without duplicate events.
- Bad: a model writes `status: passed` but omits required user-flow headings or
  points to an unprovided source. Publication must fail regardless of prose.
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
  process-group cleanup, and JSONL capture for `CodexRunner`;
- path/symlink rejection, metadata and source binding, immutable conflict,
  Living Document snapshots, and atomic batch behavior for `ArtifactStore`;
- state compare-and-swap, JSONL idempotence, task reconciliation, content hash
  validation, and completed-run idempotence;
- dynamic parallel fan-out, zero-result output, S5 evidence/rejection limits,
  and fresh-session S9/S10 repair loops.

A live paid Codex run is explicit and is not part of the default test suite.

### 7. Wrong vs Correct

#### Wrong

```python
# Trusts free-form output and destroys resume provenance.
result = await runner.run(task)
(run_dir / "ideas" / "final.md").write_text(result.text)
state.status = "completed"
```

#### Correct

```python
result = await runner.run(task)
published = artifacts.promote(
    PromotionRequest(
        staged_path=staged_output,
        canonical_path=expected_path,
        expected_metadata=expected_binding,
        allowed_source_refs=allowed_refs,
    )
)
task.output_refs = [published.relative_path]
task.data["output_hashes"] = {published.relative_path: sha256(published.path)}
state_store.upsert_task(task)
```

The real implementation uses the atomic state and publication helpers; the
example highlights the required order and bindings.
