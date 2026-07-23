# Orchestration Layer（编排层）

> 父任务：`.trellis/tasks/06-26-foundagent-v6`。四层骨架第 ④ 层。状态：in_progress。
> **范围已演进**：早期只做 broker MVP（起多容器，OC1–OC4 已完成）；**现在主体 = 编排层 + Goal 协议，且全程容器化（DooD）**。broker 退成其中一个（容器化的）搬运组件。

## Goal（目标）

让一套**自主编排**跑起来：上面派「要的结果」(goal)、下面 agent 一轮轮干到验收通过——**派 goal 不派 task、确定性状态机管流程、验收交 agent、看门狗防瞎耗**。全程零人，全在容器里（DooD），宿主近空、一键启动。

## 原则 / 约束

- **零人**：运行期人类零介入——**验收也绝不许有人**（零人公司核心信条）。
- **确定性外壳先定、大模型那半 defer**：能用程序按死规矩判的（状态 / 锁 / 流转）先写实；模糊的（goal 具体字段、验收细则）等真实 case 再长，不现在拍死。
- **容器化（DooD）**：broker 进容器挂宿主 socket、起兄弟容器（非嵌套）；宿主近空 + 一键启动。
- **不照搬业界**：调研（`research/goal-definition-survey.md`）只作参考。
- **测试期先放权**：socket 提权等安全收窄后置。

## 已完成的基础（broker MVP，OC1–OC4 ✅）

broker 能一条命令起 N 个隔离 `foundagent/cua-agent` 容器、并发干活、收成败+输出、干净 teardown（已验证：op-a 开 Firefox、op-b 描述桌面，互不影响）。这是地基；本期在它之上长 Goal 协议 + 把 broker 搬进容器。

## Requirements

- **R1 派 goal 不派 task**：派发单元 = 想要的结果，执行者自己想步骤；goal 可递归套子 goal。
- **R2 goal 与「一次尝试(run)」解耦**：goal 持续活着，同一执行者跨多 session 死磕、验不过接着改，**不杀了从零重起**。
- **R3 确定性状态机外壳**：状态枚举 + 单一领取加锁（俩 agent 不抢同一 goal）+ 看门狗刹车（做不成就升级/kill），纯程序判定。
- **R4 验收 = 统一派验收 agent**：去公司 assets 查成果有没有/好不好；要确定性就让它自己写检查程序跑。**零人**。
- **R5 成果落公司 assets**：goal 记录只管「派了、到哪步」，不存成果本身（成果=名词进记忆层，记录=动词进 ledger）。
- **R6 容器化（DooD）**：broker 进容器、挂 socket 起兄弟容器；宿主只剩 docker 引擎 + 一键启动（compose）。
- **R7（defer）**：goal 的大模型侧字段、验收细则、约束（预算/时限）等，等真实 case 再长。

## Acceptance Criteria

- [x] **AC1** 端到端：真实 e2e 跑通（派 goal → executor 写成果进公司记忆 → 验收 agent 读判 `VERDICT: PASS` → `done`，0 重试、全程无人）。注：happy path 1 session 即过；跨 session 重试由单测 + e2e bug 期间真实复现覆盖。
- [x] **AC2** 失败回路：验不过 → 回 `running` 接着干（非重起）、attempts 累加 → N 次 watchdog `kill`。单测覆盖 + e2e 调试期真实观测到。
- [x] **AC3** 并发锁：8 线程争抢单测，单一领取生效（俩 agent 不抢同一 goal）。
- [x] **AC4** 容器化（DooD）：broker 在容器里（`FROM docker:cli`+python3+pyyaml）、挂宿主 socket 起兄弟容器（hello-world + sibling-proof 验证、宿主 `docker ps` 确认平级非嵌套）；一句 `docker compose up -d` 起控制平面（宿主近空）。路径一致技巧（`${PWD}:${PWD}`）使 broker.py 零改动。
- [x] **AC5** 成果在公司 assets 里可被验收 agent 查到；goal 记录不含成果副本（e2e 验证：executor 写 `/company`、验收 agent 读到判过）。
- [x] **OC1–OC4** broker MVP（多容器并发起停 + 结果回收）—— 已完成。

## Out of Scope（本期不含 / 已拆出）

- **外设层**（外部信号归一）→ `06-28-peripheral-layer`。
- **compact / agent 工作记忆**（执行者跨 session 的记忆维护）→ `06-28-agent-compact`。
- **CEO 顶层决策逻辑**（选题 / kill 判断）→ skill+hook 阶段。
- **heartbeat**（没人叫就自检）→ 同编排层、待写。
- **goal 大模型侧细则**、**安全收窄**（socket-proxy → 语义化 broker → 强隔离 runtime）。

## 后续 / 风险

- 安全演进路线见 `research/container-orchestration.md`；socket 挂载=提权，硬化后置。
- ⚠️ Docker Desktop 已升级（engine 29.5.3）修复 CVE-2025-9074。
