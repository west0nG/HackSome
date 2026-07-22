{common_contract}

# S9 — Red-Team Idea

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

Use only the latest Idea Card revision, its passed Problem and Gateway, necessary verified evidence, this Idea's competition research, and the Product Red Team rules. Do not read S8 chat history, `ComplianceView`, implementation plans, Feasibility, another Idea, or any earlier Red Team document. This exclusion applies equally to product-repair and scope-reduction re-review modes.

{context_manifest}

## Task

Attack whether the Idea exists as a real product Idea. Do not polish or complete it. Test five independent claims:

1. A real target user can concretely feel the promised value in use, rather than receiving an abstract claim of intelligence or efficiency.
2. There is a User Flow with a trigger, real input, actual product processing, usable result or real-world action, and a felt-value moment—not pages or a feature list.
3. The Flow causally delivers the value without hidden human work, fake data, or unexplained magic in a critical step.
4. The user has an evidence-grounded reason to adopt or switch from the current workaround and alternatives.
5. The Idea remains faithful to the passed user, scenario, and Problem instead of quietly changing the question.

For every test, provide an attack, a checkable reference to the Idea or source facts, and a conclusion. Do not use a score.

Set the document status and Decision to exactly one of:

- `pass`: all five claims withstand attack.
- `repairable`: the Problem and core value remain sound, but one explicit local Flow or product-mechanism defect can be repaired without changing the Problem.
- `invalid`: felt value or a real User Flow is absent, value delivery is fundamentally false, or the Idea works only by replacing the passed Problem.

## Blind-Review Boundary

- Never look for, mention, or infer an earlier Red Team conclusion.
- Do not judge engineering difficulty, hackathon time, Sponsor technology, or competition-rule compliance.
- Do not edit the Idea or prescribe the rewritten solution. For `repairable`, describe the failure condition and boundary of a valid repair.
- Do not compare Ideas or reject one because another is similar.

## Output Document Contract

Write exactly one immutable Markdown review at `{output_target}`. Its YAML front matter must contain:

- `schema_version: 1`
- `artifact_id`, `idea_ref`, `red_team_id`, and `review_mode` copied from the manifest
- `artifact_type: idea_red_team`
- `run_id: {run_id}` and `stage: S9`
- `status` exactly `pass`, `repairable`, or `invalid`
- `revision: 1`
- `created_by_session: {session_marker}` and `updated_by_session: {session_marker}`
- `source_refs` limited to the latest Idea, Problem, Gateway, verified evidence, and competition inputs; never include an earlier Red Team or Feasibility review
- `supersedes: null`

The body must use these exact H2 headings:

## Review Scope

Identify the Idea revision and blind mode without mentioning earlier review outcomes.

## Felt Value

Label Attack, Evidence, and Conclusion.

## Real User Flow

Label Attack, Evidence, and Conclusion.

## Value Delivery

Label Attack, Evidence, and Conclusion.

## Adoption Reason

Label Attack, Evidence, and Conclusion.

## Problem Fidelity

Label Attack, Evidence, and Conclusion.

## Decision

State exactly `pass`, `repairable`, or `invalid`. For `repairable`, name one bounded defect and the invariant Problem/value that must remain. Do not write the fix.

## Completion

Return only a completion-envelope JSON object with `status` set to `completed` and `output_paths` containing exactly `{output_target}`.
