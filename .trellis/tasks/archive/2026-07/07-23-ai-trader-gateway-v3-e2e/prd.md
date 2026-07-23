# AI Trader Gateway v3 复跑

## Goal

使用相同的 PandaAI「Build the Next AI Trader」赛题完整复跑 Useful Idea 工作流，验证 Problem Gateway v3 是否减少错误拒绝，同时不降低最终产品质量。

## Requirements

1. 输入与 `07-23-ai-trader-e2e` 使用的完整赛题保持一致。
2. 使用 `gpt-5.6-terra` 与 `high` reasoning effort。
3. 保持默认配置：最多 5 个 Audience、每个 Audience 1 个 Research Session、每个通过 Problem 3 个独立 Generator Session、全局并发 4。
4. 使用 Problem Gateway v3、Idea Generator v4 与 Idea Red Team v3。
5. 保存全部 Session、Prompt、Research、Problem、Idea、评审与最终 Idea Card。
6. 对比 `runs/ai-trader-e2e-v1-20260723`，重点分析 Problem 通过率、v1 被错误拒绝的问题是否存活、Idea 的真实产品性、重复程度和 Red Team 淘汰原因。

## Acceptance Criteria

- [x] Run 使用正确模型、配置与 Prompt 版本并成功结束。
- [x] Run 离线完整性验证通过。
- [x] 输出新旧漏斗、Gateway 决策和最终 Idea Card 的人工质量分析。
- [x] 用中文向用户解释值得继续看的 Idea，以及新版 Gateway 是否放得过松或仍然过严。

## Result

- Run: `runs/ai-trader-e2e-v2-gateway-v3-20260723`
- Full analysis: `runs/ai-trader-e2e-v2-gateway-v3-20260723/analysis/e2e-evaluation.md`
- Funnel: 19 Problems → 14 pass → 65 Ideas → 36 pass
- Gateway v3 符合“只淘汰明显不成立的问题”的预期；下一步问题集中在
  Generator 对“证据账本／核验台／审计 Agent”产品原型的同质化。

## Out of Scope

- 修改现有 Prompt、Workflow 或质量门。
- Build、Pitch 或 A2A 服务实现。
- 宣传策略收益或提供投资建议。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
