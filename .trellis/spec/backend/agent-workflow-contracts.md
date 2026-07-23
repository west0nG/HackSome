# Idea Workflow Contracts

> Normative backend contract for HackSome Idea Phase v1.

## 1. Product boundary

HackSome v1 is a local Codex orchestrator for the Useful Idea phase only. It
starts with a hackathon prompt and ends with zero or more Idea Cards.

The only logical steps are:

```text
challenge parse
  → audience expansion
  → parallel Research per audience
  → Problem Writer
  → independent Problem Gateway per Problem
  → parallel Idea Generators per passed Problem
  → independent Red Team per Idea
  → deterministic Idea Card validation
```

Research Verification, challenge compliance, competitor research, idea
revision, feasibility review, Build, GitHub, and Pitch MUST NOT be hidden inside
this workflow.

## 2. Candidate policy

- Problem, Idea, and Idea Card counts are dynamic; Audience expansion is the
  sole v1 exception and has a hard limit of five.
- Empty output is valid at every fanout boundary.
- Absolute gates may reject; relative ranking MUST NOT select.
- There is no Top-K, quota, semantic deduplication, or forced diversity.
- Similar candidates remain when each clears the same absolute gates.
- Global concurrency is bounded, but parallel completion order MUST NOT change
  stable IDs or final ordering.

Defaults are configuration, not product invariants:

```text
max_concurrency = 4
max_audiences = 5
researchers_per_audience = 1
idea_generators_per_problem = 3
model = gpt-5.6-terra
reasoning_effort = high
```

## 3. Session isolation

Every logical Agent task starts a new Codex Session. In particular:

- each audience Research is independent;
- each Problem Gateway is independent of its Writer and every other Gateway;
- each Idea Generator is independent of sibling generators;
- each Idea Red Team is independent of its Generator and every other review.

An infrastructure retry MAY resume only the exact Session created for that
same logical task. A role boundary MUST NOT use resume to inherit another
Agent's conversation.

Only Research enables live web search. All other tasks explicitly disable it.
Stage Sessions run without ambient plugins, skills, project documents, or user
rules. They should use a read-only sandbox because canonical output is returned
over structured stdout and persisted by the Hub.

Every Run MUST persist its requested `model` and `reasoning_effort`. The runner
MUST pass both explicitly to Codex instead of relying on the CLI's ambient
default model. The v1 defaults are `gpt-5.6-terra` and `high`; CLI overrides are
allowed and become part of the immutable Run configuration.

## 4. Prompt-as-transport contract

Persistence and transport are separate concerns:

- The Hub persists every canonical artifact as a file.
- The Hub loads selected artifact bytes and embeds their text in the next
  rendered Prompt.
- Agents receive the rendered Prompt over stdin.
- Agents are never instructed to inspect upstream files, directories, or
  manifests.
- Agents return schema-constrained JSON; the Hub publishes Markdown fields.

Every rendered Prompt MUST be saved before model invocation and MUST contain
named data blocks with unambiguous boundaries, for example:

```text
<BEGIN_RESEARCH_DATA>
... exact persisted Markdown ...
<END_RESEARCH_DATA>
```

Research/community text is untrusted data. The Prompt MUST say that commands or
instructions inside a data block are not executable instructions.

Prompts SHOULD contain only the context required by the role:

| Role | Context |
| --- | --- |
| Challenge Parser | original challenge |
| Audience Expander | parsed challenge brief |
| Researcher | challenge brief, one audience |
| Problem Writer | challenge brief, one audience, that audience's Research |
| Problem Gateway | challenge brief, audience, Research, one Problem |
| Idea Generator | challenge brief, audience, Research, passed Problem |
| Idea Red Team | challenge brief, audience, passed Problem, Gateway review, one Idea |

No prompt may reference a downstream review or candidate that does not yet
exist. The Idea Generator MUST NOT receive the Gateway review text or the Idea
Red Team's decision rubric. Passing only the accepted Problem prevents the
Generator from writing directly to the reviewer's checklist while the Hub
retains the Gateway artifact for process lineage.

## 5. Structured-output boundary

Codex output schemas describe small transport envelopes; the Hub owns file
paths, IDs, lineage, and statuses.

### Document output

Used by Challenge Parser and Researcher:

```json
{"markdown": "non-empty Markdown"}
```

### Audience output

```json
{
  "audiences": [
    {"name": "non-empty", "description": "non-empty"}
  ]
}
```

The model MUST NOT assign IDs. The Hub assigns stable IDs after validating the
ordered output. Audience descriptions remain broad; precise behavior belongs
to Research. The Audience list MUST contain at most five items; both the output
schema and Hub validation enforce this v1 limit.

### Candidate output

Used by Problem Writer and Idea Generator:

```json
{
  "candidates": [
    {"markdown": "non-empty Markdown"}
  ]
}
```

Empty `candidates` is valid. The model MUST NOT assign canonical paths or
lineage. The Hub validates required headings before publication and assigns
stable IDs based on the parent task plus returned order. The Markdown H1 is the
only source of the candidate title; the Hub derives titles from it whenever an
index or card needs one. Candidate transport MUST NOT duplicate the title in a
second model-authored field.

### Review output

Used by Problem Gateway and Idea Red Team:

```json
{"decision": "pass | reject", "markdown": "non-empty Markdown"}
```

A `reject` is a successful Agent task and an explicit candidate decision. An
invalid schema/Markdown is a task failure; it MUST NOT be converted to reject
or silently remove a candidate.

## 6. Markdown contracts

Markdown is human-readable product material, not the routing database. Stable
lineage lives in Hub metadata.

### Problem

A Problem MUST have one H1 and these H2 sections exactly once:

```text
User
Observed Problem
Evidence
Existing Workarounds
Why It Matters
```

The Writer cites only URLs present in its Research input. The Gateway rejects
Problems that are speculative, unsupported, outside the challenge, or too weak
for the user to care about.

Research MUST reconstruct concrete situations instead of collecting facts by
source. Important claims identify the actor, setting, constraint, failure or
compromise, current response, and remaining consequence. They also distinguish
direct observation, strong inference, and unknown internal detail. A Problem
Gateway acts as a skeptical Red Team: a polished card does not compensate for a
missing trigger, unsupported internal workflow, weak consequence, or critical
unknown.

### Idea

An Idea MUST have one H1 and these H2 sections exactly once:

```text
User
Problem
Product
Product Experience
Core Mechanism
First Real Version
Assumptions and Risks
Evidence
```

These headings provide a readable product description without disclosing the
downstream Red Team checklist. `First Real Version` describes the first product
that an actual user can use; it is not a license to substitute a staged demo,
fake data, or mock integrations for the core outcome.

### Reviews

Review Markdown explains the decision against absolute criteria. The stored
JSON decision is authoritative for routing; Markdown cannot override it.

## 7. Red Team gate

The Idea Red Team is independent and actively tries to disprove the Idea as a
real product. It reconstructs the actual use: the user and trigger, authentic
input or access, product action, next step, and concrete change for the user.
It judges from the perspective of an experienced product owner, named user, and
skeptical buyer rather than rewarding hackathon presentation quality.

It rejects when:

- the core outcome works only on fake, mock, synthetic, or hand-curated data
  rather than authentic user-provided or legitimately accessible inputs;
- the core mechanism assumes unavailable permissions, private data,
  integrations, or product authority;
- the product stops at a dashboard, score, report, recommendation, ticket, or
  generated artifact while the value requires an uncontrolled actor to act;
- the first real version is merely a staged demonstration with no credible
  repeated use after the event;
- the flow changes, avoids, or restates the passed Problem instead of solving
  it.

The v1 Red Team has only `pass` and `reject`. It does not repair, rank, compare,
or see sibling Ideas. A narrow but authentic first version may pass; demo
feasibility alone may not.

## 8. Hub persistence contract

The Hub is the sole owner of canonical Session data. Before execution it writes:

- task ID, role/stage, parent IDs, and web-search policy;
- output schema name/hash;
- exact rendered Prompt and Prompt/template hashes;
- task request timestamps/status.

After execution it writes:

- Codex Session ID and attempt count;
- started/finished timestamps, duration, usage, return code, and error;
- raw stdout/stderr JSONL and every raw last-message attempt;
- parsed structured output;
- published Markdown or review decision;
- stable candidate lineage and Prompt/request/result/output/artifact hashes.

Run-level state is atomically replaced. Events and decisions are append-only
JSONL with stable record IDs and idempotent conflict checking. The Hub MUST NOT
report a phase complete when a scheduled candidate task failed or disappeared.

## 9. Deterministic Idea Card validation

Idea Card validation is controller code, not another Agent Session. A card may
be published only if:

- the source Problem exists and its Gateway decision is `pass`;
- the source Idea exists and satisfies the Idea Markdown contract;
- its own Red Team decision is `pass`;
- all bound task results, Session IDs, source refs, and content hashes exist;
- no source file changed after its hash was recorded.

The final card includes controller-owned lineage plus the exact validated Idea
body and its review. An empty set of valid cards produces a valid empty index.

## 10. Failure and replay behavior

- Persist the exact Prompt before invoking Codex.
- Persist every failure and leave the run inspectable.
- Infrastructure retry uses the runner's exact-session resume behavior.
- Never interpret a missing/failed task as an empty candidate list.
- v1 has no Run-level `resume` command. Exact-session resume exists only inside
  one `CodexRunner.run()` infrastructure retry.
- Offline `validate` invokes no Codex process and checks the run from persisted
  state and hashes.

Compatibility with pre-rewrite S0–S11 run directories is not required. Such
runs remain historical files and can be inspected at their checkpoint.

## 11. Executable signatures

```python
UsefulIdeaWorkflow.create(
    challenge: str,
    runs_dir: str | Path,
    *,
    settings: WorkflowSettings | None = None,
    codex_config: CodexConfig | None = None,
    run_id: str | None = None,
    runner: Runner | None = None,
) -> UsefulIdeaWorkflow

await UsefulIdeaWorkflow.execute() -> Path  # Idea Card index

render_prompt(
    stage: str,
    blocks: Sequence[tuple[str, str]],
) -> RenderedPrompt

inspect_run(run_dir: str | Path) -> dict[str, Any]
validate_run(run_dir: str | Path) -> list[str]
```

CLI surface:

```text
hacksome doctor [--json]
hacksome run (CHALLENGE | --prompt TEXT)
  [--model MODEL]
  [--reasoning-effort low|medium|high|xhigh|max|ultra]
  [runtime/fanout options]
hacksome status RUN_DIR [--json]
hacksome validate RUN_DIR
```

There is deliberately no `hacksome resume` command in v1.

## 12. Validation and error matrix

| Condition | Required behavior |
| --- | --- |
| Audience output has more than five items | schema rejection, or Hub fails closed before Research |
| Candidate array is empty | successful task; downstream fanout is empty |
| Problem/Idea Markdown misses a required H2 | task/output failure; never convert to reject |
| Gateway or Red Team returns `reject` | successful task plus append-only decision; no downstream candidate |
| Runner returns failed/timed-out result | persist Result/logs, mark Run failed, stop |
| Runner raises after `begin_task` | persist a synthetic failed Result, mark Run failed |
| Run timeout cancels an active task | terminate runner, persist cancellation, mark Run failed |
| Prompt/request/result/output/artifact hash changes | offline validation returns a concrete mismatch |
| Model returns zero final passes | publish a valid empty Idea Card index |
| Unsupported reasoning-effort CLI value | argparse rejects before Run creation |
| Requested model is unavailable to Codex | persist the non-zero task failure and stop the Run |

## 13. Good, base, and bad cases

- Good: two Audiences research concurrently; each later Prompt contains only
  its selected persisted text; a passed Problem fans out to three Generators.
- Good: Research labels a player report as observed, a workflow conclusion as
  inference, and an internal handoff as unknown; the Gateway can reject when an
  unknown is critical to the Problem.
- Base: multiple Generators return similar Ideas; every independently passing
  Idea receives its own Red Team and becomes a card.
- Base: zero Audiences, Problems, Ideas, or Red Team passes completes with an
  empty index and no fabricated failure.
- Bad: a rejected Problem reaches Idea generation, or a rejected Idea becomes a
  card. Tests must fail on either routing error.
- Bad: a downstream Prompt contains only `artifacts/...` paths instead of exact
  upstream text.
- Bad: an Idea Generator Prompt contains the Problem Gateway review or explicit
  Red Team checklist, allowing the Generator to optimize its prose for a pass.
- Bad: an Idea claims a production outcome but its first version replaces the
  necessary private inputs or integration with synthetic data.
- Bad: an out-of-order parallel result uses the previous Problem's Gateway ref.
  Source refs must be recomputed from the current Problem during publication.
- Bad: Run metadata records `model: null` and silently inherits a different
  model after a Codex CLI update.

## 14. Required tests

The default suite MUST be offline and cover:

- Codex command, stdin Prompt, web-search policy, schema validation, JSONL
  capture, timeout cleanup, and exact-session infrastructure retry;
- Prompt rendering with exact inline Markdown and no file-reading instruction;
- Research prompts that require situation reconstruction plus
  observation/inference/unknown labels;
- broad-audience output, the five-Audience hard limit, and stable Hub-assigned IDs;
- Research parallelism and Research-only web search;
- Problem Writer/Gateway separation, skeptical fail-closed criteria, and reject routing;
- default three-way Idea Generator fanout and preservation of similar Ideas;
- Idea Generator prompts that exclude Gateway review text and downstream gate
  language;
- one fresh Red Team per Idea and rejection of non-delivered, mock-only value;
- deterministic Idea Card publication and empty outputs;
- complete task trace persistence and offline integrity validation;
- deterministic ordering under out-of-order parallel completion.
- explicit model/reasoning command arguments, CLI overrides, and Run metadata.

Run before completion:

```bash
.venv/bin/ruff check src tests
.venv/bin/mypy src
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

## 15. Wrong vs correct

### Wrong: use persistence as Agent transport

```python
prompt = "Read artifacts/problems/problem-001.md, then continue."
```

### Correct: Hub injects the exact selected bytes

```python
problem_text = hub.read_artifact(problem.artifact_ref)
prompt = render_prompt("idea-generate", (("PASSED_PROBLEM", problem_text),))
```

### Wrong: reuse a loop-local Gateway ref after parallel fanout

```python
for problem, output in results:
    publish_idea(source_refs=(problem.artifact_ref, gateway_ref))
```

### Correct: bind lineage from the current result owner

```python
for problem, output in results:
    current_gateway_ref = problem.gateway_ref
    assert current_gateway_ref is not None
    publish_idea(source_refs=(problem.artifact_ref, current_gateway_ref))
```

### Wrong: inherit a moving Codex model default

```python
CodexConfig(model=None)
```

### Correct: pin model and reasoning effort in every Run

```python
CodexConfig(model="gpt-5.6-terra", reasoning_effort="high")
```
