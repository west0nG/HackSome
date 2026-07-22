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

For each entry, provide a stable local `audience_id`, a concise name, its broad type, its direct relationship to the DiscoveryView, and aliases useful for later searches.

## Forbidden Work

- Do not write a task, workflow, scenario, pain point, need, product, feature, or solution for an audience.
- Do not narrow an audience using an imagined behavior.
- Do not mention required or Sponsor technology.
- Do not rank audiences, target a fixed count, or force categories to differ.

## Empty Result

An empty `audiences` array is valid when the DiscoveryView supports no audience without speculation. Explain only genuine unresolved scope in `unknowns`; do not create an audience to avoid an empty output.

## Output

Return one JSON object matching the controller-provided S1 JSON Schema. Use its fixed English keys and write human-readable values in `{language}`. The controller will persist the valid object at `{output_target}`. Do not write Markdown, a completion envelope, or any additional file.
