# 技术设计 — 聪明中枢 Hub（child②）

> 基线（已对照通过的单测核实真实接口）：`orchestration/{agent_loop,inbox,goal_ledger,goal_loop,goal_runtime,goal_pump,messaging}.py`。
> 本文只装技术设计；需求 / 约束 / AC 见 `prd.md`，执行清单见 `implement.md`。调研依据见 `research/async-state-machine-survey.md`。
> ⚠️ 重要前提：现有 `goal_ledger` **已经是完整确定性状态机**（见 §4），child② 大部分是「接线」而非「重建状态机」。

## 1. 架构总览

新增一个常驻进程 **Hub**（key=`hub`），是 5 个 LLM agent 之外的第 6 个常驻实例。所有 agent 间消息都先到 `hub`，由 Hub 持有 ledger + 转投。Hub 是**非 LLM 的确定性 Python**，不 spawn 容器、不做业务判断。

```
              ┌─────────────── hub (确定性, ledger 单写者 + notifier→inbox) ──────────────┐
 CEO ─send──▶ │ add_goal(parent=ceo,role=researcher) → claim → 转投 researcher           │ ─▶ researcher
              │ ◀── researcher report ── to_reported → to_verifying → 转投 ──────────────┼─▶ verifier
              │ ◀── verifier VERDICT ─── parse_verdict:                                   │
              │       PASS → pass_verify → (notifier 自动通知 parent=ceo) ────────────────┼─▶ CEO
              │       FAIL → fail_verify(feedback); should_kill? kill(notifier) : 重投    │ ─▶ researcher / CEO
              │ sweep tick: 扫 deadline，running/verifying 超时 → 失败尝试 / kill          │
              └───────────────────────────────────────────────────────────────────────────┘
```

**关键不变式**：部门所有出站消息都进 `hub`，**物理上到不了 CEO**；且 ledger 只有 Hub 进程能写。因此「干完=直接告诉 CEO done」结构上不可能——只有 Hub 在独立 verifier `PASS` 后经 `pass_verify` 触发 `notifier` 才把完成通知转给来源（`parent`）。这是 doer≠judge 的代码级强制。

## 2. 组件边界

| 组件 | 职责 | 明确不做 |
|---|---|---|
| **Hub** | 路由转投、驱动 ledger 转移、编排验收、watchdog/sweep、崩溃对账、`notifier`→inbox 接线 | 不跑 LLM、不 spawn、不判断「派什么活 / 上层 goal 是否达成」 |
| CEO / 部门（LLM agent_loop 实例） | 业务决策、干活、`messaging send/report` | 不直接投递给对方、不写 ledger、不自判 done |
| Verifier（LLM agent_loop 实例，read-only） | 读 `/company` 判 `VERDICT: PASS/FAIL` | 不重做工作、无 record hook（沿用 `agents/verifier.yaml`） |
| `goal_ledger` | 已有的完整确定性状态机 + 终态 notifier seam | 唯一写者是 Hub 进程 |

**Hub 与 `agent_loop` 的关系**：抽出共享循环骨架 `poll(key,heartbeat) → handler(events) → sleep`。LLM 实例 handler = 现有 `build_wake_prompt`+`wake`+`save_session`（claude 子进程）；Hub handler = 确定性 `hub_handler`。保住「人人都是一个 loop 实例」，Hub 唯一不同是 handler 不 spawn claude。

## 3. 消息路由：投递路径回改（child① → Hub）

child① 现状：`messaging.send/report` 直接 `inbox.append(对方key, IME)`。改为**第一跳一律投 `hub`**，真实 `to/reply_to/goal_id` 写进 IME `body`（IME 保持 5-field，不加信封字段）。

```
messaging.send(to, intent, reply_to=self)
  → inbox.append("hub", ime(to="hub", body="DISPATCH to=<to> reply_to=<self> :: <intent>"))
messaging.report(to, summary, goal_id)
  → inbox.append("hub", ime(to="hub", body="REPORT goal=<goal_id> to=<to> :: <summary>"))
```

- agent 心智模型不变（charter 仍写 `send --to researcher` / `report --to ceo`），只物理首跳进 Hub。
- Hub 解析 body 的 `DISPATCH/REPORT/VERDICT` 前缀决定动作；解析失败 = fail-loud（记一条审计），不静默丢。
- Hub 第二跳转投 / `notifier` 回投：`inbox.append(真实目标key, IME)`（渲染成部门/CEO/verifier 可读的 text+body）。
- **goal 类消息**（DISPATCH/REPORT/VERDICT）驱动状态机；**其余业务消息**（部门间协调、闲聊）Hub 仅透明转发 + 审计，不碰 ledger。

## 4. 复用现有状态机 + 唯一新增（deadline）

`goal_ledger` 真实 API（已被通过的单测锁定，**不重建**）：

```
状态: open → claimed → running → reported → verifying → done | killed
       (verify-fail: verifying → running, attempts++, feedback)
方法: add_goal(intent, parent=None, role=None) → id   # parent=来源, role=执行部门(R7)
     claim(id, worker)→bool / claim_open_goal(worker)→goal
     start_run(id, EXECUTE|VERIFY)→run_id / finish_run(id, run_id, ok, summary)
     to_reported(id) / to_verifying(id)
     pass_verify(id)              # verifying→done, 自动 _emit(EVENT_DONE) 给 parent
     fail_verify(id, feedback)    # verifying→running, attempts++ (不自动 kill)
     should_kill(id, max)→bool / kill(id, reason)  # →killed, 自动 _emit(EVENT_KILLED)
     notifier(key, event): 终态自动调用，key = parent or CEO_KEY
```

**「通知来源」无需新增字段**：`add_goal(parent=<来源key>)` + 现成 `notifier` seam。Hub 构造 ledger 时注入 `notifier = lambda key, ev: inbox.append(key, _ime_from_event(ev))`——`pass_verify`/`kill` 触发即把终态 IME 投回来源 inbox。**「执行部门」= `role`/`assignee`**，retry 重投 `assignee`。

**唯一 ledger 改动 = 异步超时**（同步 `run_goal` 没有、异步世界新增的失效面）：

1. 新增 `deadline` 字段：进入 `running`/`verifying` 时写 `now + timeout`；其余转移清空/顺延。
2. 新增超时处理（`fail_verify` 要求 `verifying` 前态，无法覆盖 `running` 超时）：
   - 落成 ledger 方法 `time_out(id, max_attempts)`：从 `running`/`verifying` → 当作一次失败尝试（`attempts++` + `feedback="timed out"`），`should_kill` 则 `kill`，否则回 `running` 待 Hub 重投 `assignee`。
   - deadline 持久在 ledger → Hub 重启扫一遍即恢复超时判定（借 Temporal durable-timer 思想，时间戳+sweep，不引框架）。

| 收到事件（hub inbox） | 守卫前态 | Hub 调用序列 | 转投/通知 |
|---|---|---|---|
| DISPATCH | （新 goal） | `add_goal(parent,role)`→`claim` | append intent 给 `role`/assignee |
| REPORT | claimed/running | `to_reported`→`to_verifying` | append 验收请求给 `verifier`（reply_to=hub） |
| VERDICT PASS | verifying | `pass_verify` | notifier 自动投 parent |
| VERDICT FAIL | verifying | `fail_verify`；`should_kill`?`kill`:重投 | 重投 assignee(带 feedback) / kill→notifier |
| sweep 超时 | running/verifying | `time_out(max)` | 重投 assignee / kill→notifier |

所有转移仍走 `_require` 守卫 + 目录 flock；非法跳转抛 `GoalError`（被 Hub 当「已应用，跳过」→ 幂等）。

## 5. 验收分权

- 部门 `report` → 物理到 Hub → Hub `to_reported`+`to_verifying` → 投 verifier。部门**拿不到** `pass_verify`（它不写 ledger、消息也到不了 CEO）。
- verifier 是独立 agent_loop 实例，读 `/company`，输出经 `goal_runtime.parse_verdict`（复用现有 `VERDICT: PASS / FAIL: <reason>` 闸门）→ Hub 据此 `pass_verify` / `fail_verify`。
- FAIL 的 `reason` 经 `fail_verify` 存入 `goal.feedback`，下次重投经 `goal_runtime.build_task` 注入执行 prompt（续 context、非重起）= 用户要的「打回带一条消息」。

## 6. watchdog

两套，全在 Hub、状态写 ledger：

1. **attempts / retry / kill（复用现有原语）**：`fail_verify(feedback)`（→running, `attempts++`）→ Hub 查 `should_kill(id, max_attempts=3)` → 真则 `kill(reason)`（触发 notifier），否则重投 `assignee`。默认 3 可调。
2. **deadline / liveness（§4 新增）**：Hub 每个 tick `list_goals` 扫非终态，`now > deadline` 者调 `time_out(id, max)`（重投或 kill）。兜「部门 hang 住永不回报」。

## 7. 崩溃可恢复（AC5）

Hub **内存无状态**，状态全在 ledger。两层防护：

1. **reconciliation（启动 + 每 tick）**：对每个非终态 goal 从 `status` 推「下一步」并**幂等重发**：
   - `claimed`/`running` 且超 deadline 或无在途 → 重投 `assignee`；`verifying` → 重投验收请求；
   - 重发 IME 用确定性 id（`goal_id:status:attempts`）→ 命中 inbox `.seen` 去重，常驻 agent 不重复执行；
   - K8s controller「desired vs actual 对账」思路，比 event-replay 简单稳。
2. **ack-after-process（防丢 REPORT 事件）**：现 `poll_one` 读取即推进 cursor——Hub 在「cursor 已进、ledger 未写」间崩则事件丢。给 Hub 消费侧加**非推进读 + 显式 `ack`**（处理完落 ledger 才 `ack`）。crash 则重投，靠 `_require` 状态层幂等兜。单纯 reconciliation 补不回丢失的 REPORT（ledger 仍 running），由 §6 deadline sweep 兜底重投。

**dual-write**：ledger 写与 inbox append 非原子。不引事务，靠「reconciliation 幂等重发」吸收 = 接受 at-least-once + 幂等而非追求 exactly-once 的明确取舍。

## 8. 兼容 / 回滚

- `goal_pump.py` / `goal_loop.run_goal` / `goal_runtime`（同步 claim→drive）：保留在树（已 stood-down），Hub 是其异步重生。回滚 = 重新激活旧路径、Hub 下线。
- ledger 改动**纯增量**（加 `deadline` 字段 + `time_out` 方法），现有方法签名/语义不动 → 现有 ledger 单测原样通过（AC7 无退化）。
- 需回填（落地后）：父任务 AC-P3 / `goal_pump 退役`表述、child① spec `resident-agent-contracts.md`「no central pump」节注明业务经 Hub。

## 9. 测试策略 + fail-loud 注入项

- **纯单测（无 docker/token）**：① ledger 增量（`deadline` 字段、`time_out` 各前态、不破坏现有转移）；② Hub body 解析（DISPATCH/REPORT/VERDICT + 解析失败 fail-loud）；③ `hub_handler` 事件→ledger 调用→转投 IME 映射；④ `notifier`→inbox 接线（终态投对 parent）；⑤ reconciliation 幂等（重发 id 去重）；⑥ messaging 改投 hub 后 IME 形态。
- **现有测试迁移**：`goal_pump`/`run_goal`/`goal_runtime` 测试标停用路径；ledger/inbox/messaging/agent_loop 现有单测保持绿（纯增量，理应不破）。
- **gated e2e（PAID，自动跑，§见 implement Step 6）**：CEO→hub→researcher→hub→verifier→hub→CEO 全闭环；FAIL 重投续 context；`should_kill` kill。
- **fail-loud 故障注入**：① 「to_verifying 后、投验收请求前 kill Hub」→ 重启后 reconciliation 正确补投验收；② 部门 hang 超 deadline → sweep 重投/kill；③ 重复投递（同 goal_id 重发）被 `.seen` + `_require` 双重幂等吸收，不重复执行。
- 任一不成立显式报错，不静默回退旧 pump。

## 10. 崩溃安全加固（2026-06-30 code-review 后修订）

首轮实现的 ack-after-process 对**状态变更类动词**（DISPATCH/REPORT）不是真正幂等——崩溃在「处理后、ack 前」会重投并被按新状态重新解读（评审 #1/#2）。加固为四道防线，AC5「不丢、不重复执行」由它们共同保证：

1. **发送者身份门（`from`）= doer≠judge 的结构强制（#4）**：REPORT 现带 `from=<AGENT_KEY>`。`running` 态只接受 `from==assignee` 的工作回报，`verifying` 态只接受 `from==verifier` 的 verdict；其余一律 audit 丢弃。所以「部门发一条含 `VERDICT: PASS` 的报告自我认证」结构上不可能，且一条**错相位重投**的报告（工作回报落到 verifying / verdict 落到 running）被身份门挡掉，不会被错误解读。
2. **确定性 dispatch goal id + 幂等 `add_goal`（#2）**：goal id 由 dispatch 消息 id 派生；`add_goal(goal_id=...)` 已存在则 no-op。重投的 DISPATCH 不再造出第二个 goal。
3. **已处理 id 集合（`hub.processed`，idempotent-consumer 模式，#1）**：`hub_drain` 处理前查、处理后记、再 ack。已处理事件重投直接跳过。残留微窗（处理后、记录前崩溃）由第 1/2 道防线兜成「安全丢弃 / 幂等」而非「错误解读」。
4. **reconcile 归一化 + 终态补发（#6/#5）**：reconcile 把半途转移（`claimed→running`、`reported→verifying`）推进到位，避免崩在 dispatch/report 中段卡死；并对终态 goal **补发一次** done/killed 通知（`notified` 标记 + 确定性 `gid:kind` id 去重），堵住「终态写了、通知 append 崩了」导致 CEO 永远收不到完成的洞（AC6）。

> 诚实边界：file-based 无事务，真正的 exactly-once 不可得。上述把危险的「重投→错误解读/双执行」降级为「安全丢弃→deadline sweep 兜底重试」+「幂等重投」。`_route_id` / 终态 id 的确定性 + `.seen` 去重是这套幂等的载荷点。
> 回归测试：`tests/test_hub_crash_safety.py`（重投 DISPATCH 不重复建 goal、已处理事件跳过、错相位报告被身份门挡、reconcile 归一化 claimed/reported、终态通知补发）。
