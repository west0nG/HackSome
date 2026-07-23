# Journal - weston (Part 1)

> AI development session journal
> Started: 2026-06-26

---



## Session 1: Agent Layer phases 0-5: declarative single-agent wrapper + E2E

**Date**: 2026-06-27
**Task**: Agent Layer phases 0-5: declarative single-agent wrapper + E2E
**Branch**: `main`

### Summary

Built the Agent layer (foundagent-v6 skeleton layer 2) on top of the VM layer. Ran a pre-spike first (S1-S3) that caught two latent bugs and corrected design.md: stream-json result parsing must use is_error not subtype (401 keeps subtype=success), and ANTHROPIC_API_KEY silently overrides CLAUDE_CODE_OAUTH_TOKEN so credential injection must be mutually exclusive. Then implemented phases 0-3 (agent/ package: spec/credentials/provider/loadout/runner + agents/ declarations; 26 unit tests + live smoke), phase 4 (broker refactored to single path calling the agent layer; regression demo green), phase 5 (AC6 end-to-end on public test login the-internet: computer-use + browser + account injection + skill/hook/charter loadout + provider/cred seam all proven, ok=True, token zero-leak verified). AC1/2/4/5/6/7 met; AC3 subscription side + mutual-exclusion seam met. FOLLOW-UP: AC3 api-key real-key end-to-end is DEFERRED — no real ANTHROPIC_API_KEY available; path/recognition/priority verified, re-verify minimal call when a key is provided (config into accounts/, no code change needed). Spike contracts sunk into .trellis/spec/backend/agent-execution-contracts.md. Task archived; parent foundagent-v6 now 1/4.

### Main Changes

- 将 `foundagent.net` 地址改为 Company 级永久认领，全局唯一且每 Company 固定最多 5 个。
- 新增平台单实例 mail-router、Company journal、CEO 单播与 Department/Worker 受控 peek/send。
- 重写邮件 Skills、角色 loadout、Compose/Makefile 运维入口及跨层可执行规范。
- 对齐 rebase 后主干已删除的 `company-methods` / `submit-verdict` Skill 契约。

### Git Commits

| Hash | Message |
|------|---------|
| `38be826` | (see git log) |
| `8574e49` | (see git log) |
| `f6176b2` | (see git log) |
| `6a70dbc` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete

## 2026-07-03 · 07-02-visual-asset-skills 三原子落地（feat/growth-visual-asset）
- design-asset(7da42fd) / gen-image(9f164af) / visual-iterate(aeb2937) 三 commit 落齐；growth 挂 7 skill；43 测试绿；trellis-check 末轮全过（含 3 文件 verbatim 字节级抽查）。
- 实证链：盲评 agent 无上下文产出合格 XHS 封面 → 校验器戳穿其"密度≥75%"自评(实际67%) → fresh 评审 1High/2Medium → 2 处外科修复 → 校验器全绿 + delta 复核 PASS。doer≠judge + 脚本门先行两条教义都拿到了实锤。
- 教训№2 依赖闭包：guizang 文档假设的种子模板/webgl/image-overlay 又漏 vendor，被盲评抓出（de-ai-ify 同款教训，断言已锁）。
- 半开：AC4 API 主路径缺 OPENAI_API_KEY（副路径 Codex e2e 已通）；AC6 尺寸未对官方复核（host 已改诚实标注，首次真实发布时闭环）。
- 偏离已记档：俄语译文附录放弃(LLM 原样读)；调研 render.mjs 之说有误(上游无此文件)。


## Session 2: Per-company state/ consolidation + persistent agent sessions

**Date**: 2026-07-03
**Task**: Per-company state/ consolidation + persistent agent sessions
**Branch**: `main`

### Summary

Investigated persistence: ledger/inbox/company state were durable but scattered (companies/, orchestration/{ledger,inbox}) and agent claude sessions were container-local (lost on rebuild). Consolidated all mutable host state into per-company state/<company>/{company,ledger,inbox,sessions/<role>} with COMPANY env (was PUMP_COMPANY) selecting the stack's company; container paths unchanged. Sessions persist via /sessions mount + CLAUDE_CONFIG_DIR per role — verified RESUMED-OK across full container rebuild. Fixed hardcoded container_name blocking a second compose project; verified two-company ledger isolation. Migrated 4 wikis + 6 goals + all inboxes; 191 tests green; specs updated.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `75768f6` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 3: Company loadout overlay: per-company skill/charter/hooks/MCP/peripheral toggles

**Date**: 2026-07-03
**Task**: Company loadout overlay: per-company skill/charter/hooks/MCP/peripheral toggles
**Branch**: `main`

### Summary

Planned (prd/design/implement reviewed by user), implemented and live-verified the per-company loadout overlay: state/<company>/config/loadout.yaml declares diffs vs role-yaml baselines (skills on/off incl. beyond-baseline, charter/hooks/mcp tri-states, defaults block, peripheral adapter allowlist). Single parser agent/overlay.py shared by resident_loadout, agent_loop, peripheral runner, and the new make loadout-check offline validator (warnings promoted to errors). materialize() gained manifest-based reconcile (.loadout-manifest.json) so off-toggled skills/hooks are removed on restart without touching agent-installed content; check pass caught and fixed a manifest path-traversal hole and a shape-crash. 230 tests + live e2e (COMPANY=e2e-loadout: all toggles observed in logs/disk, on->off->restart reconcile confirmed). Merged as PR #205; spec captured in .trellis/spec/backend/loadout-overlay-contracts.md; SOP updated (test combos via overlay, never edit baselines).

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `237a548` | (see git log) |
| `f466405` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 4: CLI toolchain e2e

**Date**: 2026-07-03
**Task**: CLI toolchain e2e
**Branch**: `main`

### Summary

Baked pinned gh/vercel/wrangler/linkinator and common shell tools into the agent image, documented account env provisioning, verified real GH/Vercel/Cloudflare token e2e, then archived the CLI toolchain task.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `64bf8e4` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 5: Proxy slot: per-account static egress (CUA_PROXY)

**Date**: 2026-07-03
**Task**: Proxy slot: per-account static egress (CUA_PROXY)
**Branch**: `main`

### Summary

Split the residential-IP proxy slot out of 07-03-social-rail and shipped it early (user call). CUA_PROXY in accounts/<id>/secrets.env expands via agent/proxy_env.sh, sourced ONLY in the computer-server subshell of the startup hook. Key finding (squid-verified): claude CLI ignores host-based NO_PROXY entries — only '*' is honored — so LLM-traffic insulation must be structural scoping, not an exclusion list. e2e on isolated ceo stack: six vars in computer-server environ, agent_loop clean, real wake produced zero Anthropic CONNECTs through squid; negative path zero-impact. Spec updated in resident-agent-contracts.md.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `ac9cf9b` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete

---

## Session 6: Model/effort pin per role yaml (default opus-4.8 + xhigh)

**Date**: 2026-07-03
**Task**: `07-03-model-effort-config` (archived)

### Summary

User asked what model/effort the agents run at — answer was "account default,
unconfigured". Fixed: agents/<role>.yaml now takes optional model:/effort: keys;
fleet defaults claude-opus-4-8 + xhigh live in agent.spec (DEFAULT_MODEL/
DEFAULT_EFFORT, single source of truth); explicit null opts back into the CLI
default. Wired through all three invocation paths: ClaudeCodeProvider.build_exec
(one-shot), agent_loop.main() via _role_model_effort (resident; missing/broken
yaml -> WARN + defaults, never-brick), and the objective reviewer (fleet
defaults, no role yaml).

### Git Commits

| Hash | Message |
|------|---------|
| `626825d` | feat(agent): pin model/effort per role yaml (default opus-4.8 + xhigh) |

### Testing

- [OK] 279 unit tests green (7 new: provider defaults/override/null-optout,
  spec parsing, argv builders, _role_model_effort never-brick, reviewer pin)
- [OK] e2e in-container: image CLI 2.1.197 has --model/--effort; subscription
  creds serve opus-4.8 (`claude -p ... --model claude-opus-4-8 --effort xhigh`
  returned success, cost ~$0.04)

### Status

[OK] **Completed**

## Session 7: MCP loadout: per-role mcp.json (GA4 / DataForSEO / GSC / Playwright)

**Date**: 2026-07-03
**Task**: `07-03-mcp-loadout` (in_progress — AC2 real-credential e2e pending user provisioning)

### Summary

Per-role MCP baselines replaced the fleet-wide AGENT_MCP env: agents/mcp/<role>.json
declared by each role yaml's mcp_config (researcher = cua+dataforseo+gsc+playwright,
ceo/growth = cua+ga4, builder/verifier = cua-only). agent_loop resolves
AGENT_MCP env > role yaml > baked-in fallback via _role_config (renamed from
_role_model_effort); loadout overlay applies on top unchanged. --strict-mcp-config
is now unconditional so overlay `mcp: off` is truly off. Servers pinned into the
image: dataforseo-mcp-server@2.9.11 + @playwright/mcp@0.0.77 (npm),
analytics-mcp==0.6.0 + mcp-gsc==0.1.0 (pip, wheel-verified SA mode), chromium
baked at /opt/ms-playwright. Fixed latent provider.py bug (yaml-relative
mcp_config resolved against cwd). Playwright-vs-CLI timebox: MCP won (33% faster;
"4x token" claim did not reproduce — ~14% cost gap on claude 2.1.x ToolSearch +
mcp 0.0.77 file snapshots); numbers in task research/playwright-vs-cli.md.

### Git Commits

| Hash | Message |
|------|---------|
| `f4b5e84` | feat(agent): per-role mcp.json baseline (GA4/DataForSEO/GSC) + strict-mcp-config |
| `77a0015` | feat(vm): pin GA4/DataForSEO/GSC MCP servers into the agent image |
| `49a0a81` | docs(accounts): DataForSEO keys + Google SA provisioning for MCP loadout |
| `4328c0e` | chore(task): mcp-loadout planning artifacts (design/implement + manifests) |
| `009c3b7` | docs(spec): per-role MCP baseline contracts (07-03 mcp-loadout) |
| `7830a7f` | feat(agent): playwright MCP joins the researcher loadout |
| `581f4c2` | docs: playwright-vs-cli findings + spec sync for researcher loadout |

### Testing

- [OK] 308 unit tests green (argv strict unconditional, _role_config precedence,
  asset pins incl. ${VAR}-only credentials, overlay regression = AC3)
- [OK] trellis-check: 6/6 focus areas pass, 0 fixes needed
- [OK] smoke in-container: boot mcp=agents/mcp/researcher.json; credless
  dataforseo/gsc fail gracefully while cua-local screenshots (CUA_OK) and
  playwright navigates (PW_OK, baked chromium, uid 1000)
- [OK] AC2 DataForSEO half (2026-07-04): real creds injected, researcher
  fetched "coffee" search volume 6,120,000 via MCP (DFS_OK; balance $48.43)
- [DEFERRED] AC2 GSC half -> domain-rail follow-up task (user decision:
  foundagent.net root domain provisioned; property verification + SA grant +
  GSC e2e move there)

### Status

[OK] **Completed — archived with GSC half handed to domain-rail**


## Session 6: Social rail MVP: the agent's browser is its own browser (X cookies e2e)

**Date**: 2026-07-06
**Task**: Social rail MVP: the agent's browser is its own browser (X cookies e2e)
**Branch**: `main`

### Summary

07-03-social-rail delivered end-to-end in one session. Two user rulings reshaped the task: scope cut to an X-cookies MVP (IG token-refresh job, three OAuth mint helpers, four-platform checklist all deferred), then the two-browser split overruled — one browser per agent, default logged-in, like a human never using incognito. Shipped agent/browser_mcp.sh (three independent degradations over load-bearing --browser chromium: no DISPLAY -> --headless; /account/cookies/storage-state.json -> --isolated --storage-state pair; CUA_PROXY -> --proxy-server), rewired all five role MCP jsons, gitignored accounts/*/cookies/, exact-argv wrapper tests (325 total green), README export doc, spec contract update. Verified in-container: headed chromium on kasm DISPLAY, isolated seed branch, then real-cookies e2e — extension-export cookies converted to storage-state, x.com logged in as @Solvotheagent, one test tweet posted and confirmed. All ACs green; task archived.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `6c11b76` | (see git log) |
| `0d2318f` | (see git log) |
| `026662f` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 7: create-role: runtime role creation + unified verifier review seat

**Date**: 2026-07-06
**Task**: create-role: runtime role creation + unified verifier review seat
**Branch**: `main`

### Summary

Delivered 07-06-create-role end to end: role CLI (propose/verdict/list/retire/status, AGENT_KEY identity gate, fail-closed pending), non-LLM provisioner (queue -> 4-file materialization + compose override rendered from the live x-agent anchor + own git commits + registry authorization gate), create-role/review-role skills (v1 positive-guidance only), verifier becomes the company's single review seat (objective propose migrated, inline reviewer deleted, company verdict vocabulary unified to PASS/FAIL). 385 unit tests. Real-LLM sandbox e2e all green: objective PASS round-trip; mediocre role proposal FAILed with rubric-grounded reasons while a qualified one PASSed, was materialized, survived restart, completed a real Hub-routed goal past blind verifier acceptance, then retired. Gate opened (create-role wired into ceo.yaml); observing a production CEO wake deferred to the next make up.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `5807c50` | (see git log) |
| `5da66d8` | (see git log) |
| `7fca5e6` | (see git log) |
| `159e4c1` | (see git log) |
| `d288d9d` | (see git log) |
| `cb5e5bf` | (see git log) |
| `e2a458b` | (see git log) |
| `a9869d6` | (see git log) |
| `58eb2ff` | (see git log) |
| `81c2c1c` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete

## Session 8: Domain rail completed

**Date**: 2026-07-07
**Task**: Domain rail completed
**Branch**: `main`

### Summary

Completed foundagent.net domain rail: GSC Domain property and service-account MCP e2e, Cloudflare DNS create/delete e2e, GA4 account-level service-account access, provision-ga4 skill, account README, and backend account-package spec.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `210f4bb` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete

## Session 9: codex-runtime: dual-runtime abstraction (claude-code / codex per-role switch)

**Date**: 2026-07-07
**Task**: Runtime abstraction: claude-code / codex switchable agent runtime
**Branch**: `worktree-codex-runtime`

### Summary

Delivered 07-07-codex-runtime end to end: neutral runtime contract (agent/runtimes/base.py: RunRequest/RunResult/Runtime protocol) with the two CLI adapters as the only files knowing their CLIs; merged the duplicated claude argv builders (agent_loop's inline build_claude_argv + provider.py's build_exec) into one ClaudeCodeRuntime locked by a 192-case pre-refactor golden snapshot (3 deliberate diffs only); CodexRuntime built on real captured 0.142.5 fixtures (gpt-5.5 + xhigh defaults, user decision). Session token redefined as adapter-returned (codex can't pre-set thread ids; uses_session_hint keeps timeouts from poisoning resume). Per-role CODEX_HOME nests under /sessions/<role>/codex; config.toml rendered from the same agents/mcp/<role>.json (env refs expanded, chmod 600); subscription auth seeded from accounts/<id>/codex-auth.json (per-role copy, refresh writes back). Four-var credential exclusion — live-pinned: CODEX_API_KEY silently outranks auth.json. Both CLIs ARG-pinned in the image (claude 2.1.202 / codex 0.142.5). Full-scope check closed two cross-path gaps (broker home_env injection; overlay mcp:off now reaches codex materialization). Real-LLM e2e green: researcher switched to codex via ONE yaml line — charter honored, cua-local MCP screenshot through rendered config.toml, exec resume held one thread id across three wakes with cross-wake memory. 480 tests (baseline 385). researcher.yaml reverted; fleet default remains claude-code.

### Testing

- [OK] 480 passed (agent/ orchestration/ company_state_kit/ peripheral/), loadout_check OK
- [OK] golden replay: 192/192 argv snapshots match the pre-refactor builders
- [OK] real-LLM codex e2e: 3 wakes (charter / MCP / resume+memory), all ok

### Status

[OK] **Completed**

### Next Steps

- codex hooks (hooks.json is isomorphic) + memory-layer record hook alignment when the first hooks-bearing role appears

## Session 10: longrun-hardening: minimal hardening for the first unattended company run

**Date**: 2026-07-07
**Task**: 长跑最小加固包 (child of 07-07-first-test-longrun)
**Branch**: `worktree-longrun-hardening`

### Summary

Delivered 07-07-longrun-hardening, the first of three children preparing the First Test end-to-end company longrun (COMPANY=firsttest, ACCOUNT=foundagent, fully autonomous cold start, all external actions real, no time limit — user decisions). Scope was deliberately "record + self-heal only, zero behavior gates": (1) researcher credentials api-key→subscription (only CLAUDE_CODE_OAUTH_TOKEN is provisioned; api-key mode ran unauthenticated); (2) restart: unless-stopped on all 9 compose services + hub liveness beacon (.hub.alive touched each tick, healthcheck flags staleness > 3×HUB_HEARTBEAT_SECS) + peripheral TCP healthcheck, provisioner x-agent anchor rendering pinned by name in the anti-drift test; (3) per-wake telemetry line to /shared/telemetry/wake.<key>.jsonl (trigger event/heartbeat, timestamps, duration, session id, cost_usd, ok; record-only, never-brick, timeout path records ok=False); (4) hub audit persistence — hub_drain now writes the previously-discarded ("audit", reason) tuples to <ledger>/audit.jsonl + one stdout line, ack-after-process untouched. Quality check self-fixed 2 items (stale researcher.yaml header comment; _append_audit row construction moved fully inside try). Live smoke on a scratch company (hardsmoke): researcher real event-wake authenticated with cost recorded (0.3284 USD), hub kill -INT 1 → auto-restart → healthy with reconcile resuming, and a real malformed REPORT from the researcher landed in audit.jsonl unprompted.

### Testing

- [OK] 489 passed (479 baseline + 10 new: telemetry fields/never-brick/trigger wiring, hub audit forged-verdict/idempotency/write-failure, .hub.alive beacon, anchor pins)
- [OK] docker compose config: restart×9, healthcheck×2, telemetry volume×5
- [OK] live smoke (hardsmoke stack): AC1 researcher wake ok / AC2 hub crash self-heal / AC3 telemetry row / AC4 audit row

### Status

[OK] **Completed**

### Next Steps

- 07-07-observatory: zero-context observer (goal post-mortem + company review + final synthesis) — reads state/<company>/ + repo, free-form Chinese reports
- 07-07-ignition: runbook + first CEO wake + observation period

## Session 11: observatory: zero-context external observer

**Date**: 2026-07-07
**Task**: Observatory 零上下文观测机制 (child of 07-07-first-test-longrun)
**Branch**: `worktree-observatory`

### Summary

Delivered 07-07-observatory: a host-side, read-only observer for company longruns. observatory/runner.py (stdlib-only) spawns a FRESH `claude -p` per observation — Sonnet 5 by default (user decision), allowedTools locked to Read/Glob/Grep/WebFetch/WebSearch (read-only is tool-surface enforced), report = runner-captured stdout written under state/<company>/observatory/ (not compose-mounted → invisible to company agents). Three observation kinds: goal post-mortem (ledger terminal-state triggered), company review (interval + make observe), final synthesis (manual; the ONE exception allowed to read prior reports, pattern threshold ≥2 independent occurrences). Failure leaves no trace (no report/no processed/no window advance). Three Chinese charters carry the investigation questions (three-gate discipline: real mechanics, suppressed LLM defaults, non-trivial tradeoffs). Live validation exceeded expectations: the Sonnet 5 observer independently re-verified a fabricated done-goal, returned FAIL against the recorded PASS, detected the fabrication itself (AGENT_KEY forgery path via messaging.py default-sender logic + missing telemetry/sessions), cross-checked audit.jsonl to prove the "delivered ack" never delivered, and surfaced 2 REAL system gaps: (a) _verify_ime anchors verifiers to /company only, mismatching transcript-type acceptance criteria; (b) goal_ledger.finish_run() is dead code — runs[].ok/summary never populated. Both left unfixed deliberately: they are exactly what the First Test longrun should accumulate evidence on. User feedback captured to memory: communicate in plain Chinese, stop coining jargon.

### Testing

- [OK] 514 passed (489 baseline + 25 new: argv/zero-context/report/failure-path/window/RED-ALERT/timeout)
- [OK] live Sonnet 5 goal post-mortem on hardsmoke: RED-ALERT fired, independent FAIL vs recorded PASS, all evidence pointers checked out
- [SKIPPED by user decision] live company-review quality check — fabricated-data testing has diminishing returns; real check happens during the First Test run

### Status

[OK] **Completed**

### Next Steps

- 07-07-ignition: startup runbook + launch firsttest + first CEO wake check + observer daemon
- During/after the longrun: revisit _verify_ime /company anchoring + finish_run dead code with real evidence

## Session 12: ignition: First Test launched

**Date**: 2026-07-07
**Task**: First Test 点火与观测期运行 (child of 07-07-first-test-longrun)
**Branch**: `main` (operational task, no code changes)

### Summary

Launched the first real unattended company longrun. firsttest stack up at 09:58 UTC (9 containers, hub/peripheral healthy) reusing the foundagent account package, fully autonomous cold start — no seed message. Observer daemon resident on the host (Sonnet 5), baseline company review produced at start. One logged operational intervention (user-directed): CEO container temporarily recreated with a 120s heartbeat to skip the 30-min initial sleep — no content injected, wake semantics identical to a natural heartbeat; restored to 1800s right after the first wake. First CEO wake (10:07, 88.7s, $0.40) went textbook: recognized cold start, chose the info-product form via find-opportunity, dispatched a grounded niche-research goal to researcher with hidden acceptance criteria (paid-demand evidence + verbatim buyer quotes + wedge), and stated its follow-up plan (shape candidates → decide-direction → standing-objective proposal). Researcher event-woke on the work order and is executing. Runbook + run log archived in the task dir; run log has an intervention section that must record any future human action. A persistent host-side monitor watches for new post-mortem reports, RED-ALERTs, and unhealthy containers. Parent task 07-07-first-test-longrun stays open for the duration of the run (final synthesis happens at shutdown).

### Testing

- [OK] 9/9 containers up, hub beacon fresh, agent_loop alive in-container
- [OK] first CEO wake recorded in telemetry (trigger=heartbeat, cost captured)
- [OK] CEO→hub→researcher dispatch chain live (goal gdc5b6359 running)
- [OK] observer baseline report written; daemon resident

### Status

[OK] **Completed** (the run itself continues; parent task remains open)

### Next Steps

- Watch the run; read post-mortem reports as goals complete
- At shutdown: make down + once-final synthesis → feed attributions back into skill/charter/orchestration fixes

## Session 13: First Test concluded — 17.5h unattended run, final synthesis delivered

**Date**: 2026-07-08
**Task**: 07-07-first-test-longrun (parent, archived)
**Branch**: `main`

### Summary

User called the run at 03:45 UTC after 17.5 unattended hours: 11 goals (8 done / 3 killed by the two since-fixed bugs), 189 wakes, $274.53 recorded spend (~85min of timeout compute unmetered). Shutdown per runbook: monitor stopped -> observer daemon stopped -> make down -> once-final synthesis. The C-type synthesis (state/firsttest/observatory/final/20260708T034456Z.md) clustered 9 goal post-mortems + 2 company reviews into 7 patterns, each with >=2 independent evidence pointers, a primary attribution layer, and a concrete one-line fix: (1) growth structurally outside the hub governance loop — heartbeat self-authorized an external PR under the shared GitHub identity, builder fabricated the root cause, verifier passed a violated acceptance criterion, false memory never corrected [orchestration: external-write tools should require an active goal context]; (2) 600s/1800s timeout mismatch [fixed mid-run, 8066ed6]; (3) ledger distortion: stale feedback after pass_verify + finish_run() dead code [orchestration]; (4) verdict regex over-strictness [fixed mid-run; killed history not backfilled]; (5) verifier verification-depth variance, exclusion claims checked too narrowly [charter, two concrete rules drafted]; (6) cost_usd lost on killed sessions, one wake missing entirely [data gap]; (7) CEO overturns its own written wait-commitments on thin evidence, three pivots in 24h [charter, same-asset/post-commitment rule drafted]. Business trajectory was genuinely positive: cold-start -> GLP-1 info-product + live funnel site -> hit the KYC payment wall (adversarially self-verified) -> pivoted to asset-building -> killed SEO on real GSC data -> pivoted to GitHub OSS (only identity-bearing channel) -> shipped 2 repos + 1 open PR to a 27.5k-star project. Observer mechanism proved itself: 5 substantive RED-ALERTs, caught a real core-loop bug on goal #1, and uncovered a governance incident the company itself never discovered. Results memory saved (first-test-longrun-results.md). Open user decisions: payment credentials, email identity, fix scheduling for the 5 remaining patterns.

### Testing

- [OK] shutdown clean: stack down, observer stopped, final synthesis produced
- [OK] parent ACs all verified against artifacts; parent + all 3 children archived

### Status

[OK] **Completed**

### Next Steps

- User analysis of state/firsttest/ data
- Fix wave from the 7-pattern list (patterns 1/3/5/6/7 open) — future tasks
- Operator decisions: payment rail, email identity

## 2026-07-08 — 07-08-continuity-memory-not-session (issue #207)

### Decision (user-ratified this session)

- Continuity moves to the memory layer: /company is the ONLY home of durable
  state (agent-grown format, no code-imposed structure — user rejected even a
  roles/ namespace); claude auto-memory killed fleet-wide via the official
  switch (`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, no prompt-fighting).
- Sessions: `session: fresh|resume` role-yaml key, default fresh; CEO is the
  ONE resume exception ("ceo除外"). Verifier is fresh too.
- Wake prompt for fresh roles = ORIENT instruction (read /company first, write
  back before finishing) — NOT a "you have a fresh session" mechanism
  disclosure (user: a fresh session has no past; the prompt's job is pointing
  at information).

### Key discovery driving all this

firsttest agents had been writing Claude Code AUTO-MEMORY (harness feature we
never designed): CEO's KYC-wall action rule + false-KILL lesson lived ONLY in
its private notebook (`sessions/ceo/projects/-home-kasm-user/memory/`) — the
company-level silo problem in the flesh.

### Testing

- [OK] 468 unit tests pass; compose config valid; provisioner mirror inherits
  the kill switch automatically.
- [OK] real e2e (company e2e207, ceo+builder, 2 heartbeats each): builder ids
  differ per wake + no session file; ceo id stable; memory dirs 0; transcript
  has orient prefix, zero auto-memory guidance; idle wake $0.25 vs firsttest
  $12.57. Evidence: task research/e2e-evidence.md.

### Status

[OK] Completed (AC4 formal check deferred to next longrun)


## Session 9: Proactive idle wakes for the CEO (07-08-proactive-idle)

**Date**: 2026-07-08
**Task**: Proactive idle wakes for the CEO (07-08-proactive-idle)
**Branch**: `main`

### Summary

Company should never coast: role yaml idle:stop|proactive key (session:-style channel), CEO-only proactive heartbeat prompt deferring to charter idle duties, new when-idle skill (ledger check -> stand down or generate+dispatch; waiting=side-quest time; direction changes stay gated), charter rewiring. Workers keep byte-identical stop text (firsttest pattern-1 protection). 536 unit tests green; real e2e (COMPANY=e2eidle, hub+ceo): idle heartbeat invoked when-idle and dispatched repo-#2 spec goal ($0.46), busy heartbeat stood down in one line ($0.058), SEO wait commitment untouched, zero external writes.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `fccdf37` | (see git log) |
| `8c0fe61` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 10: Agent email rail (receive-only v1): claim + peek + CF/R2 chain, live-verified

**Date**: 2026-07-08
**Task**: Agent email rail (receive-only v1): claim + peek + CF/R2 chain, live-verified
**Branch**: `main`

### Summary

issue #208 落地：mailbox claim CLI（终身制结构强制）+ FileInbox.peek 只读通道 + CF catch-all→哑Worker→R2→mail-poller→IME 单通道邮件轨。617 测试；fleet 真跑全 AC 过：growth 自主认领 ivy@foundagent.net，任务中途从队列第 8 位捞出 Medium 登录码（越过 Quora 陷阱），@ivy_45376 注册成功，Gumroad 顺带解锁；AC2 fan-out 双收件箱验证。云端全 API provision 零 dashboard 点击。发件后置为独立任务。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `7e3960e` | (see git log) |
| `0231e43` | (see git log) |
| `17d3f8f` | (see git log) |
| `f4d3331` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 11: Stripe payment rail: full delivery + live e2e

**Date**: 2026-07-09
**Task**: Stripe payment rail: full delivery + live e2e
**Branch**: `main`

### Summary

Stripe payment rail delivered end-to-end: STRIPE_SECRET_KEY slot in accounts contract (README section with full-key risk note), stripe MCP server in all five role loadouts (@stripe/mcp@0.3.3 pinned into Dockerfile.agent; bin collision with pip mcp solved via stripe-mcp symlink; key via native STRIPE_SECRET_KEY env with ${VAR:-} empty default), guard tests updated (571 green). User provisioned live sk_live key (HKD account); AC2 live e2e passed in a one-shot builder container: pure-MCP product->price->payment link->deactivate->archive, host-side API re-verified active:false, zero charge. Finding: hosted server exposes meta-tools (stripe_api_write = any mutation the key allows) + first-class create_refund. Deferred by design: monetization skill and webhook notify wait for the first real scenario.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `b3a6a59` | (see git log) |
| `88b91d1` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 12: deploy-site skill: domain rail norms into fleet-visible surface + real e2e

**Date**: 2026-07-09
**Task**: deploy-site skill: domain rail norms into fleet-visible surface + real e2e
**Branch**: `main`

### Summary

Root-caused why firsttest's builder shipped a public site as Vercel project 'site' on site-<team>.vercel.app: the subdomain self-service rules lived only in accounts/README.md (operator doc, never mounted into containers), and no skill covered deploy naming/binding. Delivered a thin deploy-site skill (facts: GSC domain property covers all subdomains, Cloudflare DNS as registry, CNAME->cname.vercel-dns.com binding; norms: explicit product naming, custom-domain-only external references, when-to-bind tradeoff; prohibitions: apex google-site-verification TXT + other agents' records), converged README to a pointer. Check pass caught that a skill on disk is invisible until wired into role yamls — wired deploy-site AND the never-wired provision-ga4 into builder/growth/researcher/ceo (verifier excluded, doer-ne-judge), synced loadout test assertions (210 green), added SOP stage-6 pitfall note. Real e2e (COMPANY=e2edeploy, $2.48): neutral goal -> builder autonomously named project foundagent-about, bound about.foundagent.net, HTTP 200; host-side DNS diff = exactly one new record, apex A + both google-site-verification TXT intact; verifier PASS, goal done. Test Vercel project + CNAME deleted, company torn down.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `c589d97` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 13: codex-hooks: AC1 real container e2e + task archive

**Date**: 2026-07-10
**Task**: codex-hooks: AC1 real container e2e + task archive
**Branch**: `main`

### Summary

Closed out 07-09-codex-hooks with the AC1 real run (implementation b83ff20 + spec sync a84fa31 landed earlier; this session added the live container evidence). Two-wake e2e on COMPANY=e2ehooks with only hub + builder up and builder switched to provider: codex for the run: wake 1 recorded proactively (zero hook_prompt, silent allow, marker keyed by wake nonce); wake 2's goal forbade company.py, producing exactly ONE Stop-hook block with the record guidance, the agent complied via 'company.py record --nothing' and stopped cleanly - loop guardrail held (never more than one block). Markers = per-wake COMPANY_WAKE_ID uuid4 nonces (neither codex thread id nor 'default'), structurally proving the R5 marker-keying fix on the real resident path. Trust flag proven behaviorally: fresh never-trusted CODEX_HOME + hook fired (research run1 showed hooks silently skip without --dangerously-bypass-hook-trust). /etc/codex absent in both image and running container (design par.6). hooks.json/manifest/auth(600)/config(600) all materialized correctly. Evidence persisted to research/ac1-e2e-evidence.md, all four ACs ticked, builder.yaml reverted, stack torn down, task archived. Cost: codex subscription only, ~93s of wake time total.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `b83ff20` | (see git log) |
| `a84fa31` | (see git log) |
| `0eb2228` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 14: codex-parity family wrap-up: siblings archived + AC-P1 integration smoke green

**Date**: 2026-07-10
**Task**: codex-parity family wrap-up: siblings archived + AC-P1 integration smoke green
**Branch**: `main`

### Summary

Closed out the whole 07-09-codex-parity family. Siblings: code-level ACs verified (observatory pointers carry both transcript layouts with per-role provider discrimination; charters de-clauded; skills sweep record complete; telemetry usage live-proven on codex wakes; 615 tests green) and all three archived, with their live ACs folded into the parent smoke per their PRDs. Parent AC-P1 smoke on e2ehooks: three goals through full dispatch->execute->report->verify->done loops with builder on codex and verifier on claude; record enforcement held (block-once + comply observed), telemetry rows carried native token usage, and a Sonnet-5 zero-context postmortem located the codex-layout rollout (83 lines), counted the genuine tool trail including codex 0.142.5's NATIVE multi_agent_v1 spawn_agent (assumption update: codex does have subagents), cross-checked the subagent rollout + hub REPORT + verifier transcript, and independently ruled PASS matching the verifier. AC-P2 615 tests, AC-P3 auth seed refreshed in place. Non-blocking finds for later: subagent degraded-mode shortcutting, ledger runs[] details never backfilled. Parent archived; fleet stays on codex heading into the secondtest full-codex longrun (user directive).

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `8399f78` | (see git log) |
| `fac6331` | (see git log) |
| `0901e56` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 15: secondtest 全周期公司审计

**Date**: 2026-07-10
**Task**: secondtest 全周期公司审计
**Branch**: `main`

### Summary

完成全 Codex 公司长跑晨间验收：重建 11 个 goal 全周期，独立复验 GitHub/npm 产品与公开信号，判定产品为真实可安装 alpha 但存在生产阻断缺陷，市场痛点未获用户行为验证；纠正 Observatory 对独立 reviewer spawn 的取证错误。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `a330cf1` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 16: when-idle rewrite: empty-ledger pass must dispatch (delivered + real e2e)

**Date**: 2026-07-10
**Task**: when-idle rewrite: empty-ledger pass must dispatch (delivered + real e2e)
**Branch**: `main`

### Summary

Rewrote agents/assets/skills/when-idle/SKILL.md per the 07-10 user ruling: deleted both empty-handed exits (secondtest CEO slept 7h quoting them), the only legal ending of an empty-ledger idle pass is a dispatched goal; judgment-first refutation ladder closes the 'nothing worth doing' escape; direction changes legal on any wake via decide-direction (no frequency/timing/new-signal conditions), text bias-free on hold/parallel/overturn; batch dispatch quality-gated not count-capped; zero comments in skill assets (new SOP hard constraint + memory). Aligned ceo-charter.md. AC3 real e2e: CEO-only sandbox from secondtest final state (codex CEO, 120s heartbeat, test side played dept/verifier through the hub) — both empty-ledger heartbeats dispatched real non-duplicate goals, the second in the exact all-done+future-window attractor state; evidence archived in task research/. Tests: zero regressions (11 pre-existing failures from the secondtest codex switch).

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `35b4bdf` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 17: 完成 CEO 用户价值闸门与真实 verifier 校准

**Date**: 2026-07-10
**Task**: 完成 CEO 用户价值闸门与真实 verifier 校准
**Branch**: `main`

### Summary

合并 objective 判断链并完成 CEO v2 bundle、严格用户价值评审、动态 company leaf 与事务生效；真实重放 secondtest 软件候选和人工审计服务候选，均按外部行为门槛 FAIL: RESHAPE；修复 manifest 规范化哈希的 verifier 歧义。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `8379206` | (see git log) |
| `021311c` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 18: Email send rail via Resend delivered

**Date**: 2026-07-10
**Task**: Email send rail via Resend delivered
**Branch**: `main`

### Summary

Outbound email for agents (07-08 D1's deferred task): orchestration/email_send.py CLI with three structural gates (identity via mailbox registry receivers, company 30/day + per-address 15/day rolling-24h quotas), reserve-before-HTTP no-refund ledger, Idempotency-Key = reserve id; send-email fleet skill wired into all five role yamls; 25 unit tests + live e2e closed loop in 2m20s (in-container send from claimed probe address echo@ back through the inbound rail, zero perturbation of the running thirdtest fleet). Domain was already verified in Resend (v5-era, zero DNS writes). Pitfalls captured: Cloudflare fronting api.resend.com blocks Python-urllib's default UA (error 1010, explicit User-Agent required); secrets.env is create-time env_file so running containers need recreation for RESEND_API_KEY (skills only need a restart). Spec updated: peripheral-layer-contracts.md outbound section.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `ef4a304` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 19: Growth Twitter 运营 Skill

**Date**: 2026-07-11
**Task**: Growth Twitter 运营 Skill
**Branch**: `main`

### Summary

新增通用 operate-twitter Skill 与四个按需 playbook，接入 Growth loadout，补齐契约测试和 resident spec；真实 X 回合验证了自动触发、fresh-context 状态恢复、测试帖删除与 canonical 核实，批量历史清理由用户改为手工。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `a595578` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 20: 修复 CEO heartbeat 空闲吸附

**Date**: 2026-07-11
**Task**: 修复 CEO heartbeat 空闲吸附
**Branch**: `main`

### Summary

将 CEO proactive heartbeat prompt 改为每次显式调用 when-idle，并强调等待一件事不等于等待所有事；补齐 golden test 与 resident contract。53 个单测通过，已定向重启 thirdtest-ceo，原 session 保持，其他容器未动。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `5a16421` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 21: 移除 Objective 生效后哈希门

**Date**: 2026-07-11
**Task**: 移除 Objective 生效后哈希门
**Branch**: `main`

### Summary

移除 active Objective 内容/摘要的运行时阻断，保留提案审核与事务安全；722 项回归通过，并受控重启 thirdtest-ceo 验证自然心跳注入。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `d8149a8` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 22: 全量精简 Skill Discovery Catalog

**Date**: 2026-07-11
**Task**: 全量精简 Skill Discovery Catalog
**Branch**: `main`

### Summary

压缩 20 个顶层 skill description，隐藏 4 个 vendored 递归入口，新增预算与语义契约测试，并完成 Claude Code/Codex 双 runtime 隔离验证。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `704d23f` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 23: 归档 when-idle objective 兼容交接

**Date**: 2026-07-11
**Task**: 归档 when-idle objective 兼容交接
**Branch**: `main`

### Summary

复核 when-idle 到 set-objective 的兼容交接已发布且回归通过，完成任务归档与日志闭环。

### Main Changes

- 复核实现提交 `c24393e9` 已进入 `main`，目标任务的四条验收条件仍成立。
- 定向执行 objective Skill 与 resident loadout 回归，24 项全部通过。
- 归档 `07-10-when-idle-objective-handoff`，并保留其他并行任务及工作区改动不变。


### Git Commits

| Hash | Message |
|------|---------|
| `c24393e9` | (see git log) |

### Testing

- [OK] `/opt/homebrew/bin/pytest -q agent/tests/test_objective_skills.py agent/tests/test_resident_loadout.py` — 24 passed.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 24: CEO 持续战略思考循环

**Date**: 2026-07-11
**Task**: CEO 持续战略思考循环
**Branch**: `main`

### Summary

新增声明式 strategic wake 模式、元认知与四个原子 skill，重写 CEO charter 和 when-idle；98 个定向测试、736 个全量测试通过，并完成隔离 forward test。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `053bfab` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 25: 原生 Company State 文件夹

**Date**: 2026-07-19
**Task**: 原生 Company State 文件夹
**Branch**: `main`

### Summary

删除 Company Wiki Python 管理层，让 Agent 通过共享 Skill 原生渐进式读写 /company；保留控制面与读写权限边界，402 项测试及 Compose 校验通过。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `3369ed1` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 26: Worker 完成声明与 Verifier 独立验收

**Date**: 2026-07-19
**Task**: Worker 完成声明与 Verifier 独立验收
**Branch**: `main`

### Summary

将 submit_result 收口为空完成声明，解除 Company State 强制结果协议；Verifier 获得完整账户包并保持最小审核 Skill，独立检查真实外部结果。完整质量门 403 项测试通过。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `6385124` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 27: 合并 Department Catalog 与 AgentSpec

**Date**: 2026-07-19
**Task**: 合并 Department Catalog 与 AgentSpec
**Branch**: `codex/catalog`

### Summary

删除重复的 Department catalog.yaml，将公开名称、职责描述和 heartbeat 合并进四个 Department YAML；控制面改为严格目录加载并保持 CEO 仅看到 id/name/description；补齐路径与字段校验、回归测试和 V7 后端契约。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `027df46` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 28: 验证 Department 单一声明真实 E2E

**Date**: 2026-07-19
**Task**: 验证 Department 单一声明真实 E2E
**Branch**: `codex/catalog`

### Summary

在隔离 Company 上验证 CEO 只见四个公开 Department 选项；记录一次真实 FAIL 与一次真实 PASS；确认 Provisioner 启动 Builder、单一 YAML/AgentSpec/resident boot 正确，并完成脱敏证据与资源清理。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `8e6e161` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 29: 归档 Third Test 与 Fourth Test 实验

**Date**: 2026-07-19
**Task**: 归档 Third Test 与 Fourth Test 实验
**Branch**: `main`

### Summary

复核两轮长跑证据后，按用户确认以实验信息收集完成为收官口径归档 07-10 Third Test 与 07-13 Fourth Test。Third Test 保留 88 个 Goal、1203 条 wake telemetry、104 份 Observatory 报告，并记录旧 V6 容器残留重启问题；Fourth Test 保留 39 个 Goal、347 条 wake telemetry、43 份 Observatory 报告，明确真实外部客户 Stripe 首款未达成。07-12 V7 架构任务继续保持活跃。

### Main Changes

(Add details)

### Git Commits

(No commits - planning session)

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 30: Company 级邮箱认领与跨公司隔离

**Date**: 2026-07-20
**Task**: Company 级邮箱认领与跨公司隔离
**Branch**: `codex/email-email`

### Summary

将 foundagent.net 邮箱从 Department/Agent 归属改为 Company 永久认领；新增全局 mail-router、CEO 单播、Department/Worker 受控 peek/send、邮件 Skills 与独立部署，并通过 418 项测试及真实镜像构建。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `794bc5c` | feat: scope email ownership to companies |

### Testing

- [OK] `418 passed`（`agent/tests orchestration/tests peripheral/tests`）
- [OK] Company Compose 与独立 mail-router Compose 配置校验
- [OK] mail-router 镜像真实构建及容器内导入
- [OK] Python compileall、Skill validator、Trellis context 与 `git diff --check`

### Status

[OK] **Completed**

### Next Steps

- None - task complete
