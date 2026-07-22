{common_contract}

# S3 — Verify Evidence

## Execution Metadata

- Run ID: {run_id}
- Task ID: {task_id}
- Attempt: {attempt}
- Mode: {mode}
- Output language: {language}
- Session marker: {session_marker}
- Assigned output target: {output_target}
- Web search: allowed only to reopen and locate the cited original sources

## Context Allowlist

Use only one Research document, its Audience record, verification rules, and—only for blind recheck mode—the local evidence ids to recheck. No earlier Verification result is allowed. Do not inspect sibling verifier files or search for replacement evidence.

{context_manifest}

## Task

Independently reopen every assigned original URL. For each Evidence Candidate, check accessibility, whether the quoted material is actually present, omitted context that changes its meaning, whether the speaker belongs to the Audience, and whether the tentative claim stays within what the source supports.

Assign exactly one English routing verdict per item:

- `supported`: accessible, accurate, correctly contextualized, and supports the claim.
- `partially_supported`: real material supports only a narrower part of the claim.
- `unsupported`: accessible material does not support the quotation, Audience match, context, or claim.
- `inaccessible`: the original material cannot be independently opened or located.

## Blind-Review Boundary

- Do not read or infer an earlier Verifier's decision, including in blind recheck mode.
- Do not find substitute sources for a weak or inaccessible citation.
- Do not create or gate a Problem, propose an Idea, or discuss Sponsor technology.
- Do not modify the Research document.

## Output Document Contract

Write exactly one immutable Markdown document at `{output_target}`. Its YAML front matter must contain:

- `schema_version: 1`
- `artifact_id`, `audience_id`, `research_ref`, `researcher_id`, `verifier_id`, and `verification_round` copied from the manifest
- `artifact_type: verification`
- `run_id: {run_id}` and `stage: S3`
- `status: complete`
- `revision: 1`
- `created_by_session: {session_marker}` and `updated_by_session: {session_marker}`
- `source_refs` limited to the assigned Research document and Audience input
- `supersedes: null`
- on the first verification, `needs_second_verifier: true` only when one or more assigned items remain partially supported, internally conflicting, or genuinely ambiguous; otherwise `false`
- `recheck_evidence_ids` containing exactly the affected local Evidence ids when `needs_second_verifier` is true, otherwise an empty list
- in blind recheck mode, always set `needs_second_verifier: false` and `recheck_evidence_ids: []` because the two-Verifier budget is exhausted; preserve remaining uncertainty in the body instead of requesting a third review

The Markdown body must use these exact H2 headings:

## Verification Scope

Name the Research document and, for blind recheck mode, the assigned evidence ids. Do not mention an earlier review.

## Evidence Checks

Use one H3 per original local Evidence id. Label Evidence ref, URL accessible, Quote accurate, Context complete, Audience match, Claim support, Verdict, Reason, and Narrower supported claim where applicable.

## Conflicts and Uncertainty

List unresolved ambiguity without voting, smoothing over disagreement, or changing the upstream evidence.

## Empty Result and Completion

A Research document with no Evidence Candidates is valid. Record that fact and perform no substitute search. Return only a completion-envelope JSON object with `status` set to `completed` and `output_paths` containing exactly `{output_target}`.
