# AC2 排查清单（fleet skills claude-only 指令全量 sweep）

实施 agent 排查 + 质检 agent 独立复扫（两轮 grep：原始 pattern + 宽泛 `Task tool|TodoWrite|general-purpose|spawn|claude` 大小写不敏感），2026-07-09。

| 文件 | 结论 |
|---|---|
| decide-direction/SKILL.md | 唯一违规项 → 已修（R1：降级模式 + 双路径引用） |
| decide-direction/references/direction-critic.md | 干净（无 claude/subagent/路径引用） |
| visual-iterate/SKILL.md | 已达标（自带降级模式，SKILL.md:39-41）— 未动 |
| mine-customer-voice/SKILL.md | 已达标（双路径适配层；references/ 为 vendored 上游，按其"只重拷不改"同步策略不动） |
| create-role/SKILL.md | `/opt/foundagent-orch/...` 为容器挂载路径，runtime 中性；provider 行按 R3a 修 |
| de-ai-ify（en/zh + references） | "Claude Code" 全是内容示例（专有名词保留规则），非 runtime 指令 — 合规 |
| gen-image/SKILL.md | 调用层是 `scripts/generate_image.py`（runtime 中性）；references/codex/* 为 vendored 上游文档提及 Claude Code host，适配层已接管 — 合规 |
| design-asset、find-opportunity、visual-iterate references | 仅 ATTRIBUTION/示例文案命中，无指令 — 合规 |
| 其余 11 个 skill（check-email、claim-mailbox、company-state、deploy-site、provision-ga4、receive-goal、review-objective、review-role、send-goal、set-objective、when-idle） | grep 零命中 — 合规 |
| 非 .md 文件（.mjs/.py/.sh/.json） | 零命中 |
