# Agent Layer（Agent 层 / 单 Agent 能力封装层）

> 父任务：`.trellis/tasks/06-26-foundagent-v6`。四层骨架自底向上第 ② 层，构建在 VM 层（AC1-6 已 merge @ 5381775）之上。
> 状态：规划中（brainstorm 已收敛，待 design/implement 定稿后 `task.py start`）。
> 设计基调（用户已收敛）：**先骨架、留接口、不过度投入**。关联 memory `foundagent-working-style`。

## Goal（目标）

把 VM 层「容器里裸跑的一个 claude 进程」升级为一个**可声明、可指派任务、可换 provider、能加载公司 skill/hook/prompt 的单-Agent 能力封装**。本层只负责「单个 agent 的能力 + 执行接口」；多 agent 调度/回收归编排层。

**测试驱动**：先做最小可运行的 agent 抽象 → 跑通 VM 层悬空的 AC3（容器内 agent 用浏览器+账号完成一件真实任务）→ 按需扩展。

## Background / 现状地基（VM 层已交付，Agent 层在其上构建，不要重造）

- 镜像 `foundagent/cua-agent`（`vm/docker/Dockerfile.agent`）：base + node + claude CLI + cua-computer + 薄 MCP `/opt/foundagent/cua_mcp.py` + `/opt/foundagent/mcp.json`（`cua-local`，`CUA_HOST_SERVER=1`，连容器内 computer-server:8000）。
- `orchestration/broker.py` `spawn()`（broker.py:39-105）：`docker run` → 等 computer-server(:8000) → `docker exec` 跑
  `claude -p {task} --mcp-config /opt/foundagent/mcp.json --dangerously-skip-permissions --output-format text`，运行时注入 `CLAUDE_CODE_OAUTH_TOKEN`（订阅）。
- 账号注入：`accounts/<id>/secrets.env` → `--env-file`（VM AC2）。
- 静态出口 IP：`proxy` → 容器 `HTTP(S)_PROXY`（VM AC4）。
- 可观测：`.claude` JSONL transcript 挂宿主 `vm/data/<name>/claude`（VM AC5）。
- graceful shutdown + `claude --resume`（VM AC6）。
- **关键现状（本层要解决的痛点）**：`broker.py:91-105` 把「VM spawn」与「agent 启动逻辑」**耦合**在一起；agent 的「定义」散落为硬编码（image / mcp-config / flags / token）。Agent 层 = 把这层抽出来、声明化、加 seam。

## Confirmed Decisions（已收敛，brainstorm 全部 open question 已 resolve）

- **D1 范围** = seam + 装载骨架，测试驱动，**不写实际判断力 skill**（判断力留到骨架之后）。
- **D2 Provider** = 只实现 Claude Code 并做扎实；Provider 抽象层留好 Codex/OpenCode 接口占位但不实现（只声明真正验证过的 provider，占位接口不算已支持）。
- **D3 凭证** = 双轨可切 seam；默认已验证的 Claude 订阅（`CLAUDE_CODE_OAUTH_TOKEN`，成本最低），可一键切 API key（`ANTHROPIC_API_KEY`）。
- **D4 边界** = 本层只封装单 agent 能力 + 执行接口；多 agent 调度/回收归编排层（`06-26-orchestration-layer`）。
- **D5 定义形态** = 纯通用模板 + 声明文件（如 `agents/<role>.yaml`，与 `accounts/secrets.env` 同风格）；「角色」= 声明文件实例，由编排层选用，**Agent 层不内建角色枚举**。**agent spec（能力维度）与 account（账号维度）正交，运行实例 = 二者组合（M×N）**。
- **D6 装载范围** = 三类载体全覆盖：system-prompt/`CLAUDE.md` + `.claude/skills/` + `.claude/settings.json` hooks，各一个 trivial 示例证明注入生效，不写判断逻辑。
- **D7 broker 处置** = 重构为单一路径：agent 启动逻辑迁入 Agent 层，`broker.py` 改为调用 Agent 抽象；实现需含 VM 层回归测试（不退化）。

## Requirements（需求）

- **AG1 声明式 Agent 定义**：把散落在 broker 的 agent 配置收成一个**声明文件**：provider、凭证来源、挂载的 skill/hook/prompt、system prompt、mcp 配置。新增/调整 agent 只改声明、不改核心代码。
- **AG2 Provider seam**：抽象「在容器内执行一个 agent 任务」的接口契约；实现 `ClaudeCodeProvider`；留 Codex/OpenCode 接口占位（stub 抛 NotImplemented）。
- **AG3 凭证 seam**：`CredentialSource` 抽象，与 provider 解耦；默认订阅、可切 API key；负责注入容器的正确凭证 env。
- **AG4 Skill/Hook/Prompt 装载（三类全覆盖）**：注入机制覆盖 system-prompt/`CLAUDE.md` + `.claude/skills/` + `.claude/settings.json` hooks；每类一个 trivial 示例证明注入生效（**不写实际判断逻辑**）。可扩展、声明式。判断力=skill+hook，本期打通装载机制、后续无缝接入。
- **AG5 任务执行接口**：给 Agent 一个任务 → 执行 → 回**结构化结果**（final text + ok/error + 可选 cost），基于现有 headless `claude -p`。
- **AG6 端到端打通（收编 VM AC3）**：容器内 agent **加载示例 skill/hook** → 浏览器打开网站 → 用注入的**低风险账号**（自建邮箱 / 测试站登录页，非真实业务）登录 → 截图确认。
- **AG7 broker 收敛**：`broker.py` 改为调用 Agent 抽象，消除重复的 agent 启动逻辑；VM 层行为回归不退化。

## Acceptance Criteria（可测试验收）

- [x] **AC1（AG1+D5）声明式定义**：新增/修改一个 agent 只需改/加一个声明文件，**不改任何 `.py`**；声明里能配 provider / 凭证来源 / 挂载的 skill/hook/prompt / system-prompt。验证：照声明加一个 agent 实例，跑通无代码改动。 ✅ `operator.yaml`+`researcher.yaml` 零代码改动加载（单测 `test_ac1_*`）。
- [x] **AC2（AG2）Provider seam**：Provider 抽象接口存在；`ClaudeCodeProvider` 实现并跑通一个任务；Codex/OpenCode 占位 provider 被调用时抛 `NotImplementedError`。验证：单测 + 跑通 Claude provider。 ✅ 26 单测 + live smoke。
- [~] **AC3（AG3）凭证 seam**：默认订阅（`CLAUDE_CODE_OAUTH_TOKEN`）跑通；切到 API key（`ANTHROPIC_API_KEY`）时注入正确 env 并能跑通最小调用。验证：两种凭证各跑一次、env 注入正确。 **订阅侧✅ + 互斥注入 seam✅**（spike 实测 api-key 静默压订阅，已钉死）；**api-key 真 key 端到端 DEFERRED**——无真实 key，路径/识别/优先级已验证，待有 key 时复核「能跑通最小调用」。
- [x] **AC4（AG4+D6）三类装载生效**：① system-prompt 注入 → agent 输出体现注入的人设/宪章；② skill 注入 → agent 能识别/调用该示例 skill；③ hook 注入 → 示例 hook（如 PreToolUse 打日志）被触发。验证：三类各有可观测证据。 ✅ AC6 跑中证据：`[charter-ack]` / `Skill hello-foundagent` / `hook.log` PreToolUse×59。
- [x] **AC5（AG5）结构化执行接口**：调用执行接口跑一个任务，返回结构化结果（final text + ok/error 至少二者）。验证：断言返回结构字段。 ✅ `AgentResult` 解析按 spike 真实字段（is_error/result/total_cost_usd）。
- [x] **AC6（AG6）端到端**：容器内 agent 加载示例 skill/hook → 浏览器打开网站 → 低风险账号登录 → 截图确认，五者（computer-use + 浏览器 + 账号注入 + skill 装载 + provider/凭证 seam）打通。验证：跑通并留存截图 + transcript。 ✅ 公开测试站 the-internet 登录成功（`ok=True`/$0.979/63turns），截图+9.5MB transcript 留存；账号注入用 `DEMO_ACCOUNT_EMAIL` 填页面证明、token 零泄漏。详见 `research/ac6-e2e.md`。
- [x] **AC7（AG7+D7）broker 单一路径**：`broker.py` 不再含重复的 agent 启动逻辑、改为调用 Agent 抽象；原 broker demo（firefox / describe desktop）回归不退化。验证：重构后跑原 demo 通过。 ✅ 回归 demo 两 operator `ok=True`，行为不退化。

## Out of Scope（本层不做）

- 多 agent 调度 / 任务分发 / 结果回收（→ 编排层）。
- 实际商业判断力 skill（→ 骨架就绪之后）。
- Codex / OpenCode 的真实实现（只留 seam 接口占位）。
- 常驻长跑 / 多轮长会话（沿用 VM 层 task-per-container posture；如需多轮只留 `--resume` 接口，不做实现）。
- 真实业务账号 / 防关联指纹精调（按需后续加，本层只用低风险账号验证打通）。

## Open Questions

- 无阻塞项（AGQ1-AGQ4 已全部收敛，见 Confirmed Decisions D5/AG6/D6/D7）。
</content>
