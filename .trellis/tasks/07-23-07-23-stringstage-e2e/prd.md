# StringStage 赛题 E2E

## Goal

使用用户提供的游戏全球发行赛题与 StringStage Idea Card，真实运行一次
Hackathon Team runtime，验证 Lead → Worker → Verifier 可以自主开始并持续推进一个
可运行的 Hackathon 项目。

## Requirements

- Team 名固定为 `stringstage-e2e`。
- `challenge.md` 使用本任务目录中的赛题原文。
- `initial-idea-card.md` 使用用户附件
  `/Users/weston/.codex/attachments/9ca30904-dbb4-486d-93a8-b834ed2e8c1e/pasted-text.txt`。
- 必须通过真实 Docker Compose runtime 启动 resident Lead、Worker manager 与
  Verifier manager，而不是用单元测试模拟状态。
- 运行后不加入人工 Goal、固定目录或阶段；让 Lead 根据 initializer 自主决定工作。
- Lead 只负责检查、判断、设计下一步并创建 Goal；即使保留完整权限，也不得直接实现
  产品代码。真实修改必须由 Worker 执行并由 Verifier 验证。
- 记录容器状态、Goal/review 状态、Agent 日志以及 `/project` 中的真实产物。
- 若发现阻塞 E2E 的 runtime 缺陷，允许在 `buildfactory/` 内修复并重新验证。
- 不修改其他并行 session 的 Trellis task。

## Acceptance Criteria

- [ ] 两份 initializer 被正确写入 `state/stringstage-e2e/project/reference/`。
- [ ] Hub、Lead、Worker manager、Verifier manager 均成功启动。
- [ ] Lead 至少创建一个真实 Goal，Worker 实际领取并对 `/project` 产生实质变更。
- [ ] Verifier 对至少一个 Worker result 提交真实 PASS 或 FAIL verdict。
- [ ] 若 FAIL，证据显示同一 Worker/session 被恢复；若 PASS，系统继续下一 Goal或唤醒 Lead。
- [ ] `/project` 中存在足以证明项目已被实际推进的产品代码、验证结果或提交材料。
- [ ] 保存一份不含凭证的 E2E 证据摘要。

## Notes

- 本任务验证 runtime 与真实 Agent 行为，不把 StringStage Idea Card 当作冻结 Objective。
