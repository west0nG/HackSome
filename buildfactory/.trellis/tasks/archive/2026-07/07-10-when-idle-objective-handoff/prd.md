# when-idle 与 set-objective 的兼容交接

> 状态：实现与回归已完成，已由提交 `c24393e9` 随主任务发布并归档。

## Goal

在独立 `decide-direction` 被并入 `set-objective` 时，仅迁移 `when-idle` 中的旧入口引用；不改变空账本、派单或换向行为。

## Requirements

- 只处理 `agents/assets/skills/when-idle/SKILL.md` 中现存的三类交接：冷启动候选进入 objective 评审、所有候选均不成立时重审 objective、任何 wake 上推翻当前 objective。
- 三类交接统一改为进入 `set-objective`；不得再指向已删除的 `decide-direction`，也不得新增 `choose-next-goal` 或其他中间 Skill。
- 保持现有 `when-idle` 行为不变：先检查 ledger；有在途工作时停下；空账本时必须派发下一项 Goal；hold、并行推进和换向仍由 CEO 按原规则判断。
- 不修改或回填已归档的 `07-10-when-idle-rewrite` 任务文档。本任务只做删除旧 Skill 所必需的兼容交接。
- 该改动必须与 `07-10-ceo-user-value-gate` 同一发布序列落地，并在物理删除 `decide-direction` 前完成，避免出现悬空入口。

## Acceptance Criteria

- [x] `when-idle/SKILL.md` 中对 `decide-direction` 和 `direction-critic` 的引用清零，所有 objective 层换向入口明确指向 `set-objective`。
- [x] ledger 检查、空账本必派单、在途即停和“任何 wake 可换向”的既有语义没有改变。
- [x] 没有新增运营选择 Skill，也没有修改原 `when-idle` rewrite 的 PRD、设计或回归证据。
- [x] 相关 loadout/Skill 测试通过，且删除 `decide-direction` 后不存在运行时悬空引用。

## Non-goals

- 不重新设计 `when-idle`。
- 不改变 `set-objective` 的价值评审规则；它由 `07-10-ceo-user-value-gate` 定义。
