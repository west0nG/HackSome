# 将 submit_result 简化为纯完成声明

## Goal

把 `submit_result` 从“Worker 提交一份可供验收的结果描述”改成“Worker 声明自己已经完成当前 Goal”的纯控制信号。

Worker 的真实工作可以发生在 `/company`、公开网站、社交平台、外部账户或其他系统中；是否需要维护 Company State 应由工作本身决定，不能成为提交完成的前置条件。独立 Verifier 根据 Goal intent、只对其公开的 acceptance 信息以及自身可用的查证能力完成验收，不能依赖 Worker 自述。

## Background

当前实现把三件本应分离的事情绑在一起：

1. Worker 必须把成果或结论写进 `/company`；
2. Worker 必须向 `submit_result` 提交非空 `summary` 和 `/company` 下的 `company_refs`；
3. Verifier Prompt 把 Worker 摘要和引用路径作为主要验收入口，并要求结果必须持久存在于 `/company`。

代码证据：

- `orchestration/company_hub.py:409-449`：`submit_result` 强制要求 `summary`、`company_refs`，随后把两者写入 review payload；
- `orchestration/scheduler.py:316-342`：Scheduler 校验并持久化摘要与 Company State 引用；
- `orchestration/worker_manager.py:433-455`：初始与返工 Prompt 强制 Worker 写 `/company` 后提交路径；
- `orchestration/verifier_runtime.py:219-230`：Goal Verifier Prompt 依赖 Worker 摘要与引用，并把“不持久存在于 `/company`”定义为 FAIL；
- `agents/assets/worker-v7-charter.md:3-12`、`agents/assets/skills/submit-work/SKILL.md:6-20`：Agent-facing 契约重复上述要求；
- `.trellis/spec/backend/three-layer-agent-company-contracts.md:43-49`、`.trellis/spec/backend/company-state-contracts.md:36-44`：活跃规范把 `/company` 结果引用写成硬契约。

已确认的现有能力：Verifier 已获得 Goal intent、私有 acceptance、只读 `/company`、浏览器与桌面查证能力；Verifier runtime 当前不注入 account secrets（`agents/mcp/verifier-v7.json:1-12`、`orchestration/verifier_runtime.py:80-132`）。本任务将改变这一边界，使 Verifier 能独立检查需要登录的外部结果。

## Requirements

### R1：`submit_result` 是无业务内容的完成信号

- Worker 调用 `submit_result` 时不提交 `summary`、`company_refs` 或任何其他结果正文；业务 payload 为空对象。
- 稳定 `request_id` 继续保留，它属于幂等传输协议，不属于 Worker 的结果内容。
- 方法名继续使用 `submit_result`；本任务不引入新的完成方法。

### R2：Company State 写入与完成声明解耦

- Worker 不得因为提交协议而被迫创建 `/company` 文件、brief、summary、result marker 或其他占位记录。
- 如果工作自然产生值得公司长期共享的事实或资产，Worker 仍可按 Company State 契约直接维护 `/company`；这是业务行为，不是 `submit_result` 的必需输入。
- 对外操作可以在公司文件夹中完全不留下专门结果记录。

### R3：完成声明仍受确定性状态机约束

Hub 仍必须校验：

- 调用者是当前 Goal 绑定的 Worker；
- Goal 仍处于允许完成声明的运行状态；
- Goal 尚未越过绝对 deadline；
- 相同 `request_id` 重放不重复创建 review，不同内容复用同一 `request_id` 仍触发幂等冲突。

### R4：声明完成后自动进入独立验收

- 有效 `submit_result` 继续推动 Goal 从 `running` 经 `reported` 进入 `verifying`。
- Hub 自动创建 `goal_result` review；Worker 无需选择、通知或提供材料给 Verifier。
- 等待 verdict 期间继续保留同一 Worker lifecycle，以便 FAIL 后原地返工。

### R5：Verifier 不接收 Worker 自述

Goal review 至少包含：Goal ID、owner Department、Goal intent、Verifier 私有 acceptance 和绝对 deadline。

Goal review 不包含 Worker summary、Worker 提供的 Company State 引用或其他由 Worker 为验收专门组织的 result payload。

### R6：Verifier 独立取证和判定

- Verifier 根据 Goal、acceptance、自身上下文与可用工具自行决定到哪里、用什么方式查证。
- `/company` 只是 Verifier 可读的一种证据来源，不是所有 Goal 的必需结果载体。
- Verifier 不能因为 Worker 没写 Company State、没提供摘要或没提供路径而自动 FAIL。
- PASS/FAIL 仍只能由 Verifier 的结构化 `submit_verdict` 推动；Worker 的完成声明不等于 Goal 完成。

### R7：自然语言结束不能替代完成声明

Worker turn 即使自然语言声称“完成”，只要没有调用 `submit_result`，Hub 仍按“未正式声明完成”处理并续跑同一 Worker。

### R8：现有 PASS/FAIL 生命周期不变

- PASS：Goal `done`，通知 owner Department，停止 Worker；实际停止确认前不释放 Worker 槽位。
- FAIL：同一 Worker、Goal、容器、workspace、home、session token 和绝对 deadline 继续返工；下一次完成声明创建新的 review。
- 超时与显式取消语义保持不变。

### R9：Verifier 获得账户 secret

- 一次性 Verifier runtime 与 Worker 复用同一个完整账户包：注入
  `accounts/<id>/secrets.env`，并把 `accounts/<id>/` 只读挂载到 `/account`；不新增
  Verifier 专属或只读凭据体系。
- Verifier 不能因为缺少登录态或外部账户凭据而被迫依赖 Worker 自述。
- 账户凭据只用于检查当前 review 的真实外部结果；Verifier 仍不得代替 Worker 执行、修复或发布工作。
- Verifier 的 `/company` 挂载继续保持只读，Hub 方法权限继续只允许提交当前 review 的 verdict。
- 接受的安全边界：部分账户 secret 在外部系统上技术上具有写权限；第一版通过 Verifier charter、一次性生命周期和完整运行日志约束“只检查、不修改”，不新增外部服务级只读权限强制。

### R10：Verifier 保持最小 Skill 集

- Verifier 不加载 Worker 的部署、Twitter、GA4、研究、视觉或其他执行型 Skills。
- 独立验收依靠 Goal intent、私有 acceptance、完整账户包、通用浏览器/桌面、只读 Company State 与 `submit_verdict`。
- 某类外部结果未来若无法通过通用能力检查，应新增专门的只读验收能力，不把整套 Worker 执行 Skill 交给 Verifier。

## Acceptance Criteria

- [x] **AC1**：绑定到运行中 Goal 的 Worker 可以用空业务 payload 调用 `submit_result`，Goal 进入 `verifying` 并只创建一条 review。
- [x] **AC2**：`submit_result` 不接受也不要求 `summary`、`company_refs`；Agent-facing 命令不要求 Worker 填写任何结果正文。
- [x] **AC3**：Worker 在完全不新增 `/company` 内容的情况下也能声明完成并进入验收。
- [x] **AC4**：goal-result review payload 不含 Worker summary、Worker refs 或专门 result 正文，仍包含 intent、私有 acceptance、owner 和 deadline。
- [x] **AC5**：Verifier Prompt 明确要求独立取证，不得因缺少 Worker 摘要、引用或 `/company` 结果文件本身而 FAIL。
- [x] **AC6**：Verifier PASS、FAIL、超时、取消、同 Worker 返工、stop ack 后释放槽位等既有状态机行为不回归。
- [x] **AC7**：重复发送相同 request ID 的完成声明不会重复建 review；越权 Worker、终态 Goal、超时 Goal 的提交继续被拒绝或成为既有终态 no-op。
- [x] **AC8**：Worker charter、`submit-work` Skill、Worker Prompt、Verifier charter/Prompt、活跃后端规范与 Company State 规范全部统一为新语义，不再出现“提交前必须写 `/company` 并提供引用”的陈述。
- [x] **AC9**：更新相关 Scheduler、Hub、Worker Manager、Verifier runtime、Agent Skill/charter、规范和测试；完整质量门通过。
- [x] **AC10**：真实 Verifier runtime 与 Worker 使用同一个完整账户包（`secrets.env` + `/account:ro`），能够通过浏览器、桌面或已有外部工具检查登录后可见的结果；同时保持 `/company` 只读和 Hub 方法最小权限。
- [x] **AC11**：Verifier 的 AgentSpec 不新增任何 Worker 执行型 Skill；现有最小 Skill 集保持不变，并由 loadout 测试锁定。

## Out of Scope

- 改变 Goal 的 FIFO、5 Worker、3 Verifier、deadline、取消或返工策略；
- 让 Worker 自己验收或自行选择 Verifier；
- 恢复 Worker Inbox、Notes、Objective、Department 消息或创建子 Goal 的能力；
- 为了兼容旧 result payload 而长期保留摘要/引用双协议；具体存量状态容忍方式在技术设计中处理。
