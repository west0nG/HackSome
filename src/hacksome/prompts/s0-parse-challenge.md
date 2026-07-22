{common_contract}

# S0 — Parse Challenge

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

The manifest below must contain only the raw challenge prompt, rules, and user-provided attachment text. Do not use prior audiences, research, problems, Ideas, benchmarks, or inferred background knowledge.

{context_manifest}

## Task

Extract the challenge exactly as stated. Separate the full `challenge_brief` from two derived views:

- `discovery_view`: theme, problem domain, explicitly named audiences, and non-technical boundaries relevant to discovering needs.
- `compliance_view`: required technology, Sponsor requirements, time limit, submission format, required deliverables, and other hard rules.

Preserve source wording where the schema asks for it. Record every missing fact as an unknown and preserve conflicting statements as a conflict. Do not resolve ambiguity by guessing.

## Forbidden Work

- Do not expand audiences or invent a more specific user.
- Do not research problems, products, competitors, or implementation approaches.
- Do not turn Sponsor technology into a proposed use case.
- Do not silently convert a preference into a hard rule.

## Output

Return one JSON object matching the controller-provided S0 JSON Schema. Use its fixed English keys and write human-readable values in `{language}`. The controller will persist the valid object at `{output_target}`. Do not write Markdown, a completion envelope, or any additional file.
