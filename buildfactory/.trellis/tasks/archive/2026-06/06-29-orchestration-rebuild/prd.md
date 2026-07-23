# Orchestration Rebuild（编排层重构）— 父任务

> 父任务背景：`.trellis/tasks/06-26-foundagent-v6`。本任务为**父任务**：持有源需求、关键决策、子任务地图、跨子任务集成验收、待回填文档。本身不直接实现。
> 基线：编排层已 MVP 落地为**真实代码**（`orchestration/` + `docker-compose.yml` + `agents/*.yaml`），经 ceo-loop AC1–AC6 真容器 e2e + 117 单测验证。这次是在已工作系统上**换形态**的 rebuild，不是重写。
> ⚠️ **拆分已于 2026-06-29 第二轮重定向**（见「关键决策」「子任务地图」）：从「常驻 / 去 pump」两步，改为「统一 loop + P2P 机制 / 异步确定性保证」两步。子任务 slug 是首轮创建名，职责以本文为准。
> 子任务一个一个做：先 ① 再 ②（② 依赖 ①）。

## Goal（目标）

把编排层从「**中心 pump 分发 + 每 goal 一个 ephemeral worker**」改成「**统一 `agent_loop` + 全员常驻 + P2P inbox 通信**」，同时**不丢核心 IP**（验收分权、确定性状态机）。

## 动机（为什么改）

1. **worker 随起随丢丢 context**：每 goal 起新容器跑完即拆，丢弃上下文、冷启动成本高。现阶段部门少 + auto-compact 兜底，全常驻更合理。
2. **中心 pump 分发过重**：所有派活走 `goal_pump` claim→drive，过重。每个任务收发方明确，不需要中间调度。
3. **（第二轮洞察）CEO 和部门的常驻循环本质是同一个**：`ceo_loop` 不该是 CEO 专属，应是一个通用 `agent_loop`（receive 信号 → `claude --resume` 处理 → 睡）。而**统一 loop ⟹ 部门自驱 poll 自己 inbox ⟹ 天然 P2P**（CEO 直接 append goal 到部门 inbox、部门直接回），中心 pump 随之变多余。

## 关键决策（已与用户确认）

1. **统一 `agent_loop`（2026-06-29 第二轮定）**：把 `ceo_loop` 重构成通用循环，CEO + 4 部门 + 未来角色都是它的**实例**，**完全同构、区别只在 `key`（inbox 地址）+ `charter`**（computer-server / cua MCP / `/company` 全 on，含 CEO——用户定：不限制能力，用不用 ≠ 开不开）。一份循环代码，多处共用。
2. **全员常驻、同镜像**：常驻集合 = {CEO, Researcher, Builder, Growth, Verifier} 都常驻跑 `agent_loop`，统一底层镜像 `foundagent/cua-agent:latest`（坐实「CEO 只叠配置、不分叉镜像」的同构信条）。
3. **P2P inbox 通信**：派活 = `append(目标 key, goal)`；回报 = `append(caller key, result)`。统一 loop 让 P2P 自然成立，**中心 `goal_pump` 退役**（在 child① 就退役，不再 `docker exec` 同步驱动）。
4. **"broker" 一词三分**：goal 分发 pump（**退役**）/ inbox 投递层（升级为双向 P2P 通信原语，保留并扩展）/ 容器 spawn broker（瘦身不删，未来 ephemeral 用）。
5. **不能丢的核心 IP（迁到异步 P2P，child② 专做）**：
   - **验收分权 / 不自评（doer ≠ judge）**：独立 read-only verifier 判 `VERDICT: PASS/FAIL`。⚠️ child① 最简闭环**暂缺**它（中间态），child② 立即补。
   - **确定性状态机 / ledger**：现为同步 `run_goal`（execute→verify→done/retry/kill watchdog）。child② 把它迁成**异步事件驱动**（inbox 事件推进状态机）+ ledger 旁路 + 可恢复。
6. **优先级**：两重构优先于 `06-28-role-ceo` 实现（role-ceo 派活能力建在本机制上）。
7. **常驻粒度 = 按 role 拆（已定）**：4 个非 CEO agent（Researcher / Builder / Growth / Verifier）各一容器；CEO 第五个，由统一 loop 收编。role charter/skill 内容归 `06-28-role-library`，child① 用占位 charter 先跑通机制。

## 子任务地图（先机制、后确定性）

| 子任务（slug） | 重定向后职责 | 依赖 |
|---|---|---|
| ①（`resident-departments`） | **统一 loop + 全员常驻 + P2P 机制**：`ceo_loop`→通用 `agent_loop`；5 agent 常驻、自驱 poll 各自 inbox；inbox 升双向 P2P；跑通最简零人闭环（CEO 直投部门、部门直回）。**中间态**：暂不含独立验收分权 + watchdog（明确标注）。 | 无（先做） |
| ②（`p2p-goal-passing`，历史名） | **异步验收分权 + 确定性状态机 + ledger 旁路**：把现有同步 `run_goal` 的确定性保证迁到异步——独立 verifier 分权、`attempts`/retry/`kill` watchdog、ledger 旁路 + 崩溃可恢复、inbox 接口收敛。 | **依赖 ①** |

> 拆分逻辑：① 先把「统一 loop + 部门自驱 + P2P 投递」机制跑通（牺牲临时的验收/watchdog）；② 再把确定性保证（验收分权、状态机、watchdog、可恢复）补回到异步世界。两步各自可独立验收。

## 跨子任务集成验收（父任务持有）

- **AC-P1 统一 loop**：单一 `agent_loop` 代码，5 个 agent 是其实例（同镜像、`key`/`charter`/`computer-server` 参数区分）。
- **AC-P2 全员常驻 + context 连续**：5 agent 常驻；同一 agent 跨任务 resume 同 session、上下文续接。
- **AC-P3 闭环**：child① = 最简 P2P 直投闭环（无中心 pump `docker exec`）。**child② 修订（PR #195）**：业务消息改为经一个**轻量确定性中枢 Hub** 路由（仍无 spawn、无 docker.sock、不跑 LLM）——「退役的是重 pump」，Hub 是轻中枢，不违背去 pump 初衷。✅ 带独立验收 + watchdog 的完整闭环已交付。
- **AC-P4 验收分权不退化**：✅ **child② 已交付**——doer ≠ judge 由 Hub 的**发送者身份门**结构强制（verdict 只认 verifier、work 只认 assignee），部门不能自评。child① 暂缺验收的中间态不算违背。
- **AC-P5 确定性 / 可恢复不退化**：✅ **child② 已交付**——状态机异步事件驱动推进、watchdog（deadline sweep + attempts/kill）生效、Hub 内存无状态 + reconcile 崩溃可恢复（确定性 id 幂等）。
- **AC-P6 能力等价迁移**：现有 117 单测覆盖的能力迁移而非丢弃（允许重写测试，等价语义不退化）。

## 需要回填的旧决策 / 文档（落地后同步）

- `06-28-role-library` 决策 2「跳过持久 Lead 层、CEO 直派 ephemeral worker」——推翻 ephemeral，需改写。
- `docker-compose.yml` 头注（"Two long-lived containers + ephemeral workers" 拓扑）。
- `06-26-orchestration-layer` design §1 拓扑（worker「临时」）。
- 已归档 `06-28-ceo-loop` 的「`ceo_loop` = CEO 专属」描述 → 通用 `agent_loop`。

## 风险 / 开放问题

- **异步状态机协调放哪**（child②）：CEO 自协调 / 一个确定性协调 agent（非 LLM 跑 loop 收事件推状态机，= pump 异步化）/ 收发双方各推进自己那段。
- **验收分权落法**（child②）：部门干完直接送 verifier inbox vs caller 送。
- **watchdog 挂哪**（child②）：`attempts`/retry/`kill` 的确定性记录与触发位置。
- **child① 中间态期间验收缺失的可接受性**：已与用户确认可接受（child② 紧接补回）。
- **建议 child② design 前调研**：actor model / mailbox / saga（异步事件驱动状态机）的开源最佳实践。

## child① 完成状态（2026-06-29）

`06-29-resident-departments` **核心完成**：AC1-6 真容器 e2e 验证（统一 `agent_loop` + 全员常驻 + P2P 无中心 pump + context 连续 + computer-server 全 on 同构 + 零人闭环），120 单测绿，code-reviewer 过。commit `c9db480` + `9001ac1`。详见 child① prd 验收记录。
**后置 hardening（不阻塞 child②）**：AC7 跨 rm 持久化（与 ceo-loop 一致后置）、完整 loadout materialize（随 role-library）、全 5 容器 live run。
