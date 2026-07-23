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

First read `routing.review_mode`.

- In `draft_screen`, also read `routing.draft_screen_policy_version`. Version `4` is the compact-context form of the same primary-outcome closure judgment used by version `3`. Version `2` retains the strict causal-control rules without that closure test. A legacy context with version `1` or without this field retains the original four-claim screen. No historical context gains a new policy identity merely because this template was updated.
- In policy-4 `draft_screen`, use only `product_screen_view`. It is a controller-built, hash-bound projection of the passed Problem and immutable S6 Idea. Canonical references are provenance identifiers, not permission to open full documents. The full Problem, full Idea, Gateway, Research, Verification, `Current Workarounds`, Idea `Improvement over Current Workaround`, and evidence corpus are deliberately unavailable. Do not search for, infer, or reconstruct omitted material.
- In a historical policy-1, policy-2, or policy-3 `draft_screen`, use only its assigned immutable S6 Idea Draft revision, passed Problem and Gateway, and necessary verified evidence. Competition research does not exist yet and is forbidden.
- In every later mode, use only the latest S8 Idea Card revision, its passed Problem and Gateway, necessary verified evidence, this Idea's competition research, and the Product Red Team rules.

Never read S8 chat history, `ComplianceView`, implementation plans, Feasibility, another Idea, or any earlier Red Team document. This exclusion applies to `draft_screen`, product-repair, and scope-reduction re-review modes.

{context_manifest}

## Task

Attack whether the Idea exists as a real product Idea. Do not polish or complete it. The review has two scopes.

For `draft_screen`, test only these four independent claims:

1. A real target user can concretely feel the promised value in use, rather than receiving an abstract claim of intelligence or efficiency.
2. There is a User Flow with a trigger, real input, actual product processing, usable result or real-world action, and a felt-value moment—not pages or a feature list.
3. The Flow causally delivers the value without hidden human work, fake data, or unexplained magic in a critical step.
4. The Idea remains faithful to the passed user, scenario, and Problem instead of quietly changing the question.

Do not judge adoption, switching, or alternatives in `draft_screen`: S7 has not gathered the evidence. In `## Adoption Reason`, write that this test is explicitly deferred until the full post-S8 review. A missing adoption judgment is not a draft-screen failure.

For every later review mode, test all five independent claims:

1. A real target user can concretely feel the promised value in use, rather than receiving an abstract claim of intelligence or efficiency.
2. There is a User Flow with a trigger, real input, actual product processing, usable result or real-world action, and a felt-value moment—not pages or a feature list.
3. The Flow causally delivers the value without hidden human work, fake data, or unexplained magic in a critical step.
4. The user has an evidence-grounded reason to adopt or switch from the current workaround and alternatives.
5. The Idea remains faithful to the passed user, scenario, and Problem instead of quietly changing the question.

For every in-scope test, provide an attack, a checkable reference to the Idea or source facts, and a conclusion. Do not use a score.

## Evidence and Causal-Control Discipline

When `routing.draft_screen_policy_version` is `2`, `3`, or `4`, apply these rules before assigning its status. Apply the same evidence discipline to later full-review modes; do not retroactively relabel a legacy policy-1, policy-2, or policy-3 artifact:

- Every assertion made by the Idea about its own processing, inputs, integrations, permissions, state changes, or result is a claim to attack, never evidence that the claimed delivery or authority exists. Do not quote or paraphrase the proposed mechanism as proof of itself. Problem evidence can establish the user's Problem; it does not establish that this product solves it.
- Write the causal chain explicitly: passed Problem and required user value -> product-controlled trigger/input -> product-controlled processing -> immediate output/action -> felt-value moment. Distinguish the artifact the product produces from the Problem-aligned user value it actually delivers.
- A ticket, report, request, alert, export, or community post does not deliver a later answer, correction, approval, fix, or official/community action. If the passed Problem's relief arrives only after an uncontrolled third party responds or acts, mark the Idea `invalid` unless the artifact itself already delivers material Problem-aligned value before handoff.
- A workaround listed in the Problem is evidence of current user behavior and cost, not automatic proof that productizing that workaround solves the passed Problem. Reduced workaround effort counts only when it is itself a material part of the passed Problem's user value; do not silently replace understanding, recovery, completion, or another passed outcome with “easier reporting.”
- For every critical input and action, identify who owns it and whether the target user or product can plausibly control it. Naming an API, integration, internal manifest, interception hook, rollback, or state mutation does not establish access, permission, or authority.
- A missing core input or authority that the target user/product cannot plausibly control is a broken causal product boundary, not merely engineering difficulty to defer to S10. Do not reject merely because an input is private or authenticated: explicitly authorized enterprise data, customer-owned data, and first-party capabilities can be legitimate product inputs. Do not import a hackathon public-data rule into this screen; later feasibility and compliance checks own those separate questions.

## Primary-Outcome Closure Test (Policies 3 and 4)

When `routing.draft_screen_policy_version` is `3` or `4`, run this test before assigning status. Policy 4 changes only the context representation, not this judgment. Run the same test in every later full-review mode as well. Do not apply it retroactively to a policy-1 or policy-2 draft-screen artifact.

1. **Primary outcome:** Derive the blocked user state from the passed Problem's `## Problem` section itself and state it in one concrete sentence. Observed consequences may make the same Problem-native judgment or action more concrete, but they cannot substitute a different outcome. `## Current Workarounds` can never redefine the blocked state or choose an easier outcome for the product.
2. **Declared primary path:** Review only the Idea's explicitly stated Trigger -> primary output/action -> felt-value moment. Do not use an optional field, secondary audience, side effect, or reviewer-invented use to rescue a primary path that does not close the Problem.
3. **Immediate effect:** State the user-state change caused directly by that primary output or action, before any uncontrolled third party reads, responds, approves, publishes, fixes, or otherwise acts. Reformatting facts the user already supplied, or handing those facts to another actor, is not by itself a Problem-native state change.
4. **Closure comparison:** Compare that immediate effect with the exact blocked state. Apply the no-handoff counterfactual: **if no uncontrolled third party ever reads, responds, or acts, does the immediate output materially improve the exact blocked state?** If no, set `invalid`.

A useful downstream, coordination, reporting, ticketing, or workaround tool is still `invalid` for this branch when its immediate effect changes the target outcome instead of advancing the Problem's primary outcome. Making a ticket, report, or workaround easier cannot redefine the Problem unless the Problem's own `## Problem` section explicitly makes that burden the blocked user state. A partial solution may pass only when its immediate effect materially advances that same primary outcome; reducing another observed cost is insufficient.

In both `## Value Delivery` and `## Problem Fidelity`, explicitly state `Primary outcome:`, `Immediate effect:`, and `Closure comparison:` before the usual Attack, Evidence, and Conclusion. These statements must use the Problem-derived outcome and the product-controlled immediate effect, not the Idea's own value label.

Use `repairable` only for one local, bounded defect whose correction preserves the same core trigger, core output, core mechanism, felt-value moment, target user, and passed Problem. If validity requires replacing any of those core elements—or inventing control over a core dependency—set `invalid`. Do not use `repairable` as a softer label for a fundamentally different product.

Set the document status and Decision to exactly one of:

- `pass`: every claim in scope for this review mode withstands attack.
- `repairable`: the Problem and core value remain sound, but one explicit local Flow or product-mechanism defect can be repaired without changing the Problem. In `draft_screen`, this continues to S7 without editing the Idea and without consuming the later product-repair budget.
- `invalid`: felt value or a real User Flow is absent, value delivery is fundamentally false, or the Idea works only by replacing the passed Problem.

## Blind-Review Boundary

- Never look for, mention, or infer an earlier Red Team conclusion.
- Do not judge engineering difficulty, hackathon time, Sponsor technology, or competition-rule compliance.
- Do not edit the Idea or prescribe the rewritten solution. For `repairable`, describe the failure condition and boundary of a valid repair.
- Do not compare Ideas or reject one because another is similar.
- In `draft_screen`, only `invalid` is an early elimination decision. Do not turn deferred adoption evidence into `invalid` or `repairable`.

## Output Document Contract

Write exactly one immutable Markdown review at `{output_target}`. Its YAML front matter must contain:

- `schema_version: 1`
- `artifact_id`, `idea_ref`, `red_team_id`, and `review_mode` copied from the manifest
- only in `draft_screen`, `reviewed_idea_revision` and `reviewed_idea_sha256` copied exactly from the manifest; omit both fields in later modes
- `artifact_type: idea_red_team`
- `run_id: {run_id}` and `stage: S9`
- `status` exactly `pass`, `repairable`, or `invalid`
- `revision: 1`
- `created_by_session: {session_marker}` and `updated_by_session: {session_marker}`
- in policy-4 `draft_screen`, `source_refs` must be exactly the assigned Idea and Problem references from `routing.source_refs`; in historical draft screens and later modes, limit them to the assigned Idea revision, Problem, Gateway, verified evidence, and—only outside `draft_screen`—competition inputs; never include an earlier Red Team or Feasibility review
- `supersedes: null`

The body must use these exact H2 headings:

## Review Scope

Identify the Idea revision and blind mode without mentioning earlier review outcomes. In `draft_screen`, record the assigned policy version, revision, and SHA-256 binding.

## Felt Value

Label Attack, Evidence, and Conclusion.

## Real User Flow

Label Attack, Evidence, and Conclusion.

## Value Delivery

Label Attack, Evidence, and Conclusion.

## Adoption Reason

Label Attack, Evidence, and Conclusion.

For `draft_screen`, state that adoption and alternatives are deferred because no S7 evidence is available. Do not attack or conclude this claim.

## Problem Fidelity

Label Attack, Evidence, and Conclusion.

## Decision

State exactly `pass`, `repairable`, or `invalid`. For `repairable`, name one bounded defect and the invariant Problem/value that must remain. Do not write the fix.

## Completion

Return only a completion-envelope JSON object with `status` set to `completed` and `output_paths` containing exactly `{output_target}`.
