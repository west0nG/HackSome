# 异步事件驱动状态机 — 设计模式与开源最佳实践调研

> 任务 `06-29-p2p-goal-passing` design 前调研。目的：把现有**同步确定性状态机**（`goal_loop.run_goal`）迁到 child① 的**异步 P2P 世界**（5 个常驻 LLM agent + file-based inbox），同时保住核心 IP（独立验收分权、确定性状态机、watchdog、崩溃可恢复）。
>
> 阅读说明：每节先给「对本项目的结论/建议」，再给依据与来源。最后一节是「对 4 个决策的综合建议」。技术名词与代码保留英文，论述用中文。

## TL;DR（先看这个）

- **决策 1（协调者放哪）→ 选 (b)**：保留一个**非 LLM 的瘦确定性进程**（`goal_pump` 的异步重生：订阅 inbox 事件→推 ledger 状态机→投下一步消息，但不再 spawn 容器）。**不选 (a) CEO 自协调**（违反「状态推进不依赖 LLM」硬约束），**不选 (c) 纯 choreography**（implicit state + 崩溃恢复模糊，正是我们要避免的）。
- **决策 2（验收分权）→ coordinator 路由，不让部门自送**：部门干完只 `report` 给 coordinator；由 coordinator 确定性地转 `verifying` 并把验收请求投给独立 verifier。部门**结构上拿不到** `done` 这个跳转，中立性靠代码强制，不靠「相信部门会去送」。
- **决策 3（watchdog）→ 全挂在 coordinator + 状态写进 ledger**：`attempts`/retry/`kill` 沿用现有 ledger 逻辑（已确定性、已测）；**新增持久 deadline + 周期 sweep** 兜住「部门 hang 住永不回报」的异步新风险（借 Temporal 的 durable-timer 思想，落成 ledger 里的时间戳 + 扫描）。
- **决策 4（ledger 角色）→ 仍持有状态机、被事件推进，不是纯旁路**。它已经是「per-goal 状态快照 + `runs[]` 事件流」的 snapshot+log 混合体，正好是事件溯源推荐的轻量形态。崩溃恢复用 **reconciliation loop（对账循环，K8s controller 思路）** 而非 event replay。
- **决策 5（vendor 与否）→ 手写，不引框架**。mailbox/去重已经是现成的 inbox.py；FSM 已手写且被 117 测试锁定；saga/workflow 框架（Temporal/Celery）都要 server/broker，违反 file+flock 约束。只借**思想**，新增代码 ~100–200 行 coordinator。

---

## 调研问题 1 — Orchestration（中心协调）vs Choreography（各推各段）

### 对本项目的结论

**选 orchestration（中心协调），具体落成「一个非 LLM 的瘦确定性 coordinator」（决策 1 的 (b)）。** 理由是本项目的两条硬约束——「状态推进必须确定性、不依赖 LLM」与「崩溃可恢复、in-flight goal 不丢」——恰好命中 choreography 的两大已知失效面，而正是 orchestration 的强项：

- **确定性 / 可恢复**：orchestration 把每个 saga 实例的「当前在哪一步、各步结果、要往下传什么」记在一个持久存储里，崩溃后能从**精确的失败点**恢复。choreography 的整体状态是**隐式**的，只存在于多个服务日志/消息流的关联中，恢复是「取证式重建」，慢且易错。
- **可观测 / 可调试**：orchestration 失败时，状态记录直接告诉你「卡在哪一步、输入是什么、在等什么」；choreography 要跨多个服务事件日志做 forensic 关联。
- **补偿/漏判可见性**：choreography 里「某步漏做/补偿失败」**没有任何组件知道**——这正是我们绝不能接受的（验收漏判 = doer≠judge 信条破功）。

注意约束直接**排除 (a) CEO 自协调**：CEO 是 LLM，让它来翻 ledger 状态、数 attempts、判 kill，等于把确定性状态机交给一个非确定性裁判（prd 明确「watchdog 不能靠 LLM 判断」）。CEO 该做的是**业务决策**（派什么活、上层 goal 算不算达成），不是**状态推进**。

**但要诚实**：child① 刚刚因为「中心 pump 过重」才退役了 `goal_pump`、转向 P2P。重新引入 coordinator 看似走回头路。化解办法是**分层混合**（这也是 saga 文献反复给的现实建议——"choreography for high-throughput loosely-coupled flows; orchestration for complex, stateful, business-critical workflows"）：

- **业务对话层**（CEO ↔ 部门 ↔ 部门，LLM 驱动）→ 保持 P2P / choreography，松耦合、自驱，正是 child① 的价值。
- **验收+watchdog 控制层**（doer→verifier→verdict→done/retry/kill，必须确定性+可恢复）→ 收成一个瘦 coordinator 拥有。

这个 coordinator 是 `goal_pump` 的**异步重生**：差别在于它不再 claim+spawn 容器（agent 都常驻了），只「订阅事件 → 推状态机 → append 下一步 IME 给常驻 agent」。它本身可以跑成一个和 `agent_loop` 同形的常驻循环（sleep on inbox → wake → 处理），只是 wake handler 是**确定性 Python**而不是 `claude` 子进程——这样它在「人人都是一个 loop 实例」的美学里也不突兀。

### 依据 + 来源

- "Orchestration gives you explicit control, centralized visibility, and easier debugging…"；"choreography… implicit state, distributed business logic, and harder compensation guarantees." — orchestration/choreography 权衡总览。
- "The most significant operational weakness of choreography is that the overall saga state is implicit"；"reconstructing the current state of a failed saga requires correlating events from multiple services' event logs, which is slow and error-prone"；"there is no component that knows a compensation was missed." — choreography 的 implicit-state / 漏补偿失效面。
- "Each saga instance has a record in a persistent store tracking its current step…"；"the orchestrator's state record tells you exactly which step it failed on, what input it had, and what it was waiting for." — orchestration 的可恢复/可观测优势。
- "Most large systems use both — choreography for high-throughput, loosely-coupled flows; orchestration for complex, stateful, business-critical workflows." — 分层混合的现实建议。

来源：
- [Saga Orchestration vs. Choreography: Making the Right Trade-off (Alok)](https://aloknecessary.github.io/blogs/saga-orchestration-vs-choreography/) / [DEV 镜像](https://dev.to/aloknecessary/saga-orchestration-vs-choreography-making-the-right-trade-off-in-event-driven-systems-5fmm)
- [Saga Pattern Demystified: Orchestration vs Choreography (ByteByteGo)](https://blog.bytebytego.com/p/saga-pattern-demystified-orchestration)
- [Saga patterns — AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) / [Saga choreography 局限](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-choreography.html)

---

## 调研问题 2 — Saga / Process Manager 模式（补偿、重试、超时）

### 对本项目的结论

把 coordinator 落成一个 **Process Manager**（saga 的 orchestrator 变体）：它监听各服务事件，用一个状态机维护流程位置，并在每一步上声明 **retry / timeout / 补偿** 策略。映射到本项目：

1. **retry 带 feedback**：verifier 出 FAIL → coordinator 调 `ledger.fail_verify(feedback)`（`attempts += 1`，回写 feedback）→ 把带 feedback 的同一 goal 重投给**同一执行部门**（续 context、非重起，满足 AC3）。这正是 saga 的 "retriable operations… should be retried before triggering compensation"。
2. **kill（耗尽）**：`should_kill(max_attempts)` → `kill`。对应 saga 的「重试 N 次后判永久失败」。
3. **timeout watchdog（异步世界的新增项）**：同步 `run_goal` 里部门 hang 住只是阻塞调用；异步后部门可能崩/卡而**永不回报**，状态机会无限期挂起。saga 的标准解法是 **timeout transition**：「若预期响应在设定时间内未到，状态机自动触发补偿/重投/告警，避免 saga 无限期挂起」。落法见决策 3。
4. **补偿（compensation）**：本项目目前没有真正的「跨服务补偿」需求（goal 失败 = 重投或 kill，不需要回滚别人已提交的副作用）。所以**不必引入完整补偿机制**——只需 retry + timeout + kill 三件套。这是和经典金融 saga 的关键区别，能大幅简化。若未来出现「A 部门已写 /company、B 部门失败需撤回 A 的产物」才需要补偿，届时再加。

### 依据 + 来源

- "A Process Manager… listens for events from various services and maintains the state of the process in a state machine, transitioning between different states based on the events it receives… can also manage timeouts, retries, and compensating actions." — Process Manager 定义。
- "You can define timeout transitions so that if an expected response is not received within a set period, the state machine automatically triggers compensation flows or alerts operators, which prevents the saga from hanging indefinitely." — timeout transition（决策 3 的直接依据）。
- "Retriable operations fail transiently and should be retried before triggering compensation… a compensating transaction must be idempotent and retryable." — retry 先于补偿、补偿须幂等可重试。
- "If the call to the compensating transaction fails, it is the orchestrator's responsibility to retry it until it is successfully completed." — orchestrator owns 重试责任。

来源：
- [Microservices: Saga Pattern Vs. Process Manager (peerdh)](https://peerdh.com/blogs/programming-insights/microservices-saga-pattern-vs-process-manager)
- [Saga Pattern for Resilient Flight Booking Workflows (DZone, state machine + timeout)](https://dzone.com/articles/saga-state-machine-flight-booking)
- [Saga patterns — AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html)

---

## 调研问题 3 — Actor model / mailbox 模式映射到「file-based inbox + 常驻 agent」

### 对本项目的结论

**好消息：这一层我们已经无意中实现对了，几乎无需改动。** 现有架构就是教科书式的 actor/mailbox + idempotent-consumer：

| Actor/mailbox 概念 | 本项目现状（inbox.py） |
|---|---|
| 一个 actor 一个 mailbox | 一个 agent 一个 `<key>.jsonl` |
| single consumer per mailbox | 「One consumer per key」+ cursor 单读者，注释已写明；plain read-modify-write cursor 因单读者而无竞争 |
| at-least-once + 去重（inbox/idempotent-consumer pattern） | `append` 用 IME `id` 对照 `<key>.seen` 集合去重；重投同 id 直接丢弃 |
| 多 producer 写一个 mailbox 要串行 | 单个 advisory `flock`（0o666 跨 uid）串行所有 append |
| single-writer principle（漏斗：多前端→一个写者） | cursor 的单读者 = 该 mailbox 的单一推进者 |

**要补强的两点（落到 design）**：

1. **「先持久化、后 ack」的次序**：idempotent-consumer 的核心是「处理完业务**并**记下 message-id 后才 ack；若在更新 DB 后、ack 前崩溃，broker 会重投，靠 id 去重兜住」。当前 `poll/_drain` 是**先推进 cursor 再返回事件**——若 coordinator 在「cursor 已前进、但事件尚未落成 ledger 状态」之间崩溃，这条事件就**丢了**（既不会重投，cursor 也过了）。这是异步化后最隐蔽的一致性坑。建议给 coordinator 用 **`poll_one` + 显式 ack**（处理完→落 ledger→才推进 cursor），或保证「事件处理 = 幂等地把 ledger 推到目标态」从而即便丢一条也能被 reconciliation（决策 4）补回。**强烈建议两者都做**：ack-after-process 保正常路径不丢，reconciliation 兜崩溃。
2. **幂等处理**：at-least-once 意味着同一事件可能被处理多次。ledger 的 `_require` 合法跳转校验天然提供幂等性——重复处理同一 verdict 会撞到非法跳转（`GoalError`），coordinator 应把它当「已应用、跳过」，而不是崩。这把「去重」从纯 id 层升级到「状态层幂等」，更稳。

### 依据 + 来源

- "messages are delivered unreliably with at-most-once semantics by default… at-least-once delivery can be enabled, which retransmits messages until reception is acknowledged. However… the runtime engine does not detect duplicates, [so] implementing at-least-once delivery burdens developers with deduplication." — at-least-once 必须自己去重（我们已用 `.seen`）。
- "A message handler must be idempotent: the outcome of processing the same message repeatedly must be the same as processing the message once." — 幂等处理。
- "INSERT into PROCESSED_MESSAGE… the INSERT will fail if the message has been already processed… The message handler can then abort the transaction and acknowledge the message." — inbox/idempotent-consumer 的具体机制（= 我们的 `.seen` 集合）。
- "This occurs when handlers crash after updating the database but before acknowledging receipt. The acknowledgment step tells the broker the message was processed successfully and should not be redelivered." — 「先处理后 ack」次序（补强点 1 的直接依据）。
- "A persistent actor makes it easy for an actor to record its state as events and to recover from the events after a crash or restart… called event sourcing." — actor 持久化 = 事件溯源（接问题 4）。
- "If you have shared state with a single writer to it, then you need a funnel architecture where multiple front-ends send changes/events to this one writer." — single-writer principle（= ledger 应有单写者，见决策 4）。

来源：
- [Idempotent Consumer / Inbox Pattern (microservices.io)](https://microservices.io/post/microservices/patterns/2020/10/16/idempotent-consumer.html)
- [Achieving Idempotency with the Inbox Pattern (DEV)](https://dev.to/actor-dev/inbox-pattern-51af)
- [Akka in Action, Ch.15 Actor persistence (Manning)](https://livebook.manning.com/book/akka-in-action/chapter-15)
- [Single Writer Principle (Mechanical Sympathy)](https://mechanical-sympathy.blogspot.com/2011/09/single-writer-principle.html)
- [A Configurable Transport Layer for CAF (arXiv, at-least-once 语义)](https://arxiv.org/pdf/1810.00401)

---

## 调研问题 4 — Event Sourcing / Workflow engine（Temporal 思想）

### 对本项目的结论

**借三个思想，不引任何框架；ledger 保留状态机角色（决策 4 选「仍持有状态机、被事件推进」）。**

可借的思想：

1. **「持久日志 + 重放重建内存态」= 崩溃恢复的本质**（AC4）。Temporal：crash 后「replay event history 把内存态重建到 crash 前那一刻，从下一步继续，像什么都没发生」。本项目对应：coordinator 重启 → 读 ledger → 每个非终态 goal 的 `status` 就告诉你「下一步该干嘛」。
2. **显式状态机会随规模腐化**（Temporal 的核心卖点：每多一个 edge case 就多一个 state/branch，外加大量 persistence/timeout 的 plumbing 代码）。**对本项目的含义是相反方向的取舍**：我们的状态机只有 6 个状态、规模极小、且已被 117 测试锁定，"腐化" 风险尚不存在——所以**不值得**为了「更声明式」去引 Temporal/状态机框架（那才是 plumbing 暴增的来源）。我们要的是 Temporal 的**恢复思想**，不是它的运行时。
3. **durable timer = 把超时变成日志里的一条事件**：Temporal `Workflow.sleep(30 days)` 即便进程重启也能可靠唤醒，因为 timer 是持久事件而非内存定时器。本项目对应：把 watchdog 的 deadline 写成 **ledger 记录里的时间戳**，而非 coordinator 内存里的 timer——这样 coordinator 重启后扫一遍 deadline 就能恢复超时判定（决策 3 的落地依据）。

**关键取舍：event log vs snapshot。** 事件溯源圈共识是「event stream 是 source of truth，snapshot 只是性能优化（避免重放数万条事件）」。但**本项目 goal 数量极小**（个位数并发），重放成本根本不是问题，反而是「重放必须确定性、replay 与原 command 序列不匹配就崩」的 Temporal 式约束会**徒增复杂度**。所以：

- **不做** event-sourcing 式「重放事件流重建态」。
- **做** snapshot 式：ledger 的每个 goal JSON 就是**权威快照**（`status` / `attempts` / `feedback` / 拟加的 `deadline`），`runs[]` 是**审计/调试用的事件流**。这正是「snapshot + 近期事件」的推荐混合形态，且对小状态最省心。
- **恢复用 reconciliation loop（对账循环），而非 replay**：coordinator 启动时（以及每个 tick）对每个非终态 goal，**从其当前 `status` 推导「应该处于的下一步」并幂等地重新发出**（消息按 `goal_id` 去重，常驻 agent 收到重复的会被 inbox `.seen` 挡掉）。这是 K8s controller 的「desired vs actual 对账」思路，比 event replay 更稳、更简单，也天然绕开下面的 dual-write 风险。

> **为什么不是「纯旁路审计」ledger（决策 4 的 A 选项）**：若 ledger 只留痕、真正状态活在 LLM agent 脑子里和 inbox 文件里，那恢复就变成隐式、非确定性的——正是 choreography 的失效模式。AC2/AC4 要求 ledger 必须是**权威**的可推进状态机。

### 依据 + 来源

- "Temporal automatically records each significant step… creating an append-only event log… if the process or machine executing your code crashes, Temporal can seamlessly continue execution on entirely different infrastructure, picking up exactly where it left off." — 持久日志 + 跨机恢复。
- "each new scenario or edge case often means introducing additional states or branches in the state diagram" + 大量 persistence/switch-case/timeout plumbing 代码。 — 显式状态机腐化（本项目反向取舍的依据）。
- "you can call `Workflow.sleep(30 days)` and Temporal will reliably wake the workflow… even if processes restart in the meantime." — durable timer（决策 3 依据）。
- "When there's a mismatch between the expected sequence of Commands… and the actual sequence produced during Replay (due to non-determinism), Replay will be unable to continue." — replay 的确定性约束（= 我们不想背的包袱）。
- "Snapshots are not the source of truth. They are a performance optimization… The eventstream remains the source of truth." 以及 "rebuilding state from scratch every time… would take seconds, not milliseconds"（高频聚合才需 snapshot；我们规模小，反过来 snapshot 足矣）。 — snapshot vs replay 取舍。

来源：
- [Temporal: Beyond State Machines for Reliable Distributed Applications](https://temporal.io/blog/temporal-replaces-state-machines-for-distributed-applications)
- [Event Sourcing Implementation — Temporal Server (architecture)](https://www.mintlify.com/temporalio/temporal/architecture/event-sourcing)
- [Snapshots in Event Sourcing (Kurrent)](https://www.kurrent.io/blog/snapshots-in-event-sourcing/)
- [Event Sourcing Pattern — Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)

---

## 调研问题 5 — 可 vendor 的轻量 Python 实现（vendor vs 手写）

### 对本项目的结论

**手写。不 vendor saga/workflow 框架，FSM 也建议保持现有手写版。** 逐件拆解：

| 组件 | 现状 / 选项 | 建议 |
|---|---|---|
| mailbox / single-consumer / at-least-once + 去重 | **已实现**（inbox.py = actor mailbox + idempotent-consumer inbox pattern） | 不 vendor、不重写，按问题 3 补强 ack 次序即可 |
| 状态机（合法跳转） | 已手写 ~50 行（`_transition`/`_require`），含 per-file 持久化 + flock + notifier | **保持手写**（见下） |
| saga / process-manager orchestrator | 无 stdlib 友好的小库；重框架（Temporal/Celery）都要 server/broker | **手写 ~100–200 行 coordinator** |
| durable timer / 恢复 | Temporal 思想，落成 ledger 时间戳 + sweep | 手写 |

**FSM 库（transitions / python-statemachine）值不值得 vendor？** 结论是**不值得，保持手写**：

- `pytransitions/transitions`：确实轻、核心**零硬依赖**、对象可 `pickle`、支持 guards(`conditions`/`unless`) 与多阶段 callbacks、有 `HierarchicalMachine`。是「若要引一个 FSM 库就引它」的首选。
- 但本项目的难点**不在 FSM 表达**，而在**持久化（一 goal 一 JSON + flock 单写者 + notifier 副作用）**——这部分 transitions 帮不上（它的 pickle 持久化模型和我们的 per-file ledger 不是一回事，硬套反而要重做持久层）。
- 且 AC6 明确要求「能力**等价迁移**而非丢弃」、117 测试已锁定现有状态机语义。为「更声明式」去换一个库属于**无收益的 churn**，还会动到测试基线。

**坚决不引**的：Temporal（需 server 集群）、Celery / RQ（需 Redis/AMQP broker）、任何要常驻中间件的 workflow engine——全部违反「file-based + flock + stdlib 优先、轻依赖、自托管」硬约束。它们的**思想**已在问题 2/4 借完。

> 一句话取舍：这个规模（个位数 goal、6 状态、单进程协调）**手写完胜**。新增的唯一实质代码是 coordinator（reconciliation + durable-timer sweep + verdict 路由），约 100–200 行，依赖现有 ledger/inbox。

### 依据 + 来源

- transitions：「A lightweight, object-oriented finite state machine implementation… with many extensions」；"Machines are picklable and can be stored and loaded with `pickle`"；guards via `conditions`/`unless`；`HierarchicalMachine` 嵌套态；多阶段 callbacks。核心模块化、可选 extension（diagrams/threading/async）暗示核心依赖极少。
- python-statemachine：纯 Python、声明式 statecharts、sync/async 均可、支持 compound/parallel/history 态、SCXML——比 transitions 更重，本项目用不上。
- Temporal/Celery 类需独立 server/broker（与 file+flock 约束冲突）——见问题 4 来源及常识。

来源：
- [pytransitions/transitions (GitHub)](https://github.com/pytransitions/transitions)
- [python-statemachine (PyPI)](https://pypi.org/project/python-statemachine/) / [docs](https://python-statemachine.readthedocs.io/en/latest/index.html)
- [finite-state-machine (PyPI, 装饰器式轻量)](https://pypi.org/project/finite-state-machine/)

---

## 综合建议 — 对 4 个决策的最终落法

### 决策 1：异步状态机协调者放哪 → **(b) 非 LLM 瘦确定性 coordinator**

一个常驻的、非 LLM 的 coordinator 进程（`goal_pump` 异步重生，去掉 spawn）：sleep 在自己的 inbox 上，醒来后用**确定性 Python** 推 ledger 状态机、按状态 append 下一步 IME 给常驻 agent。它**只管控制层**（验收+watchdog 状态推进），业务对话（CEO↔部门）仍走 P2P。这样既满足「确定性、可恢复」硬约束，又不把 child① 的 P2P 价值推翻——属于文献推荐的「choreography 跑业务流 + orchestration 跑关键有状态流」混合。
- 排除 (a)：CEO 是 LLM，不能做确定性状态推进/watchdog。
- 排除 (c) 纯 choreography：implicit state + 漏判不可见 + 恢复模糊，命中我们最不能接受的失效面。
- **不可约的理由**：timeout watchdog 的 sweep 天然需要一个**单一、常驻、确定性**的所有者；这一条就足以否掉全 choreography。

### 决策 2：验收分权落法 → **coordinator 路由到 verifier，禁止部门自送**

```
部门完工 → report(coordinator)            # 部门只回报，拿不到 done 跳转
coordinator: reported → verifying          # 确定性转移
coordinator → append 验收请求到 verifier inbox   # coordinator 选 verifier（中立）
verifier(read-only,no record) → "VERDICT: PASS/FAIL: reason" → report(coordinator)
coordinator: parse_verdict()               # 复用现有标准化输出闸门
   PASS → pass_verify → done → 通知 caller
   FAIL → fail_verify(feedback) → 重投同一部门（续 context）
```
- **doer≠judge 靠结构强制**：部门结构上拿不到 `pass_verify`，唯一能落 `done` 的是 coordinator，且只在 verifier 的可解析 PASS 上落。中立性由「coordinator（非利益相关方）选并转发 verifier」保证，不靠相信部门会去送。
- **不选「部门直送 verifier」**：部门是利益相关方，自选/自决何时验、甚至可以不送，中立性无保障。
- 保留现有 `VERDICT: PASS / FAIL: <reason>` 标准化输出 + `parse_verdict`——这是「LLM in, 标准化 out」的关键 seam，让确定性代码能做 done/retry 判定。

### 决策 3：watchdog 挂哪 → **全在 coordinator，状态写进 ledger**

两套机制，都确定性、都可恢复：
1. **attempts/retry/kill**：沿用现有 ledger 逻辑（`fail_verify` 累加 + 回写 feedback、`should_kill(max_attempts)`、`kill`）。已确定性、已测，直接复用。
2. **timeout/liveness（异步新增）**：进入 `running`/`verifying` 时在 ledger 记录上盖 **`deadline` 时间戳**；coordinator 每个 tick **扫描超期的非终态 goal**，按一次「失败尝试」处理（带 feedback 重投）或直接 kill。deadline 持久在 ledger → coordinator 重启后扫一遍即恢复（借 Temporal durable-timer 思想，落成时间戳+sweep，不引框架）。

### 决策 4：ledger 角色 → **仍持有状态机、被事件推进（非纯旁路）**

- ledger = **权威状态快照 + `runs[]` 事件流** 的混合（snapshot+log），coordinator 是其**单写者**（single-writer principle）。
- 崩溃恢复用 **reconciliation loop**：启动/每 tick 对每个非终态 goal，从 `status` 推「下一步」并**幂等重发**（goal_id 去重、`_require` 状态层幂等兜底）。比 event replay 简单稳，且绕开「ledger 写 + inbox append」两次 flock 之间崩溃的 **dual-write / transactional-outbox** 风险。
- 拒绝「纯旁路审计」：那会让真状态隐式存在于 LLM 脑子+inbox 文件，恢复非确定性，违 AC2/AC4。

### 推荐方案的最大风险

**最大风险 = 重新引入中心 coordinator，在概念上部分回退了 child① 「退役中心 pump、转 P2P」的决策，且 coordinator 成为单点。** 具体表现与缓解：

1. **概念蔓延**：coordinator 可能慢慢长回旧的重 pump（开始做业务决策、甚至 spawn）。**缓解**：宪法式约束——coordinator **严格非 LLM、只做状态推进、零 spawn、零业务判断**；任何「派什么活/上层 goal 达成没」一律留给 CEO。
2. **单点故障（SPOF）**：coordinator 挂了，状态机停摆。**缓解**：coordinator **内存无状态**（全部状态在 ledger）→ 重启即恢复；它挂的期间，消息只是**堆在 append-only inbox 里**（不丢），重启后 reconciliation 一次性追平。所以 SPOF 是「暂停」不是「丢数据」，对零人公司可接受。
3. **dual-write 一致性**（ledger 写与 inbox append 非原子，两把 flock 之间可能崩）→ 已由决策 4 的 reconciliation + 决策 3 的「先处理后 ack」共同兜住，但这是**实现期必须显式验证**的点（design.md §10 fail-loud 应加一条：注入「转 verifying 后、投验收请求前 kill coordinator」，断言重启后该 goal 被正确补投验收）。

> 次要风险：异步后「部门 hang 住永不回报」是同步 `run_goal` 没有的新失效面——已由决策 3 的 timeout sweep 覆盖，但 deadline 取值（多久算 hang）需结合真实任务时长调参，初期宜宽松+可观测。
