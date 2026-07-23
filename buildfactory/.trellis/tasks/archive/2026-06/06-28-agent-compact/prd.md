# Agent Runtime: Context Compact（上下文压缩）

> 父任务：`.trellis/tasks/06-26-foundagent-v6`。状态：planning（**未开始**，占位 + 种子需求）。
> 从编排层 brainstorm（2026-06-28）拆出：compact 本质是 **Agent Runtime** 的事、且重，单拎一个任务。
> ⚠️ 用户明确：这块要深挖、**不能草率**；**设计不在此预先展开**，等真实数据再定。

## Goal（目标）

给 **Agent Runtime** 一个**上下文自维护 / compact** 能力：让长跑 agent（尤其 CEO，但**不限于** CEO）在「长会话内」和「跨唤醒之间」维持一个**有界、可持久的 working-set**——既不让 context 无限膨胀，也不在每次唤醒时冷启动丢掉近期 in-flight 状态。

## 定位 / 边界（为什么是独立任务）

- **属 Agent 层能力扩展，不属编排层**：编排层只「消费」一个会自维护 working-set 的 agent；怎么维护是 Agent Runtime 的事。两者正交，必须解耦。
- **跨 agent 通用**：任何长跑 agent 都可能需要，不只 CEO。
- **它重 + 深**：单独任务给它独立的规划空间。

## 上下文 / 关系

- **仿 Claude auto-compact**：working-set 自维护 ≈ 压缩。同一操作两个尺度——① 会话内 native auto-compact；② 会话间睡前蒸馏进 scratchpad。
- **复用记忆层的「形」、但 store 独立**：可借用 `company_state_kit` 渐进式披露 + `record` 写书挡的形态，但 **scratchpad 是独立 store，绝不进 company folder**（三存储红线：scratchpad=运行时"脑" / goal ledger=派发记录 / company memory=静态名词）。

## Requirements（种子，全部 TBD，待真实数据 + 深挖）

- **R1** working-set 持久化 + 有界（跨唤醒不丢近期状态、又不无限膨胀）。
- **R2** 压缩策略：压什么 / 留什么 / 什么粒度 / 何时触发 —— **核心难点，留给实验**。
- **R3** 渐进式披露：working-set 是"脑"的 MAP/OVERVIEW，历史细节按指针下钻（ledger / memory / 旧 transcript）。
- **R4** 与记忆层工具复用、但 store 独立。
- **R5** 跨 agent 通用接口（不绑死 CEO）。

## Acceptance Criteria（待 brainstorm 收敛）

- [ ] TBD

## Out of Scope（本任务不含）

- CEO 唤醒循环 / 编排逻辑（编排层）。
- 公司记忆（记忆层 `company_state_kit`）。

## Open Questions

- compact 触发时机 / 粒度？（native auto-compact 够不够，还是要自写一层？）
- scratchpad 与 goal ledger 的分工边界？
- 是否所有 worker 都需要，还是只有 CEO / 长跑 agent 需要？（短命 worker 可能根本不需要 → 别一刀切）
