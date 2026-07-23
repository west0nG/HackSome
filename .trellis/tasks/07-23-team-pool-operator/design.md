# Team Pool 与 operator 控制 — 技术设计

## 依赖

本设计只在 `07-23-single-team-runtime` 完成后实施。每个 registry row 指向一份可独立
启动的单 Team control root。

## Handoff

Build-side CLI 接受结构化输入：

```text
source_run_id
idea_card_id
idea_card_sha256
challenge_markdown
initial_idea_card_markdown
```

Team ID 由稳定 source IDs 派生，不依赖提交顺序。registry 绑定输入 hash 并使用原子写入。

## Registry 状态

Operator/control state：

```text
queued | starting | active | pausing | paused | resuming
```

这些状态不暴露为 Agent 的完成、idle 或产品评价。

## Pool

- 默认两个 active lifecycle；
- queued 按单调 enqueue sequence FIFO；
- pause 必须等待 Lead、Worker、Verifier 和 Manager 对账停止后释放 slot；
- slot 释放后调度最早 queued Team；
- resume 在有 slot 时进入 resuming，否则回 queued，但保留原 Team identity。

## Operator CLI

提供明确且幂等的：

```text
team bootstrap
team list
team pause
team resume
team inspect
```

第一版不提供 delete/archive/score/rank。
