# PRD — Wake/goal 计时器扩容（issue #206 第 1 点）

## 背景

Issue #206：单次 wake 硬超时（`AGENT_CLAUDE_TIMEOUT`，代码默认 600s）与 goal
阶段截止（`HUB_DEADLINE_SECS`，代码默认 1800s）双双小于真实工作所需，firsttest
当天连续硬杀完成中的真实工作三次。且 `HUB_DEADLINE_SECS` 在 compose 里从未接线
到 hub 容器——想调也调不到。

## 用户决策（2026-07-08 拍板）

- 员工闹钟 `AGENT_CLAUDE_TIMEOUT`：默认 600s → **3600s**（1 小时）。
- 老板闹钟 `HUB_DEADLINE_SECS`：默认 1800s → **10800s**（3 小时），并在
  compose 里接线进 hub 容器，使其真正可调。
- 失聪窗口（长 wake 期间 agent 最长 1h 读不了 inbox）：**接受 + 文档化**，
  本任务不加机制。
- 范围外（明确另开任务/另议）：inbox 中途传入机制（验证码类即时消息会被
  1h wake 卡死的问题）、kill 残留语义（late REPORT 落账/复活）、killed wake
  成本重建。

## 需求

1. 两个默认值改为 3600 / 10800，env 覆盖行为不变。
2. compose 给 hub 容器接线 `HUB_DEADLINE_SECS`（`${HUB_DEADLINE_SECS:-10800}`），
   agent 侧 `AGENT_CLAUDE_TIMEOUT` 默认同步为 3600。
3. 防再错配护栏：hub 启动时若能读到 `AGENT_CLAUDE_TIMEOUT` 且
   `HUB_DEADLINE_SECS < 2×AGENT_CLAUDE_TIMEOUT` 则打一行 WARN（不阻断）。
   compose 把 `AGENT_CLAUDE_TIMEOUT` 一并传给 hub 容器供此校验。
4. 失聪属性文档化：在 agent_loop / compose 注释里写明「wake 串行 = 最长
   timeout 秒不读 inbox，消息排队不丢」。

## 约束

- 纯参数 + 接线 + 注释改动；不改状态机、不改 kill 语义、不改 inbox 机制。
- 护栏只 WARN 不 fail——错配是运维问题，不该 brick hub。

## 验收标准

- AC1：默认值生效——不设任何 env 时，`agent_loop.CLAUDE_TIMEOUT == 3600`、
  `hub.HUB_DEADLINE_SECS == 10800`。
- AC2：compose 渲染（`docker compose config`）中 hub 容器环境含
  `HUB_DEADLINE_SECS=10800` 与 `AGENT_CLAUDE_TIMEOUT=3600`（未设 env 的默认），
  agent 容器 `AGENT_CLAUDE_TIMEOUT=3600`。
- AC3：错配护栏——`HUB_DEADLINE_SECS=1000` + `AGENT_CLAUDE_TIMEOUT=3600` 启动
  hub 时输出 WARN；正常配比不输出。
- AC4：现有测试全绿（若有测试断言旧默认值，更新为新值）。
