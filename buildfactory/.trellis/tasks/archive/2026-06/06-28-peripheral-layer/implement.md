# Peripheral Layer — 执行计划（implement）

> 配套 `prd.md` + `design.md`。状态：✅ done（Phase 0–6 全部完成、PR #193 已合并）。
> 原则：自底向上，每个 Phase 独立可测、可回滚；现有编排核心全程保持绿。
>
> **实现状态（2026-06-29 session）：Phase 0–6 全部完成并验证。** `make_ime`/`poll_one`/`receive()`/id 去重（`inbox.py` + `receive_tool.py`）、email + webhook 两个 adapter（`peripheral/`）、goal-ledger→IME 接线（`goal_inbox.py` + `goal_pump.py:64`）、常驻 `peripheral` 容器（compose）。全量 **141 passed**（原 117 + 新 24），HTTP push 路径冒烟通过。存储沿用 **JSONL+cursor**（不引 SQLite，Gate A 已定）。
>
> **Live e2e（真 LLM `claude`）也跑过并通过**：单条 / 多条 / 不同时间分批 / **处理中到达**（时间戳证明 B 在 A 处理途中到达、被缓冲、下一轮才处理、不丢不打断）/ 跨唤醒 `--resume` 记忆（agent 把后到的付款与先前的投诉/发票主动关联）均正常。Live 测试额外**抓出并修掉 2 个单测漏掉的集成 bug**：① `goal_pump` 发 IME 但 `ceo_loop.build_wake_prompt` 还按旧格式渲染（commit 7cdd6c2）；② IME prompt 以 `-` 开头被 `claude -p` 当成 CLI 选项 → 每次 IME 唤醒 rc=1（commit c547806）。并发缓冲行为已落确定性单测（`test_inbox.py`）。
>
> 已知小限制（留后续）：`<key>.seen` 去重表随见过的 id 无限增长——低量 v0 可接受，长跑需加界 / TTL。

## 依赖现状（已就绪 / 待协调）

- ✅ Goal 协议（`06-26-orchestration-layer`，done）：派活 / 验收 / DooD / role 定向派活。
- ✅ `docker-compose.yml` 有常驻 `broker` service（可挂新 inbox volume）。
- 🔧 `goal_ledger.py` 的 `pass_verify` / `kill` 已留**可选 notifier 钩子**（ceo-loop R3，默认 no-op）——Phase 5 给它接上"构造 IME 并 append"。
- ⏳ **agent 常驻 harness 循环**正式实现属 `06-28-ceo-loop`（CEO loop 泛化成 agent loop）；本任务自带一个**最小 harness 脚手架**用于 e2e 自测，生产循环由 ceo-loop 复用本层的 `receive()` + 契约。

## 建议代码布局（最终可微调）

```
orchestration/inbox.py        # inbox 实现（append/poll/ack）+ IME helper —— inbox 属编排层运行时态
orchestration/receive_tool.py # receive() 工具（包在 poll 之上）
peripheral/adapters/<name>.py # 每源一个 adapter：native → {to,text,body}
peripheral/manifest.*         # adapter 注册（name/defaultTo）
peripheral/runner.py          # 常驻外设容器入口：跑 adapters、写 inbox
tests/                        # 单测 + e2e
```

## 执行顺序

### Phase 0 — 契约骨架
- [x] `make_ime(to, text, body) -> dict`：产出 5 格信封；`id`/`time` 由 inbox 落库时补。
- [x] 轻量校验：必有 `to`(可 None)/`text`/`body`；broker 不校验内容。
- [x] 定义 inbox 抽象接口（`append` / `poll` / `ack`）。
- **验证**：`pytest tests/test_ime.py`（构造 + 校验）。 **AC**：— （为后续铺垫）

### Phase 1 — inbox 实现（dumb broker，per-agent）
- [x] **JSONL+cursor**（沿用现有 `FileInbox`，非 SQLite）落 host 侧共享 volume（**绝不进 company folder**）；多 inbox 按 `to` 分（`<key>.jsonl`）。
- [x] `append(to, ime)`：补 `id`/`time`、按 `id` 去重、路由到 `inbox[to]`（`to=None`→CEO key）。
- [x] `poll(agent, timeout)`：阻塞取该 agent 最老未读，超时→None。`ack(agent, id)`：推进 read-cursor。
- [x] broker 全程不读 `text`/`body`。
- **验证**：`pytest tests/test_inbox.py` —— append/poll/ack、去重、per-agent 隔离、**重启后未读不丢（AC6）**、阻塞+timeout 行为。

### Phase 2 — `receive()` 工具 + 最小 harness 循环（脚手架）
- [x] `receive(timeout) -> ime|null`：从**调用者自身** inbox 取（身份解析 agent），包在 `poll` 上。
- [x] 最小 harness 循环（脚手架）：`while: msg=receive(); 把 msg 当 tool 结果喂给 agent 这一轮; 处理; ack`。
- [x] 集成 demo：一个 stub/真 agent 以 **tool 返回**形态收到一条消息。
- **验证**：`pytest tests/test_receive.py` —— tool-return 形态、**一条一条**、**忙时排队不打断（AC4）**、**事件到达即被递（push，AC5）**、timeout 地板。

### Phase 3 — 第一个真实 adapter（email）+ e2e（AC1）
- [x] `peripheral/adapters/email.py`：native email → `{to, text(短), body(全文/链接)}`（无 LLM，模板渲染）。
- [x] e2e：邮件（真实源或 mock 注入）→ adapter → inbox → harness `receive()` → agent 读到 `text`/`body`。
- **验证**：`pytest tests/e2e/test_email_inbox.py` —— **AC1**。

### Phase 4 — 第二个 adapter + 零核心改动（AC2）
- [x] 再加一个源 adapter（如 webhook）= 仅**新增 adapter + 一行 manifest**。
- [x] 证明 `git diff` 只动 `peripheral/adapters/` + manifest，**核心 0 改动**。
- **验证**：e2e 跑通 + diff 审查 —— **AC2**。

### Phase 5 — 接 goal-ledger notifier（统一 inbox，AC3 + AC7）
- [x] 给 `goal_ledger.py` 的 notifier 钩子接上：goal 终态 → `make_ime`（`parent→to`，关联 mention 进 body）→ `inbox.append`。
- [x] 现有 84 单测保持绿（notifier 未接时仍 no-op）。
- **验证**：`pytest`（全量）——
  - **AC3**：一个 goal 事件 + 一个外部事件走**同一信封/同一 inbox/同一 receive**。
  - **AC7**：A 派活给 B，B 完成 → 进 **A 的 inbox** → A `receive()` 拿到（关联看 body）。

### Phase 6 — 常驻外设容器（R6）
- [x] `peripheral/runner.py` + `docker-compose.yml` 加一个常驻 service（跑 adapters、写共享 inbox volume），与 broker/CEO 平级。
- **验证**：`docker compose up` 后常驻在线；**容器重启未读不丢（AC6 容器级）**。

## 验证命令汇总

```bash
python -m pytest                      # 全量（含现有 84 + 新增），全程保持绿
python -m pytest tests/e2e -m e2e     # e2e（AC1/AC2/AC3/AC7）
docker compose up -d && docker compose restart peripheral   # R6/AC6 容器级
```

## 评审门（review gates）

- **Gate A（Phase 1 后）✅ 已定**：存储沿用 JSONL+cursor（不引 SQLite，保持 dep-light + 与现有 stub 一致）；已读语义 = cursor 自动推进（无显式 ack，留作后续 OQ）。
- **Gate B（Phase 2 后）**：receive/tool-return 语义经 demo 确认符合"像 tool 返回 / 不打断 / push" → 再接真实源。
- **Gate C（Phase 5 后）**：统一 inbox 与 ceo-loop R3/R4 对齐无冲突（与 ceo-loop 任务协调）。

## 回滚点

- 每个 Phase 都在接口/新文件后增量推进：Phase 1–4 为新增模块，回滚 = 删模块/还原 manifest。
- Phase 5 的 notifier 接线是唯一动到现有核心处：以"notifier 默认 no-op"为安全位，出问题即把 notifier 退回 no-op（核心行为不变、84 单测仍绿）。

## 与 ceo-loop 的接缝（协调备忘）

- 本层交付 `receive()` 工具 + inbox 契约 + 最小 harness 脚手架；**生产级 agent 常驻循环在 ceo-loop**（复用本层 `receive()`）。
- ceo-loop R4「inbox 留接口 stub」→ 由本层完整实现替换；ceo-loop 改当消费方。
- OQ「哪些 agent 真给 inbox / 寻址 key 规则」需与 ceo-loop（agent loop 泛化）一并定。
