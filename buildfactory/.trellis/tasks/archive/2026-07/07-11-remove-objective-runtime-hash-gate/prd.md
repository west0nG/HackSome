# 移除 Objective 生效后的全部内容阻断校验

## 目标

让已经通过 Verifier 审核并生效的 Objective 不再因为短版、`/company` 完整正文、导航摘要或 active 内容元数据发生变化而在后续唤醒中消失，同时保留提案审核期间防止“审 A、生效 B”和旧审核误批新提案的完整性保障。

## 背景与已确认事实

- Objective 最初用于跨唤醒保留长期方向；最初版本没有生效后哈希校验。
- CEO Objective v2 为了让 Verifier 同时审核完整正文和一屏短版，引入 revision、提案哈希和成套生效事务。这些机制解决的是提案审核与落盘的一致性。
- v2 同时增加了生效后的持续校验：`orchestration/objective.py:436` 每次读取都重新比较短版哈希、`/company` 完整正文哈希和导航摘要；任一不一致就不向 Agent 注入 Objective。
- thirdtest 中 Builder 对完整正文添加正常交付进度后触发失配，CEO 后续唤醒失去 Objective；现场证据位于 `.trellis/tasks/07-10-thirdtest-opus-longrun/research/observations.md:105`，警告只出现在运行日志，Agent 没有明确恢复路径。
- 当前 `orchestration/objective.py:465` 的 `_apply_ceo_pass` 还要求旧 Objective 的短版、完整正文和导航摘要继续匹配，导致失配状态可能连新的合规提案都无法正常替换。
- `docker-compose.yml:51` 将宿主 `orchestration/` 只读挂载进 resident 容器，但 resident 运行的是长期存活的 `python3 -m orchestration.agent_loop`；文件变化会立即出现在容器文件系统，已经导入的 Python 模块不会自动重载。
- 2026-07-11 现场只读检查时，`thirdtest-ceo` 的 agent loop 自 03:04 起持续运行，且有一轮 Claude wake 正在执行；此时重启会中断当前回合。
- 当前工作区除本任务目录外干净；此前与 `agent_loop` 重叠的改动已经独立提交，不再构成编辑冲突。

## 需求

### R1：保留提案审核期间的保护

- CEO 提案仍包含不可变 revision、完整正文哈希和短版哈希。
- Verifier 的 verdict 仍必须匹配当前 revision，并在生效前核对本次 staged bundle。
- 只有 Verifier 身份可以记录 PASS/FAIL。
- PASS 仍使用成套写入、异常回滚和崩溃恢复，不能留下半套新 Objective。
- 新路径不得覆盖不属于当前 Objective 的 `/company` 文档。

### R2：移除生效后的全部内容一致性阻断

- 生效后的短版 `objective.md` 变化后，下一次唤醒须直接注入其当前内容，不比较批准时的短版哈希。
- `/company` 完整正文内容变化不得让当前 Objective 在唤醒中消失。
- `/company` 导航摘要变化不得让当前 Objective 在唤醒中消失。
- `/company` 完整正文缺失或 active metadata 的非路径内容字段损坏，不得影响短版的读取和注入。
- 新 Objective PASS 时，不得因为旧短版、旧完整正文、旧导航摘要或 active metadata 中不再用于运行时判断的哈希/摘要字段发生变化而拒绝替换。
- 正常唤醒不应为了读取 Objective 而读取或锁定 `/company` 完整正文。

### R3：保留恢复能力

- 中断在一半的 Objective PASS 事务仍须在下一次 `show`、提案、裁决或 Agent 唤醒前恢复。
- “取消内容一致性校验”不得误删事务日志恢复、Verifier 身份门、revision 防迟到裁决或提案 bundle 校验。

### R4：文档与测试同步

- 现行 spec、代码注释和测试不得继续宣称“生效后 `/company` 全文失配会阻止唤醒注入”。
- 实施和自动化测试期间，thirdtest 只作为只读回归证据，不修改、不重启。

### R5：受控发布到 thirdtest CEO

- 只有代码、定向测试、全量回归和 loadout 检查全部通过后才能发布。
- 发布前须确认 `thirdtest-ceo` 没有正在运行的 Claude/Codex child wake，不能杀死进行中的回合。
- 只重启 `thirdtest-ceo`，不得重启 researcher、builder、growth、verifier、Hub 或外围服务。
- 重启后只读确认 Objective 恢复注入、旧哈希/摘要失配警告消失，并确认 session id、ledger、inbox、company 和 Objective 文件未丢失。

## 技术约束

- `objective.active.json` 继续使用 schema v2；现有 `full_sha256`、`short_sha256` 和 `company_summary` 可以保留为历史/审计信息，但不得再控制唤醒或后续替换。
- active metadata 中用于确认受 Objective 所有的安全相对路径、role、schema 和 revision 仍须做结构校验；删除内容保护不等于允许路径越界或删除任意公司文档。
- 保留 `objective_read_ready` 兼容入口，但把职责收窄为“恢复未完成事务”；除恢复失败外不再因 active 内容返回不可用，避免无必要的调用面迁移。
- `/company` 完整正文若存在且是合法 Markdown，新的 PASS 仍可把其当前内容归档；正文缺失时允许用新版本恢复。非法二进制 Markdown 的处理不在本次放宽范围内。

## 验收标准

- [x] AC1：修改已生效 Objective 的短版后，`show` 和下一次唤醒都使用修改后的当前短版，不输出哈希失配警告。
- [x] AC2：修改或删除 `/company` 完整正文后，下一次读取仍返回并注入当前短版，正常唤醒不访问 company store。
- [x] AC3：修改导航摘要，或删除 active metadata 中的哈希/摘要字段后，下一次读取仍返回并注入当前短版。
- [x] AC4：旧短版、完整正文、摘要或非路径 active 字段已经变化时，经过新 revision 审核的 PASS 仍能成功替换 Objective；当前可读旧内容按现状进入 history。
- [x] AC5：篡改 staged 完整正文、staged 短版或使用过期 revision，Verifier verdict 仍被拒绝。
- [x] AC6：PASS 中断恢复、失败回滚、Verifier 身份门、路径所有权和非 CEO 旧协议继续通过测试。
- [x] AC7：相关 Objective、Agent loop、loadout/skill 合同测试及全量回归通过。
- [x] AC8：现行 backend spec 与最终行为一致；归档任务证据不回写。
- [x] AC9：确认 CEO 空闲后只重启 `thirdtest-ceo`；下一次 wake 日志显示 `objective: injected ... chars`，且所有持久状态保持不变。

## 不在范围内

- 不删除 Objective、Verifier 审核或 `set-objective` 价值判断机制。
- 不改变 Goal、when-idle、Hub 验收或角色审批协议。
- 不修订 thirdtest 的当前经营方向或业务文档。
- 不把 active metadata schema 从 v2 迁移到新版本，也不清理存量哈希字段。
- 不将 Objective 文件改成只读挂载；用户已明确接受直接编辑短版会影响下一次唤醒。
- Skill `description` 的全量轻量化由独立任务 `07-11-slim-skill-descriptions` 规划和验收，不混入本任务。
