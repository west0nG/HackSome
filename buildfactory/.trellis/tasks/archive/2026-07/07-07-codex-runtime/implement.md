# Implement: Runtime abstraction（claude-code / codex 可切换）

> 三个 stage，每个独立可验证、独立可回滚（对应 design §7）。在独立 worktree 开发；commit 粒度自定、每 stage 至少一个 commit（回滚点）。

## Stage 1 — 收敛重构（行为零变化）

- [x] 1.1 先落 golden 快照测试：捕获当前两条路径的 argv（`build_claude_argv` 各分支 + `ClaudeCodeProvider.build_exec` 各分支）作为重构前基线 fixture。（`agent/tests/fixtures/claude_argv_golden.json`：48 resident + 144 broker 快照，重构前捕获；`agent/tests/test_claude_runtime_golden.py` 显式编码三处 deliberate diff）
- [x] 1.2 建 `agent/runtimes/base.py`：`UNSET`、`RunRequest`、`RunResult`、`Runtime` protocol、中性 effort 词表（设计 §2 原文照落）。（增补：`RunRequest.session_hint`——保 broker COMPANY_SESSION_ID↔session-id 关联与 wake 超时语义，见任务 notes）
- [x] 1.3 建 `agent/runtimes/claude_code.py`：合并两条旧路径为 `ClaudeCodeRuntime`（argv 超集见 design §3 表格；`parse_stream_json` 自 runner.py 迁入，含坑注释）。
- [x] 1.4 `agent/runtimes/__init__.py`：`runtime_for(spec)` 工厂；opencode 保持 NotImplementedError stub。
- [x] 1.5 `AgentSpec` 改造：model/effort 的 UNSET 语义（yaml 缺键 vs 显式 null 区分）；`DEFAULT_MODEL`/`DEFAULT_EFFORT` 迁入 claude adapter；`provider_for` 迁移为 `runtime_for`。
- [x] 1.6 改 `orchestration/agent_loop.py`：wake() 走 adapter；删 `build_claude_argv` 与 `agent_loop.py:36` 重复 fallback；清理 `ceo_loop.py` shim 的对应 re-export；日志行改打 RunResult 摘要（session/status/error）。（never-brick：runtimes import 失败 → `_fallback_claude_argv` 字面兜底，loop 仍可 charter-only 启动，已实测）
- [x] 1.7 改 `agent/runner.py`：run_task 走 adapter；`agent/provider.py` 删除，`agent/__init__.py` 导出面同步更新。（`AgentResult`/`ExecPlan` 移除，broker 改用 `RunResult`）
- [x] 1.8 loadout 拆分：skills 拷贝 + manifest reconcile 抽成目录无关的中性核心；claude settings.json hooks 合并留在 claude adapter 的 `materialize_home`；`resident_loadout.materialize_for` 按 provider 分发。
- [x] 1.9 全量测试 + golden 对比：只允许 design §3 表格的三处 deliberate 差异。（agent+orchestration 397 passed；company_state_kit 26 passed；loadout_check OK）
- **验证**：`python3 -m pytest agent/ orchestration/ company_state_kit/ -x -q`；golden diff 审查。
- **✅ Review gate 1**：AC1 达成（重构不回归）。回滚点：revert 本 stage commits。

## Stage 2 — Codex adapter（纯增量）

- [x] 2.1 `agent/runtimes/codex.py`：argv 构建（exec / exec resume 两分支、`--yolo`、`--skip-git-repo-check`、`-c developer_instructions`、effort 翻译表、默认 `gpt-5.5` + `xhigh`——确切模型 id 用本机 pinned CLI 验证后钉死）。
- [x] 2.2 JSONL 解析：`thread.started`→session_token、`agent_message`→text、`turn.completed.usage`、`turn.failed`/`error`/非零 rc→error；崩溃边界（无 thread.started → token=None）。**fixture 必须真实捕获**：本机装 pinned codex 跑一次 `codex exec --json` 存样，不手编。
- [x] 2.3 `materialize_home`：config.toml 渲染（mcpServers JSON→TOML + `${VAR}`/`${VAR:-def}` 展开 + chmod 600）、auth.json 预置拷贝（`accounts/<id>/codex-auth.json` → `CODEX_HOME/auth.json`，存在则跳过）、skills 拷至 `~/.agents/skills/`（复用中性核心）、hooks 留空实现 + TODO 注释。
- [x] 2.4 `agent/credentials.py`：`CodexSubscriptionCreds`（env 空）/ `CodexApiKeyCreds`（CODEX_API_KEY）；`ALL_CREDENTIAL_VARS` 扩为四元组；`credential_for` 走 `runtime.credential_kinds()`。
- [x] 2.5 broker `__main__` 凭证校验改 provider-aware。
- [x] 2.6 compose：`x-agent-env` 加 `CODEX_HOME: /sessions/<role>/codex`；`provisioner.render_role_service` 同步；`Makefile shared` mkdir codex 子目录；anchor 反漂移测试（role-lifecycle-contracts 里那套）应自动覆盖——确认。
- [x] 2.7 `role.py lint_bundle`：provider 白名单（claude-code|codex）。
- [x] 2.8 `Dockerfile.agent`：`ARG CODEX_VERSION=0.142.5` + `npm i -g @openai/codex@…`；补 `ARG CLAUDE_CODE_VERSION` pin 现有安装。
- [x] 2.9 单测：argv golden、JSONL fixture 解析、TOML 渲染（含 env 展开与特殊字符）、auth 预置幂等、凭证互斥（四变量清零）、lint 白名单。
- **验证**：`python3 -m pytest agent/ orchestration/ -x -q`；`make loadout-check`；`docker build -f vm/docker/Dockerfile.agent vm/` 后 `docker run --rm --entrypoint sh foundagent/cua-agent:latest -c 'claude --version && codex --version'`。
- **✅ Review gate 2**：AC2 / AC5 / AC6 达成。回滚点：revert 本 stage commits（claude 路径无感知）。

## Stage 3 — 真跑 e2e + 收尾

- [x] 3.0 **人工前置**：主机已有 `codex login` 登录态（0.142.5），`~/.codex/auth.json` 直接作种子 → `accounts/foundagent/codex-auth.json`（gitignore 已加 `accounts/*/codex-auth.json` + `accounts/*/google-sa.json` 洞）；无需用户再 device-auth。
- [x] 3.1 e2e 全过（researcher → `provider: codex` + `credentials: subscription`，一行切换）：①首唤醒 ok，回复 "I am Researcher…"（charter 生效）；②二次唤醒 `exec resume` 同一 thread id `019f3af8-…5249` 且准确复述上一条消息（跨唤醒记忆）；③三次唤醒 cua-local screenshot MCP 调用成功（config.toml 渲染通路）。物化产物验证：config.toml/auth.json chmod 600、skills 落 `~/.agents/skills`。验证后 yaml 已还原 claude-code。
- [x] 3.2 实测钉死（已写进 agent-execution-contracts Scenario D）：`CODEX_API_KEY` **优先级高于** `auth.json`（invalid key + 有效 auth.json → 401，与 ANTHROPIC_API_KEY>OAuth 同坑，四变量互斥正好挡住）；`codex login status` 登录态 rc=0（可作健康检查）。
- [x] 3.3 AC4 证据（以 e2e 实证代替人造改动）：`build_wake_prompt`/IME 渲染/objective 注入这整套为 claude 写的 wake 机制在 codex 上**零改动**跑通（中性层改动天然双生效）；反向证据：stage 2 全部 codex flag 工作未触碰 claude adapter，golden test 原封不动保持绿。
- [x] 3.4 spec 更新：`agent-execution-contracts.md`（标题改双 runtime + Scenario B 四变量互斥 + 新增 Scenario D：codex argv/JSONL/home 落点/凭证坑）、`resident-agent-contracts.md`（runtime dispatch、session token 语义、adapter-owned 默认值）、`role-lifecycle-contracts.md`（provider 白名单 lint 行）。
- [x] 3.5 回归：见 review gate 3 记录；researcher.yaml 已还原（fleet 默认行为与 main 一致）。
- **✅ Review gate 3**：AC3 / AC4 达成 → 走 Phase 3 收尾（commit、归档）。

## 回滚总针

- 任一 stage 失败：revert 该 stage commits 即回到上一个绿色状态；stage 1 之前的行为由 golden fixture 锁底。
- 生产逃生阀：所有角色 yaml `provider` 仍是 claude-code，线上行为与 main 一致——codex 路径不被任何默认配置触达。
