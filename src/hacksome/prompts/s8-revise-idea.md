{common_contract}

# S8 — Revise Idea

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

Always use only the current Idea revision, its passed Problem and Gateway, necessary verified evidence, this Idea's competition research, and `ComplianceView`. In product-repair mode, the manifest may additionally contain exactly the Red Team document that triggered the bounded repair. In scope-reduction mode, it may instead contain exactly the Feasibility document that triggered the bounded reduction. Initial competition revision must contain neither review. Never read another Idea or a review not explicitly allowlisted for this mode.

{context_manifest}

## Task

Develop the current Draft into its next Idea Card revision. Preserve the passed Problem while improving the product mechanism, User Flow, scope, and value claim in response to factual competition evidence or the single allowlisted repair trigger.

Address competitor overlap, current alternatives, switching barriers, and why the user would adopt this product. Explain the real role of Sponsor technology when the ComplianceView requires or suggests it; if no special technology is needed, say so. Do not self-approve compliance, product validity, or engineering feasibility.

In product-repair mode, fix only the explicit local product defect without changing the Problem. In scope-reduction mode, remove only peripheral scope while preserving the already passed felt value and complete User Flow.

## Stage Boundary

- Do not browse, replace the passed Problem, invent a new user need, or use generic AI features as fake differentiation.
- Do not read another Idea, rank candidates, or write a Red Team or Feasibility conclusion.
- Do not hide unresolved competitor, technology, or dependency risks.

## Output Document Contract

Write exactly one new revision to the assigned staging path `{output_target}`. Its YAML front matter must contain:

- `schema_version: 1`
- `artifact_id`, `idea_id`, `problem_ref`, `generator_id`, and `revision_reason` copied from the manifest
- `artifact_type: idea`
- `run_id: {run_id}` and `stage: S8`
- `status: ready_for_review`
- the exact next `revision` from routing data
- `created_by_session` copied exactly from `routing.original_created_by_session`
- `updated_by_session: {session_marker}`
- `source_refs` limited to the allowlisted Problem, Gateway, Evidence, competition, ComplianceView, and mode-specific repair trigger; never include the current canonical Idea path because the new revision is promoted to that same path
- `supersedes` set to the exact controller-provided snapshot path `revisions/<canonical-without-.md>/revision-<N-1 zero-padded to 4>.md`; only a true revision 1 may use null
- `needs_competitor_research: true` only when one concrete missing competitor, alternative, or adoption claim prevents an honest revision; otherwise `false`
- `competitor_research_gaps` containing those exact missing objects or claims when the flag is true, otherwise an empty list; after the one targeted S7 retry, this must be false with an empty list because the search budget is exhausted

Lineage to the prior Idea exists only through `supersedes`; ArtifactStore creates that immutable snapshot during promotion.

The body must use these exact H2 headings:

## Target User

Identify the evidence-backed user without broadening or replacing the passed Problem.

## Problem

State and cite the passed Problem faithfully.

## Felt Value

State what the user can concretely perceive, and at what moment in real use.

## User Flow

Describe trigger, real input, actual processing, usable result or real-world action, and the felt-value moment. A page sequence or feature list is not a User Flow.

## Core Mechanism

Explain the causal product mechanism that performs the key work.

## Minimum Features

Keep only the functions necessary for the end-to-end flow.

## Alternatives and Adoption

Explain current workarounds, competitor overlap and limits, switching barriers, and a grounded adoption reason.

## Sponsor Technology

Explain the technology's actual role and remaining compliance assumptions, or explicitly state that no special technology is needed.

## Evidence References

Cite the Problem, Gateway, Evidence, Verification, and competition artifacts supporting the card.

## Risks

Keep product, evidence, competition, technology, and dependency uncertainties explicit.

## Revision Notes

State what changed from the prior revision and why, including the mode-specific trigger. Do not quote a hidden or non-allowlisted review.

## Completion

Return only a completion-envelope JSON object with `status` set to `completed` and `output_paths` containing exactly `{output_target}`.
