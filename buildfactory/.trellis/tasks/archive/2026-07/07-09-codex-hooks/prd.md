# Codex hooks translation: record Stop hook parity

## Goal

role yaml 里声明的 `hooks` carrier 在 codex runtime 下同样生效。首个（也是当前唯一）真实用例：builder/growth 的 record Stop hook——session 结束前未跑 `company.py record` 时挡住停止并提醒补记，使记忆写回在 codex 下恢复为结构强制。

## 需求

- R1：`CodexRuntime.materialize_home` 将 role yaml 声明的 hooks snippet 翻译进 codex 的 hooks 配置（`CODEX_HOME/hooks.json`，事件模型与 Claude Code 同构，07-07 capability map 已调研：SessionStart/PreToolUse/PostToolUse/Stop 等；GA 于 2026-05，镜像 pin 的 0.142.5 已含）。
- R2：record 强制语义达到与 claude 侧等价：未 record → 挡一次并给出补记指引；已 record（含 `record --nothing`）→ 放行；循环护栏（不得无限挡）。
- R3：manifest reconcile 语义与 claude 侧一致：merge 可撤销（manifest 记录本次 merge 的条目，`off`/换角色时能精确移除）、绝不碰 agent 自己加的 hooks 条目。
- R4：hook 脚本尽量单份两用（`record_stop_hook.py` 一份适配两 runtime 的 stdin/stdout 契约差异），避免两份 record hook 漂移；确实无法两用时，差异部分收在最小垫片里。
- R5（发现的预存错位，设计必须一并回答）：resident 模式下没人导出 `COMPANY_SESSION_ID`——`company.py` CLI 的 marker 落在 `default.marker`，claude Stop hook 却查 `<真实session-id>.marker`，两侧本来就不对齐（hook 实际退化为"每次都多挡一轮"）。codex 又无法预设 session id。marker keying 需要一个 runtime-neutral 的方案（例如 agent_loop 每次 wake 前导出一个 per-wake nonce，CLI 与 hook 都从 env 取，stdin session_id 仅作 fallback）。

## 约束

- 只动 `agent/runtimes/codex.py`（及必要的中性核心/`company_state_kit` hook 脚本）；claude adapter 的 settings.json merge 路径行为逐字节不变（golden test 锁定）。
- never-brick：hooks 翻译失败降级为 WARN + 无 hooks，不 brick loadout。
- verifier 继续无 hooks（其"无 record 强制"是刻意设计，不得因本任务被动获得 hooks）。

## 验收标准

- [x] AC1（真跑）：一个 `provider: codex` 的角色完成一次 wake，session 结束前未 record 被挡一次并收到补记指引；record 后（或 `--nothing`）正常结束。挡停不超过一次（循环护栏生效）。
- [x] AC2（reconcile）：materialize 两次幂等；hooks 声明移除后再 materialize，此前 merge 的条目被精确撤销，agent 自加条目保留。
- [x] AC3（回归）：claude 侧全部现有单测/golden test 通过；R5 的 marker keying 修正后，claude 路径的 record 强制在 resident 模式下真正对齐（不再"每次多挡一轮"）。
- [x] AC4（降级）：hooks snippet 损坏/缺失时 WARN + 其余 carrier 照常，loadout 不 brick。

## 开放问题（research 阶段实测钉死，写进 design.md）

- codex Stop hook 的阻断输出契约：文档为 `continue`/`stopReason`/`systemMessage`，与 claude 的 `{"decision":"block","reason"}` 不同——能否真正把"继续补记"的指令回注给模型？挡停后模型可见的文本载体是什么？
- claude `stop_hook_active` 循环护栏的 codex 等价物是否存在；没有则护栏改由 hook 自身状态（如 marker 目录里的 attempt 标记）实现。
- hook 信任机制与 `--yolo` 的交互：headless 下是否需要 `--dangerously-bypass-hook-trust`。
- hooks.json 多源合并（user/repo 级）在隔离 CODEX_HOME 下的实际行为。
