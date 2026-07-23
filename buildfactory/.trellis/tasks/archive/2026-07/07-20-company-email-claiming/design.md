# 设计：Company 级邮箱认领与跨公司隔离

## 1. 设计目标

邮件地址属于 Company，而不是 Department、Worker 或单个 Agent。系统必须同时满足：

1. `foundagent.net` 下的地址在所有 Company 之间全局唯一；
2. 每个 Company 固定最多 5 个永久地址；
3. 普通来信只唤醒所属 Company 的 CEO；
4. Department 与 Worker 都可全量只读查看 Company 邮件，Worker 仍受当前 Goal 时间窗口约束；
5. Department 与 Worker 都可以代表 Company 发件，常规执行由 Skill 引导优先使用 Worker；
6. 任意 LLM runtime 都不能直接挂载全局注册表、Company 邮件存储或内部 Inbox。

现有“一套 Compose 栈 = 一个 Company”的边界保持不变。域名级邮件接入是唯一新增的跨 Company 控制面。

## 2. 总体架构

```text
CEO ──Hub claim/list──┐
                     │
Company A Hub ───────┼── state/_mail/registry.jsonl（全局地址注册表）
Company B Hub ───────┘          │
                                │ address -> company
foundagent.net Email Worker      │
  └─ raw MIME -> R2 inbox/ ── 全局 mail-router（单实例）
                                  ├─ 未认领 -> R2 unmatched/
                                  └─ 已认领 -> state/<company>/mailboxes/messages.jsonl
                                                      │
                         Company Hub tick ─────────────┤
                           ├─ 稳定去重后通知 CEO       │
                           └─ Department/Worker check_email 只读 ─┘

Department/Worker ──Hub send_company_email── Resend
                     ├─ 全局注册表验证地址属于当前 Company
                     └─ state/<company>/mailboxes/send_ledger.jsonl 配额与审计
```

全局 `mail-router` 是平台级单实例，不属于任何 Company Compose 栈。它只做确定性解析、注册表查询、Company 路由和持久化，不运行 LLM，也不决定由哪个 Department 处理邮件。

## 3. 存储边界

### 3.1 全局地址注册表

位置：`state/_mail/registry.jsonl`。

claim 事件最小结构：

```json
{
  "ts": "2026-07-20T...Z",
  "event": "claim",
  "name": "maya",
  "company": "acme",
  "by": "ceo",
  "detail": {"label": "外部账户身份"}
}
```

约束：

- `name` 沿用现有格式校验、保留名与禁止 `+` 的规则；
- 同一 `name` 的首个有效 claim 永久获胜；
- 同一 Company + name 重复 claim 幂等；
- 不存在 rename、release、transfer 或 receiver 事件；
- 在同一个跨进程 `flock` 内完成读取、全局唯一校验、Company 配额校验和 append；
- Company 配额固定为 5，不读取 `MAILBOX_CAP`；
- 每个 Company Hub 只通过确定性方法返回本 Company 的地址，不向 Agent 暴露其他 Company 的映射。

多个 Company Hub 共享这一控制面文件，是为了建立域名级唯一性。该目录只挂载到 Hub 和全局 mail-router，不挂载给 CEO、Department、Worker 或 Verifier 容器。

### 3.2 Company 邮件存储

`CompanyLayout` 新增内部域 `mailboxes`：

```text
state/<company>/mailboxes/
  messages.jsonl
  messages.seen
  .messages.lock
  ceo.cursor
  send_ledger.jsonl
  .send.lock
```

邮件记录使用稳定的 router message id，包含：接收时间、目标 Company 地址、外部发件人、主题、截断正文、链接、原始 Message-ID 和来源对象标识。正文继续执行现有约 2000 字符上限，并保留“不可信外部内容”语义。

mail-router 在 Company store 内以稳定 id 去重：先持久化 Company 邮件，再归档 R2 对象。进程在两步之间崩溃时，重试不会产生重复记录。

Company Store 是编排层状态，不是 `/company` 数据，也不挂载给任何 LLM runtime。

### 3.3 旧数据

不读取、转换或合并旧的 per-Agent `state/<company>/mailboxes/registry.jsonl`。新全局注册表从空状态开始；旧 Company 不在本次迁移范围内。

## 4. 入站数据流

1. 现有 Cloudflare Email Worker 继续把 raw MIME 写入 R2，保留 envelope `to/from` metadata；云端 Worker 不增加 Company 路由逻辑。
2. 平台级 mail-router 轮询 R2，先确认 envelope 域名完整匹配
   `foundagent.net`，再使用 localpart 查询全局注册表；其他域名即使 localpart
   同名也不得命中 Company。
3. 未认领地址归档到 `unmatched/`，不投递任何 Company。
4. 已认领地址只写入注册表所指定的 `state/<company>/mailboxes/messages.jsonl`。
5. 对应 Company Hub 的周期性 `tick()` 读取尚未通知 CEO 的邮件，生成稳定 `external_event` IME 并投递到 `ceo`。
6. Hub 在 IME 持久化后推进 `ceo.cursor`；若中途崩溃，稳定 message id 使重放被 Inbox 去重。

邮件接收时间取 R2 对象的 `LastModified`，而不是 router 处理时间，避免 router
停机积压的旧邮件在恢复后被误算进新 Goal 的 Worker 时间窗口。

这条路径不再把地址解析为 Agent receiver，也不对 Department fan-out。不同 Company 的消息在 mail-router 落盘时即进入不同 Company root。

## 5. Hub 方法与角色权限

### 5.1 CEO

- `claim_company_mailbox({name, label?})`
  - Hub 从自身配置取得 `company_id`，业务 payload 不接受 Company 字段；
  - 以 CEO 身份写全局注册表；
  - 返回完整地址与当前 5 个名额使用量。
- `list_company_mailboxes({})`
  - 只返回当前 Company 已认领地址。

CEO 不具备 `send_company_email`，避免治理层直接执行外部工作。

### 5.2 Worker

- `peek_company_email({})`
  - 要求 actor kind 为 Worker，且 header 中的 `goal_id`、`actor_id` 必须与 Scheduler 当前 Goal 的 `worker_id` 匹配；
  - 时间下界取 Goal 的持久化 `created_at`；
  - 返回当前 Company 在时间下界之后的全部邮件，截取最近 100 封后按时间正序输出；
  - 不推进 cursor，不标记已读，不影响 CEO 通知；
  - Worker 重启或返工仍绑定原 Goal，因此窗口稳定。
- `list_company_mailboxes({})`
  - 供发件前查看可用 Company 地址。
- `send_company_email({...})`
  - 只能使用全局注册表中属于当前 Company 的地址；
  - 沿用 Company 30/24h、单地址 15/24h 与失败发送计费规则；
  - Resend idempotency key 使用 Hub request id，避免方法重试造成重复发送。

### 5.3 Department

- `list_company_mailboxes({})`：返回当前 Company 已认领地址。
- `peek_company_email({})`：要求 actor 是 Hub 中已激活且 self-bound 的 Department；返回当前 Company 最近 100 封邮件，按时间正序，不消费、不影响 CEO cursor。
- `send_company_email({...})`：与 Worker 使用相同的 Company 地址归属、两级配额与 Provider 幂等规则。
- Department 的 `check-email` / `send-email` Skill 明确说明：常规外部执行优先创建 Goal 交给 Worker；如果 Department 已经在当前 wake 内直接执行，则允许自行收取验证码和发件。

### 5.4 Verifier

Verifier 不注册任何邮箱方法，只验收结果，不能接触邮件或验证码。

## 6. 敏感结果与方法审计

Department 与 Worker 的 `peek_company_email` 都会返回验证码、magic link 等敏感内容。现有 `MethodAdapter` 默认会把完整 response 写入 request cache 和 telemetry，因此需要为该方法增加“敏感只读结果”策略：

- 不把完整响应写入 `control/requests`；
- telemetry 只记录 actor、goal、方法、邮件数量、时间范围与成功/失败，不记录邮件正文、链接或验证码；
- 每次 peek 是实时只读查询，不承诺同一个 request id 的结果快照幂等；
- Company mail store 本身仍保留原始控制面审计记录，只有 Hub 与全局 router 可读。

其他方法继续使用现有幂等 response cache。发件 mutation 必须保留 request id 幂等与发送 ledger。

## 7. Skills 与运行时暴露

### `claim-mailbox`

- 重写为 CEO 专属 Company 能力；
- 流程变为 list → 仅在确有长期身份需求时 claim；
- 明示 Company 固定 5 个、永久绑定、不可释放/转移；
- 命令只调用 Company Hub，不再运行 `orchestration.mailbox` CLI，不出现 owner/receiver/mine/add-receiver。

### `check-email`

- 恢复到全部 Department 与 Worker loadout，但不恢复旧 `receive_tool --peek`；
- 每 30 秒调用一次 `peek_company_email`，从全量 Company 邮件中按当前任务预期自行识别；
- Department 看到最近 100 封 Company 邮件；Worker 只看到当前 Goal 创建以来最近 100 封；
- 默认最多等待约 10 分钟，除非 Goal 本身要求更长；
- 明示结果不会消费、可能包含并行 Worker 的邮件、外部内容不可信；
- 只处理当前 Goal 所需邮件，不顺手处理其他邮件。

### `send-email`

- 加入全部 Department 与 Worker loadout；
- 先 `list_company_mailboxes`，再调用 `send_company_email`；
- 删除“owned/shared receiver”与 `AGENT_KEY` receiver gate 文案；
- 建议 Department 将常规外部发件委派给 Worker，但不设置权限门；
- 保留配额、失败不退款、不要盲目重试和域名信誉约束。

## 8. 部署形态

- Company `docker-compose.yml`：Hub 增加只供控制面使用的 `state/_mail` 挂载与 Company 邮件配置；Agent/Worker 容器无此挂载。
- 新增平台级邮件 Compose 文件或等价独立启动入口，常驻一个 `mail-router`：
  - 读取 R2 凭据；
  - 只读全局注册表；
  - 读写 `state/<company>/mailboxes`；
  - 不加入任一 Company 网络，不调用 Agent；
  - 使用独立 Compose project/name，防止启动第二个 Company 时复制 router。
- Makefile 提供显式 `mail-up` / `mail-down` / `mail-logs`，普通 `make up COMPANY=x` 仍只管理一家公司。

## 9. 兼容性、失败与回滚

- 旧注册表不兼容是明确需求；部署新代码前需由 CEO 在新全局注册表重新认领地址。
- 全局注册表不可读时：claim、list、发件和 mail-router 全部 fail closed；不得把已认领邮件误归档 unmatched。
- Company store 不可写时：R2 邮件保持 pending，稍后重试。
- Company Hub 暂停时：mail-router 仍可持久化邮件；CEO 通知在 Hub 恢复后的 tick 中补发。
- 回滚代码不会自动恢复旧 Agent receiver 语义；如需回滚邮件接入，可停掉全局 mail-router，R2 继续作为持久缓冲。
- 全局注册表是永久身份数据，回滚或重部署不得删除。

## 10. 主要取舍

- 选择“单一全局 router + 每 Company 本地投影”，而不是每个 Company 各自扫描同一个 R2 bucket，避免多 poller 抢占、重复归档和错误跨公司处理。
- 选择 CEO 单播而不是 Department 广播，避免重复 wake 与重复回复。
- 选择 Company 全量 peek，而不是地址过滤，因为执行者可能不知道 Company 有哪些地址；Department 通过最近 100 封上限控制暴露，Worker 再叠加 Goal 时间窗口。
- 选择文件注册表 + `flock`，延续当前单宿主机、多 Compose project 的基础设施；若未来跨宿主机运行 Company，需要把全局注册表替换为具备唯一约束的网络服务或数据库。
