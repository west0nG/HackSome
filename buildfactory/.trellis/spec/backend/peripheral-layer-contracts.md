# V7 Peripheral / Inbox 契约

## 1. 五字段 IME

所有异步输入统一为：

```json
{"id":"...","time":"...","to":"ceo","text":"short","body":{}}
```

字段必须恰好是 `id / time / to / text / body`。来源、Goal 背景、链接和其他
扩展信息全部放入 `body`，不得扩展信封顶层。内部 V7 消息的 `body` 使用带
版本与 type 的结构化对象。

## 2. Hub-owned Inbox

`FileInbox` 的存储为每个 actor 一份 append-only JSONL、cursor 与去重集合。
目录属于编排层，不挂载给 Agent。构造 `FileInbox(root, ...)` 时必须由
`CompanyLayout` 显式提供 root；不存在 `GOAL_INBOX` 或 repo-relative fallback。

控制面只使用以下可靠接口：

- `append(key, event)`：按稳定 message id 去重并追加。
- `peek_one(key)`：读取 FIFO 队首但不消费。
- `ack_one(key)`：只在 wake 成功后前进一条。
- `wait(key, timeout)`：非消费式等待。
- `peek(key)`：仅供 Hub 内部重启恢复和 idle 去重查看未读快照。
- `was_consumed(key, id)`：恢复 cursor 已前进但 ack receipt 尚未写入的崩溃窗。

不存在 Agent 直连 `poll / poll_one / receive_tool` 路径。常驻 Agent 通过
绑定 actor 的 `RemoteInbox` 调用 Hub；一次 wake 只能得到一条消息，失败时
保持同一队首，成功后立即继续下一条。

## 3. 外部 adapter

每个来源在 `peripheral/adapters/<name>.py` 暴露 `SOURCE` 和
`to_ime(native) -> dict`，并在固定 `peripheral/manifest.py::ADAPTERS` 注册。
`peripheral.runner` 只负责规范化并通过 `deliver_external_event` 交给 Hub，
不直接向 Agent 暴露 Inbox 文件。

Hub 会重新校验目标、信封、body 大小和 message id，再按消息矩阵投递。外部
事件可以唤醒 CEO 或 active Department；普通 Worker 控制事件不进入 LLM
Inbox。Peripheral 无“没有 Hub 就直接写 FileInbox”的降级路径，启动时始终使用
绑定 `manager/peripheral` 身份的 Hub client。

## 4. 场景：Company 级邮件身份、路由与收发

### 4.1 范围与触发条件

修改 `foundagent.net` 地址认领、R2 邮件入口、Company mail journal、Hub 邮件方法、
邮件 Skills、角色 loadout、Resend 发件或 Compose 挂载时，必须同时检查域名级唯一性、
跨 Company 隔离、角色授权、敏感结果持久化和故障重试顺序。

`foundagent.net` 邮件不进入 Peripheral adapter，也不存在 `/ingest/email`。Cloudflare
Email Worker 只把 raw MIME 与 envelope `to/from` 写入 R2；独立平台级
`mail-router` 是唯一邮件消费者。

### 4.2 签名

Hub 使用版本 1 方法信封；`request_id` 位于信封而非业务 payload：

```text
claim_company_mailbox({name: str, label?: str | null})
  -> {name, company, address, label, claimed_at, created, used, limit}
list_company_mailboxes({})
  -> {mailboxes: [{name, address, label, claimed_at}], used, limit}
peek_company_email({})
  -> {messages: [MailProjection], count}
send_company_email({mailbox, to, subject, text, html?, from_name?})
  -> {sent, replayed, reservation_id, provider_id, from, to, subject}

run_once(backend, registry_root: Path, companies_root: Path)
  -> {processed: int, unmatched: int, deferred: int}
```

`mailbox` 是 localpart，不是完整地址。`MailProjection` 包含 `id / received_at /
address / from / subject / text / links / message_id`，不得返回内部 `source_key`。

### 4.3 契约

存储与身份：

- `state/_mail/registry.jsonl` 只接受永久 `claim` 事件，记录
  `localpart -> company`；全局首个有效 claim 获胜；
- 每个 Company 固定最多 5 个地址；同 Company 重复 claim 幂等；不存在 rename、
  release、transfer、owner、receiver 或旧 per-Agent 兼容分支；
- `state/<company>/mailboxes/messages.jsonl` 是该 Company 的入站 journal；
  `send_ledger.jsonl` 是其发件 reservation 与结果审计；两者均为控制面状态。

入站顺序：

1. 完整 envelope 域名必须匹配 `foundagent.net`；只比较 localpart 是禁止实现；
2. 从全局 registry 解析 Company；未认领或其他域名进入 R2 `unmatched/`；
3. 以 R2 source key 派生稳定 mail id，规范化后先 append Company journal；
4. journal 成功后才归档到 `processed/`；归档前崩溃的重试由稳定 id 去重；
5. `received_at` 优先使用 R2 `LastModified`，不能使用 router 恢复处理时间。

角色矩阵：

| 角色 | claim | list | peek | send | 普通入站通知 |
|---|---:|---:|---:|---:|---:|
| CEO | 是 | 是 | 否 | 否 | 是，仅所属 Company |
| active/self-bound Department | 否 | 是 | 最近 100 封 | 是 | 否 |
| 当前非终态 Goal 的绑定 Worker | 否 | 是 | Goal `created_at` 以来最近 100 封 | 是 | 否 |
| Verifier | 否 | 否 | 否 | 否 | 否 |

Department 直接读取验证码或发件是合法路径；`check-email` / `send-email` 仅引导常规
外部执行优先创建 Goal 交给 Worker，不能把这项建议实现成权限限制。peek 全地址、
只读、非消费，按接收时间正序返回，不推进 CEO cursor，也不影响其他调用者。

敏感与部署：

- `peek_company_email` 不写完整 response cache；telemetry 只保留数量和时间范围；
- 邮件正文最多保留 2000 字符，链接数量与长度受限，CEO 通知携带固定外部不可信标记；
- Company 发件配额默认 30/滚动 24 小时，单地址 15/滚动 24 小时；先 reserve，
  Provider 失败不退款；Hub `request_id` 同时作为 Resend idempotency key；
- Hub 使用 `MAIL_GLOBAL_ROOT` 和 `RESEND_API_KEY`；router 使用
  `MAIL_GLOBAL_ROOT / COMPANIES_STATE_ROOT / R2_ENDPOINT / R2_ACCESS_KEY_ID /
  R2_SECRET_ACCESS_KEY`，并可配置 `R2_BUCKET / MAIL_POLL_INTERVAL`；
- 只有 Hub 与确定性 router 能访问 registry/Company mailboxes；任何 CEO、Department、
  Worker、Verifier LLM runtime 都不得挂载 registry、mailboxes 或原始 Inbox。

### 4.4 校验与错误矩阵

| 条件 | 结果 |
|---|---|
| localpart 非法、保留名或包含 `+` | claim 拒绝，不写 registry |
| Company 已有 5 个地址 | 第 6 个 claim 拒绝 |
| localpart 已属于另一 Company | 冲突，原绑定永久保留 |
| registry 损坏或不可读 | claim/list/send fail closed；router 返回 deferred，R2 保持 pending |
| envelope 缺失、域名不符或地址未认领 | 归档到 `unmatched/`，不写任何 Company |
| Company journal append 失败 | deferred，R2 保持 pending |
| journal 已写但 R2 archive 失败 | deferred；重试不重复 journal，成功后归档 |
| CEO/Verifier 调用 peek/send，Department/Worker 调用 claim | Hub 返回 `forbidden` |
| Department 未激活或非 self-bound | Hub 返回 `invalid_state` |
| Worker 与 Goal/worker_id 不匹配或 Goal 已终态 | Hub 返回 `invalid_state` |
| 发件 localpart 未归属当前 Company | 拒绝 Provider 调用 |
| Provider 失败 | reservation 保留并返回失败；不得盲目退款或更换同一逻辑请求的 id |

### 4.5 正常、基础与错误案例

- Good：Company A/B 分别认领不同地址；router 各写各的 journal，各 Hub 只通知自己的
  CEO，A 的 Department/Worker 永远看不到 B 的邮件或发件身份。
- Base：Department 在当前 wake 直接 peek 并使用验证码；普通注册流程则创建 Goal，
  Worker 从 Goal 创建时间起全量扫描 Company 最近 100 封邮件。
- Good：journal append 后进程崩溃，R2 原对象仍在；恢复后稳定 id 去重并完成归档。
- Bad：为每个 Company 启一个 poller 扫同一 bucket，或恢复 receiver fan-out。
- Bad：把 `state/_mail`、`mailboxes/` 或 Inbox 挂载给 LLM runtime，以文件访问替代 Hub。

### 4.6 必需测试

- `orchestration/tests/test_mailbox.py`：全局并发 claim、固定 5 个、永久事件模型、
  journal 去重/窗口/cursor；
- `peripheral/tests/test_email_poller.py`：完整域名校验、A/B 路由、unmatched、registry/store/
  archive 故障和稳定重试；
- `orchestration/tests/test_company_hub_v7.py`：完整角色矩阵、CEO 单播、Department/Worker
  peek、Goal 窗口、返工连续性和敏感审计；
- `orchestration/tests/test_email_send.py`：Company 归属、两级并发配额、Provider 失败与幂等；
- `orchestration/tests/test_method_adapter.py`：敏感方法不缓存、审计 redactor fail closed；
- `agent/tests/test_skill_catalog.py` 与 loadout 测试：Department/Worker 都有 check/send，
  CEO 只有 claim，Verifier 无邮件 Skill，旧命令不复活；
- `orchestration/tests/test_compose_accounts.py` 与 mount 测试：平台 router 单实例、凭据和
  控制面挂载不进入 LLM runtime；
- `orchestration/tests/test_company_mail_e2e.py`：离线双 Company 端到端隔离。

### 4.7 错误与正确示例

Wrong：

```text
每个 Company poller：R2 inbox/ -> 只取 localpart -> Department receivers -> Agent Inbox
```

Correct：

```text
单一 mail-router：R2 inbox/
  -> 校验完整 foundagent.net 地址
  -> 全局 localpart -> company registry
  -> state/<company>/mailboxes/messages.jsonl
  -> Company Hub 稳定通知 CEO；Department/Worker 仅通过 Hub peek/send
```

## 5. 通用验证

- `orchestration/tests/test_inbox_ack.py`：peek/ack、崩溃重投、wait 和恢复。
- `peripheral/tests/test_adapters.py`：五字段 webhook 转换，以及 email ingress
  bypass 不得重新出现。
- `orchestration/tests/test_control_client.py`：Agent 无原始 Inbox 挂载。
