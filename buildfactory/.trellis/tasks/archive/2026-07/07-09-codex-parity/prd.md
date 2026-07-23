# Codex runtime parity for company longrun（父任务）

## 背景

下一次完整公司长跑计划以 codex 为 runtime（role yaml `provider: codex`），observation 方案沿用（host 侧 claude + Sonnet 观测者，与公司 provider 无关）。07-09 审计确认：runtime 抽象层（07-07 交付）核心链路等价——中性契约全接线、MCP/skills/session/镜像/auth 种子均就绪；但存在 4 个功能差距，其中前 2 个直接打在长跑与 observation 质量上。本父任务收敛这 4 项，最终以一次 codex smoke 运行做集成验收。

## 源需求集（审计发现，按影响排序）

1. **hooks 未翻译**：`agent/runtimes/codex.py` materialize_home 第 4 步为空实现（留有 TODO）。builder/growth 声明的 record Stop hook（强制 session 结束前 `company.py record`）在 codex 下不生效，记忆写回从结构强制退化为自觉。→ 07-09-codex-hooks
2. **observation transcript 指针写死 claude 布局**：`observatory/runner.py` `_pointers_dataplane` 只给 `sessions/<role>/projects/**/*.jsonl`；codex rollout 在 `sessions/<role>/codex/sessions/**/*.jsonl` 且事件格式不同。尸检"数 tool_use 判谎报"一环会空转或误判。→ 07-09-observatory-codex-pointers
3. **成本 telemetry 对 codex 全盲**：codex 无美元字段（cost_usd 恒 None）且 `_record_wake` 不记 usage token → `wake.<role>.jsonl` 里 codex 唤醒无任何成本数据，"花费异常 RED-ALERT" 失去数据源。→ 07-09-telemetry-usage
4. **个别 skill 含 claude 专属指令**：decide-direction 依赖 `Agent` 工具 spawn subagent + `~/.claude/skills/...` 路径；create-role 模板 provider 默认 claude-code。→ 07-09-skills-runtime-neutral

## 任务地图

| 子任务 | 体量 | 依赖 |
|---|---|---|
| 07-09-codex-hooks | 复杂（需 research + design） | 无 |
| 07-09-observatory-codex-pointers | 轻量（PRD-only） | 无 |
| 07-09-telemetry-usage | 轻量（PRD-only） | 无 |
| 07-09-skills-runtime-neutral | 轻量（PRD-only） | 无 |

四个子任务相互独立，可并行；集成验收在本父任务做。

## 跨子任务验收标准（集成 AC）

- [x] **AC-P1（codex smoke 真跑）**：全部子任务归档后，将至少 builder（或 growth）切 `provider: codex` 起一次短程公司运行，完成一次 goal 闭环，确认：①session 结束时 record 强制生效；②`wake.<role>.jsonl` 该角色行含 token usage；③对该 goal 真跑一次 observation 尸检，报告能定位到 codex transcript 并数出工具轨迹。
- [x] **AC-P2（claude 路径零回归）**：现有单测全绿（含 claude runtime golden test）；provider 不切换的角色行为不变。
- [x] **AC-P3（auth 前置核验）**：smoke 前先验证 `accounts/foundagent/codex-auth.json` 种子仍可用（token 可刷新）；不可用则先人工 `codex login` 重新落种（一次性动作，不留 repo 脚本）。

## 约束

- 遵循 07-07 抽象层扩展规则：双 runtime 都需要的能力 → 扩中性契约/中性核心，两 adapter 各实现一次；runtime 专属 → 只动该 adapter 文件；调用方永不依赖具体 adapter。
- never-brick 立场不变：任何 carrier 损坏降级为 WARN，不得 brick 循环。
