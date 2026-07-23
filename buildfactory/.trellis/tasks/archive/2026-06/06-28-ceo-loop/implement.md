# CEO Orchestration Loop — 执行计划（MVP）

> 配套 `prd.md` / `design.md`。分 5 个增量，**先纯逻辑（便宜、可单测）→ 再 de-risk resume → 再接闭环 → 最后打包一键**。每增量独立 commit，可单独回滚。

## 增量 1 — inbox 接口 + 状态机 notifier（纯 Python，无 docker）

最便宜、解锁后续。

- [ ] 1.1 `orchestration/inbox.py`：`Inbox` Protocol（`append` / `poll`）+ `FileInbox` stub（`<root>/<key>.jsonl` + `.cursor`，`poll` 轮询至 timeout）+ 常量 `CEO_KEY="ceo"`。`root` = env `GOAL_INBOX`，默认 `orchestration/inbox`。
- [ ] 1.2 `goal_ledger.py`：`__init__` 加 `notifier=None`；加 `_emit`；`pass_verify` / `kill` 末尾各调一次（状态落盘后）。引入 `CEO_KEY`（从 inbox 或本地常量）。
- [ ] 1.3 单测：`tests/test_inbox.py`（append→poll 取回、cursor 已读不重取、空 poll 超时返回 `[]`）；`tests/test_ledger_notify.py`（fake notifier：done/killed 各发一次、字段正确、parent=None→"ceo"、parent 有值→该 id；**notifier=None 时零调用**）。

**验证**：`python -m pytest orchestration/tests -q` 全绿（含原 84 + 新）。
**门槛（AC6）**：现有 84 测试不破；done+killed 必通知。
**回滚**：revert 本 commit；notifier 默认 None，对既有协议零影响。

## 增量 2 — resume 验证 + ceo_loop 骨架（heartbeat-only，真容器）

**最大未知先 de-risk**：证明 `claude -p --resume` 能 headless 续上下文。

- [ ] 2.1 **resume 验证闸（先做，独立验证）**：手动在一个 cua-agent 容器内：① `claude -p --session-id S "记住数字 42"`；② `claude -p --resume S "我刚让你记的数字是多少"` → 输出含 42。**不过则停下来重新设计连续性方案**（退路：`--continue` / 自带上下文）。
- [ ] 2.2 `orchestration/ceo_loop.py`：主循环 = `inbox.poll(CEO_KEY, HEARTBEAT_SECS)` → `build_wake_prompt(events)` → `wake_ceo`（首次 `--session-id` 新建并存 `SESSION_FILE`，后续 `--resume`）。`HEARTBEAT_SECS` = env，默认 1800。
- [ ] 2.3 `agents/ceo.yaml`：CEO loadout（charter：你是 CEO、只思考+派活、派活用 `goal add`；含 goal skill；`bypass_permissions: true`）。
- [ ] 2.4 本地手测（heartbeat-only）：起一个 CEO 容器跑 ceo_loop，无事件 → 看日志按 HEARTBEAT 周期 resume-唤醒-睡；连续 ≥2 次唤醒确认是**同一 session**（CEO 记得上次说过的话）。

**验证**：2.1 输出含 42；2.4 日志显示周期唤醒 + resume 续上。
**门槛（AC1/AC2/AC4）**：CEO 容器常驻、heartbeat 唤醒、resume 生效。
**回滚**：revert；ceo_loop / ceo.yaml 为新增。

## 增量 3 — goal-pump，接通"事件唤醒"

- [ ] 3.1 `orchestration/goal_pump.py`：常驻循环 `claim_open_goal("pump")` → `run_goal(ledger, id, make_execute_fn(..., resolve_role_spec(goal["role"])), make_verify_fn(...))`；`ledger = GoalLedger(notifier=FileInbox().append)`。串行 + `poll_interval` sleep。
- [ ] 3.2 在 broker 容器内起 pump（compose `command` 或 supervisor，见增量 5；本步可先手动 `docker compose exec broker python -m orchestration.goal_pump`）。
- [ ] 3.3 端到端（seeded）：`goal add` 一条 → pump 自动 claim+drive→done → 状态机 push 进 CEO inbox → CEO loop **在事件下**（不等满 heartbeat）被唤醒、wake prompt 含该 goal 结果。

**验证**：真实 e2e 一次（付费、需 `CLAUDE_CODE_OAUTH_TOKEN`）：seeded goal → done → CEO 事件唤醒日志可见。
**门槛（AC3）**：goal 完成事件驱动唤醒、CEO 看得到结果。
**回滚**：revert；pump 为新增、与既有 `run_goal_e2e` 并存。

## 增量 4 — CEO 派活原语 + 全闭环（AC5）

- [ ] 4.1 `orchestration/goal_cli.py`：`add --intent "<结果>" [--role <r>]` → `GoalLedger.add_goal`。挂进 CEO 容器、charter/skill 指明用法。
- [ ] 4.2 零人闭环 e2e：给 CEO 一个触发（如 inbox 注入一条"请启动 X"或首次冷启动 prompt）→ CEO 唤醒中**自己** `goal add` → pump 驱动 → done → 通知 → CEO 下次醒来收结果。全程零人。

**验证**：真实 e2e：CEO 自派 goal→worker 干→验收→CEO 回醒收结果，日志/ledger/inbox/company memory 四处可对账。
**门槛（AC5）**：派活→完成→回醒 零人闭环跑通。
**回滚**：revert goal_cli + charter 改动。

## 增量 5 — 打包一键（compose 服务 + Makefile）

- [ ] 5.1 `docker-compose.yml`：加 `ceo` 服务（cua-agent 镜像、`command: python -m orchestration.ceo_loop`、挂 ledger/inbox/companies/`~/.claude` 卷/env_file，**不挂 docker.sock**）；broker 服务跑 pump（command 或入口脚本同时拉起 pump）。
- [ ] 5.2 `Makefile`：`up` 起 broker(+pump)+ceo；`logs-ceo` 等便捷；`down` 全拆。
- [ ] 5.3 一键验收：`make up` → 三类容器就位 → 重跑增量 4 闭环 → `make down` 干净。

**验证**：`make up` 后 `docker compose ps` 见 broker+ceo 常驻；闭环 e2e 通过；`make down` 无残留。
**门槛**：一键起停 + 闭环在 compose 下复现。
**回滚**：revert compose/Makefile 改动；不影响 §增量 1–4 的代码。

## 全局验证（最后一轮全量）

- [ ] 单测全绿（原 84 + 新增 inbox/notify）。
- [ ] AC1–AC6 逐条对账（prd 验收表）。
- [ ] 三存储红线复查：inbox 在 `orchestration/inbox/`、**不在** `companies/`；CEO 会话态在专属卷。
- [ ] `goal_ledger` notifier 默认 None 路径仍存在（既有 e2e 入口不破）。

## 风险与退路

- **resume 不支持 headless 续接** → 增量 2.1 提前暴露；退 `--continue` 或每次冷启动 + 轻量态注入（但这会把 scratchpad 拉回来，尽量避免）。
- **inbox 文件 poll 抖动/竞态** → stub 用 append-only jsonl + cursor，单消费者（CEO）无并发读；pump 单写 per key。
- **pump 与 CEO 抢 ledger 锁** → ledger 已有 flock 串行化，天然安全。
