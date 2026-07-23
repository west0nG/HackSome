# 聪明中枢 Hub：把核心 IP 迁到异步世界 — 子任务 ②

> 父任务 `06-29-orchestration-rebuild`；**依赖 child① `resident-departments`**。
> child① 跑通了「统一 loop + 全员常驻 + 双向 inbox」机制，但**有意暂缺**独立验收分权与 watchdog。本任务把这些核心 IP 补回，并从同步 `run_goal` 迁到异步事件驱动。

## 目标

把现有同步编排的确定性保证，迁到 child① 的异步常驻世界，一条都不丢：

1. 独立验收分权（doer ≠ judge）
2. 确定性状态机（goal 生命周期由事件驱动推进）
3. watchdog（验不过带反馈重投、超次 / 超时则 kill）
4. 崩溃可恢复（in-flight goal 不丢）

## 约束

- **架构形态：中枢 Hub（2026-06-29 与用户确认）。** 所有 agent 消息经一个**非 LLM 的确定性中枢**路由分发，由它持有状态机、编排验收、跑 watchdog —— 作为单一的可观测 / 可修复点。具体设计（Hub 如何同构于 `agent_loop`、投递路径如何回改、崩溃如何对账恢复等）见 `design.md`。
- 复用 child① 资产（`agent_loop` / `inbox` / `messaging` / IME），不另起炉灶。
- 验收沿用现有 read-only verifier 资产（`VERDICT` 标准化输出）。
- 重试次数默认 3，可调（不影响架构）。

## 范围

**IN**
- 新增确定性 Hub，承接路由 + 状态机 + 验收编排 + watchdog。
- 把 child① 的「agent 直投对方 inbox」改为「经 Hub 路由分发」。
- 独立验收接回异步流：部门干完不自判，由 Hub 路由到独立 verifier。
- ledger 旁路留痕 + 崩溃可恢复。

**OUT**
- 外设层统一信封 IME（归 `06-28-peripheral-layer`；本任务只保证不冲突）。
- 删除 ephemeral spawn / broker（瘦身保留，可回退）。
- 新 role 内容（归 `06-28-role-library`）。

## 验收标准

- [ ] **AC1 单一中枢**：所有 agent 间消息经 Hub 路由，无 agent 直投对方；全程无 spawn、无中心 pump `docker exec`。
- [ ] **AC2 验收分权**：执行部门不能给自己的 goal 判 `done`；由独立 read-only verifier 出 `VERDICT`，Hub 据此推进。
- [ ] **AC3 异步状态机**：goal 由事件驱动从 `open` 确定性走到 `done` / `killed`，不再依赖同步 `run_goal`。
- [ ] **AC4 watchdog**：验不过带反馈重投同一部门（续 context）；超次 / 超时 → `kill`。
- [ ] **AC5 可恢复**：Hub 或任一容器崩溃重启后，in-flight goal 经留痕恢复到正确状态，不丢、不重复执行。
- [ ] **AC6 零人闭环**：CEO → 部门 → 独立验收 → 回 CEO 的端到端闭环在新架构下通过。
- [ ] **AC7 能力等价迁移**：现有单测覆盖的能力（状态机、验收分权、watchdog、派活原语）迁移不退化。

## Notes

- 复杂任务：`task.py start` 前补 `design.md` + `implement.md`；design 前调研已完成（`research/async-state-machine-survey.md`）。
- 继承 child① review 两项待办（m3 首轮 wake 失败仍存 session id；n1 wake prompt 文案对部门错位），随本任务处理。
