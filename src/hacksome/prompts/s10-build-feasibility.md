{common_contract}

# S10 — Build Feasibility

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

Use only the latest Idea Card revision, its current `pass` Red Team review, the explicit hackathon time/team/local-environment budget, and known API, model, data, account, dependency, and permission facts in this manifest. Do not read another Idea, competition research, `ComplianceView`, Sponsor scoring, market analysis, or an earlier Feasibility review.

{context_manifest}

## Task

Determine whether the Idea can become a real, locally runnable, end-to-end Beta inside the stated budget. Trace every necessary step in the core User Flow. Verify that the hardest processing, data, APIs, permissions, accounts, and integration points are actually available or honestly unknown.

The Demo must accept real input repeatedly, perform the claimed core processing, and return a usable result or action. Normal user actions are allowed; hidden human substitution for product work, fake data, a static interface, or a prerecorded result are not implementation.

Set the document status and Decision to exactly one of:

- `feasible`: the complete core path can be built, connected, and verified within the constraints.
- `scope_reduction`: deleting only peripheral scope could make delivery feasible while preserving the same felt value and complete User Flow.
- `infeasible`: delivery requires fake processing, hidden human work, an unavailable critical dependency, or destruction of the passed value or Flow.

## Stage Boundary

- Do not reevaluate market value, user adoption, the Product Red Team result, or Sponsor technology meaning.
- Do not browse for optimistic dependencies; judge only the supplied, known environment facts and mark unknowns.
- Do not compare Ideas, ration slots, or reject an otherwise feasible Idea because many candidates remain.
- Do not edit the Idea. A `scope_reduction` result states constraints for the one bounded S8 revision.

## Output Document Contract

Write exactly one immutable Markdown review at `{output_target}`. Its YAML front matter must contain:

- `schema_version: 1`
- `artifact_id`, `idea_ref`, `review_id`, and `review_mode` copied from the manifest
- `artifact_type: feasibility`
- `run_id: {run_id}` and `stage: S10`
- `status` exactly `feasible`, `scope_reduction`, or `infeasible`
- `revision: 1`
- `created_by_session: {session_marker}` and `updated_by_session: {session_marker}`
- `source_refs` limited to the latest Idea, current passing Red Team review, and explicit build-constraint inputs
- `supersedes: null`

The body must use these exact H2 headings:

## Review Scope

Identify the Idea revision, review mode, delivery budget, and known environment.

## Critical Path

Trace every required step from real input through actual processing to result or action.

## Deliverable Beta Scope

State the smallest complete product that still delivers the passed User Flow and felt value.

## Highest-Risk Dependencies

List data, API, model, account, permission, performance, and integration risks with their known availability and failure impact.

## Time and Integration

Explain whether the whole path can be connected and tested in time, not merely whether components can be written separately.

## Repeatable Demo

Explain how a judge can run the core path again with real input and observe a real result.

## Scope Integrity

For `scope_reduction`, label Must keep, May remove, and Still validate. Demonstrate that felt value and User Flow remain intact. For other outcomes, explain why the proposed Beta does or does not preserve them.

## Decision

State exactly `feasible`, `scope_reduction`, or `infeasible`, with the decisive constraints. Do not write a new Idea revision.

## Completion

Return only a completion-envelope JSON object with `status` set to `completed` and `output_paths` containing exactly `{output_target}`.
