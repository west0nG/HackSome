# 放宽 Problem Gateway 的错误拒绝

## Goal

校准 Problem Gateway，使它继续淘汰明显不成立的问题，同时不再把“尚未达到审计级证明”的真实产品机会全部拒绝。

## Requirements

- Gateway 继续拒绝把猜测根因写成事实、只有职业职责而没有流程缺口、来源无法支持核心主张、以及把互不相关证据拼成虚构场景的问题。
- 当证据能够确认具体用户、具体任务，并观察到真实失败或重复、昂贵、脆弱的 workaround 时，允许 Problem 通过。
- 缺少量化损失、覆盖面尚不明确或已有临时 workaround，不能单独构成拒绝理由；这些不确定性应在评审中保留。
- Gateway 仍是独立 Red Team，只做绝对门槛判断，不修复、不排名、不比较 Problem。
- 更新 Prompt 版本并用自动化测试锁定新的判断边界。

## Acceptance Criteria

- [x] Problem Gateway Prompt 明确区分“核心事实缺失”和“影响尚未量化”。
- [x] Prompt 明确认可真实失败或重复、昂贵、脆弱 workaround 所代表的产品问题。
- [x] Prompt 明确禁止仅因 workaround 存在、影响未量化或并非所有团队都受影响而拒绝。
- [x] 原有虚构场景、未经证实根因、职责描述等拒绝边界继续保留。
- [x] Prompt 版本提升，相关单元测试通过。

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
