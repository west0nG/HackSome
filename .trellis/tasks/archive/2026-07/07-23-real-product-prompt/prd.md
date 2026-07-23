# 强化真实产品身份 Prompt

## Goal

在不拆分赛题、不改变 Workflow 的前提下，让 Idea Generator 以真实产品团队的身份工作，而不是围绕一次性展示设计方案；同时保持 Generator 不知道 Idea Red Team 的具体检查表。

## Requirements

1. 完整赛题继续通过现有 Prompt 流转，不拆成 Product Context 与 Event Envelope。
2. Idea Generator 只接受高层产品原则：面向真实用户、持续使用、真实输入与真实结果，产品在展示结束后仍能独立成立。
3. Idea Generator 不得获得 fake/mock data、不可控第三方、权限或完整用户价值闭环等 Red Team 具体拒绝规则。
4. Idea Red Team 删除 `hackathon`、`judge`、`pitch` 等会激活比赛语境的措辞，继续依据真实使用判断产品。
5. Prompt 模板提升版本并由回归测试锁定上述边界。
6. 本任务只做离线验证；新的真实 E2E 等待用户提供下一道赛题。

## Acceptance Criteria

- [x] Generator Prompt 明确产品需要在展示结束后独立成立，并且不以 presentation、submission 或 showcase 要求决定产品概念。
- [x] Generator Prompt 不包含 Red Team 的 fake/mock、不可用权限或不可控第三方等详细拒绝清单。
- [x] Red Team Prompt 不包含 `hackathon`、`judge` 或 `pitch`。
- [x] Prompt 版本断言、工作流测试、lint 和类型检查全部通过。

## Result

- Idea Generator Prompt version: `4`
- Idea Red Team Prompt version: `3`
- 51 tests passed; Ruff, Mypy, compileall, and diff checks passed.
- The fake-process timeout test startup allowance changed from 0.4 to 0.8 seconds
  after repeated full-suite timing failures; production timeout behavior is
  unchanged.

## Out of Scope

- 拆分或过滤赛题内容。
- 修改 Research、Problem Gateway、并行数量或 Hub 数据流。
- 启动新的 E2E。
