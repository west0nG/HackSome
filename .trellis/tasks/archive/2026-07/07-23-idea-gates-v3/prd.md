# 强化 Idea 质量门与重新 E2E

## Goal

在不改变现有 Idea 阶段编排、并行规模和“只淘汰、不排名”原则的前提下，提高 Research、Problem Gateway 和 Idea Red Team 的判断质量，减少只适合演示、依赖 fake/mock data 或用完整文案掩盖产品缺陷的 Idea。

## Requirements

1. Audience Research 的目标不是堆积资料。每条重要证据都要解释它揭示的具体真实处境：什么人在什么约束下做什么、哪里发生失败或妥协、造成什么后果，以及该结论是直接观察、可靠推断还是未知。
2. Problem Gateway 是主动挑刺的独立 Red Team。只有在证据足以还原真实场景、痛点有实质后果、现有应对方式确实不足且问题属于赛题范围时才通过；关键事实依赖猜测时应拒绝。
3. Idea Generator 不得看到 Problem Gateway 的评审文本，也不得提前获知 Idea Red Team 的具体验收问题，避免围绕检查表写答案。
4. Idea Generator 仍需产出完整产品构想，但输出结构不得以 `Demo Scope`、`Felt Value` 或 `End-to-End User Flow` 直接提示下游评审答案。
5. Idea Red Team 要像有经验的产品负责人、目标用户或购买者一样主动寻找 Idea 不成立的原因。它必须区分“能演示”与“真实可用”，拒绝只能处理 fake/mock data、依赖不可获得数据/权限/人工接力，或没有真实用户价值闭环的方案。
6. 不新增赛题合规阶段，不强制方向差异，不做 Top-K、排序或语义去重，不改变默认每个 Problem 三个独立 Generator Session。
7. 提示词需提升版本号并由自动化测试锁定关键边界。
8. 使用同一份米哈游“发行二周目”赛题，以 `gpt-5.6-terra`、`high` reasoning effort 完整复跑；保存所有 Session、产物和统计供新旧对比。

## Acceptance Criteria

- [x] Research Prompt 明确要求从来源还原真实情况并标记观察/推断/未知，而非只列信息。
- [x] Problem Gateway Prompt 采用严格、主动证伪、关键不确定即拒绝的通过标准。
- [x] Idea Generator Prompt 不含 Red Team 的两条显式检查问题，不再要求 `Demo Scope`、`Felt Value`、`End-to-End User Flow` 三个标题。
- [x] Workflow 不向 Idea Generator 注入 `GATEWAY_REVIEW`。
- [x] Idea Red Team Prompt 明确拒绝 fake/mock-only、不可获得数据/权限、人工接力和“只有演示没有产品”的 Idea。
- [x] 单元测试、lint、类型检查及运行验证通过。
- [x] 米哈游 E2E 完成，运行验证通过，并输出相对旧运行的漏斗、淘汰原因、产品真实性和 AI slop 观察。

## Result

- Run: `runs/mihoyo-e2e-v3-20260723`
- Evaluation: `runs/mihoyo-e2e-v3-20260723/analysis/e2e-evaluation.md`
- Funnel: 22 Problems → 1 pass → 5 Ideas → 0 pass
- The empty Idea Card index is a valid quality-gate outcome, not a runtime failure.

## Out of Scope

- 调整 Agent 数量、并发策略或 workflow 阶段。
- 给 Idea 强制分配不同方向。
- 处理 PAWN 赛题。
- Build 或 Pitch 阶段。
