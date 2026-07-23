# CEO Orchestration Loop（唤醒循环）— MVP

> 父任务：`.trellis/tasks/06-26-foundagent-v6`。状态：planning。
> 从 `06-26-orchestration-layer`（已 done：Goal 协议 + 验收 + DooD）拆出的 CEO 顶层。
> 背景见 memory `foundagent-orchestration-protocol`。本版 = **最小可行版**：只搭让 CEO 真正跑起来的骨架，复杂机制全部后置。

## Goal（目标）

让 **CEO** 真正跑起来的最小闭环：一个**长期常驻容器**里，CEO 每次唤醒用 `claude --resume` 续**同一个会话**，盯着 inbox + heartbeat，醒来就用已建好的 Goal 协议派活、收 goal 完成事件、做决策，然后睡。

终态（非 MVP）：把这个常驻容器变成一台长期在线、随时可 resume 的云上 VM。

## 本次重写定下的关键决策

1. **持久容器 + `claude --resume` 承载连续性** → 砍掉草稿里整套 scratchpad / 睡前蒸馏。连续性由 Claude 原生会话 + auto-compact 自己扛，跨唤醒靠 resume 同一 session。
2. **唤醒源 = inbox 事件 + heartbeat**，二者满足其一就醒。goal 完成不靠消费端轮询，靠状态机 **push**（见 3）。
3. **goal 终态 → 自动通知 parent，逻辑放进状态机**（不变式）：`pass_verify`（→done）和 `kill`（→killed）在锁内顺手把一条完成事件 append 到 parent 的 inbox。任何到达终态的路径都一定通知 parent，调用方无法遗漏。`parent == None`（顶层 goal）→ 投到 **CEO inbox**。
4. **inbox 只定接口、不定架构（留接口）**：本任务确定投递/消费**契约**，不锁定存储形态，也不在本任务里把"统一 inbox（外设层信号/自定条件也走同一口）"拍死。MVP 用一个最小 stub 实现顶在接口后面，可整体替换。
5. **判断力（选题 / kill 智能）、外设层、复杂成本闸、scratchpad —— 全部后置**，本版只搭循环骨架。

## 统一循环（MVP 形态）

```
醒来（inbox 有未读事件  ||  距上次唤醒已过 heartbeat 间隔）
  → claude --resume <ceo-session> -p "<这次触发: 哪些 goal 完成/失败，或仅 idle 巡检>"
  → CEO 看 open goals + 完成事件 → 决策 / 用 Goal 协议派新活（带 role）
  → 标记 inbox 已读 + 重置 heartbeat 计时
  → 睡（等下一次 inbox 事件或 heartbeat）
```

> 首次冷启动无 session 可 resume → 第一次 `claude -p` 新建会话并记下 session id，之后都 `--resume`。

## Requirements（需求）

- **R1 持久容器 + resume**：CEO 跑在一个常驻容器里（加进现有 `docker-compose.yml`，与 broker/外设层同列常驻），会话状态挂共享 volume。每次唤醒 = 在该容器里 `claude --resume <ceo-session> -p ...`，续同一会话。worker 容器仍用完即拆（不变）。
- **R2 唤醒源 = inbox + heartbeat**：CEO loop 等待"inbox 有未读事件 **或** heartbeat 到点"，满足其一即唤醒 CEO。heartbeat = idle 兜底巡检（间隔可配，默认建议 30min，待调）；它同时充当 MVP 的成本闸下限（不比此更勤）。
- **R3 状态机终态 push 到 parent inbox（不变式）**：扩展 `goal_ledger.py` 的 `pass_verify` 与 `kill`，在锁内 append 一条完成事件到 parent inbox。事件含 `{kind: goal_done|goal_killed, goal_id, parent, intent, feedback, ts}`。**done 和 killed 都通知**（CEO 需知失败才能改方向/重派）。`parent == None` → CEO inbox。实现形态：给 `GoalLedger` 注入一个**可选 notifier**（默认 no-op，不破坏现有 84 测试），状态机只多"发事件"一个确定性动作，不耦合 CEO/inbox 具体实现。
- **R4 inbox = 接口/契约（架构待定，留接口）**：定义最小契约——
  - 生产侧（状态机调用）：`append(parent_key, event)`，`parent_key` = parent goal id；`None` 归一为约定的 CEO key。
  - 消费侧（CEO loop 调用）：取未读事件、标记已读、可带超时等待（供 R2 的"inbox 有事或 heartbeat 到点"）。
  - **不锁定**：存储形态（文件 / JSONL / 目录 / 其它）、是否就此演化成承载外设层信号的统一 inbox——这些留作后续。MVP 提供一个满足契约的最小 stub 实现即可。
  - 约束：inbox 落 **host 侧、绝不进 company folder**（三存储红线：scratchpad / ledger / company memory 之外，inbox 属编排层运行时态）。
- **R5 CEO 决策派 Goal**：CEO 在唤醒里用已有 Goal 协议拆任务 / 派活（goal 带 `role`，调度器按 role 起全新 agent、用完即拆）/ 读 ledger 看状态。本版只要求"能派、能看、能在完成事件驱动下接着决策"，**不要求**复杂选题/kill 判断力。
- **R6 判断力后置**：选题、kill 标准、巡检智能等靠 skill+hook，本任务不做，留给后续。

## 依赖（已就绪 / 待建 / 推迟）

- ✅ **Goal 协议**（`06-26-orchestration-layer`，done）：派活 / 验收 / DooD / role 定向派活协议侧均已就绪，e2e 通过。
- 🔧 **本任务内改动**：① 扩展状态机（R3 parent 通知）；② 新增 inbox 接口 + 最小 stub（R4）；③ CEO 常驻容器 + loop（R1/R2）；④ CEO agent 定义（R5）；⑤ loop 运行时状态（session id / heartbeat 计时 / 已读位点，host 侧）。
- ⏳ **推迟（独立任务）**：外设层 `06-28-peripheral-layer`（外部信号归一进 inbox）、compact `06-28-agent-compact`、安全收窄、判断力 skill/hook、scratchpad、统一 inbox 的最终架构。

## 不做（Out of scope，MVP）

- scratchpad / 睡前蒸馏 / 渐进式披露下钻（被 resume 替代）。
- 外部世界信号摄入（邮件/Stripe/webhook）——外设层任务。
- CEO 自写"下次满足 X 才醒"的条件集（本版唤醒源只有 inbox + heartbeat）。
- 复杂成本闸 / 预算配额（本版用 heartbeat 间隔当下限）。
- 选题 / kill 智能、judge 类判断力。
- inbox 统一架构落地（本版只留接口 + stub）。

## Acceptance Criteria（验收）—— 全部达成（2026-06-28，真容器 e2e + 单测）

- [x] **AC1 常驻**：`make up` 后 `foundagent-ceo` 持续 Up（实测）。
- [x] **AC2 heartbeat 唤醒**：无事件时 heartbeat 到点 → CEO 被 `--resume` 唤醒巡检、睡回（实测：闭环中途 `wake (heartbeat, 0 event(s))` → "still running — wait"）。
- [x] **AC3 事件唤醒**：goal 跑完 `done` → 状态机 push `goal_done` 进 CEO inbox → CEO 在**事件触发**下被叫醒、看到结果（实测 `c84eac86d568`）。
- [x] **AC4 resume 生效**：闭环全程 3 次唤醒（事件→heartbeat→事件）同一 session `fd4d935b…`（实测）。
- [x] **AC5 零人自治闭环**：CEO 唤醒中**自己** `goal_cli add` 派 goal → pump 驱动 worker(execute)+verifier → done → 回推 → CEO 醒来收结果并决策下一步。派活→完成→回醒 全程零人（实测）。
- [x] **AC6 不变式**：`done`/`killed` 任一终态必通知 parent 一次；notifier 默认 no-op、既有路径不变。**117 单测全绿**。

> resume 验证闸（最大未知）单独实测：`claude -p --resume <id>` headless 续接成功（回答 42）。

## 后续（非本 MVP，已记入 memory）

- **CEO 判断力 / 成本闸**：闭环中 CEO 每次收到完成就再派后续 goal（持续烧 token）——judgment（选题/何时停/kill）后置给 skill+hook；heartbeat 是目前唯一成本下限。
- **CEO 跨 `rm` 持久**：claude 会话现只活在容器生命周期内（stop/start 存、`rm`/`down` 丢）；真正"随时 resume 的常驻 VM"需 chown-on-init 把持久卷给 kasm-user（named volume 默认 root-owned 会废掉 claude）。
- **CEO 源码隔离**：现只 ro 挂 orchestration 包（非整 repo）；完整隔离 = 把包烤进镜像。
- **inbox 架构落地**（留接口 → 统一 inbox，接外设层）。

## Open Questions

- **inbox 架构**：存储形态、parent_key 归一规则、是否就此长成承载外设层信号的统一 inbox（与 `06-28-peripheral-layer` 的边界）。
- heartbeat 默认间隔具体值。
- killed 之外，watchdog 升级 / 多次失败是否要额外事件类型。
- CEO 自身是否要在 ledger 里建一个顶层 mandate goal（影响 `parent` 归属与 inbox keying），还是顶层 goal 一律 `parent=None` → CEO key。
- 多层 goal 树里"parent 是仍存活的 worker"时通知怎么投（MVP 只跑 CEO 这条异步路径；同步 await 的 worker 仍走协议原有 `await_result`，本版不动）。
