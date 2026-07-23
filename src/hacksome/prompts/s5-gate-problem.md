{common_contract}

# S5 — Gate One Problem

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

Use only one Problem revision, the `DiscoveryView`, and the exact canonical Research and Verification subset explicitly cited in that Problem's `Evidence` or `Counterevidence and Uncertainty` body sections, plus the absolute threshold and current evidence-loop count. No uncited same-Audience file is available merely because it appeared in the Problem's front-matter `source_refs`. No previous Gateway document is allowed in any mode. Do not read another Problem, any Idea, competition, `ComplianceView`, Red Team, or Feasibility artifact.

{context_manifest}

## Task

Independently test this Problem against all five absolute thresholds:

1. The described user and scenario are observed rather than inferred by an Agent, and the Problem directly belongs to the challenge theme or problem domains in `DiscoveryView`. Merely appearing in the challenge text does not make hackathon participants, judges, submission mechanics, public-data authors, or other meta roles valid product users unless improving that role is itself part of the challenge domain.
2. The Problem recurs, or a one-off has a concrete severe consequence.
3. Users already pay with time, money, risk, or a materially awkward workaround.
4. Software could materially improve the situation rather than add only another interface; do not invent the software.
5. The document does not disguise an unverified assumption, isolated extreme, or preferred solution as a Problem fact.

For each threshold, output exactly one routing result: `met`, `not_met`, or `insufficient_evidence`, with file-and-local-id evidence. A recurring Problem normally needs two independently verified first-hand sources. A severe one-off may meet the floor with one verified first-hand source demonstrating a concrete consequence. This is a minimum, never a score or quota.

Judge only from the cited subset provided in the manifest. Do not assume an uncited Research or Verification document exists, reconstruct omitted evidence from the Problem's front matter, or treat a prose claim without its paired Research id and Verification as verified.

Set the document status and Decision to exactly one of:

- `pass`: every necessary threshold is met.
- `needs_evidence`: a threshold cannot yet be decided and there is a concrete searchable gap.
- `reject_candidate`: existing evidence shows at least one necessary threshold is not met.

## Blind-Review Boundary

- In blind rejection-confirmation mode, do not seek or infer the first Gateway's decision. Evaluate all thresholds from the facts.
- Do not edit the Problem, find new evidence, propose an Idea, rank candidates, or compare this Problem with another.
- A first `reject_candidate` is only a candidate decision; the controller owns confirmation and elimination.

## Output Document Contract

Write exactly one immutable Markdown document at `{output_target}`. Its YAML front matter must contain:

- `schema_version: 1`
- `artifact_id`, `problem_ref`, `gateway_id`, `gateway_mode`, and `evidence_loop_count` copied from the manifest
- `artifact_type: problem_gateway`
- `run_id: {run_id}` and `stage: S5`
- `status` exactly `pass`, `needs_evidence`, or `reject_candidate`
- `revision: 1`
- `created_by_session: {session_marker}` and `updated_by_session: {session_marker}`
- `source_refs` limited to the assigned Problem, `DiscoveryView`, and the exact cited Research/Verification subset supplied by the controller
- `supersedes: null`
- `failed_thresholds` containing only threshold ids `T1` through `T5` whose result is `not_met`; use an empty list when none failed
- `evidence_gaps` containing concrete searchable gaps for every `insufficient_evidence` result; use an empty list when no evidence is missing

The Markdown body must use these exact H2 headings:

## Gateway Scope

Identify the Problem revision, mode, and evidence-loop count without mentioning an earlier Gateway conclusion.

## Threshold Checks

Use H3 headings `T1` through `T5`. Under each, label Result, Evidence, and Reason.

## Decision

State exactly `pass`, `needs_evidence`, or `reject_candidate` and identify the determining threshold facts. Do not write an orchestration action beyond this decision.

## Evidence Gap

For `needs_evidence`, state exactly what real-world claim is missing, who or what source could establish it, and a bounded search target. For the other outcomes, write `None`.

## Completion

Return only a completion-envelope JSON object with `status` set to `completed` and `output_paths` containing exactly `{output_target}`.
