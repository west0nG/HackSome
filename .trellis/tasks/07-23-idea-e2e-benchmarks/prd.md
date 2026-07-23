# Run PAWN and miHoYo E2E benchmarks

## Goal

使用当前 Idea-only workflow 对两个用户指定输入执行真实、独立的端到端基准测试，并保存可复盘的完整 Run 数据与质量结论。

## Requirements

- 基准 A 的唯一输入是 `PAWN`。
- 基准 B 的唯一输入是“发行二周目——带着 AI，重打一遍米哈游游戏的全球发行”完整赛题。
- 两个基准使用独立 Run、独立 Agent Session，不混合 Prompt 或中间上下文。
- 使用真实 Codex 调用；Research 阶段允许并要求使用 Web Search。
- 使用第一版默认编排：最多 5 个人群、每个人群 1 个 Research Session、每个通过 Gateway 的 Problem 默认 3 个全新 Idea Generator Session。
- 保留所有 Prompt、模型输出、Session 元数据、Gateway/Red Team 决策和最终 Idea Card。
- 不覆盖或删除任何既有 Run。

## Acceptance Criteria

- [x] 米哈游 Run 从原始输入走到终态，且 `hacksome validate` 通过。
- [x] 按用户指令在 Idea Generator 阶段停止 `PAWN`，保留全部中间数据且不再运行模型进程。
- [x] 两个 Run 的 Session ID 集合不相交，且交叉 Prompt 污染检查为零。
- [x] 每个 Run 的人群数量不超过 5；米哈游 16 个通过 Problem 均产生 3 个 Generator Session。
- [x] 米哈游 Run 中被 Red Team 淘汰的 4 个 Idea 均未生成 Idea Card。
- [x] 输出一份中文 E2E 结果记录，包含数量漏斗、失败信息、质量观察和产物路径。

## Notes

- fixture 来自已归档任务 `07-22-hackathon-agent-product`，运行前必须复核 SHA-256。
- 本任务以测试执行和结果记录为主；只有发现阻断 E2E 的实现缺陷时才修改代码。
- 原验收要求两个 Run 都到终态；用户在观察 `PAWN` 中间结果后明确要求停止该 Run，并将本轮重点收敛到米哈游赛题。
