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

- Candidate counts are dynamic.
- Empty output is valid at every fanout boundary.
- Absolute gates may reject; relative ranking MUST NOT select.
- There is no Top-K, quota, semantic deduplication, or forced diversity.
- Similar candidates remain when each clears the same absolute gates.
- Global concurrency is bounded, but parallel completion order MUST NOT change
  stable IDs or final ordering.

Defaults are configuration, not product invariants:

```text
max_concurrency = 4
researchers_per_audience = 1
idea_generators_per_problem = 5
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
| Idea Generator | challenge brief, audience, Research, passed Problem, Gateway review |
| Idea Red Team | challenge brief, audience, passed Problem, Gateway review, one Idea |

No prompt may reference a downstream review or candidate that does not yet
exist.

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
to Research.

### Candidate output

Used by Problem Writer and Idea Generator:

```json
{
  "candidates": [
    {"title": "non-empty", "markdown": "non-empty Markdown"}
  ]
}
```

Empty `candidates` is valid. The model MUST NOT assign canonical paths or
lineage. The Hub validates required headings before publication and assigns
stable IDs based on the parent task plus returned order.

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

### Idea

An Idea MUST have one H1 and these H2 sections exactly once:

```text
User
Problem
Product
End-to-End User Flow
Core Mechanism
Felt Value
Why This Technology
Demo Scope
Assumptions and Risks
Evidence
```

The User Flow must start with a real trigger, include user/product interaction,
and terminate at a value moment delivered by the product. Describing a report,
recommendation, or ticket is insufficient when the claimed user value still
depends on an uncontrolled third party acting.

### Reviews

Review Markdown explains the decision against absolute criteria. The stored
JSON decision is authoritative for routing; Markdown cannot override it.

## 7. Red Team gate

The Idea Red Team is deliberately narrow and independent. It answers:

1. Can the named user genuinely perceive the claimed value?
2. Is there a complete User Flow in which this product delivers that value?

It also rejects when:

- the product only creates an artifact but the value requires someone else to
  act;
- the core mechanism assumes unavailable permissions, private data, or product
  authority;
- the flow changes the passed Problem rather than solving it;
- the claimed technology is decorative and does not participate materially.

The v1 Red Team has only `pass` and `reject`. It does not repair, rank, compare,
or see sibling Ideas.

## 8. Hub persistence contract

The Hub is the sole owner of canonical Session data. Before execution it writes:

- task ID, role/stage, parent IDs, attempt policy, web-search policy;
- output schema name/hash;
- exact rendered Prompt and Prompt/template hashes;
- task request timestamps/status.

After execution it writes:

- Codex Session ID and attempt count;
- started/finished timestamps, duration, usage, return code, and error;
- raw stdout/stderr JSONL and every raw last-message attempt;
- parsed structured output;
- published Markdown or review decision;
- stable candidate lineage and content hashes.

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
- Resume skips only tasks with complete, schema-valid, hash-valid persisted
  results. It schedules incomplete tasks with the same stable task IDs.
- Offline `validate` invokes no Codex process and checks the run from persisted
  state and hashes.

Compatibility with pre-rewrite S0–S11 run directories is not required. Such
runs remain historical files and can be inspected at their checkpoint.

## 11. Required tests

The default suite MUST be offline and cover:

- Codex command, stdin Prompt, web-search policy, schema validation, JSONL
  capture, timeout cleanup, and exact-session infrastructure retry;
- Prompt rendering with exact inline Markdown and no file-reading instruction;
- broad-audience output and stable Hub-assigned IDs;
- Research parallelism and Research-only web search;
- Problem Writer/Gateway separation and reject routing;
- default five-way Idea Generator fanout and preservation of similar Ideas;
- one fresh Red Team per Idea and rejection of non-delivered value;
- deterministic Idea Card publication and empty outputs;
- complete task trace persistence and offline integrity validation;
- deterministic ordering under out-of-order parallel completion.

Run before completion:

```bash
python3 -m compileall -q src tests
python3 -m unittest discover -s tests -v
git diff --check
```
