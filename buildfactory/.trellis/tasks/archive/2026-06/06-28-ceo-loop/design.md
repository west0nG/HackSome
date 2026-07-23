# CEO Orchestration Loop — 技术设计（MVP）

> 配套 `prd.md`。目标 = 让 CEO 真正跑起来的最小闭环。本设计落在现有编排层真实接口上，尽量**集成而非重写**。

## 1. 范围与边界

**本任务新增/改动：**
- `orchestration/inbox.py`（新）：inbox 接口 + 最小文件 stub。
- `orchestration/goal_ledger.py`（改）：`GoalLedger` 注入可选 `notifier`；`pass_verify` / `kill` 终态时发事件。
- `orchestration/goal_pump.py`（新）：常驻 claim→drive 循环（包已有 `run_goal`）。
- `orchestration/ceo_loop.py`（新）：CEO 唤醒循环（盯 inbox + heartbeat → `claude -p --resume`）。
- `orchestration/goal_cli.py`（新）：CEO 在容器内派活的原语（`add`）。
- `agents/ceo.yaml`（新）：CEO 声明式 loadout（charter + goal skill；无 record hook 顾虑同 verifier 另说，见 §3.4）。
- `docker-compose.yml` / `Makefile`（改）：加 `ceo` 常驻服务、pump 进 broker、一键。

**复用、不动：** `broker.spawn/teardown`、`run_goal`、`make_execute_fn` / `make_verify_fn` / `resolve_role_spec`、verifier/company-operator 路径、memory 层 `/company` 挂载。worker 仍用完即拆。

**仍排除（prd Out of scope）：** scratchpad、外设层信号、CEO 自写条件集、复杂成本闸、judge 判断力、inbox 统一架构落地。

## 2. 拓扑（compose）

```
host: dockerd + `make up`
常驻容器:
  broker  (DooD, 挂 docker.sock)  ──► 跑 goal-pump；spawn worker(兄弟容器)
  ceo     (cua-agent 镜像, 无 sock) ─► 跑 ceo_loop；只 claude --resume + 写 ledger
临时容器:
  worker  (cua-agent, 用完即拆)     ◄─ broker 起
共享 volume:
  ledger/   (goal 状态机)   inbox/   (本任务新增)   companies/<id>/ (company memory)
  ceo 专属:  ~/.claude 持久卷 (claude 会话 transcript → resume 续上)
```

CEO 容器**不挂 docker.sock**：它只思考、写 ledger，不 spawn worker（spawn 归 broker）。这既是隔离也是职责划分。CEO 用 cua-agent 同一底层镜像（同构），但 `command` 覆盖成跑 `ceo_loop.py`，不需要桌面/`:8000`。

## 3. 组件与契约

### 3.1 Inbox（接口 + stub，架构留空）

契约（`orchestration/inbox.py`，`Protocol`）：
```python
class Inbox(Protocol):
    def append(self, key: str, event: dict) -> None: ...      # 生产侧（状态机）
    def poll(self, key: str, timeout: float) -> list[dict]: ...# 消费侧：阻塞至有事或超时；返回未读事件（空=heartbeat 触发）
```
- `key`：parent goal id；顶层 goal（`parent is None`）→ 约定常量 `CEO_KEY = "ceo"`。
- `event`：`{"kind": "goal_done"|"goal_killed", "goal_id", "parent", "intent", "feedback", "ts"}`。
- **MVP stub = `FileInbox`**：`<inbox_root>/<key>.jsonl` append；`<key>.cursor` 记已读偏移；`poll` 轮询新行至 timeout。host 侧、独立 store、**绝不进 company folder**（三存储红线）。`inbox_root` = env `GOAL_INBOX`，默认 `orchestration/inbox`（运行时态、不进 git，同 ledger）。
- **留接口**：存储形态 / `key` 归一 / 是否长成承载外设层信号的统一 inbox —— 全部不在本任务锁定，`Inbox` 协议后面可整体换实现。

### 3.2 状态机 notifier（goal_ledger 改动 = 不变式）

`GoalLedger.__init__(self, root=None, notifier=None)`：`notifier: Callable[[str, dict], None] | None`，默认 `None`（no-op）→ 现有 84 测试不受影响。

终态转移内发事件（状态已落盘后调一次）：
- `pass_verify`（→done）：`_emit(goal, "goal_done")`
- `kill`（→killed）：`_emit(goal, "goal_killed")`

```python
def _emit(self, goal, kind):
    if not self._notifier: return
    key = goal["parent"] or CEO_KEY
    self._notifier(key, {"kind": kind, "goal_id": goal["id"], "parent": goal["parent"],
                         "intent": goal["intent"], "feedback": goal.get("feedback"), "ts": _now()})
```
- 放进状态机 = **不变式**：任何到达终态的路径都必通知 parent，调用方无法遗漏（prd R3 的核心理由）。
- notifier 在 ledger 锁外、状态持久化后调用（inbox 有自己的锁，避免跨 store 锁序问题）。
- 单元测试用 fake notifier（记录调用），不碰 docker。

### 3.3 goal-pump（claim → drive → 终态通知）

`orchestration/goal_pump.py`：常驻循环，跑在 broker 容器内（有 docker.sock）。
```
ledger = GoalLedger(notifier=FileInbox().append)      # ← 终态 push 进 inbox
while True:
    goal = ledger.claim_open_goal(worker_id="pump")    # 原子认领最老 open
    if goal is None: sleep(poll_interval); continue
    execute_fn = make_execute_fn(exec_op, company_id, spec=resolve_role_spec(goal["role"]))
    verify_fn  = make_verify_fn(verify_op, company_id)
    run_goal(ledger, goal["id"], execute_fn, verify_fn)  # → pass_verify/kill → notifier 发事件
```
- 复用 `goal_runtime` 全部现成件；pump 只是把 `run_goal_e2e` 的"一次性 add+claim+drive"拆成"持续 claim+drive"（add 由 CEO 做，见 3.5）。
- MVP 串行（一次一个 goal）即可满足 AC；并发留后。

### 3.4 CEO 容器 + ceo_loop

CEO 容器 = cua-agent 镜像 + `command: python -m orchestration.ceo_loop`。挂载：ledger(rw)、inbox(rw)、companies(ro 够用，CEO 只读公司态做决策)、`goal_cli`/skill、`~/.claude` 持久卷、`CLAUDE_CODE_OAUTH_TOKEN`(env_file)。

`ceo_loop.py` 主循环：
```
session = load_or_none(SESSION_FILE)
while True:
    events = inbox.poll(CEO_KEY, timeout=HEARTBEAT_SECS)   # 有事或到点返回
    prompt = build_wake_prompt(events)                     # 列出完成/失败的 goal；空=idle 巡检
    session = wake_ceo(session, prompt)                    # claude -p (--resume session | --session-id new)
    # CEO 进程内自行用 goal_cli 派活；这里无需额外动作
```
- `wake_ceo`：首次 `session is None` → `claude -p --session-id <new>`，记 id 到 `SESSION_FILE`（持久卷）；之后 `claude -p --resume <id>`。每次唤醒 = 新 claude 进程、resume 续盘上会话（连续性靠 Claude 原生会话 + auto-compact，**无 scratchpad**）。
- CEO loadout（`agents/ceo.yaml`）的 skill/charter 在容器启动时 `materialize` 进 `~/.claude`，resume 时已就位。
- heartbeat 间隔 = env，默认 1800s（待调）；它同时是 MVP 成本闸下限。

### 3.5 CEO 派活原语（goal_cli）

`orchestration/goal_cli.py`：薄 CLI，CEO 容器内可执行，`add --intent "<结果>" [--role <r>]` → `GoalLedger.add_goal(intent, role=role)`（写 open goal，parent=None）。CEO 的 charter/skill 告诉它"派活就 `goal add ...`"。CEO **不** drive、不 spawn —— 写完 ledger 就完事，pump 接手。

### 3.6 resume 机制（provider 复用 or 直调）

CEO loop 在容器内**直接**调 claude（不走 `run_task` 的 docker-exec 路径，因为它已在容器内）。argv：
```
claude -p "<prompt>" [--resume <id> | --session-id <new>] --output-format stream-json --verbose --dangerously-skip-permissions [--mcp-config ...]
```
`--resume` 当前 `provider.py` 未覆盖（只有 `--session-id`，line 58）。MVP 在 ceo_loop 内自建 argv 即可；是否回填进 `provider`/`runner` 统一成一条路 = 后续重构，不阻塞。

## 4. 数据流（端到端时序）

**A. heartbeat 唤醒（AC2）**：无事件 → `inbox.poll` 超时返回 `[]` → CEO 被 resume、空巡检、睡回。

**B. goal 完成唤醒（AC3）**：（seeded）open goal → pump claim+drive → worker 写 /company → verify PASS → `pass_verify` → notifier `append("ceo", goal_done)` → CEO loop `poll` 立即返回该事件（不等满 heartbeat）→ CEO resume、看到结果。

**C. 零人自治闭环（AC5）**：CEO 唤醒中 `goal add`（open, parent=None）→ pump claim+drive→done→notifier→inbox→CEO 下次 poll 醒来收结果。**派活→完成→回醒** 全程零人。

## 5. 三存储边界

| store | 性质 | 位置 | 本任务 |
|---|---|---|---|
| company memory | 静态名词（成果） | `companies/<id>/` (容器内 `/company`) | 不动 |
| goal ledger | 编排派发记录 | `orchestration/ledger/` | 加 notifier |
| **inbox** | 编排运行时事件（动词） | `orchestration/inbox/` | **新增、host 侧、绝不进 company folder** |

CEO 会话态（`~/.claude` transcript）= 第四类运行时态，挂 CEO 专属持久卷，亦不进 company folder。

## 6. 兼容性

- `notifier` 默认 None → 现有 84 单测、`run_goal_e2e` 行为不变。
- broker / worker / verifier / memory 挂载路径零改动。
- pump 与 `run_goal_e2e` 共用 `run_goal`，逻辑一致（后者保留作手动 e2e 入口）。

## 7. 取舍与备选

- **CEO 自跑 loop（选）vs broker exec 进 CEO（备）**：选前者 —— 贴 memory 拓扑（CEO 是独立常驻容器）、CEO 无 sock 更隔离。代价：CEO 容器 `command` 覆盖、需 ~/.claude 持久卷。
- **pump 串行（选）vs 并发**：MVP 串行够用，少并发 bug；并发后置。
- **goal_cli（选）vs MCP tool 派活**：CLI 最薄、零新协议；MCP 后续可包。
- **inbox 文件 stub（选）vs 即上统一 inbox**：接口先行、实现最小，守"留接口"。

## 8. 回滚

每 increment 独立 commit。inbox/pump/ceo_loop 均为**新增文件**，回滚 = revert 该 commit；`goal_ledger` 的 notifier 是**纯增量**（默认 None），revert 不影响既有协议。compose 的 `ceo` 服务可单独 `down` 不影响 broker。
