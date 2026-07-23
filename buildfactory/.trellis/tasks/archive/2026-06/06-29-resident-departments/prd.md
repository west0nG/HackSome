# Unified Agent Loop + 全员常驻 + P2P 机制 — 子任务 ①

> slug `resident-departments` 是首轮创建名；2026-06-29 第二轮重定向后，本任务 = **统一 `agent_loop` + 全员常驻 + P2P 通信机制**。父任务：`.trellis/tasks/06-29-orchestration-rebuild`。**先做（child② 依赖本任务）**。
> 一句话：把 `ceo_loop` 重构成通用 `agent_loop`，CEO + 4 部门都是它的实例（全常驻、自驱 poll 各自 inbox），通信走 inbox P2P，跑通最简零人闭环。

## Goal（目标）

1. `ceo_loop` → 通用 `agent_loop`（receive 信号 → `claude --resume` 处理 → 睡），参数 = `key` / `charter` / `computer-server` flag。
2. CEO + Researcher + Builder + Growth + Verifier 全部常驻、各跑一个 `agent_loop` 实例（同镜像、参数区分）。
3. inbox 升为**双向 P2P 通信原语**：CEO `append` goal 到部门 inbox → 部门自驱醒来 `claude --resume` 干活 → `append` 结果回 CEO inbox。
4. 跑通一个**最简零人闭环**，证明「统一 loop + 全员常驻 + P2P」机制成立。

## 动机

- **统一**：`ceo_loop` 本质与 CEO 无关，就是「收信号→唤醒→睡」；CEO 与部门只差 `key`/`charter`/是否要 computer-server。一份循环代码三处共用。
- **自驱即 P2P**：部门自己 poll inbox ⟹ CEO 直接投部门、部门直接回 ⟹ 中心 pump 多余。
- **context 连续**：部门跨任务 `--resume` 同 session。

## 范围

**IN（本任务做）**
- **通用 `agent_loop`**：重构 `orchestration/ceo_loop.py`，抽出 `key`/`charter`/`computer-server` 参数；CEO 与部门都用它启动。循环体 = `poll(key) → wake(resume) → save_session(key)`。
- **5 agent 常驻 + 完全同构**：`docker-compose.yml` 把 CEO + 4 部门都做成跑 `agent_loop` 的常驻 service。**5 容器完全同构**——同镜像、同 entrypoint、都起 computer-server `:8000`、都挂 cua MCP、都挂 `/company`、都无 docker.sock，**只差 `key` + `charter`**。computer-server 对 CEO 也 on（用户定：不限制能力，用不用 ≠ 开不开）。
- **inbox 双向 P2P 原语**：IME 带 `reply_to`（caller key）；派活原语（CEO `send goal to <key>`，由现有 `goal_cli` 改 / 扩）；部门回报原语（干完 `report result to <reply_to>`）。
- **provider / runner 加 `--resume`**：`agent/provider.py` `build_exec` + `agent/runner.py` `run_task`（现仅 `--session-id`）。
- **session per-key 持久化**：每个 agent 一个 session 文件 + 持久 `~/.claude` 卷（chown-on-init，跨 `rm` resume）。
- **最简闭环 e2e**：CEO `append` goal → 部门干（写 `/company`）→ `append` 回 CEO → CEO 醒来收到。

**OUT（→ child② 或其它）**
- 独立验收分权（最简闭环**暂不含**，见「中间态声明」）。
- 确定性 watchdog（`attempts`/retry/`kill`）。
- ledger 旁路化 + 异步事件驱动状态机。
- 外设层 IME 统一（归 `06-28-peripheral-layer`；本任务只需 IME 形状不与之冲突）。
- ephemeral spawn 能力（broker docker.sock 瘦身保留，不删）。
- 4 role 的真实 charter/skill 内容（归 `06-28-role-library`；本任务用占位）。

## ⚠️ 中间态声明（重要）

为先证明「统一 loop + P2P」机制，child① 的最简闭环**暂时不含独立验收分权和 watchdog**——这暂时违反核心信条「验收分权 doer ≠ judge」，是**明确的、有意的中间态**，由 child② 立即补回。期间：
- 不得对外宣称"验收"已就位；
- 最简闭环里部门干完直接 `append` 回 CEO，CEO 暂时自看结果（无独立 verifier）；
- 现有同步 `run_goal` / `goal_pump` 在 child① **停用**（不删，child② 重建异步版）。

## 与 `06-28-role-library` 的关系（机制 vs 内容，解耦）

- **本任务做机制**：通用 loop + 5 常驻容器 + P2P 通信 + session。
- **role 内容归 role-library**：4 role 的 charter/skill 由 role-library 子任务产出（声明式 yaml，零 .py 改动）。
- **不互相阻塞**：child① 用**最小占位 charter** 先跑通机制；真实内容随 role-library 填进同一批容器。
- **现有占位**：`agents/{company-operator,operator}.yaml` 是 ceo-loop 跑闭环时的泛用执行体占位；`builder.yaml`/`growth.yaml` 不存在，本任务建最小占位。

## 关键决策 / 待 design

- 部门回报原语形态（IME `reply_to` + report cli/skill 注入容器）。
- 派活原语：现有 `goal_cli`（写 ledger）改 / 扩成「append goal 到目标 inbox」。
- pump 退役与 `run_goal` 同步状态机停用的处理方式（不删、child② 重建异步版）。
- Verifier 这个 agent 在 child①：也常驻跑 loop，但最简闭环可能先不调它（分权接入在 child②）。
- 统一 entrypoint 对 5 容器一致（都起 `:8000`、都 materialize、都 exec `agent_loop`），只读 `AGENT_KEY`/`AGENT_CHARTER`。

## Acceptance Criteria（验收标准）

- [x] **AC1 统一 loop**：单一 `agent_loop` 代码，CEO + 4 部门都是其实例（同镜像、`key`/`charter`/computer-server 参数区分）；`ceo_loop` 不再是独立实现。
- [x] **AC2 全员常驻**：5 agent 都是常驻 compose service，`make up` 后在线，不再每 goal `docker run`/`rm`。
- [x] **AC3 P2P 投递**：CEO `append` goal 到部门 inbox，部门**自驱**醒来处理，结果 `append` 回 CEO inbox，CEO 醒来收到——**全程无中心 pump `docker exec`**。
- [x] **AC4 context 连续**：同一部门连续处理两个相关 goal，第二个能看到第一个上下文（同 session resume）。
- [x] **AC5 完全同构**：5 agent 同镜像、同 entrypoint、都起 `:8000`、都挂 cua MCP + `/company`，仅 `key` + `charter` 不同（含 CEO，不限制能力）。
- [x] **AC6 最简零人闭环**：CEO 派 → 部门干（写 `/company`）→ 回 CEO，全程零人；明确标注未含独立验收/watchdog（中间态）。
- [ ] **AC7 持久化（后置 hardening，2026-06-29 决定）**：agent 容器 `rm` 后重建仍能 resume 原 session（chown-on-init 持久卷）。与 ceo-loop 一致**后置**——核心 AC1-6 不依赖它，作为独立 deployment hardening 项。

## 验收记录（2026-06-29，self 实现 + code-reviewer 过 + M1 修复）

真容器 e2e 验证：
- **最简闭环（dep-light）**：directive → CEO `messaging send builder` → builder 写 `/company/mission.md` → `report` 回 ceo → CEO 醒来收到。零人、无中心 pump、纯 P2P；CEO 两次 wake 同 session（resume）。
- **computer-server 全 on（kasm 全 on）**：builder 在完整 kasm 桌面 + computer-server（:8000）+ agent_loop 共存下，跑通一轮 goal → 写 `/company/greeting.md` → report 回 ceo（ceo inbox 收到）。
- **AC4 context 连续**：连续派第二个 goal，builder resume 同 session `5ce0a181`，产出 `greeting_fr.md` 是上一条 greeting 的法语翻译（引用了自己刚写的内容）。
- **5 agent 同构**：compose anchor，`docker compose config` OK，只差 `AGENT_KEY`/`AGENT_CHARTER`。
- 120 单测绿。commit：`c9db480`（核心 agent_loop + messaging）+ `9001ac1`（同构 compose）。

**后置（独立 hardening，不阻塞核心）**：AC7 跨 rm 持久化；完整 loadout materialize（skill/hook，随 role-library 真实内容）；全 5 容器 live run（资源重，已 builder 代表验证）；n1 文案打磨（随真实 charter）。

## Notes

- 复杂任务：`task.py start` 前补 `design.md` + `implement.md`。`design.md` 已随本轮重定向重写。
- 相关代码基线：`orchestration/{ceo_loop,inbox,goal_cli,goal_ledger,goal_pump,goal_runtime,goal_loop}.py`、`agent/{provider,runner}.py`、`docker-compose.yml`、`agents/*.yaml`。
