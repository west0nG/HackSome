# HackSome Common Stage Contract

- Perform only the assigned stage. Do not take over an upstream or downstream role.
- Treat the Context Manifest as the complete input allowlist. Read only the listed files and facts; do not inspect the wider run directory, conversation history, project rules, hooks, apps, goals, or other candidates.
- Do not spawn sub-agents. One Codex session produces only its assigned output.
- Follow the stage's web-search boundary exactly. When search is forbidden, do not browse. When it is allowed, stay inside the stated purpose.
- Never invent a user, scenario, quote, source, product capability, dependency, or rule. Mark missing facts as unknown. A truthful empty result is valid.
- Apply absolute criteria only. Never rank, score, select a Top-K, enforce a candidate quota, force different directions, merge similar candidates, or remove a candidate merely because it resembles another.
- Preserve upstream artifacts. Write only to the assigned output target, and never silently overwrite evidence or review records.
- Use the exact English Markdown headings and routing values required by the stage. Write prose beneath those headings in the configured input language.
- A structured completion envelope reports only status and paths. It must not duplicate a Markdown artifact's body.
- Stop when the stated output is complete or when honest evidence is exhausted. More prose is not a substitute for evidence or judgment.
