# 强化 Generator 产品性与有趣度

## Goal

调整 Idea Generator 与 Idea Red Team 的产品门槛，阻止以报告、卡片、清单、Dashboard、账本或控制台为核心价值的 Idea，并推动 Generator 产出用户会真实觉得有意思、愿意尝试的具体产品。

## Requirements

1. Idea Generator 明确禁止把信息生成、整理或展示本身作为产品核心价值。
2. 报告、卡片、清单、Dashboard、账本、控制台、摘要、审计包和待办只能作为实际完成工作或改变用户工作流的产品的次要输出。
3. 改名为 Agent、Copilot、Workspace、Operating System 等不得绕过上述限制。
4. Generator 要求产品有明确观点、具体核心体验和一个强产品构想，目标用户会真实觉得有意思并愿意尝试。
5. 不加入“去掉 AI 后仍成立”、限制 AI 使用、追求 Agent-native、刻意猎奇或强制方向差异等要求。
6. Idea Red Team 对核心价值停留在上述信息产物的 Idea 直接拒绝，不再因产物本身属于岗位交付物而放行。
7. 提升两个 Prompt 的版本并以自动化测试锁定边界；不向 Generator 暴露 Red Team 的完整检查表。

## Acceptance Criteria

- [x] Generator Prompt 包含硬性信息产品禁令和用户觉得有意思的正向要求。
- [x] Generator Prompt 不包含移除 AI、避免 AI、Agent-native 或 novelty/surprise 限制。
- [x] Red Team Prompt 对报告、卡片、清单、Dashboard、账本、控制台、摘要、审计包和待办型核心产品直接拒绝。
- [x] Generator v5 与 Red Team v4 版本正确持久化。
- [x] Prompt 契约测试、完整单元测试、lint 与源码类型检查通过。

## Notes

- 本任务只修改产品生成与评审 Prompt，不改变 Workflow、并发、扇出、Markdown 结构或结构化输出 Schema。
