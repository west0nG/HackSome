{common_contract}

# S1 — Expand Audiences

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

Use only the `DiscoveryView` in this manifest. The full Challenge Brief and `ComplianceView` are not allowed, and no material from another run may be used.

{context_manifest}

## Task

Expand the challenge into relevant broad occupations, populations, communities, organization types, or life stages. A valid entry is at the natural level of “teacher,” “student,” or “independent developer”: it names who might be relevant without claiming what that person is doing.

Treat the `DiscoveryView`, including `explicit_audiences`, as clues rather than a list that must appear in the output. Include an audience only when the challenge theme or `problem_domains` independently ties that natural group to problems it directly experiences or participates in inside the domain.

Do not include a role merely because the challenge mentions it as a participant, judge, organizer, submission actor, Q&A contact, Sponsor, evidence author, or public-data source. If a mentioned person also has a genuine role inside the problem domain, name that domain role instead of the meta role.

For each entry, provide a stable local `audience_id`, a concise name, its broad type, its direct relationship to the challenge theme or `problem_domains`, and aliases useful for later searches. `direct_relevance` must explain that independent domain relationship; saying only that the prompt or `explicit_audiences` mentions the group is invalid.

## Forbidden Work

- Do not write a task, workflow, scenario, pain point, need, product, feature, or solution for an audience.
- Do not narrow an audience using an imagined behavior.
- Do not mention required or Sponsor technology.
- Do not rank audiences, target a fixed count, or force categories to differ.

## Empty Result

An empty `audiences` array is valid when the DiscoveryView supports no audience without speculation. Explain only genuine unresolved scope in `unknowns`; do not create an audience to avoid an empty output.

## Output

Return one JSON object matching the controller-provided S1 JSON Schema. Use its fixed English keys and write human-readable values in `{language}`. The controller will persist the valid object at `{output_target}`. Do not write Markdown, a completion envelope, or any additional file.
