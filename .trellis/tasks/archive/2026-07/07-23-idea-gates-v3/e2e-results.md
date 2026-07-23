# 米哈游 E2E v3 结果

完整本地分析位于：

`runs/mihoyo-e2e-v3-20260723/analysis/e2e-evaluation.md`

## 漏斗

| Stage | v2 | v3 |
| --- | ---: | ---: |
| Audience | 5 | 5 |
| Research | 5 | 5 |
| Problem | 16 | 22 |
| Problem pass | 16 | 1 |
| Idea Generator Session | 48 | 3 |
| Idea | 105 | 5 |
| Idea pass | 101 | 0 |
| Idea Card | 101 | 0 |
| Agent task | 181 | 42 |

v3 使用 `gpt-5.6-terra`、`high` reasoning effort。42 个任务全部成功，Run 离线校验通过。

## 观察

1. Research Prompt 修改有效。输出围绕具体场景组织，并明确区分直接观察、强推断和未知内部细节，同时保留反证。
2. Problem Gateway 开始真实收缩漏斗。21 个拒绝主要来自玩家公开结果无法证明内部岗位工作流、一次事件无法证明严重度，以及主动策略或主观分歧被写成问题。
3. `1/22` 暴露了结构性张力：人群集中于内部岗位，但赛题只允许公开数据；Research 越诚实地标记内部流程未知，Gateway 越倾向于拒绝。
4. 5 个 Idea 仍有明显 AI slop：机制收敛为 archive/replay 或“内部数据 → dashboard → 建议 → 审批”，产品命名也集中于 Planner、Builder、Control Tower、Vault 和 Replay。
5. Idea Red Team 的 5 次拒绝基本正确。所有方案的核心价值都依赖不可获得的内部数据、游戏引擎权限、活动重开能力或跨部门批准；其中多数第一版明确使用 synthetic/simulated data。
6. 新 Red Team 没有消灭生成层的 slop，但成功阻止 slop 成为 Idea Card。最终零卡是有效空结果，不是运行故障。

## 后续讨论点

暂不建议放松 Idea Red Team。更值得讨论的是 Problem Gateway 是否应区分：

- “这个用户问题是否被可信证据证明”；
- “这个问题是否被证明正在某一家目标公司内部发生”。

另一个可测试方向是让 Research 更主动寻找目标岗位的公开一手叙述，例如从业者复盘、GDC 分享、GitHub issue、工具讨论和工作样例，而不是主要从玩家结果倒推员工处境。
