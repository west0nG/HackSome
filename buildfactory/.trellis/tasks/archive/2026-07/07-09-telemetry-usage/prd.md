# Wake telemetry: record token usage

## Goal

`wake.<role>.jsonl` 对 codex 唤醒不再成本全盲：把 RunResult.usage（token 计数）写进每行 telemetry，两 runtime 统一受益（claude 行同时保留 cost_usd）。

## 需求

- R1：`orchestration/agent_loop.py` `_record_wake` 行新增 `usage` 字段：RunResult.usage 原样透传（各 CLI 原生 shape——claude：input/output/cache 等；codex：input/cached_input/output/reasoning_output）；无可用值时为 None。
- R2：`wake()` 把 `result.usage` 传入 `_record_wake`；timeout 路径、runtime 缺失的 fallback 路径 usage=None（现状语义不变）。
- R3：telemetry 仍是 RECORDING ONLY——不加阈值/预算/告警逻辑；never-brick 语义不变（写失败只 WARN）。

## 约束

- 只动 `orchestration/agent_loop.py` 及其单测；不改 RunResult 契约（usage 字段已存在）。
- 既有字段（cost_usd 等）名称与语义不变，消费方（observatory 指针里对 telemetry 的描述）如提及字段列表则同步一句话。

## 验收标准

- [x] AC1：codex 唤醒的 telemetry 行含非空 usage（token 计数可读）；claude 唤醒行 cost_usd 照旧且新增 usage。
- [x] AC2：timeout / fallback 路径 usage=None，不抛错。
- [x] AC3：单测覆盖新字段（成功/timeout/fallback 三路径）；现有测试全绿。
