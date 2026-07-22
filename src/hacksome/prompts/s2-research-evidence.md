{common_contract}

# S2 — Research Evidence

## Execution Metadata

- Run ID: {run_id}
- Task ID: {task_id}
- Attempt: {attempt}
- Mode: {mode}
- Output language: {language}
- Session marker: {session_marker}
- Assigned output target: {output_target}
- Web search: allowed, only for real problem evidence for the assigned Audience

## Context Allowlist

Use only the assigned `DiscoveryView`, one Audience record, source rules, search budget, and—only in a targeted evidence mode—the explicit gap plus prior URL/query list contained here. Do not read Verification, Problem, Gateway, Idea, competition, Red Team, Feasibility, or `ComplianceView` artifacts.

{context_manifest}

## Task

Find natural first-hand material showing what this Audience actually experiences. First decide where this group naturally discusses work or problems. Prefer GitHub Issues/Discussions and Reddit when relevant; also use App Store reviews, product review sites, professional forums, Hacker News, or another source that better fits the Audience. There is no platform quota.

On GitHub, look for bugs, feature requests, workflow friction, repeated manual steps, and user-written workarounds. On Reddit and forums, look for concrete “how do you handle,” “is there a tool,” “I am tired of,” switching, failure, time, cost, or risk accounts and substantive replies that support or contradict them.

Retain an exact URL, a locatable quotation or direct description, page date when available, access time, surrounding context, Audience fit, tentative problem claim, observed workaround, counterevidence, and the query that found it. A tentative claim is not a verified fact.

## Stage Boundary

- Do not create a Problem Card or apply the Problem Gateway threshold.
- Do not propose an Idea, feature, or Sponsor technology use.
- Do not treat SEO summaries or product marketing as first-hand user evidence.
- Do not allocate imagined pain directions or avoid evidence because another researcher may find something similar.

## Output Document Contract

Write exactly one immutable Markdown document at `{output_target}`. Its YAML front matter must contain these routing fields and no contradictory duplicates:

- `schema_version: 1`
- `artifact_id`, `audience_id`, `researcher_id`, and `research_round` copied from the manifest
- `artifact_type: research`
- `run_id: {run_id}` and `stage: S2`
- `status: complete`
- `revision: 1`
- `created_by_session: {session_marker}` and `updated_by_session: {session_marker}`
- `source_refs` copied from the allowlisted inputs
- `supersedes: null`

The Markdown body must use these exact H2 headings:

## Research Scope

State the Audience, search mode, bounded objective, and places searched.

## Evidence Candidates

Use one H3 per candidate with a local id such as `E-001`. For each, label Platform, URL, Page date, Accessed at, Quote, Context, Audience fit, Tentative claim, Observed workaround, Counterevidence or uncertainty, and Query.

## Query Log

Record every material query, search location, relevance, and access failure, including searches that returned nothing useful.

## Counterevidence and Uncertainty

Preserve contradictions, weak Audience matches, second-hand claims, and ambiguity.

## Coverage Gaps

List only concrete missing evidence or state that no further bounded gap was identified.

## Empty Result and Completion

If no credible evidence is found, still write the document with `None found` under Evidence Candidates and a truthful Query Log and Coverage Gaps section. Then return only a completion-envelope JSON object with `status` set to `completed` and `output_paths` containing exactly `{output_target}`. Never fabricate evidence to avoid an empty research result.
