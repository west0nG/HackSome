# Peripheral Layer — 技术设计

> 配套 `prd.md`。状态：planning（设计稿，待评审）。
> 调研依据：memory `peripheral-layer-research-findings`（两轮、34 个 research agent）。
> 一句话定位：业界把"事件送到门口"（信封 / 投递 / 鉴权）已有现成开放标准可复用；**没人**标准化"事件 → 变成 agent 的一条消息并把它叫醒"这层——**本层就是那一层**。

## 1. 架构总览

```
外部世界（email / 社媒 / webhook / 收款 / 订阅 …）
        │   每源一个 adapter（跑在常驻外设容器内）
        ▼
   归一成 IME（统一信封：{ to, text, body }，broker 落库时补 id/time）
        ▼
   inbox.append(to, ime)            ← dumb broker：塞 / 去重 / 按 to 投，绝不读 text/body
        ▼
   ┌─────────── 统一收件箱（host 侧共享 volume，抗重启）───────────┐
        ▲                                                         │
        │  goal 完成事件也 append 到同一口                          │
        │  （编排层 goal-ledger notifier，见 §6）                   │
        │                                                         ▼
   任一常驻 agent（含 CEO）—— 每个 agent 一个 inbox，进程里一个固定 harness 循环
        │  循环不断 receive() → 消息一到就当【tool 调用返回结果】喂给 agent 这一轮
        ▼
   agent 读 text/body（像读 tool 返回）→ 判断 → 用 Goal 协议派活 / 写记忆 / 回复 / 忽略
```

**每 agent 一个 inbox**：上图的"收件箱"物理上是**按 `to` 分的多个 inbox**，每个常驻 agent 一个，CEO 的是顶层那个。dumb broker 按 `to` 把 IME 路由到对应 inbox；agent 的 harness 循环只读自己那个。

**DooD 拓扑**：外设层 = `docker-compose.yml` 里一个**常驻 service**（需常开监听 / 轮询外部源），与 broker、CEO 容器平级；adapters 跑在里面；归一后写**共享 inbox volume**，不直接进 agent 容器。

**数据流一句话**：`外部源 → adapter → {to,text,body} → inbox.append → agent 的 harness 循环 receive() 的返回值`。

## 2. IME — 统一收件箱信封（the Standard Point）

**核心思想**：信封只放 dumb broker **机械要用的格** + 给 agent 看的**正文**；**其余一切扩展都写进正文 `body`，不加字段**。新外设 = 写更丰富的 body，信封形状永不变。

### 2.1 字段（就 5 格）

| 字段 | 谁读 | 说明 |
|---|---|---|
| `id` | broker | 去重 + 标记已读的句柄。**可由 broker 落库时生成**（adapter 不必管）。 |
| `time` | agent / broker | 事件发生时间（ISO-8601）。adapter 给，或 broker 落库补。 |
| `to` | **broker** | 投到哪个 agent 的 inbox；`null` = 顶层 CEO。**broker 唯一要路由的字段。** |
| `text` | agent | **非常简短**的一句（扫一眼就懂，像邮件标题）。 |
| `body` | agent | 正文：全文 / 细节 / 链接 / "回的哪件活"等关联，都 mention 在这。**内部结构 v0 freeform，以后再说。** |

> dumb broker 只碰 `id` / `to`，**永不读** `text` / `body`。agent 读 `text` 快速 triage、读 `body` 看细节。所以从 **adapter 视角产出的就是 `{ to, text, body }`**。

### 2.2 示例

外部事件：
```json
{ "id": "evt_9c2", "time": "2026-06-28T22:09:50Z", "to": null,
  "text": "新邮件：jordan 问上周发票收到没",
  "body": "来自 jordan@acme.com，主题「Invoice overdue?」。全文：blob://email/msg_AbC123#1" }
```

派的活回来了（"回哪件活"的关联写在正文里，不占字段）：
```json
{ "id": "0b7e", "time": "2026-06-28T22:14:03Z", "to": "<派活那个 agent>",
  "text": "✅「写 Q3 博客」完成了",
  "body": "你之前派的 goal 8f1c36（写 Q3 launch 博客）已通过验收。成果：company://marketing/blog/q3-launch.md" }
```

> 三种入站（外部事件 / goal 完成 / tool 结果）**信封同形**：是不是"我派的活回来了"、来源、截止时间、结构化数据…… 全 mention 在 `body`，agent 读得出来，不需要专门字段。

### 2.3 扩展靠正文，不靠字段

- 新外设要带结构化数据 → 写进 `body`（散文 +（需要的话）一个小 JSON 块），agent 自己读。
- 大负载 → `body` 里放链接，agent 按需取（不要 `ref` 字段）。
- 关联（回哪件活）、截止时间、来源、信任级别…… → 现在全 mention 在 `body`。**信封永远这 5 格。**
- 真有哪样东西将来被**实证**证明"broker / runtime 必须机械读它"，再从 body 提升为字段——按需演进，不预先拍。

## 3. inbox / broker 契约（dumb，per-agent）

每个常驻 agent 一个 inbox，按 `to` 寻址。broker 提供：

```
# 生产侧（adapter 与 goal-ledger notifier 都调它）
append(to: str | None, ime: dict) -> None       # to=None → 顶层 CEO key；落库补 id/time；去重；路由到 inbox[to]

# 消费侧（agent 的 harness 循环背后调它，见 §3.1）
poll(agent: str, timeout: float | None) -> ime | None   # 阻塞取 inbox[agent] 最老未读；超时→None
ack(agent: str, id: str) -> None                        # 推进 read-cursor（已读语义见 OQ）
```

- `to` 是**唯一** match key（机械匹配，不看 text/body）。
- **落 host 侧、绝不进 company folder**（三存储红线之外，inbox 属编排层运行时态）。抗容器重启。
- broker **不读 text/body、不做任何判断**：所有"理不理 / 怎么理"是**收件 agent** 在上下文里的临场决策。
- 存储形态（SQLite WAL / JSONL / 目录）留 OQ；建议 SQLite WAL（去重 + 有序 long-poll + 多 inbox 表最省事）。

### 3.1 `receive()` —— 消息如何到达 agent（本层定义）

**契约**：每个常驻 agent 的进程里有一个**固定的 harness 循环**：

```
while 活着:
    msg = receive(timeout)        # 阻塞，直到 inbox 被 push 进一条；超时→None（定时器地板）
    把 msg 作为一个 tool 调用的【返回结果】喂给 agent 这一轮
    agent 读 msg.text / msg.body → 判断 → 处理
```

- **agent 不需要"记得"去查收件箱**：收消息是 harness 循环的固定动作，不靠 agent 自觉——它**结构上不会变聋 / 漏收**。
- **像 tool 返回**：msg 以一个 tool 调用结果的形态进入 agent 上下文（**不是"用户发言"**）。
- **push、非轮询**：`receive()` 阻塞 long-poll，进程 parked、不空转、不耗 token；inbox 来消息由 broker 推醒。"什么时候有结果什么时候返回"——正是普通 tool 返回的语义。
- **一条一条 / 不打断**：一次返回最老一条；循环处理完才回到 `receive()` 取下一条；agent 正忙别的（在跑别的工具）时它没挂着，消息在 inbox 排队。

**关于"能不能调一次就一直收"**：LLM 的 tool 协议是**一次调用 = 一次返回**（回合制），做不到"一次订阅、无限流式回包"。但**不需要**——把 `receive()` 放进 harness 循环后，重新调用是 harness 自动做的、且每次都 parked-until-push，所以效果就是"agent 这边设好一次、消息自己不停飘回来"，而 agent 既不轮询、也不会忘记收。

**边界**：`receive()` 工具 + 上述交付契约在**本层**定义；把它跑成每个 agent 常驻进程的那个 harness 循环，在 orchestration/ceo-loop 落地（CEO loop 泛化成 agent loop）。

## 4. adapter 契约（可扩展性的"缝"）

- **adapter 唯一职责**：`原始信号 → { to, text, body }`（一句好 `text` + 正文 `body`；大负载在 body 里放链接）。核心与 agent 永不碰源的原生协议。
- **manifest 一行**：`{ name, defaultTo? }`——dumb broker 只读它取默认投递键 / 去重策略，仍不解读 text/body。
- **加一个新外设的完整流程**：写 `adapters/<name>.py`（产出 `{to,text,body}`）→ 加一行 manifest → 部署进常驻外设容器。**核心 0 改动**（= AC2）。
- **dumb adapter 无 LLM**：`text` 用模板渲染（"新邮件：X 问 Y"），全文 / 深度放 `body`（或 body 里的链接）。富源（长邮件 / 大 diff）的渲染丢失度是 OQ。

## 5. 消费模型（tool-return / push / 不打断）—— 对每个 agent 一视同仁

任一 agent 收到的东西分两类，**都以一个 tool 调用的返回值形态拿到**（不是"用户发言"）：

- **(同步、同一轮) 进程内工具调用**：`web_search(...)` 这种当轮就返回的——普通 inline tool 返回，**不过 inbox**。
- **(异步、跨轮) 一切跨 agent / 外部的东西**：派给别的 agent 的子活完成、外部事件——**进本 agent 的 inbox**，由它的 harness 循环 `receive()` 取到、作为该调用的返回递过来。是不是"我派的活回来了"看 `body`（"✅你派的X完成了" vs "新邮件…"）。

详见 §3.1（harness 循环 / push / 不打断 / 定时器地板）。

## 6. 与 CEO-loop / 编排层的统一（drop-in，非重写）

ceo-loop R3 已定：goal 终态 → 状态机在锁内 push 一条完成事件到 parent inbox。**本层让那条事件 = 一个 IME**，于是两套合一：

| ceo-loop R3 事件 | → IME |
|---|---|
| `kind: goal_done\|goal_killed` | 渲染进 `text`（"✅完成" / "✗被 kill"）/ `body` |
| `goal_id` | mention 在 `body`（"回的哪件活"） |
| `parent`（None→CEO） | `to`（null→CEO） |
| `intent` / `feedback` | 渲染进 `text`（短）/ `body`（详） |
| `ts` | `time` |

- 落地 = `goal_ledger.py` 的 notifier 改成"构造一个 IME 并 `inbox.append(to, ime)`"，**不是重写**（R3 的 `append(parent_key, event)` 契约不变，`event` 升级成 IME）。
- **回答 ceo-loop R4 的 open question**：inbox **就此长成统一口**——外设层信号与 goal 事件同一套收件箱、同一信封、同一 receive 路径。
- **多层 goal 树自然解决**：所有 agent 常驻 + 各有 inbox → `parent` 是哪个 agent，完成事件就进**那个 agent 的 inbox**（不再只有 CEO 这条路）；ceo-loop 列的"parent 是仍存活 worker"OQ 在此收口——它就是 `to=<那个 worker>` 的普通一例。

## 7. 扩展性（为什么"加新外设零改核心"成立）

1. **信封固定 5 格，永不为新外设加字段**：新外设带的任何额外信息都写进 `body`（散文 / 小 JSON 块 / 链接），agent 自己读。
2. **加一个新外设 = 写一个把"原始信号 → {to,text,body}"的小 adapter + 部署**。核心 0 改动（= AC2）。
3. **broker 只认 `id`/`to`，对任何 `text`/`body` 内容免疫**，所以新外设天然不碰它。
4. **按需演进**：将来若某样东西被**实证**证明"broker / runtime 必须机械读"，再从 body 提升为字段——不预先拍一堆"以后也许用得上"的字段（这正是上一版过度设计、本版砍掉的教训）。

## 8. 已知风险 / 边界（v0）

- **安全四项 v0 故意不管**（见 prd「已知风险」）：注入 / 信任传染 / 顺序一致性 / 限流。碰真钱前必补。
- **同步 / 会话 / 流式不接**（见 prd 决策 1）：将来由各自 adapter 在边缘扛实时，处理完只投"已发生的事"进本收件箱。

## 9. 关键取舍记录

- **tool-return 而非 user-message**：系统事件 / peer 完成不是"人在说话"；按 tool 返回喂，语义更准，且与"派活回来"天然同形（Anthropic 本就把 tool_result 当一条消息追加）。
- **harness 循环驱动 receive，而非 agent 自觉**：LLM 回合制做不到"调一次无限收"；放进固定循环 = 效果等价 + agent 不会漏收。
- **push = parked-await 而非轮询**：一次 `receive()` 调用 + parked，事件推醒。
- **信封砍到 5 格、扩展进正文**：我们是一家公司内部、唯一一个消费者（agent 读 text/body），不是多厂商互操作；预先加结构化字段是过度设计，统一收进 `body` + 按需演进。
- **只异步**：同步 / 流式现在没有消费端，留接口=留债。
