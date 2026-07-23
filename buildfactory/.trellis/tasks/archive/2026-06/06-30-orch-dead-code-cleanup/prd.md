# Orchestration dead-code cleanup (pump-era)

> 父任务：`../06-26-foundagent-v6`。轻量任务（删除 + 引用修正），PRD-only。
> 实现已在分支 `chore/orchestration-cleanup-skill-loadout` 完成，commit `9a85b87`，本工件如实记录。

## Goal

删除 06-29 编排层重构（resident-agent + Hub 取代中心 pump）后**停用未删**的上一代
死代码。它们零活引用，却仍被测试背书（让套件显得臃肿、也误导读者以为是活路径）。

## Confirmed facts（代码库已验证）

- **死簇**：`goal_pump`（中心 pump）→ `{goal_inbox, goal_loop, goal_runtime→broker}` +
  `goal_cli`（旧 `goal add` CLI）。活核心（`hub`/`messaging`/`agent_loop`/`ceo_loop`/
  `inbox`/`goal_ledger`）**均不 import 这 5 个**；唯一运行时触碰是 `Makefile` 的一句
  `import goal_pump` 烟雾测试。
- **不是死的、保留**：`receive_tool.py`（peripheral-layer `receive()` 活基础设施，
  `test_receive.py` 在用）；`broker.py`（ephemeral spawn 休眠路径，删 `goal_runtime`
  后无 import，但保留作未来 ephemeral worker 路，标 DORMANT）。
- **悬空引用**（删除会暴露）：`Makefile:27` 烟雾测试、`docker-compose.yml` broker 注释、
  `agents/ceo.yaml` 旧 goal_cli 注释、`orchestration/__init__.py` docstring、`hub.py`
  提及 goal_runtime 的注释。

## Requirements

- **R1 删死簇**：删 `goal_pump/goal_loop/goal_inbox/goal_runtime/goal_cli` 五个模块
  + 各自测试（`test_goal_pump/loop/inbox/runtime/cli`）。
- **R2 保留非死代码**：不动 `receive_tool.py`、`broker.py`（后者标注 DORMANT）。
- **R3 修悬空引用**：上述 5 处引用全部更新到现状，删后无指向已删模块的活引用。
- **R4 套件保持绿**：删测试后全套通过。

## Acceptance Criteria

- [x] AC1：5 模块 + 5 测试已删；`grep` 确认 `orchestration/`、`agents/`、`Makefile`、
  `docker-compose.yml` 内无指向已删模块的活引用（仅 archive 任务文档里的历史提及保留）。
- [x] AC2：`receive_tool.py` 与 `broker.py` 保留；broker 在 `__init__`/compose 标 DORMANT。
- [x] AC3：悬空引用全修——Makefile 烟雾测试改 `import orchestration.broker`；compose/
  ceo.yaml/__init__/hub.py 注释更新到现状。
- [x] AC4：`pytest orchestration/tests agent/tests` → **147 passed**（删前 171，少的 24 即被删的死测试）。

## Out of Scope

- broker / ephemeral spawn 路径本身的去留（保留休眠，未来另议）。
- skill 接线（独立任务 `06-30-container-skill-loadout`）。
