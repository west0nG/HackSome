# Claude Code Runtime Coupling Map — BuildFactory（代码库耦合点扫描）

> 扫描时间 2026-07-07（main @ b18b1db）。用途：runtime 抽象层的改造清单。
> 结论：两条 agent 启动路径各自硬编码 `claude` CLI；provider seam 已存在但只覆盖休眠的 broker 路径。

Two independent agent-spawn paths exist, each hard-codes the `claude` CLI separately:

- **Resident path** (production, `docker compose up`): `orchestration/agent_loop.py` builds its OWN `claude` argv inline and `subprocess.run`s it inside the container.
- **Ephemeral broker path** (dormant): `orchestration/broker.py` → `agent/runner.py` → `agent/provider.py` builds an `ExecPlan` argv and runs it via `docker exec`.

A provider seam already exists (`agent/provider.py` with `CodexProvider`/`OpenCodeProvider` stubs), but the resident loop bypasses it entirely.

## Layer 1 — Spawn path & CLI flags

### Resident loop (the live path — builds `claude` argv WITHOUT the provider seam)
- `orchestration/agent_loop.py:132-160` — `build_claude_argv()`, the resident argv builder. Hardcodes: `:145` `["claude", "-p", prompt]`; `:146-147` `--resume <sid>`; `:148-149` `--session-id <new>`; `:151` `--append-system-prompt <charter>`; `:153` `--mcp-config`; `:155-157` `--model`/`--effort`; `:158` `--strict-mcp-config`; `:159` `--dangerously-skip-permissions`.
- `orchestration/agent_loop.py:216-235` — `wake()` runs the argv via `subprocess.run` (in-container, no docker exec); parses only `returncode` + stdout/stderr (no stream-json here).
- `orchestration/agent_loop.py:44` — `DEFAULT_MCP_CONFIG = "/opt/foundagent/mcp.json"` roleless fallback.
- `orchestration/agent_loop.py:45-46` — `CLAUDE_TIMEOUT` from `AGENT_CLAUDE_TIMEOUT`/`CEO_CLAUDE_TIMEOUT`.
- `orchestration/agent_loop.py:96-98` — comment: leading-dash prompts break `claude -p` (CLI-arg-parsing quirk baked into prompt construction).
- `orchestration/ceo_loop.py:19-31` — compat shim re-exporting `build_claude_argv`/`wake` (CEO = `agent_loop(key="ceo")`).

### Broker/runner path (the provider-seam path — dormant)
- `agent/provider.py:39-71` — `ClaudeCodeProvider.build_exec()`, `name="claude-code"` (`:42`). Argv: `:55` `["claude","-p",task,"--mcp-config",...]`; `:58-59` `--model`; `:60-61` `--effort`; `:63` `--append-system-prompt`; `:67` `--session-id`; `:68` `--output-format stream-json --verbose`; `:70` `--dangerously-skip-permissions`.
- `agent/provider.py:74-89` — `CodexProvider` / `OpenCodeProvider` stubs, both `raise NotImplementedError` (the existing runtime seam to extend).
- `agent/provider.py:15-20` — `ExecPlan` dataclass (`argv` + `env`), the seam's return type.
- `agent/runner.py:76-125` — `run_task()`: assembles ExecPlan → `docker exec` (`:115` `["docker","exec",*env_flags,container,"bash","-lc",shlex.join(plan.argv)]`) → parses stream-json.
- `agent/runner.py:36-73` — `parse_stream_json()`: Claude-Code-specific NDJSON contract (`type=="result"`, `is_error`, `result`, `total_cost_usd`, `api_error_status`).
- `agent/runner.py:122-124` — surfaces stderr when "claude not found / bad flags".
- `orchestration/broker.py:46-140` — `spawn()`: `docker run` the cua-agent image, wait for `:8000`, then `run_task`. `:112` `IMAGE, "--wait"`; `:121-122` `docker exec ... grep ':8000'`; `:136-140` delegates to `runner.run_task`.
- `orchestration/broker.py:165-166` — hard requires `CLAUDE_CODE_OAUTH_TOKEN` at `__main__`.

### stream-json consumers (output-format coupling)
- `agent/runner.py`, `agent/provider.py`, `agent/__init__.py`, `orchestration/broker.py`, plus tests `agent/tests/test_runner.py`, `agent/tests/test_provider.py`.

## Layer 2 — Claude-Code config assets (generated & consumed)

### `.claude` home materialization (skills / hooks / settings.json)
- `agent/loadout.py:46-92` — `materialize()` writes the per-agent `.claude` tree: `:55` `settings.json`, `:71-76` `skills/<name>/` copytree, `:78-83` merges hook snippets into `settings.json`, `:87` reads system_prompt. Encodes the Claude `settings.json` hooks-array schema (`_merge_hooks`/`_remove_hooks` `:153-215`), `.loadout-manifest.json` bookkeeping.
- `agent/resident_loadout.py:33-40` — `AGENTS_DIR`, `CLAUDE_HOME`/`CLAUDE_CONFIG_DIR` (→ `~/.claude`), `AGENT_LOADOUT`. `:50-81` `materialize_for()` runs at container startup. `:84-100` env-driven `main()`.
- `agent/resident_loadout.py:16-19` — comment: "claude auth rides on CLAUDE_CODE_OAUTH_TOKEN (env), not ~/.claude".

### AgentSpec declaration schema (per-role capability yaml)
- `agent/spec.py:33-61` — `_FIELDS` + `AgentSpec`: `:52` `provider` (default `claude-code`), `:53` `credentials`, `:54` `model` (default `claude-opus-4-8`), `:55` `effort` (`xhigh`), `:56` `system_prompt`, `:57` `skills`, `:58` `hooks`, `:59` `mcp_config`, `:60` `permission_mode` (`bypass`).
- `agent/spec.py:29-30` — `DEFAULT_MODEL`/`DEFAULT_EFFORT` fleet defaults (also imported by `agent_loop.py:34`, literal fallback `agent_loop.py:36`).
- `agent/spec.py:95-97` — `bypass_permissions` property → `--dangerously-skip-permissions`.
- `agent/spec.py:100-110` — `provider_for()` maps `claude-code`/`codex`/`opencode` → classes.
- `agent/spec.py:113-122` — `credential_for()` maps `subscription`/`api-key`.

### Company loadout overlay (charter/hooks/mcp/skills tri-states)
- `agent/overlay.py` — `_ROLE_FIELDS=("skills","charter","hooks","mcp")` (`:22`); `effective_charter` (`:180-183`), `effective_mcp` (`:186-188`), `apply_to_spec` (`:152-177`).
- `orchestration/agent_loop.py:283-312` — `_overlay_charter_mcp()` applies overlay before argv build.
- `agent/loadout_check.py` — offline validator of overlay vs `agents/*.yaml`.

### Role yaml assets
- `agents/{ceo,builder,growth,researcher,verifier}.yaml` — `provider: claude-code`, `credentials`, `system_prompt`, `skills`, `mcp_config: mcp/<role>.json`, `permission_mode: bypass`（researcher 是 `credentials: api-key`）。

### MCP loadout files (`--mcp-config` payloads — `mcpServers` schema)
- `agents/mcp/{ceo,builder,growth,researcher,verifier}.json` — per-role full server set (cua-local, dataforseo, gsc, ga4, playwright)，byte-identical (capability-first)。
- `vm/docker/agent-mcp.json` — baked-in fallback (`/opt/foundagent/mcp.json`), cua-local only。
- `agent/browser_mcp.sh` — playwright-mcp launcher referenced by each mcp json。

### System-prompt / charter injection
- Charters in `agents/assets/*-charter.md`, injected via `--append-system-prompt` at `agent_loop.py:151` and `provider.py:63`, read by `agent_loop.py:178-184` and `spec.py:82-87`。
- Root `CLAUDE.md`/`AGENTS.md` are dev-facing, NOT injected into runtime agents。

### create-role bundle schema
- `agents/assets/skills/create-role/SKILL.md:118-131` — role.yaml template pins `provider: claude-code`, `system_prompt`, `mcp_config`, `permission_mode`; `:79-94` skills/hooks/MCP loadout; `:109` bundle `mcp.json` optional。

## Layer 3 — Env / credentials

- `agent/credentials.py:21` — `ALL_CREDENTIAL_VARS = ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")`. `:35-45` `SubscriptionCreds`, `:48-58` `ApiKeyCreds`, `:61-71` `injection_env()` mutual-exclusion（Anthropic 特有的 api-key > subscription 优先级规则）。
- `agent/runner.py:104-113` — injects credential env + non-credential env as `docker exec -e` flags。
- `agent/proxy_env.sh:22-27` — `CUA_PROXY` → `HTTP(S)_PROXY`; `NO_PROXY` default includes `.anthropic.com`/`.claude.ai`。
- `vm/docker/agent_startup.sh:20-26` — proxy_env sourced ONLY for computer-server subshell（LLM 流量结构性避开 proxy）。`:32` `agent.resident_loadout`; `:34` `exec ... orchestration.agent_loop`。
- `docker-compose.yml:40` — `env_file: vm/.env.local`（CLAUDE_CODE_OAUTH_TOKEN）。`:76,106,116,126,136,146` — `CLAUDE_CONFIG_DIR: /sessions/<role>` per service。`:87-90,105-107` — `AGENT_KEY`/`AGENT_CHARTER`/`AGENT_SESSION_FILE`。
- `orchestration/broker.py:84-87` CUA_PROXY → HTTP_PROXY; `:100-110,136-140` session_id + `COMPANY_SESSION_ID`（memory 层 Stop-hook 关联）。
- Env-driven entry: `orchestration/agent_loop.py:339-375` `main()` reads `AGENT_KEY`/`AGENT_CHARTER`/`AGENT_SESSION_FILE`/`AGENT_HEARTBEAT_SECS`/`AGENT_MCP`/`AGENT_OBJECTIVE`/`AGENT_LOADOUT`/`AGENTS_DIR`。

## Layer 4 — Image / provisioning

- `vm/docker/Dockerfile.agent:16-18` — Node 20 via nodesource。`:38` `RUN npm install -g @anthropic-ai/claude-code` — **UNPINNED（浮动 latest）**，与其他 ARG-pinned 工具不一致。`:42-90` — pinned CLI/MCP toolchain（gh 2.96.0、vercel 54.20.0、wrangler 4.86.0、dataforseo-mcp 2.9.11、playwright-mcp 0.0.77、analytics-mcp/mcp-gsc）。`:83` pip `cua-computer mcp pyyaml`。`:93-94` COPY `cua_mcp.py` + `agent-mcp.json`。
- `docker-compose.yml:37-97` — `x-agent`/`x-agent-env` anchors: image `foundagent/cua-agent:latest`, mounts（`agent/`、`agents/`、`charters/`、`/sessions`、`/account`、startup script）, agents 无 docker.sock。`:149-248` hub/broker/provisioner/peripheral services。
- `Makefile:19` — `ROLES` from `agents/*.yaml` glob。`:24-28` auto-merges `docker-compose.roles.yml`。`:30-36` `shared` pre-creates `sessions/<role>` dirs。

### Runtime role provisioner
- `orchestration/provisioner.py:300-320` — `render_role_service()` sets `CLAUDE_CONFIG_DIR: /sessions/<name>` (`:317`), `AGENT_KEY`/`AGENT_CHARTER`/`AGENT_SESSION_FILE`。Renders from `x-agent` anchor。
- `orchestration/provisioner.py:119` — `CANONICAL_MCP = agents/mcp/ceo.json`。`:437-462` materializes `agents/<name>.yaml`、charter、`mcp/<name>.json`、skills。`:476` compose up。

## Layer 5 — Role registry

- `orchestration/role.py:70` imports `agent.spec._FIELDS` as `SPEC_FIELDS`（role-yaml schema 唯一来源，含 `provider`）。`:216-358` `lint_bundle()`：`:281-289` pins `system_prompt`/`mcp_config` 路径（不校验 `provider` 值——前向兼容）；`:314-357` mcp.json credential/env-ref lint。
- `orchestration/role.py:492-516` — `list_roles()`。registry 事件 schema `{ts,role,event,by,detail}` 无 provider 字段——provider 只活在 role yaml 里。
- `agent/loadout_check.py:31-67` — validates overlay vs `agents/*.yaml`。

## Layer 6 — Codex-relevant material already present

- **Provider seam stubs**: `agent/provider.py:74-89`, wired in `agent/spec.py:102-109`, exported in `agent/__init__.py`。Role yamls 注释 `# claude-code | codex(stub) | opencode(stub)`。
- **已有真实 codex CLI 调用**（图片生成用途，非 runtime）：`agents/assets/skills/gen-image/scripts/generate_image.py:122-173` — `codex exec --skip-git-repo-check -C <dir> --sandbox workspace-write --enable image_generation`（`GEN_IMAGE_VIA_CODEX=1` opt-in），读 `~/.codex/generated_images`。参考文档在 `agents/assets/skills/gen-image/references/codex/`。
- **repo 根的 `.codex/` 是 Trellis 开发工具配置**（给人类的 coding agent 用），不是 BuildFactory runtime——勿混淆。
- 镜像里未装 codex CLI；gen-image 路径靠 `shutil.which("codex")` guard。

## Key observations for the abstraction design

1. **两个 argv builder 要合一**：`agent_loop.build_claude_argv`（生产）与 `ClaudeCodeProvider.build_exec`（休眠）独立硬编码 claude flags；常驻路径完全没走 seam。
2. **输出契约耦合**：常驻路径只看 exit code；broker 路径解析 claude stream-json `result` 事件（`agent/runner.py:36-73`）。
3. **配置资产形态是 claude 专属**：`.claude/settings.json` hooks schema、`~/.claude/skills/` 发现、`mcpServers` JSON。
4. **凭证 seam 原则上已解耦**但只认 Anthropic 变量。
5. **无 codex 直接对应的 flags**：`--append-system-prompt`、`--resume`/`--session-id`、`--strict-mcp-config`、`--dangerously-skip-permissions`、`--effort`、`--output-format stream-json`——逐一映射点见 codex-cli-capability-map.md。
6. **模型默认值重复**：`agent/spec.py:29` + `orchestration/agent_loop.py:36` fallback。
