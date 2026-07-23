# Runtime abstraction: claude-code / codex switchable agent runtime

## 背景 / 目标

目前 fleet 里所有 agent 的底层 runtime 都是 Claude Code CLI，且 runtime 知识散落在两条独立路径里（常驻唤醒 `orchestration/agent_loop.py` 硬编码 argv；broker 路径走 `agent/provider.py` 的 seam）。本任务引入 runtime 抽象层，使每个角色可以通过 `agents/<role>.yaml` 的 `provider` 字段选择 **claude-code 或 codex** runtime。

核心价值主张（用户原话）：**以后修改只改一份代码，两个 runtime 同时自适应**——runtime 差异必须收敛到 adapter 内部，所有调用方与角色声明保持 runtime 中性。

## 需求

1. **可切换**：`agents/<role>.yaml` 里 `provider: claude-code | codex` 真正生效；切换 runtime 只需改这一行，charter / skills / mcp json 等声明资产无需分叉。
2. **两条路径都支持**：常驻唤醒路径（agent_loop，生产在用）和 broker 一次性任务路径（runner）都通过同一抽象层跑两种 runtime。
3. **单一 runtime 知识点**：每种 runtime 的 CLI 细节（argv、输出解析、session 续接、凭证、home 物化）只存在于它自己的 adapter 文件里；调用方只面对中性模型。现有 `build_claude_argv` 与 `ClaudeCodeProvider.build_exec` 两份重复必须合并。
4. **能力对齐**：codex 侧要覆盖 claude 侧现有能力面——charter 注入、session 续接（跨 wake 连续性）、per-role MCP 配置（等价 strict 语义）、model/effort 指定、bypass 权限、skills 物化；hooks 物化留骨架（当前角色未用 hooks，不做完整实现，见"范围外"）。
5. **凭证对称**：codex 侧支持 `subscription`（预置 `$CODEX_HOME/auth.json`，主用）与 `api-key`（`CODEX_API_KEY`）两种，与 claude 侧现有模式对称；互斥注入清单扩展到 OpenAI 变量。
6. **镜像**：`Dockerfile.agent` 安装 pinned 版本的 `@openai/codex`；顺手把现有 `@anthropic-ai/claude-code` 的浮动 latest 也 pin 住；容器内禁用/规避 codex self-update。
7. **provisioner 兼容**：create-role 物化出的新角色在 `provider: codex` 下也能正常起容器（compose 模板不感知 provider，`CLAUDE_CONFIG_DIR` 与 `CODEX_HOME` 两个 env 恒注入）。

## 约束

- **默认行为零变化**：fleet 默认 provider 仍是 claude-code；不改任何角色 yaml 的现有值；重构后 claude 路径的 argv 语义与现在等价，现有测试全部保持通过。
- **声明资产单一来源**：`agents/mcp/<role>.json`（mcpServers JSON）保持唯一 source of truth，codex 侧由 adapter 翻译渲染，不手工维护第二份 TOML。
- **never-brick 契约延续**：loadout / overlay / objective 的"降级不崩"立场对 codex 路径同样适用。
- **codex 无法预设 session id**（上游 open issue）：session 续接令牌以 adapter 返回值为准，抽象接口不得假设"调用方指定 id"。
- opencode 仍保持 stub；`gen-image` skill 里的 `codex exec` 图片生成调用不属于本任务，不动。
- 遵循 repo 惯例：代码/注释英文；worktree 内开发、自治 commit。

## 验收标准（AC）

- [x] **AC1（重构不回归）**：golden test 以重构前实跑捕获的 argv 快照（48 resident + 144 broker 用例）锁定，仅三处 deliberate diff 显式放行；全量测试绿（基线 385 → 468）。
- [x] **AC2（单测覆盖 codex adapter）**：29 个 codex 单测；JSONL 解析全部基于真实捕获 fixture（`agent/tests/fixtures/codex/`，codex-cli 0.142.5 + gpt-5.5 实录，含非致命 error item 与 turn.failed 场景）；config.toml 渲染经 tomllib 往返验证；四变量凭证互斥有测。
- [x] **AC3（切换即生效）**：researcher 一行切 `provider: codex` + `credentials: subscription` → 容器内真 LLM 三连唤醒（2026-07-07）：charter 生效（自报 Researcher 身份）、cua-local MCP screenshot 调用成功（config.toml 通路）、第二/三次唤醒 `exec resume` 同一 thread id `019f3af8-…5249` 且准确复述历史消息（跨唤醒记忆）。验证后 yaml 已还原。
- [x] **AC4（一份代码两边自适应）**：为 claude 写的 wake prompt/IME 渲染/objective 注入机制**零改动**跑通 codex（中性层改动天然双生效）；反向证据：stage 2 全部 codex flag 工作未触碰 claude adapter，golden test 原样保持绿。
- [x] **AC5（镜像可复现）**：`ARG CLAUDE_CODE_VERSION=2.1.202` + `ARG CODEX_VERSION=0.142.5`，重建镜像内 `--version` 实测输出与 pin 一致。
- [x] **AC6（provisioner 兼容）**：lint provider 白名单（codex 通过、opencode/未知拒绝）+ compose/provisioner 双 home env（CLAUDE_CONFIG_DIR + CODEX_HOME）同步渲染 + anchor 反漂移测试扩展覆盖，全部单测通过。

## 范围外

- opencode provider 实现。
- codex hooks（hooks.json）完整物化——当前没有角色声明 hooks，仅在设计里留同构映射位，等第一个用 hooks 的角色出现再实现。
- memory 层 record_stop_hook 在 codex 侧的对齐（依赖上一条 hooks 物化）。
- 多 runtime 混合成本核算（codex 无美元 cost 字段，RunResult.cost_usd 允许 None，聚合报表不在本任务）。

## e2e 凭证前置（用户已拍板）

- 主用 **ChatGPT 订阅**：需要用户执行一次 `codex login --device-auth`，产出的 `auth.json` 预置进 per-role `CODEX_HOME`（落点设计见 design.md）。
- 代码同时支持 `CODEX_API_KEY`（api-key 模式），e2e 以订阅为准。
