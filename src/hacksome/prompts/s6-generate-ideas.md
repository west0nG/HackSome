{common_contract}

# S6 — Generate Ideas

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

Use only one passed Problem revision, its `pass` Gateway record, cited verified evidence, the `DiscoveryView`, and Useful Idea principles. Do not read `ComplianceView`, Sponsor requirements, competitors, another Problem, another Generator's output, or an existing Idea.

{context_manifest}

## Task

Generate zero or more independent product Idea Drafts for the passed Problem. First ground yourself in the evidence-backed user, scenario, problem, and current workflow. Then choose a product intervention that preserves that Problem.

Each Idea needs an end-to-end core path: a real trigger, real user input, actual product processing, a usable result or real-world action, and the moment the user feels the value. Prevention, step completion, decision support, handoff reduction, and recovery are optional thinking aids, not direction quotas.

## Stage Boundary

- Do not browse, research competitors, read Sponsor requirements, or choose a technology to satisfy a rule.
- Do not output only a name, slogan, feature list, generic chat wrapper, page sequence, fake-data front end, or hidden-human workflow.
- Do not rank, merge, deduplicate, force direction differences, or approve a Draft for the next quality gate.
- Do not change the passed user, scenario, or Problem to make an Idea sound better.

## Output Document Contract

`{output_target}` is the only allowed output directory. Write one Markdown file per independently coherent Idea using the manifest's assigned paths and the Generator's local id space. Every file's YAML front matter must contain:

- `schema_version: 1`
- `artifact_id`, `idea_id`, `problem_ref`, and `generator_id` copied from routing data or allocated within the assigned local id space
- `artifact_type: idea`
- `run_id: {run_id}` and `stage: S6`
- `status: draft`
- `revision: 1`
- `created_by_session: {session_marker}` and `updated_by_session: {session_marker}`
- `source_refs` limited to the passed Problem, Gateway pass, DiscoveryView, Research, and Verification inputs
- `supersedes: null`

Every Idea Draft body must use these exact H2 headings:

## User and Problem

Name the user and cite the passed Problem without changing it.

## Trigger

Describe when and why the user begins this flow.

## End-to-End User Flow

Describe real input, actual processing, result or action, and the felt-value moment.

## Core Mechanism

Explain what the product actually does, not merely its interface.

## Minimum Necessary Features

Include only features needed to deliver the core flow.

## Improvement over Current Workaround

State the evidence-grounded time, cost, risk, or failure expected to improve.

## Evidence

Cite the Problem and the evidence relevant to the proposed intervention.

## Assumptions and Failure Modes

State dependencies, untested causal assumptions, and the strongest reason the Idea may fail.

## Pending Checks

State that competition and Sponsor-technology fit have not yet been checked.

## Empty Result and Completion

Zero Idea Drafts is valid when no honest end-to-end intervention can be formed. Then write no placeholder file and return `status: empty` with an empty `output_paths` array. Otherwise return `status: completed` and every created path. Never target a fixed Idea count.
