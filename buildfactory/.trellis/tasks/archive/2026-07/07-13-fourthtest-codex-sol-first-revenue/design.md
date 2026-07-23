# Fourth Test 并行运行设计

## 设计结论

Fourth Test 与 `thirdtest` 并行运行，但不共享运行目录、Compose project、容器、模型配置、Company State、Inbox、Ledger、Session 或 Observatory 状态。两家公司只共享用户明确授权的 `foundagent` 外部账号包及其外部服务账户。

为避免修改主工作区的全局 `agents/*.yaml`，从当前提交创建独立 Git worktree：

- 分支：`codex/fourthtest-run`
- worktree：`/Users/weston/dev/BuildFactory-fourthtest`
- Compose project：`fourthtest`
- Host peripheral：`127.0.0.1:8901`
- 运行状态：主仓库 `/Users/weston/dev/BuildFactory/state/fourthtest/`
- Observatory：从主仓库启动独立 daemon，读取上述状态目录

worktree 内只修改五个角色声明，将它们固定为：

```yaml
provider: codex
model: gpt-5.6-sol
effort: xhigh
credentials: subscription
```

角色 charter、skills、hooks、MCP 和权限保持现有基线，不为本实验另做行为定制。

## 并行拓扑

```text
thirdtest Agent Company（mail-poller 除外，其余保持不变）
  主工作区 + Compose project buildfactory + :8900 + Sonnet 5 observer A

fourthtest
  独立 worktree + Compose project fourthtest + :8901 + Codex GPT-5.6-Luna high observer B
       │
       ├── ceo / researcher / builder / growth / verifier
       ├── hub / peripheral / broker / provisioner
       └── state/fourthtest/{company,ledger,inbox,sessions,telemetry,...}

共享且只读注入
  accounts/foundagent + vm/.env.local
       └── Codex auth、Stripe、GitHub、Vercel、Cloudflare、GA4/GSC、
           DataForSEO、Resend、R2 与已有浏览器登录态

全局邮件入口（只负责复制，不做业务路由）
  Cloudflare catch-all Email Worker（单一可审计 fan-out 边界）
       ├── foundagent-mail（thirdtest 独立副本）→ thirdtest poller → :8900
       └── foundagent-mail-fourthtest（Fourth Test 独立副本）
            → fourthtest poller → :8901
```

## Worktree 与数据挂载

- worktree 的 `accounts/foundagent` 指向主仓库现有账号包；容器继续按基线只读挂载到 `/account`。
- worktree 的 `vm/.env.local` 指向主仓库现有环境文件；不复制或展示 secret 值。
- worktree 的 `state/fourthtest` 指向主仓库同名状态目录，使运行状态和 Observatory 报告仍集中在主工作区。
- 使用 `docker compose -p fourthtest`，并向 worktree 内的 provisioner 注入 `COMPOSE_PROJECT_NAME=fourthtest`，保证它后续启动动态角色时不会操作 `thirdtest` project。
- 五个 Agent 及控制面使用已有镜像和 `--no-build`，避免并行实验重写全局 `latest` 镜像标签。mail-poller 的冲突保护需要代码升级，因此单独构建带版本标签的镜像并由两套 poller 显式固定；不得覆盖 `foundagent/mail-poller:latest`。

## 启动时序

为保证 Initial Message 是 CEO 的第一次模型 wake，不能先启动 CEO 再抢时间投递：

1. 创建全新状态目录、worktree 配置和独立 Compose project。
2. 只启动 `hub / peripheral / broker / provisioner`，确认 Hub 与 `:8901` Peripheral 健康。
3. 通过 Fourth Test 的 `/ingest/webhook` 投递带固定唯一 ID 的 Initial Message。
4. 验证 `inbox/ceo.jsonl` 只有该消息，且 CEO cursor 尚未产生或仍为 0。
5. 再启动五个常驻 Agent；CEO 启动后的第一次 poll 必然得到该 event。
6. 从 boot log 验证五个角色均为 `codex / gpt-5.6-sol / xhigh`，并从 transcript/telemetry 验证第一次 Codex turn 成功。
7. 启动独立 Codex `gpt-5.6-luna / high` Observatory daemon，并记录 PID 与日志。

## Initial Message 数据流

HTTP payload 固定使用可审计 ID `fourthtest-initial-first-stripe-revenue-v1`，目标为 `ceo`；正文使用 `prd.md` 中已经确认的中文消息。数据路径为：

```text
POST :8901/ingest/webhook
  → webhook adapter
  → state/fourthtest/inbox/ceo.jsonl
  → CEO event wake
  → Codex GPT-5.6-Sol xhigh
```

这条消息只规定结果与 Stripe 成功口径，不替 Agent 指定产品、用户、价格或渠道。

## 权限与 Secret 验证

- 只检查账号文件存在性、容器内预期变量是否为非空，以及对应服务的只读认证探针是否成功；任何输出都只显示键名与 PASS/FAIL。
- 禁止使用 `docker inspect ... .Config.Env` 或打印 env 文件内容。
- Codex 在一次性临时 HOME 中使用 `/account/codex-auth.json` 做 `gpt-5.6-sol + xhigh` smoke test；该测试不写入正式 `state/fourthtest/sessions/`。
- Stripe 使用 live 只读探针验证认证与收款能力；不创建产品、价格、付款或退款。
- 正式 Agent 容器继续使用 `permission_mode: bypass` 和现有完整 MCP 配置，符合用户“之前所有 secrets”的授权。

## Observatory

- 使用 `observatory/runner.py --company fourthtest daemon`，显式设置 `OBSERVER_PROVIDER=codex`、`OBSERVER_MODEL=gpt-5.6-luna`、`OBSERVER_EFFORT=high`，并固定 Fourth Test 的版本化 Codex CUA image。
- 每次观测使用临时 `CODEX_HOME`、`codex exec --ephemeral`、禁用用户配置与仓库 rules；worktree 与其 Fourth Test state symlink target 均由 Docker 只读挂载，并叠加 Codex `read-only` sandbox。容器以非 root 用户运行；只为让内层 bubblewrap 创建 namespace 而设置 `seccomp=unconfined`，不改变外层 `:ro` 挂载或内层只读策略。prompt 走 stdin；runner 只接受完整 `turn.completed`、非空 agent message 且至少一次本地读取命令成功的 JSONL，随后才落盘并推进窗口。
- 日志写入 `state/fourthtest/telemetry/observatory-daemon.luna.log`，PID 写入同目录，报告写入 `state/fourthtest/observatory/`；报告头记录 provider、model 与 effort。
- 该 provider 选择只存在于 Fourth Test daemon 的环境中；Third Test 的 `claude-sonnet-5` Observatory 不重启、不改配置。
- Observatory 只读，不自动干预经营行为；机制故障由 operator 处理并记录。

## 两套独立入站邮件路由

两个 poller 只有在上游对象也隔离时才能安全地各自丢弃“不属于本公司”的邮件。为此保留现有 `thirdtest` bucket，不让 Fourth Test 读取同一个 `inbox/`；Cloudflare Email Worker 在收到一次邮件后，使用两个 R2 binding 将同一个原始 MIME stream 分成两个分支，并以同一个关联 key 分别写入：

- `foundagent-mail`：现有 `thirdtest` 路径，`R2_BUCKET` 与 registry 不变；
- `foundagent-mail-fourthtest`：新建的 Fourth Test 路径，只供 `fourthtest-mail-poller` 使用。

两边各自拥有 `inbox/processed/unmatched/conflict`，因此 `thirdtest` 把 Fourth Test 地址的副本归档 unmatched 时，只删除自己的副本；Fourth Test bucket 中的副本仍会被它自己的 poller 正常读取，反向同理。第三次实验的 poller 不需要切换到共享队列，但为了加入对称的 peer-registry 冲突保护，需要在新镜像和配置就绪后执行一次 `--no-deps` 受控重建；停顿期间邮件继续留在原 R2 pending queue，不停止任何 Third Test Agent 或 Peripheral。

### 写入与失败语义

- Worker 对原始 `ReadableStream` 使用 `tee()` 后分别通过定长流写入两个 binding，不解析 MIME；两次 R2 `put()` 都 resolve 后本次 fan-out 才算复制完成。
- 两份对象使用同一个关联 key 与相同 `{to, from}` metadata，便于端到端核对。
- 若只有一边写入成功，Worker 记录关联 key、成功端与失败端并抛出错误，不能把单边结果记为双写成功。Cloudflare 官方文档没有承诺 Email Worker 脚本异常后自动重试，因此监控必须把这种情况视为 ingress 故障；成功端可能已有对象，后续重复邮件由既有 Message-ID 去重吸收。
- 每个 poller 独立维持 at-least-once：自己的 Peripheral 返回全部 2xx 后才归档 processed，否则自己的副本留在 pending；一边故障不授权另一边移动它的对象。
- 新 bucket 必须在 Worker 部署双写版本前创建并通过绑定验证；部署失败时旧 Worker 与 `thirdtest` poller 保持原状。

### 同名邮箱冲突

外部地址 `<localpart>@foundagent.net` 仍是全局身份。如果两个公司都认领同一个 localpart，简单双写会让两边都认为邮件属于自己。为防止跨公司泄露：

- 两个 poller 只读挂载对方 mailbox registry 作为冲突检查源，但仍只写自己的 Inbox 与 R2 bucket；
- 本公司未认领时照常归档自己的 unmatched 副本；
- 本公司已认领且 peer 也认领时，不向任何 Agent 投递，把自己的副本移到 conflict 并高亮告警；
- peer registry 不可读时，对本公司已认领的邮件 defer，不能在无法排除冲突时放行。

该保护发生在投递时，而不是把两套 registry 合并为共享写库：两个 Agent Company 仍各自认领和维护邮箱；若出现同名认领，两边都不收到该地址的邮件，等待 operator 处理身份冲突。

### 受控切换顺序

1. 构建并记录专用 mail-poller 镜像的版本标签与 digest，先跑完本地自动化测试。
2. 创建并验证 Fourth Test bucket；旧 Worker 仍只写 Third Test bucket。
3. 启动 Fourth Test 控制面与新 poller，但在双写 Worker 上线前不把邮件能力记为就绪。
4. 用同一版本镜像和只读 Fourth Test registry mount，`--no-deps` 只重建 `thirdtest-mail-poller`；记录前后容器 ID 并确认原 bucket backlog 正常继续消费。
5. 部署双写 Worker，先做 Worker tail/Activity Log 观察，再发送随机未认领地址的 smoke mail。
6. 任一步失败时先回滚 Worker 到单 bucket 版本，再恢复 Third Test poller 原镜像/配置；不得重建其他 Third Test 服务。

### 上线验证

- 自动化测试覆盖两个独立 MockBackend、双 bucket 写入、单边复制失败的显式告警、复制后单边投递失败、unmatched 与同名 conflict。
- 实机用一个随机、未认领的 `@foundagent.net` 地址发送 smoke mail；两边必须出现同关联 key 的 unmatched 副本，且不唤醒任何 Agent。
- Fourth Test 正式认领地址后的真实邮件只允许进入其 Inbox；`thirdtest` 的对应副本应成为 unmatched。

外部账号本身仍是共享资源。Agent 必须遵循既有 Skill 的“不修改其他 Agent 资产”规则；DNS 名称、Vercel 项目、GitHub 仓库和 Stripe 对象在创建前均应查询现有对象，避免覆盖。

## 风险与回滚

- 第二套五 Agent fleet 会增加 Docker 内存、CPU 和同一 Codex subscription 的并发压力；启动后持续观察容器 OOM、重启和限流。
- Stripe 使用 live full secret key，权限面包含退款等高风险动作；这是用户明确要求沿用的既有授权，不在本实验另行收窄。
- 双写会使 R2 写入、存储与 catch-all spam 副本约增加一倍；这是换取两家公司故障隔离与各自 unmatched 语义的明确成本。
- catch-all Worker 仍是两条路由共同的 fan-out 边界；两次写入完成后才实现故障隔离，边缘脚本或任一绑定在复制阶段失败会成为两条路由的共同 ingress 告警，而不是被误报为成功。
- 常规回滚只停止 `fourthtest` Compose project 和对应 Observatory PID，保留 `state/fourthtest/` 作为证据；唯一允许影响 `buildfactory` project 的动作是以 `--no-deps` 单独恢复 `thirdtest-mail-poller` 的原镜像与 mount，不得修改 `state/thirdtest/` 或触碰其他服务。
- worktree 和分支在实验收官、报告完成后再清理；运行中不删除。
