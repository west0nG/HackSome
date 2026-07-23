# AI Trader 赛题 E2E

## Goal

使用新的真实产品身份 Prompt，对 PandaAI「Build the Next AI Trader」赛题执行一次完整 Useful Idea E2E，并分析新的质量门在公开数据较丰富的金融 ToB 场景中的表现。

## Requirements

1. 使用用户提供的完整赛题，不删减赛道要求、A2A 接入规范、评选标准或合规条款。
2. 使用 `gpt-5.6-terra` 与 `high` reasoning effort。
3. 保持默认配置：最多 5 个 Audience、每个 Audience 1 个 Research Session、每个通过 Problem 3 个独立 Generator Session、全局并发 4。
4. 使用 Idea Generator v4 与 Idea Red Team v3。
5. 保存全部 Session、Prompt、Research、Problem、Idea、评审与最终 Idea Card。
6. 对比米哈游 v3，重点分析 Research 证据类型、Problem 通过率、真实产品性、fake/mock 依赖和 AI slop。

## Acceptance Criteria

- [x] Run 使用正确模型与 Prompt 版本并成功结束。
- [x] Run 离线完整性验证通过。
- [x] 输出完整漏斗与质量分析。
- [x] 人工复核通过的 Idea，并向用户解释最值得继续看的产品。

## Result

- Run: `runs/ai-trader-e2e-v1-20260723`
- Full analysis: `runs/ai-trader-e2e-v1-20260723/analysis/e2e-evaluation.md`
- Funnel: 23 Problems → 1 pass → 5 Ideas → 2 pass
- The two Idea Cards are independent variants of the same Decision-Date Data
  Gate product thesis.

## Out of Scope

- 修改现有 Workflow 或质量门。
- Build、Pitch 或 A2A 服务实现。
- 评价或宣传任何策略收益，提供投资建议、荐股或代客理财。
