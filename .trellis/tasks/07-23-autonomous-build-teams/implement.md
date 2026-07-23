# 自主 Hackathon Build Teams — 父任务实施图

父任务只拥有跨子任务需求、目录边界和最终集成验收，不直接作为代码实施目标。

## 子任务顺序

1. `07-23-single-team-runtime`
   - 先证明一个 Team 的三角色 Prompt、项目状态、零 Skill 和顺序 Goal batch。
2. `07-23-team-pool-operator`
   - 依赖单 Team runtime，再增加 handoff bootstrap、global pool 和 operator 控制。
3. 后续独立 integration task
   - 由 Idea 面实现显式 Human Review Gate，并调用稳定 handoff contract。

## 跨子任务质量门

- [ ] 所有 Build 实现保持在 `buildfactory/`。
- [ ] Idea workflow 并行改动不被覆盖。
- [ ] 单 Team runtime 在引入 global pool 前独立通过真实 E2E。
- [ ] Pool 不改变 Team 内 Lead/Worker/Verifier Prompt 或 Goal 语义。
- [ ] 最终 handoff contract 不依赖 `src/hacksome` 私有 Python 类型。
