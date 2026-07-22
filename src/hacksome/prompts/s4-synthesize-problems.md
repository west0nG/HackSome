{common_contract}

# S4 — Synthesize Problems

## Execution Metadata

- Run ID: {run_id}
- Task ID: {task_id}
- Attempt: {attempt}
- Mode: {mode}
- Output language: {language}
- Session marker: {session_marker}
- Assigned output target: {output_target}
- Web search: forbidden

## Context Allowlist

Use only the `DiscoveryView`, one Audience, and that Audience's allowlisted Research and Verification documents. An evidence-revision mode may also include the current Problem revision. Do not read `ComplianceView`, Sponsor technology, Ideas, competition, Gateway decisions, other Audiences, or another Problem Writer's output.

{context_manifest}

## Task

Turn verified research material into zero or more independent Problem documents. Discover a concrete scenario and, when evidence supports it, a narrower user group; do not project an imagined task onto the broad Audience.

Only `supported` evidence may independently carry a positive claim. `partially_supported` evidence may support only the narrower claim recorded by the Verifier. `unsupported`, `inaccessible`, conflicting, or still uncertain evidence cannot carry a positive claim. Preserve counterevidence and do not substitute source count for judgment.

Describe only the user's situation, problem, consequence, cost, risk, and workaround. Do not propose a product or decide whether the Problem passes.

## Stage Boundary

- Do not browse, create an Idea, discuss features, or use Sponsor technology.
- Do not apply a Gateway outcome, rank Problems, enforce a count, merge similar Problems, or read another Writer's work.
- Do not split one claim merely to manufacture more documents.

## Output Document Contract

`{output_target}` is the only allowed output directory. Write one Markdown file per genuinely supported Problem using the manifest's assigned relative paths. Every file's YAML front matter must contain:

- `schema_version: 1`
- `artifact_id`, `audience_id`, `writer_id`, and `problem_id` copied from the manifest or allocated within the Writer's assigned local id space
- `artifact_type: problem`
- `run_id: {run_id}` and `stage: S4`
- `status: draft`
- `revision` copied from the task routing data
- for a new Problem, `created_by_session: {session_marker}` and `updated_by_session: {session_marker}`; in evidence-revision mode, copy `created_by_session` from `routing.original_created_by_session` and set only `updated_by_session: {session_marker}`
- `source_refs` listing only the allowlisted DiscoveryView, Audience, Research, and Verification inputs; never include the current canonical Problem path because the new revision is promoted to that same path
- `supersedes: null` for revision 1; for revision N, the exact controller-provided snapshot path `revisions/<canonical-without-.md>/revision-<N-1 zero-padded to 4>.md`

For an evidence revision, lineage to the prior Problem exists only through `supersedes`; ArtifactStore creates that immutable snapshot during promotion.

Every Problem body must use these exact H2 headings:

## Audience and Scenario

Identify the evidence-backed specific user and real setting. Explain the evidence for any narrowing from the original Audience.

## Problem

State one user problem without embedding a solution.

## Observed Consequences

Describe observed time, money, risk, failure, or other real consequence.

## Current Workarounds

Describe only workarounds supported by cited material.

## Frequency or Severity Signals

Record evidence of recurrence or a concrete severe one-off consequence without announcing that a threshold passed.

## Evidence

For every positive claim, cite the Research path plus local Evidence id and its Verification path.

## Counterevidence and Uncertainty

Keep contradictions, weak signals, and unverified assumptions visible.

## Search Gaps

List a concrete, searchable gap or state that none was found.

## Empty Result and Completion

Zero Problem documents is valid when verified evidence cannot support a real Problem. In that case, write no placeholder document and return a completion envelope with `status: empty` and an empty `output_paths` array. Otherwise return `status: completed` and list every created path. Do not include document bodies in the envelope.
