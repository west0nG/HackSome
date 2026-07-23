# AI Trader 产品性 Prompt E2E

## Goal

使用相同的 PandaAI「Build the Next AI Trader」赛题完整复跑 Useful Idea 工作流，验证 Idea Generator v5 与 Idea Red Team v4 是否减少报告、卡片、清单、Dashboard、账本和控制台型产品，并产生更具体、更有意思的产品构想。

## Requirements

1. 输入与前两次 AI Trader Run 使用的完整赛题一致。
2. 使用 `gpt-5.6-terra` 与 `high` reasoning effort。
3. 保持默认配置：最多 5 个 Audience、每个 Audience 1 个 Research Session、每个通过 Problem 3 个独立 Generator Session、全局并发 4。
4. 使用 Problem Gateway v3、Idea Generator v5 与 Idea Red Team v4。
5. 保存全部 Session、Prompt、Research、Problem、Idea、评审与最终 Idea Card。
6. 对比 `runs/ai-trader-e2e-v2-gateway-v3-20260723`，重点分析信息产物型 Idea 数量、实际完成的产品动作、产品构想是否有意思、Red Team 的新淘汰原因与最终 Idea Card 质量。
7. 不因新 Prompt 强制减少 AI 使用，不要求 Agent-native 机制，不做 Top-K、语义去重或方向差异。

## Acceptance Criteria

- [x] Run 使用正确模型、配置与 Prompt 版本并成功结束。
- [x] Run 离线完整性验证通过。
- [x] 输出新旧漏斗与人工质量分析。
- [x] 明确说明新 Prompt 是否减少信息产物型产品，以及是否产生新的副作用。

## Result

- Run: `runs/ai-trader-e2e-v3-product-taste-20260723`
- Full analysis: `runs/ai-trader-e2e-v3-product-taste-20260723/analysis/e2e-evaluation.md`
- Funnel: 24 Problems → 18 pass → 54 Ideas → 32 pass
- 信息产物型产品显著减少；产品动作转向编译、执行、重跑、写入、阻断、同步和
  控制。新副作用是 Gate/Replay/Patch/Relay/Witness 式英文命名模板。

## Out of Scope

- 修改 Prompt、Workflow 或质量门。
- Build、Pitch 或 A2A 服务实现。
