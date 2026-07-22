# Useful Idea v0.1 — Implementation Plan

## Scope

Implement the local Codex-only vertical slice defined by `prd.md`, `design.md`,
and `workflow-contracts.md`. The executable workflow starts with a challenge
prompt and ends with `idea-report.md` after S0–S11. Build, repository creation,
Pitch, the Creative route, Claude Code, Docker/VM isolation, and a generic
provider framework remain out of scope.

## Implementation defaults

- Python 3.11+ with `asyncio`; PyYAML is the only runtime dependency.
- Default maximum concurrency: 4 Codex processes.
- Default task timeout: 20 minutes; one infrastructure retry per task.
- Default whole-run deadline: 6 hours. All limits are CLI/config overrides.
- Long artifacts use Markdown with YAML front matter. Briefs, audiences, state,
  and indexes use JSON. Events and decisions use append-only JSONL.
- Stable Markdown headings are English so the controller can validate and
  render them; prose follows the challenge input language unless configured.
- A recurring problem normally needs two independently verified first-hand
  sources. A severe one-off may proceed with one verified first-hand source
  that demonstrates a concrete consequence. This is a floor, not a quota or
  ranking signal.
- Codex runs with `workspace-write`, approvals disabled, live web search only
  for S2, S3, and S7, and isolated task directories. Project/user rules,
  hooks, apps, goals, and nested multi-agent fan-out are disabled for stage
  sessions.

## Data flow and validation boundaries

```text
CLI input
  -> immutable raw challenge
  -> S0/S1 structured JSON output
  -> isolated Codex task workspace
  -> staged Markdown output
  -> path/front-matter/heading/reference validation
  -> atomic canonical artifact publication
  -> state transition + append-only decision event
  -> deterministic S11 report
```

Every routing decision is read from validated YAML front matter. Free-form
body text never decides the next workflow stage. Each task receives a copied,
allow-listed context packet and a unique output path. Completed canonical
artifacts are never silently overwritten; Living Document revisions are
snapshotted before replacement.

## Ordered implementation

### 1. Package and core contracts

- [x] Add `pyproject.toml`, package entry points, `.gitignore`, and a concise
      local-use README.
- [x] Define configuration, stage/outcome enums, task/run records, stable IDs,
      and completion envelopes.
- [x] Implement one JSON/JSONL decoder boundary and atomic JSON writes.
- [x] Implement Markdown front-matter parsing, stage-specific artifact specs,
      safe path checks, reference checks, revision snapshots, and atomic
      promotion from task staging directories.

Validation:

```bash
python3 -m compileall -q src tests
python3 -m unittest discover -s tests -v
```

### 2. Concrete Codex runtime

- [x] Implement `CodexRunner` with argument-array subprocess invocation,
      prompt-over-stdin, concurrent stdout/stderr draining, JSONL capture,
      explicit session-id extraction, structured final-output parsing,
      timeout cancellation, token-usage capture, and bounded concurrency.
- [x] Resume only the explicit session ID for an infrastructure retry. New
      research, verification, writing, Gateway, Red Team, and Feasibility roles
      always start new sessions.
- [x] Add a startup doctor for Codex presence/version/login-facing failures and
      keep the real Codex smoke path explicit through `hacksome run`.

Validation:

```bash
python3 -m unittest tests.test_codex_runner -v
python3 -m hacksome doctor
```

### 3. Prompt and context contracts

- [x] Add a short common prompt contract plus one external template for S0–S10.
- [x] Add JSON Schemas for S0, S1, and the long-artifact completion envelope.
- [x] Build per-task context manifests that copy only the stage's allowed
      artifacts and record prompt/input hashes.
- [x] Enforce web-search policy and blind-review exclusions in code, including
      the second Verifier, second Gateway, and subsequent Red Team sessions.

### 4. S0–S5 problem discovery and gating

- [x] Implement S0 challenge parsing and deterministic Discovery/Compliance
      views, then S1 non-web audience expansion.
- [x] Implement configurable S2 research fan-out and S3 independent source
      verification, including conditional second verification.
- [x] Implement configurable S4 Problem Writer fan-out without consolidation.
- [x] Implement the finite S5 state machine: pass, one targeted evidence loop,
      blind rejection confirmation, and terminal elimination after exhausted
      disagreement. Infrastructure retries remain separate.

### 5. S6–S10 idea development and adversarial gates

- [x] Implement configurable S6 Idea Generator fan-out without ranking,
      direction quotas, consolidation, or semantic deduplication.
- [x] Implement per-Idea S7 competitor research and one specific-gap retry.
- [x] Implement S8 Living Document revisions with immutable snapshots.
- [x] Implement S9 independent product Red Team with one product-repair budget.
- [x] Implement S10 independent build feasibility with one scope-reduction
      budget, followed by fresh S9 and S10 sessions.

### 6. S11, CLI, and recovery

- [x] Implement deterministic hard-field checks and `idea-report.md` rendering
      without an Agent, ranking, or semantic rewriting.
- [x] Add `run`, `resume`, `status`, `validate`, and `doctor` CLI commands.
- [x] Reconcile state with validated canonical artifacts on resume; completed
      task IDs must be skipped and append-only events must be idempotent.
- [x] Preserve zero-result runs as valid reports with complete elimination or
      failure traces.

## Automated acceptance scenarios

- [x] Straight-through run keeps two similar, independently valid Ideas and
      renders both without ranking or deduplication.
- [x] Problem loop covers one evidence retry and one double-confirmed rejection;
      no second evidence retry or third Gateway is created.
- [x] Idea loop covers one S9 repair and one S10 scope reduction; revisions are
      snapshotted and every re-review uses a new logical task/session.
- [x] Interrupted parallel run resumes without rerunning completed task IDs,
      duplicating artifacts, or duplicating decision events.
- [x] Zero passed Ideas still produce a valid report.
- [x] Codex subprocess contract is tested with a fake executable; a paid/live
      smoke run is opt-in and is not part of the default test suite.

## Quality gate

```bash
python3 -m compileall -q src tests
python3 -m unittest discover -s tests -v
git diff --check
```

After the automated gate, run one real challenge manually and record observed
source coverage, evidence misclassification, false rejection/acceptance, Idea
completeness, duplicate-but-valid Ideas, and runtime failures for v0.2.

## Rollback points

- Core stores and contracts can be tested before any Codex invocation.
- S0–S5 and S6–S11 are separate commits/rollback boundaries if needed.
- A failed or cancelled run never rewrites upstream canonical artifacts; remove
  only its staging directory to retry from the last validated task state.
