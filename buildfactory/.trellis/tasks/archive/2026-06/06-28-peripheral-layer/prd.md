# Peripheral Layer（外设层）— 异步通知 inbox 标准

> 父任务：`.trellis/tasks/06-26-foundagent-v6`。状态：✅ done（PR #193 已合并；147 测试 + 真 LLM live e2e 通过；契约见 spec `backend/peripheral-layer-contracts.md`）。
> 本版 = 2026-06-28 与 weston 现场 brainstorm 后**重写**。旧占位 PRD 作废（那份是 agent 自动生成、未经审批）。
> 业界调研依据见 memory `peripheral-layer-research-findings`（两轮、34 个 research agent）。

## Goal（目标）

做一个**规范化的"外设层"**：把公司从外部世界收到的所有**异步通知**（email、社媒回复、平台 webhook、收款、订阅…）**归一成一个统一的消息信封**，投进一个**统一收件箱**，让 CEO 像"一个 tool 调用返回了结果"那样、被动地、及时地收到并处理。

核心价值 = **归一 + 标准 + 可扩展**：

- agent 永远只面对**一种信封**，永远不碰各外部源的原始协议；
- 加一个新外部源 = 写一个**小 adapter**，**核心一行不改**；
- 外部源现在猜不准（只有真把零人公司跑起来、从现实拿到反馈，才知道要接什么），所以**重点不是"接哪些源"，而是把"标准接口"和"可扩展"做对**。

## 本次 brainstorm 定下的关键决策

1. **只管异步通知。** 同步/会话/流式输入（打进来的电话、实时音频、每秒上千条的行情流）**明确不接**——它们现在根本没有消费端（agent 还不会接电话 / 处理实时音频 / 聚合行情）。没有的能力就不留接口；将来真要接，那类输入由它**自己的 adapter 在边缘扛住实时那摊**，处理完只往收件箱投一条"已经发生的事"，照走本标准。**未来不堵死，核心现在不背这复杂度。**
2. **消费 = "像 tool 调用返回结果"，push，不打断。** 消息以一个 tool 调用的**返回值**形态交给 CEO（不是"用户发言"）：CEO 留一声"有事叫我"挂着，事件到达把 CEO **推醒**、并作为那个调用的返回递过来；及时、一条一条、不攒；CEO 正忙别的时消息在收件箱排队，**等它当前这摊干完**再递下一条。（这对**每个常驻 agent** 一视同仁，CEO 只是其一；**`receive` 工具在本层定义**，驱动它的常驻进程 loop 在 orchestration/ceo-loop 落地。）
3. **一套统一信封 + 一套统一收件箱机制。** 外部事件 **和** 编排层的 goal 完成事件**走同一种信封、同一套收件箱、同一个 receive 路径**（物理上按 `to` 分到各 agent 的 inbox，见决策 6）——这正好回答了 `06-28-ceo-loop` 留的"inbox 是否长成统一口"的 open question：**是**。
4. **安全先放后面（留欠条）。** 注入 / 信任传染 / 顺序一致性 / 外部事件限流 —— v0 **故意不管**，碰真钱前必须回头补（见"已知风险"）。
5. **下半层抄现成标准，上半层自建。** 信封形状借 CloudEvents、签名投递借 Standard Webhooks（v0 可先不验签）、相关性借 A2A/FIPA；真正自建的是"外部事件 → 变成 agent 的一条消息"这层（业界无标准，见调研）。
6. **inbox 是每个 agent 的通用能力，不是 CEO 专属。** 现在所有 agent 都常驻 → 凡需要"被动收异步消息"的 agent（派了子活等回包的、或外部事件的目标）都有自己的 inbox + `receive()`，CEO 只是其中顶层那一个。纯一次性 leaf worker 自己不需要 inbox（其完成由 goal-ledger 投到**派活者**的 inbox）。`to` 字段寻址到哪个 agent 的 inbox。

## 与编排层 / CEO-loop 的边界

- **本层负责**：① 统一信封（IME）；② 每个 agent 的 inbox + 投递/读取契约（append / receive / ack）；③ **`receive()` 工具**（任何 agent 被动收消息的入口）；④ 外部源 adapter。
- **不在本层**：agent 怎么决策/派活（Goal 协议，已 done）、**驱动 `receive()` 的常驻进程 loop**（orchestration/ceo-loop——现在要从"CEO loop"泛化成"agent loop"）、判断力（skill/hook，后置）。
- 依赖：Goal 协议（`06-26-orchestration-layer`，done）。**inbox 契约从 ceo-loop R4 的"留接口 stub"上收到本层完整定义**，ceo-loop 改为**消费方**。

## Requirements（需求）

- **R1 统一信封（IME）**：定义一个标准信封，外部信号 + goal 事件都归一成它。**就 5 格**：`id`（去重/已读，broker 可代生成）、`time`、`to`（投给谁，broker 唯一要读的）、`text`（非常简短一句）、`body`（正文，含"回哪件活"等一切扩展；内部结构 v0 freeform）。**dumb broker 只碰 id/to，永不读 text/body。** 一切新东西写进 `body`，**信封永不加字段**（adapter 视角产出的就是 `{to,text,body}`）。
- **R2 每源一个 adapter，加源零核心改动**：adapter 唯一职责 = 原始信号 → IME（含一句好人话 + 可选结构化 data / 重负载指针 ref）。接新源 = 新增一个 adapter + 一行 manifest，**不改核心**（与 VM 层"账号注入可扩展接口"同口味）。
- **R3 只接异步通知**：同步 / 会话 / 流式不在本层（见决策 1）。
- **R4 投递契约（dumb broker）**：`append(to, envelope)`；按 `(source, id)` 去重；按 `to` 路由到**对应 agent 的 inbox**（`to=null` → 顶层 CEO key），**绝不解读 payload**。外部事件与 goal 事件同走这一套。
- **R5 `receive()` 工具（本层定义）**：每个 agent 可调 `receive(timeout?)` 从**自己的 inbox** 取下一条未读 IME，作为该 tool 调用的**返回值**拿到（="像 tool 返回"）。语义：**阻塞 / push**（有消息推醒、无消息挂着、超时=定时器地板返回 null）、**一条一条**（最老一条）、**不打断**（仅 agent 主动调用时才递）。驱动它在循环里反复调的常驻进程在 orchestration/ceo-loop 落地。
- **R6 可靠性**：信号不丢；收件箱落 **host 侧、绝不进 company folder**、抗容器重启；外设层 = `docker-compose.yml` 里一个**常驻 service**（一键启动，与 broker / CEO 平级）。
- **R7 测试驱动、按需接入**：不一开始接全部源；先接跑通自主运营闭环必需的少数几个，运行中观察缺什么再加。
- **R8 每 agent 一个 inbox**：inbox + `receive()` 是**通用 agent 能力**，非 CEO 专属。凡需被动收异步消息的 agent（派子活等回包 / 外部事件目标）都有自己的 inbox，按 `to` 寻址；CEO = 顶层那一个。纯一次性 leaf worker 自己不需要（其完成投到**派活者**的 inbox）。

## Acceptance Criteria（验收）

- [x] **AC1 真实源 e2e**：一个真实外部源（建议 email）→ adapter 归一成 IME → 进收件箱 → CEO 通过 receive 以 **tool 返回**拿到、读到那句人话。 ✅ `email` adapter + `tests/e2e`，真 LLM live e2e 通过。
- [x] **AC2 可扩展性（核心零改动）**：再接**第二个**源 = 只新增一个 adapter + 一行 manifest，**核心代码 0 改动**即可 e2e（diff 可证）。 ✅ `webhook` 为第二源，仅动 `peripheral/adapters/` + `manifest.ADAPTERS` 一行。
- [x] **AC3 统一性**：一个 goal 完成事件与一个外部事件，**走同一信封、同一收件箱、同一 receive 路径**被 CEO 收到；CEO 侧无需为两条来路写不同代码。 ✅ `goal_inbox.ime_notifier`（drop-in，ledger 核心未改）。
- [x] **AC4 不打断 + 一条一条**：CEO 忙于当前一摊时，新到消息在收件箱排队；当前干完才被递下一条（日志可观察"忙 → 排队 → 干完 → 收下一条"）。 ✅ `poll_one` 一条一条 + 处理中到达缓冲，确定性单测 `test_inbox.py` + live e2e。
- [x] **AC5 push 语义**：外部事件到达即把 CEO 推醒拿到它（不靠轮询、不靠 heartbeat 兜底也能在事件到达时被递）。 ✅ HTTP ingress → append → 阻塞 `receive` 即返。
- [x] **AC6 抗重启**：容器重启后，未读消息不丢、可继续被 receive 取到。 ✅ host 侧 JSONL+cursor，重启未读不丢。
- [x] **AC7 多 agent 收发**：agent A 派一个子活给 B，B 干完 → 完成事件进 **A 的 inbox**（不止 CEO）→ A 通过自己的 `receive()` 以 tool 返回拿到，靠 `replyTo` 认出是哪件活的回包。 ✅ `to`/`reply_to` 寻址 + body 关联（后由 06-29 P2P/Hub 复用）。

## Out of Scope（本任务不含）

- 同步 / 会话 / 流式输入（电话、实时音频、行情流）。
- CEO 决策 / 判断力、receive 工具与常驻挂等进程的实现（ceo-loop）。
- 第一批接哪些源的最终选择（取决于第一个 business 形态）。
- 签名验真的强制实施（v0 可留字段不强制；见已知风险）。

## 已知风险（v0 故意不管，碰真钱前必补）

> 一行欠条，写在这避免将来误以为已覆盖：

- **注入**：所有消息汇进一条"被当输入读"的流、跑在 CEO 最高权限下 → prompt injection 面最大；`trust` 标签本身也是流内字符串，可被注入绕过。
- **信任传染**：内部产物可能携带外部不可信内容（worker 总结的恶意邮件）→ 按 source 一刀切打 `internal` 会洗白；将来需沿数据来源传染（taint）。
- **顺序一致性**：同一线程事件乱序到达（扣款成功 / 退款）→ 按过时内容行动有风险；将来需每线程递增序号 / supersede。
- **限流 / 背压**：外部事件是攻击者可控的无限量（垃圾邮件 / webhook 风暴）→ 收件箱将来需对外部事件类限流。

## Open Questions

- 收件箱存储形态（SQLite WAL / JSONL / 目录）——与 ceo-loop R4 对齐后定。
- 已读语义：read-cursor 保留（可重读 / 审计）vs 取走即删。
- 无 LLM 的 dumb adapter 把"长邮件 / 大 diff"压成一句人话的丢失度——多大就必须靠 `payload.ref` 按需取。
- `to` 取值规则 / agent 寻址：默认 CEO；inbox key 用 role、role+instance、还是 goal 树里的 agent id（与 `resolve_role_spec()` / goal-carries-role 对齐）。
- **哪些 agent 真给 inbox**：全体常驻 agent 都给（最一致），还是只给"会收异步消息"的（派活者 + 外部目标）？前者要算**常驻进程 + parked session 的成本**账。
- 第一批接入哪些源（取决于第一个 business 形态）。
