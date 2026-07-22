# Research: 2026 local Codex / Claude Code runtime landscape

- Query: What current runtime constraints matter when a local orchestrator drives Codex and Claude Code end to end, including parallel production of multiple candidate projects?
- Scope: mixed (local environment inspection + primary official documentation/repositories + vendor research)
- Date: 2026-07-22

## Findings

### Executive product constraints

1. **There is no symmetric, provider-neutral runtime contract.** Both products can run headlessly and emit machine-readable streams, but event names, completion/error semantics, permission models, session identifiers, and budget controls differ. The product therefore needs to own a small normalized run record rather than treating either provider transcript as workflow state. *(Inference from the facts below.)*
2. **Parallel candidate production increases the value of orchestration, but also makes isolation a v1 requirement even without VM/Docker.** Each candidate needs a separate working directory or git worktree, process group, provider session, logs, and budget ledger. Otherwise concurrent agents can overwrite files, resume the wrong session, contend for ports, or leak one candidate's context into another. This is process/workspace isolation, not strong hostile-code isolation. *(Inference.)*
3. **“Local, no Docker” and “unattended full access” are in tension.** Both vendors explicitly reserve permission-bypass/full-access modes for externally isolated environments. A first local release can be autonomous inside scoped workspaces, but should not equate that with safely running arbitrary dependencies, publishing, or exposing user credentials. *(Inference grounded in both vendors' security docs.)*
4. **Budget controls are asymmetric.** Claude exposes dollar and turn ceilings through its Agent SDK; its CLI exposes a dollar ceiling. Codex emits token usage but the inspected CLI has no equivalent whole-run `max budget` or `max turns` switch. Portfolio-level limits therefore cannot be delegated to the providers: the orchestrator must aggregate cost/time across all candidate projects and be able to terminate processes. *(Fact + inference.)*
5. **MCP helps, but does not erase the asymmetry.** Codex's MCP server exposes an agent-start tool plus a thread-continuation tool. `claude mcp serve` exposes Claude Code's file/shell tools to another MCP client; Anthropic explicitly says the client remains responsible for confirmations. It is not the same agent-session RPC abstraction. *(Fact.)*
6. **Existing coding benchmarks do not validate the proposed product.** They provide evidence for repository editing and terminal work, not opportunity discovery, novelty, product taste, demo coherence, deck truthfulness, or portfolio selection. OpenAI now also warns that SWE-bench Verified is contaminated and estimates roughly 30% of SWE-Bench Pro tasks are broken. End-to-end hackathon evaluation must therefore be a separate product requirement. *(Fact + inference.)*

### Files found

- `.trellis/tasks/07-22-hackathon-agent-product/prd.md` — current product requirements; local Codex/Claude orchestration is required at lines 20-24 and 39-43, while time/cost and external-action boundaries remain open at lines 64-70 and 82-89.
- `.trellis/workflow.md` — Trellis planning/research workflow; no runtime implementation exists yet.
- `AGENTS.md` — repository-level Trellis instructions.
- No application code, runtime adapter, dependency manifest, or tests were found in the repository as of this review.

### Local environment snapshot

Read-only CLI inspection on 2026-07-22 found:

- `codex-cli 0.142.5`
- `Claude Code 2.1.209`

This snapshot is useful for flag-level feasibility, but these tools release frequently; production code should pin and capability-check versions rather than parse an assumed “latest” surface. *(Inference.)*

### Capability comparison: official facts

| Concern | Codex | Claude Code |
|---|---|---|
| Headless invocation | `codex exec` is documented for scripts/CI. Normal mode streams progress to `stderr` and leaves the final message on `stdout`. | `claude -p` / `--print` is non-interactive; stdin piping is supported. |
| Event stream | `--json` changes stdout to JSONL. Documented events include `thread.started`, `turn.started`, `turn.completed`, `turn.failed`, `item.*`, and `error`; `turn.completed` includes input, cached-input, output, and reasoning token usage. | `--output-format stream-json` emits JSON messages/events; partial model events are available with `--include-partial-messages`. Retry events are explicitly surfaced as `system/api_retry`. |
| Typed final output | CLI `--output-schema <file>` requests a JSON-Schema-conforming final response. The TypeScript SDK supports per-turn `outputSchema`. | CLI `--output-format json --json-schema ...` returns `structured_output`. Agent SDK supports JSON Schema and reports a distinct `error_max_structured_output_retries` terminal subtype. |
| Session continuation | `codex exec resume <SESSION_ID>` / `--last`; SDK `resumeThread(id)`. `--ephemeral` prevents session rollout persistence. | `--continue`, `--resume <id>`, explicit `--session-id`, and `--fork-session`; `--no-session-persistence` disables persistence. Print/SDK sessions can be resumed by ID even though they do not appear in the picker. |
| Branching semantics | No explicit thread-fork operation appears in the inspected CLI/SDK docs. | Native fork/branch creates a new session ID and leaves the original unchanged. Session-only permission approvals do not carry into the fork. |
| Cost / iteration limits | JSONL reports token usage. No whole-turn `--max-budget`, `--max-turns`, or wall-clock deadline appears in `codex exec --help` for 0.142.5 or its official non-interactive guide. | CLI has `--max-budget-usd` in print mode. Agent SDK has `maxTurns` and `maxBudgetUsd`; limit exits have typed result subtypes and still carry session ID, usage, turn count, and normally cost. Anthropic says an SDK session itself has no timeout. |
| Filesystem permissions | `codex exec` defaults to a read-only sandbox; explicit `workspace-write` and `danger-full-access` modes exist. Sandbox and approval policy are separate controls. | Fine-grained allow/ask/deny rules apply to tools. Bash sandboxing uses OS primitives and filesystem/network boundaries; built-in file tools remain permission-controlled separately. |
| Failure closed | A required Codex MCP server that fails initialization makes `codex exec` error. | If the Claude Bash sandbox cannot start, the documented default is to warn and run commands unsandboxed; `sandbox.failIfUnavailable: true` is required to make absence a hard failure. |
| Programmatic SDK | TypeScript SDK (Node 18+) wraps the Codex CLI and exchanges JSONL; Python SDK (Python 3.10+, beta) controls local app-server via JSON-RPC and pins a CLI runtime. | TypeScript/Python Agent SDK streams typed messages, supports hooks, permissions, session resume/fork, structured output, MCP, subagents, max turns, and budget. SDK packages bundle a native Claude Code binary. |
| MCP as client | Codex supports MCP servers as tools; permissions remain configurable. | Claude Code supports local stdio and remote HTTP MCP servers with per-tool permissions and managed allow/deny policy. |
| MCP as server | `codex mcp-server` exposes `codex` (start) and `codex-reply` (continue by thread ID), with model, cwd, sandbox, and approval overrides. | `claude mcp serve` exposes Claude Code tools such as file viewing/editing; Anthropic says the MCP client must implement confirmations. |

Primary docs: [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive), [Codex SDK](https://developers.openai.com/codex/sdk), [Codex TypeScript SDK repository](https://github.com/openai/codex/tree/main/sdk/typescript), [Codex MCP server](https://learn.chatgpt.com/docs/mcp-server), [Codex sandboxing](https://learn.chatgpt.com/docs/sandboxing), [Claude headless mode](https://code.claude.com/docs/en/headless), [Claude CLI reference](https://code.claude.com/docs/en/cli-usage), [Claude sessions](https://code.claude.com/docs/en/sessions), [Claude Agent SDK loop](https://code.claude.com/docs/en/agent-sdk/agent-loop), [Claude structured outputs](https://code.claude.com/docs/en/agent-sdk/structured-outputs), [Claude permissions](https://code.claude.com/docs/en/permissions), [Claude sandboxing](https://code.claude.com/docs/en/sandboxing), [Claude MCP](https://code.claude.com/docs/en/mcp), [Claude Agent SDK hosting](https://code.claude.com/docs/en/agent-sdk/hosting).

### Consequences for parallel multi-project production

These are product-definition inferences, not vendor promises:

- **Concurrency must be explicit and bounded.** “Generate many projects” should mean a configured portfolio size and maximum simultaneous runs, not unconstrained agent fan-out. Each child agent and retry consumes provider quota, context, local CPU/RAM, ports, and wall time.
- **Budgets need at least three scopes:** per run, per candidate project, and total portfolio. Claude's native caps can enforce part of the first scope; Codex and the cross-provider total require controller-side accounting and cancellation.
- **Provider sessions are caches, not the source of truth.** Candidate identity, stage, evidence, decision status, and artifact paths should survive a provider session becoming unavailable. Cross-provider handoff cannot resume the other vendor's session ID.
- **Use separate filesystem roots/worktrees per candidate.** Both CLIs key important behavior and session lookup to working directories. Parallel agents sharing one checkout would make diffs, current branch, ports, session selection, and evidence attribution ambiguous.
- **Credential and network scope become multiplicative.** One over-privileged run is risky; many concurrent over-privileged runs widen exposure and make attribution harder. GitHub push/deploy should remain a separately authorized capability rather than an ambient credential available to every candidate builder.
- **Selection evidence must be comparable.** Parallelism only helps if every candidate emits the same minimal evidence envelope (run status, usage/cost, tests, runnable demo path, screenshots, claims), so a selector compares artifacts rather than persuasive self-reports.

### Permission boundary that matters for v1

Official documentation from both vendors treats strong bypass modes as appropriate only with external isolation. Since v1 explicitly omits VM/Docker, the defensible autonomous boundary is narrower:

- Codex: scoped workspace-write sandbox, explicit network policy, no `danger-full-access` default.
- Claude: enable Bash sandboxing in settings, set `sandbox.failIfUnavailable: true`, use explicit tool allow/deny rules, and avoid `bypassPermissions`.
- Both: give each candidate only its own workspace; keep publishing credentials and destructive external actions out of the ambient process environment.

The last bullet is an inference, but follows both vendors' guidance that sandbox boundaries and permission approval are distinct and that bypass/full access is intended for externally isolated environments.

### Evaluation evidence and its limits

- OpenAI reports strong current coding/terminal benchmark results for GPT-5.6, but those numbers are model-and-harness results, not evidence for this orchestrator's full Idea → Build → Pitch loop: [GPT-5.6 evaluation report](https://openai.com/index/gpt-5-6/).
- OpenAI says SWE-bench Verified is no longer a useful frontier signal because of contamination and recommends SWE-Bench Pro instead: [Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/).
- OpenAI's 2026 audit then estimates roughly 30% of SWE-Bench Pro tasks are broken, underscoring that automated tests can misgrade both successes and failures: [Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/).
- Anthropic system cards report SWE-bench and Terminal-Bench results under defined harnesses, budgets, and timeout policies; the Opus 4.7 card explicitly notes Terminal-Bench sensitivity to inference latency: [Claude Opus 4.7 System Card](https://www-cdn.anthropic.com/037f06850df7fbe871e206dad004c3db5fd50340/Claude%20Opus%204.7%20System%20Card.pdf).

**Inference:** runtime acceptance testing should include provider-adapter contract tests plus a small fixed set of end-to-end hackathon tasks. Coding benchmarks may inform model choice, but cannot be the success metric for novelty, taste, useful demand, pitch quality, or consistency between Repo, Demo, and Deck.

### Recommended decisions to carry into the PRD (not a full system design)

1. Treat “parallel production of multiple candidate projects” as a first-class requirement with explicit portfolio size, max concurrency, and per-run/per-candidate/portfolio budgets.
2. Define one provider-neutral terminal result with at least: candidate/run ID, provider + pinned version/model, provider session ID, status/reason, timestamps, usage/cost, artifact paths, permission profile, and evidence references.
3. Require hard controller cancellation/deadlines even when provider SDKs expose their own limits.
4. Require fail-closed sandbox initialization for unattended runs; do not allow full-access/bypass as the default while external isolation is out of scope.
5. Keep workflow state and decision history outside provider transcripts; use resume only as an optimization for continuity.
6. Version-gate adapters with startup capability probes because CLI surfaces evolve independently.

## Related specs

- `.trellis/spec/guides/index.md` — flags cross-layer contracts such as JSONL records and event kinds as requiring deliberate end-to-end treatment.
- No backend/frontend implementation spec currently governs this runtime because the repository has no application code yet.

## Caveats / Not Found

- The OpenAI developer-docs MCP server was not callable in this research session. Because this researcher role may write only inside the task's `research/` directory, it did not install or modify global Codex MCP configuration; official OpenAI documentation and the official `openai/codex` repository were used instead.
- Negative claims about missing Codex budget/turn flags are bounded to the inspected `codex-cli 0.142.5` help and current official guide, not a guarantee that no lower-level/private setting exists.
- No paid live agent runs were executed, so JSON event compatibility, schema retry behavior, actual cost accounting, and cancellation were not empirically tested.
- No claim is made that local sandboxing is equivalent to VM/container isolation. Anthropic documents Bash-only sandbox coverage, and both products retain other tool/credential trust boundaries.
- Vendor benchmark results are not directly comparable unless model, scaffold, reasoning effort, token/time budget, and task subset match.
