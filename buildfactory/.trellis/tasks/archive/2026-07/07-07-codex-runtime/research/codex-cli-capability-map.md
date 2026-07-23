# Codex CLI headless 能力面 × Claude Code 映射（调研报告）

> 调研时间 2026-07-07。Codex CLI 最新稳定版 **0.142.5**（2026-07-01 发布）；npm `latest=0.142.5`、`alpha=0.143.0-alpha.37`。
> 用途：runtime 抽象层设计输入。结论：两 CLI 同构度高，五个抽象面均可映射；缺口清单见文末。

## 映射总表

| Claude Code | Codex 等价物 | 备注（版本 / 置信度） |
|---|---|---|
| `claude -p "prompt"` | `codex exec "prompt"`（可缩写 `codex e`；`-` 或省略参数则读 stdin） | 官方文档；进度走 stderr、最终消息走 stdout |
| `--output-format stream-json` | `codex exec --json`（JSONL 事件流；`--experimental-json` 为同义别名） | 官方文档；typed schema 约 v0.44（2025-10）稳定 |
| `--output-format json`（单块聚合） | **无等价物** — 只有 JSONL 流；用 `--output-last-message <file>` 拿最终消息 | 缺口：抽象层需自聚合 |
| 最终消息提取 | `item.completed` 且 `item.type=="agent_message"` 的 `text` 字段；或 `-o/--output-last-message <path>` | 官方文档 |
| cost/usage | `turn.completed` 事件的 `usage`：`input_tokens`/`cached_input_tokens`/`output_tokens`。**无美元 cost 字段** | 官方文档；成本需自算（缺口） |
| 错误状态 | `turn.failed` 事件 + `error` 事件；进程非零退出码 | 官方确认非零退出，但**无退出码枚举表**；SIGINT 曾返回 0（issue #4721） |
| `--resume <id>` | `codex exec resume <SESSION_ID> ["prompt"]` | 官方文档；2025-09（~v0.39）引入 |
| `--continue` | `codex exec resume --last`（默认限当前 cwd；`--all` 跨目录） | 官方文档 |
| `--session-id <uuid>`（预设） | **无等价物** — open feature requests：issues #13242、#15271、#15767 | 硬缺口：只能事后从 `thread.started` 事件或 rollout 文件名取 id |
| `--append-system-prompt` | `-c developer_instructions="..."`（inline 追加注入，不替换基础指令） | 官方 config-reference |
| `--system-prompt`（整体替换） | `model_instructions_file = "<path>"`（替换内置指令；旧名 `experimental_instructions_file`） | 官方文档 |
| `CLAUDE.md` | `AGENTS.md`（cwd 向上走到项目根，逐层加载；`project_doc_max_bytes`、`project_doc_fallback_filenames` 可调） | 官方文档 |
| `--mcp-config <file>` | **无 per-invocation MCP 文件 flag** — 用重复 `-c 'mcp_servers.foo.command="npx"'` 覆盖，或项目级 `.codex/config.toml` | 缺口（官方文档确认只有 config 途径） |
| `--strict-mcp-config` | 近似：`--ignore-user-config`（跳过 `$CODEX_HOME/config.toml`，auth 仍走 CODEX_HOME） | 官方文档；语义不完全等价 |
| `claude mcp add` | `codex mcp add <name> [--env K=V] [--url ...] [--bearer-token-env-var ...] -- <command...>`；另有 `list/get/remove/login/logout`，`list --json` | 官方文档 |
| `--model` | `--model/-m`（如 `gpt-5.4`） | 官方文档 |
| effort 控制 | `-c model_reasoning_effort="minimal\|low\|medium\|high\|xhigh"`（另有 `model_verbosity`、`model_reasoning_summary`） | 官方文档 |
| `--settings` / profile | `--profile/-p <name>`（叠加 `$CODEX_HOME/<name>.config.toml`）；`-c key=value` 可重复、TOML 解析 | 官方文档 |
| `--dangerously-skip-permissions` | `--dangerously-bypass-approvals-and-sandbox`（别名 `--yolo`） | 官方文档；docker 内官方推荐姿势（见 §7） |
| `--permission-mode` | `--sandbox/-s read-only\|workspace-write\|danger-full-access` + `--ask-for-approval/-a untrusted\|on-request\|never`；config `approval_policy` 支持 `{granular={...}}` | 官方文档；`--full-auto` 已弃用 |
| `--allowedTools/--disallowedTools` | 仅 MCP 粒度：`enabled_tools`/`disabled_tools`/`default_tools_approval_mode`/`tools.<t>.approval_mode`；内置工具无 allowlist flag | 部分缺口 |
| `--add-dir` | `--add-dir`（同名同义） | 官方文档 |
| `--max-turns` | **无等价物** | 缺口 |
| `ANTHROPIC_API_KEY` | `CODEX_API_KEY`（exec 专用推荐）；`OPENAI_API_KEY`（SDK 也识别）；否则回落 `auth.json` | 官方文档（precedence 无明文，需实测） |
| 订阅 auth | `codex login`（浏览器 OAuth）/ `codex login --device-auth`（设备码，headless 首选）/ `auth.json` 可预置进容器 | 官方文档 |
| `CLAUDE_CONFIG_DIR` | `CODEX_HOME`（默认 `~/.codex`） | 官方文档 |
| Stop/SessionStart hooks | **已有完整 hooks 系统**（2026 新增）：`SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`PermissionRequest`、`Pre/PostCompact`、`SubagentStart/Stop`、`Stop` | 官方文档；~v0.116-0.117（2026-03）引入、v0.124 稳定、2026-05-14 GA |
| skills (SKILL.md) | 支持，同一开放标准，格式兼容；位置 `.agents/skills`（repo）、`~/.agents/skills`（user）、`/etc/codex/skills`（admin） | 官方文档；2025-12 上线 |
| headless 无会话残留 | `--ephemeral`（不落盘 rollout 文件，与 resume 互斥） | 官方文档 |
| `--verbose` | `RUST_LOG` env + `log_dir` config | 社区常识，中置信 |

## 分主题细节

### 1. `codex exec` 一次性执行
- 语法：`codex exec "prompt"`；省略 prompt 或用 `-` 读 stdin；stdin 管道 + prompt 参数并存时，prompt 是指令、管道内容作 context。
- stderr=进度，stdout=最终消息（非 `--json` 时），天然可管道。
- 退出码：官方只说 "exits non-zero on failure"，无枚举表；错误细分靠 `turn.failed`/`error` 事件。
- 其他实用 flag：`--skip-git-repo-check`（非 git 目录必带）、`--cd/-C <path>`、`--color`、`--image/-i`、`--ignore-rules`（跳过 execpolicy `.rules`）、`--strict-config`（config 含未识别字段时报错——锁版本 fail-fast 用）。

### 2. 结构化输出
- `--json`：stdout 变 JSONL。事件类型：`thread.started`（含 session/thread id）、`turn.started`、`turn.completed`（含 `usage`）、`turn.failed`、`item.started/item.completed`、`error`。
- item 类型：`agent_message`、reasoning、command execution、file change、MCP tool call、web search、plan update。
- 官方推荐 CI 组合：`--json` + `--output-last-message`。
- `--output-schema <schema.json>`：约束最终回复符合 JSON Schema（v0.14x 起 `exec resume` 也支持，PR #23123 2026-05）。
- exec 的 `--json` 无 token 级增量；无聚合型单 JSON 输出。

### 3. Session 连续性
- 存储：`~/.codex/sessions/YYYY/MM/DD/rollout-YYYY-MM-DDTHH-MM-SS-<uuid>.jsonl`（完整对话+工具调用+usage）；归档到 `~/.codex/archived_sessions/`；另有 SQLite 状态库（`sqlite_home` 可配，v0.140 起损坏自动备份重建）。
- id 发现：`--json` 流首条 `thread.started` 事件，或 rollout 文件名内 uuid。
- **预设 session id：不支持**（issues #13242/#15271/#15767 均 open）。抽象层须维护「自有 id → codex thread id」映射（或直接以 codex 返回的 id 为准），并处理「进程崩溃在 thread.started 之前」的边界。

### 4. System-prompt 注入
- `-c developer_instructions="..."`：追加注入（≈ `--append-system-prompt`），不显示在 UI。
- `model_instructions_file`：整体替换内置指令（危险，不用）。
- AGENTS.md：cwd → 项目根（`.git` 或 `project_root_markers` 判定）逐层收集；`project_doc_max_bytes` 限字节；全局层 `~/.codex/AGENTS.md`（文档较略，中置信）。

### 5. MCP
- `[mcp_servers.<id>]` schema：`command`/`args`/`env`（stdio）、`url`+`bearer_token_env_var`（streamable HTTP，OAuth 走 `codex mcp login`）、`enabled`、`required`（初始化失败则启动失败）、`startup_timeout_sec`(默认10)/`tool_timeout_sec`(默认60)、`enabled_tools`/`disabled_tools`、`default_tools_approval_mode` 与 per-tool `approval_mode`、`scopes`/`oauth_resource`、`experimental_environment = local|remote`。
- 无 per-invocation MCP 文件 flag；只能 `-c mcp_servers.x.y=...` 或 config.toml。推荐解法：**每 agent 独立 CODEX_HOME，整体渲染 config.toml**（等价 strict 语义）。
- transport 只有 stdio + streamable HTTP，无独立 SSE 键。

### 6. Model/effort
`--model/-m`、`-c model_reasoning_effort="high"`（值：`minimal|low|medium|high|xhigh`）、`--profile/-p`、`--oss`（本地 Ollama）。config 优先级：CLI flag > profile > 项目 `.codex/config.toml` > `~/.codex/config.toml` > `/etc/codex/config.toml` > 默认。

### 7. Sandbox/权限（docker 内场景）
- 直接等价 `--dangerously-skip-permissions` 的是 `--dangerously-bypass-approvals-and-sandbox`（`--yolo`），官方明说 "only use inside an externally hardened environment" —— **已在 docker 容器内时用这个**。Linux 原生沙箱用 Landlock/seccomp，在无特权容器里常不可用，bypass 反而是官方姿势。
- 温和档：`--sandbox danger-full-access -a never` 或 `--sandbox workspace-write` + `--add-dir`。
- `--full-auto` 已弃用。config 侧 `approval_policy`、`sandbox_mode`、`[sandbox_workspace_write]`（`writable_roots`/`network_access` 等）。

### 8. Auth
- `CODEX_API_KEY`：exec/CI 官方推荐 env var。`OPENAI_API_KEY` SDK 亦识别；两者与 `auth.json` 的确切优先级**无官方明文**（上线前实测钉死）。
- 订阅 auth：`codex login`（浏览器）、`codex login --device-auth`（设备码，headless 首选）、`codex login --with-api-key`（stdin 读 key）、`codex login status`（登录时 exit 0，可做健康检查）。
- `auth.json` 在 `$CODEX_HOME/auth.json`，官方明确支持 scp/docker 预置进容器；`cli_auth_credentials_store = file|keyring|auto`。企业侧 `forced_login_method = chatgpt|api`。

### 9. Hooks/生命周期
- 完整 hooks 系统（2026）：事件模型与 Claude Code 高度同构（`SessionStart`(含 startup/resume/clear/compact source)、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`PermissionRequest`、`Pre/PostCompact`、`SubagentStart/Stop`、`Stop`）。
- 配置：`~/.codex/hooks.json` 或 config.toml `[hooks]`；repo 级 `.codex/hooks.json`；多源合并不覆盖。`features.hooks` 现默认开启。
- stdin payload：`session_id`、`turn_id`、`cwd`、`hook_event_name`、`model`、`transcript_path`、`permission_mode` + 事件字段；输出 JSON 支持 `continue`/`stopReason`/`systemMessage`/`suppressOutput`。有 hook 信任机制，`--dangerously-bypass-hook-trust` 可跳过。
- 旧 `notify = ["prog"]` 仍在：仅 `agent-turn-complete` 事件，payload 单个 JSON 参数：`type`、`thread-id`、`turn-id`、`cwd`、`input-messages`、`last-assistant-message`。

### 10. Skills
- Agent Skills 开放标准，`SKILL.md`（YAML frontmatter：`name`/`description`）与 Claude Code 格式兼容（社区大量实测互通）。
- 发现位置：repo `.agents/skills`（cwd 向上到 repo root）、`~/.agents/skills`、`/etc/codex/skills`。同名不合并。可选 `agents/openai.yaml` 加元数据。config `[[skills.config]] path=... enabled=false` 可禁用。
- exec 模式下靠隐式匹配触发；显式 `$`/`/skills` 语法是 TUI 特性，exec 显式调用无官方文档（中置信）。

### 11. Config home
`CODEX_HOME`（默认 `~/.codex`）＝ `CLAUDE_CONFIG_DIR` 等价物，内含：`config.toml`、`auth.json`、`sessions/`、`archived_sessions/`、`log/`、`hooks.json`、profile 文件、SQLite 状态库。`--ignore-user-config` 跳过 config 但 auth 仍走 CODEX_HOME。

### 12. 安装/锁版本
- npm meta 包 `@openai/codex`（9.7KB launcher），实际二进制在平台包（linux-x64 unpacked 约 293MB，单个 Rust 静态二进制，运行时零依赖、不需要 Node）。
- Docker 锁版本：`npm i -g @openai/codex@0.142.5`，或直接下 GitHub release 的 `codex-x86_64-unknown-linux-musl.tar.gz`（musl 静态，最适合容器）。CLI 有内建 self-update（v0.128+），容器里应禁用/忽略。
- 版本节奏：约每周一个 minor；配 `--strict-config` 可在升级破坏 config 时 fail-fast。

## 抽象层必须补齐的缺口清单

1. **无 `--session-id` 预设** —— 需以 codex 返回的 thread id 为续接令牌 + `thread.started` 解析 + 崩溃边界处理（最大缺口）。
2. **无聚合单 JSON 输出** —— 自聚合 JSONL。
3. **无美元 cost 字段** —— 只有 token 数，cost_usd 允许为 None。
4. **无退出码枚举表** —— 错误细分靠 `turn.failed`/`error` 事件。
5. **无 per-invocation MCP config 文件 flag** —— 每 agent 独立 `CODEX_HOME` 渲染 config.toml（等价 strict）。
6. **无 `--max-turns`** —— 外部 watchdog（现有 timeout 已覆盖）。
7. **内置工具无 allow/deny flag** —— 靠 sandbox/approval 粒度与 `PreToolUse` hook 兜。
8. **`CODEX_API_KEY`/`OPENAI_API_KEY`/`auth.json` 优先级无明文** —— e2e 阶段实测钉死。

## Sources

- https://developers.openai.com/codex/noninteractive
- https://developers.openai.com/codex/cli/reference
- https://developers.openai.com/codex/config-reference
- https://developers.openai.com/codex/config-advanced
- https://developers.openai.com/codex/hooks
- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/auth
- https://developers.openai.com/codex/changelog
- https://github.com/openai/codex/issues/15271 · #13242 · #15767 · #4721
- https://github.com/openai/codex/discussions/3827
- https://github.com/openai/codex/releases
- https://takopi.dev/reference/runners/codex/exec-json-cheatsheet/
- https://blakecrosley.com/blog/codex-hooks-make-the-harness-real
- https://codex.danielvaughan.com/2026/04/15/codex-cli-hooks-complete-guide-events-policy-patterns/
- https://www.robert-glaser.de/claude-skills-in-codex-cli/
