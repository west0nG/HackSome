{common_contract}

# S7 — Research Competitors

## Execution Metadata

- Run ID: {run_id}
- Task ID: {task_id}
- Attempt: {attempt}
- Mode: {mode}
- Output language: {language}
- Session marker: {session_marker}
- Assigned output target: {output_target}
- Web search: allowed, only for alternatives to the assigned Idea and Problem

## Context Allowlist

Use only one Idea Draft, its passed Problem and Gateway record, necessary evidence, source rules, and—only in targeted-gap mode—the explicit missing object or claim plus prior URL/query list. Do not read another Idea or its research, `ComplianceView`, Sponsor requirements, Red Team, Feasibility, or an earlier competition report as a conclusion.

{context_manifest}

## Task

Research reality after the Idea has already been formed. Search from the user's language, current workflow, Problem, and core mechanism—not only the invented product name.

Cover direct products, tools solving an adjacent step, manual or general-purpose alternatives, relevant open-source projects, and discontinued or failed approaches. Look for why users adopt, tolerate, replace, or abandon them. Marketing claims alone do not establish user behavior.

For every factual claim about audience, workflow, capability, pricing, availability, or status, retain a URL, quotation or locatable fact, and access date. Mark anything unverified as unknown. A highly similar product is evidence, not an automatic rejection.

## Stage Boundary

- Do not modify the Idea or propose its next revision.
- Do not decide whether the Idea survives, rank alternatives, or apply a Gateway.
- Do not evaluate Sponsor technology fit.
- Do not turn a vague wish for “more research” into an unbounded second round.

## Output Document Contract

Write exactly one immutable Markdown document at `{output_target}`. Its YAML front matter must contain:

- `schema_version: 1`
- `artifact_id`, `idea_ref`, `researcher_id`, and `research_round` copied from the manifest
- `artifact_type: competition`
- `run_id: {run_id}` and `stage: S7`
- `status: complete`
- `revision: 1`
- `created_by_session: {session_marker}` and `updated_by_session: {session_marker}`
- `source_refs` limited to the assigned Idea, Problem, Gateway, and evidence inputs
- `supersedes: null`

The Markdown body must use these exact H2 headings:

## Research Scope

State the Idea, Problem, mode, and bounded search coverage.

## Direct Competitors

Record verified target user, core flow, capabilities, access or pricing, status, and sources. `None found` is valid.

## Indirect Alternatives and Workarounds

Include adjacent tools, manual methods, and general-purpose substitutes.

## Open Source Projects

Record relevant repositories and verified maintenance or capability facts.

## Adoption and Abandonment Evidence

Preserve first-hand reasons users adopt, tolerate, switch, or stop using alternatives.

## Overlap and Differences

State factual overlap, unmet portions, and switching barriers without a survival conclusion.

## Sources and Query Log

Record URLs, facts or quotations, access dates, searches, relevance, and failures.

## Counterevidence and Coverage Gaps

Keep contrary signals and only concrete unsearched gaps visible.

## Empty Result and Completion

If no relevant competitor is found, still write a truthful report with the queries and coverage limits. Return only a completion envelope with `status: completed` and `output_paths` containing exactly `{output_target}`.
