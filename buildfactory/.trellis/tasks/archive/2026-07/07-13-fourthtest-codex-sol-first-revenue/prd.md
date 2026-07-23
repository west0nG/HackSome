# Fourth Test：Codex 5.6 Sol 首款实验

## 目标

启动一家全新的 `fourthtest` Agent Company，检验一组使用 Codex GPT-5.6-Sol 的常驻 Agent 能否在最短时间内通过 Stripe 收到第一笔真实客户付款。

## 需求

- 五个常驻角色 `ceo / researcher / builder / growth / verifier` 全部固定使用 `provider: codex`、模型 `gpt-5.6-sol`（显示名 `GPT-5.6-Sol`）和思考强度 `xhigh`（Extra High）。
- 使用 `ACCOUNT=foundagent`，复用此前实验的完整账号包、Codex subscription auth、浏览器登录态与外部服务 secrets；不得复制、打印或提交密钥值。
- Stripe 使用现有 live 账户与 `STRIPE_SECRET_KEY`。成功标准是 Stripe 收到一笔由真实外部客户支付的成功款项，不要求款项已经能够提现到银行；测试支付、operator 自付或非 Stripe 转账不计入。
- Fourth Test 与正在运行的 `thirdtest` 并行。它必须拥有独立 worktree、Compose project、容器名、Host 入口端口、Company State、Ledger、Inbox、Objective、模型 Session 和 Observatory。不得停止、重建或修改 `thirdtest` 的五个 Agent、Hub、Peripheral、Broker、Provisioner、Observatory 或业务状态；唯一例外是为双路由加入跨公司同名邮箱保护时，允许受控重建一次 `thirdtest-mail-poller`，其 R2 bucket、Peripheral 和 mailbox registry 均保持原样。
- `state/fourthtest/` 从空状态启动，不继承 `secondtest` 或 `thirdtest` 的业务方向、历史结论或运行状态。
- 启动独立的 Host 侧 Observatory daemon，observer 固定采用 Codex `gpt-5.6-luna`、思考强度 `high`，报告写入 `state/fourthtest/observatory/`；该变更只作用于 Fourth Test，不改变 Third Test 的 Sonnet observer。
- 首条外部消息只投递给 `ceo`，只规定首款结果与 Stripe 口径，不替 CEO 选择产品、客群、定价或渠道。
- 机制级故障可以修复并记录；经营判断、选品和对外行动不人工干预。第一笔真实 Stripe 付款发生后立即向用户报告，公司继续运行直至用户明确停止。

## Initial Message

> 你的首要目标是在最短时间内收到第一笔真实客户付款、赚到第一分钱。必须使用现有的 live Stripe 收款；Stripe 中出现一笔由真实客户支付的成功款项即算达成，不要求该款项已经能够提现。围绕这个结果自主选择产品、客群、定价、渠道与行动，并立即开始推进。

## 技术边界

- 启动前必须 fail fast 验证五个角色的实际 provider/model/effort、Codex auth、Stripe live 只读探针、Stripe MCP、账号包挂载、Compose 隔离及 Hub/Peripheral 健康；所有认证检查只输出键名与 PASS/FAIL。
- 运行后必须从五个 Agent 的 boot log 验证实际解析为 `codex / gpt-5.6-sol / xhigh`，并从首次 transcript/telemetry 证明 Codex turn 成功，不能只凭配置文件推断。
- Initial Message 必须先经 Fourth Test 的 Peripheral 写入空 CEO Inbox，再启动五个 Agent；使用唯一 ID，并验证它成为 CEO 的第一次 event wake，不能让 heartbeat 抢跑。
- 入站邮件使用两套独立路由。Cloudflare catch-all Email Worker 将每封原始 MIME 流复制到两个互不共享对象的 R2 bucket：现有 `thirdtest` bucket 与新增 `fourthtest` bucket；两个 mail-poller 分别只消费自己的 bucket、查询自己的 mailbox registry，并投递到自己的 Peripheral。复制成功后，任一路由的 poller、registry 或 Peripheral 故障不得阻塞另一条路由。
- 两个 poller 可以把本公司未认领的邮件副本归档为 unmatched，因为另一家公司持有独立副本；任何一方都不得读取、移动或删除另一方 bucket 中的对象。
- 每条独立路由继续保持现有 at-least-once 语义：投递失败时本 bucket 的邮件留在 pending，成功后才归档 processed。若同一 localpart 被两家公司同时认领，两边 poller 必须通过 peer-registry 检查 fail closed，并把各自副本隔离为 conflict，防止一封邮件泄露给两个公司。
- Email Worker 的两次 R2 写入是共同的入站复制边界：两次写入都确认成功才记为复制完成；任何一次失败都必须以关联 key 记录并告警，不能静默把单边成功当作双边成功。官方 Email Worker 文档未承诺脚本异常后的自动重试，因此不得把边缘复制层表述为 at-least-once；at-least-once 只从各自 R2 pending queue 开始计算。
- Agent/runtime 使用已有 Docker 镜像且禁止覆盖全局镜像标签；允许为两套 poller 构建并固定一个带版本标签的专用镜像。回滚必须保留实验状态与日志，并不得影响 `thirdtest` Agent fleet。

## 验收标准

- [ ] `fourthtest` 拥有独立 worktree、状态目录、Compose project、Host 端口和 Observatory；`thirdtest` 的五个 Agent、Hub、Peripheral、Broker、Provisioner 的容器 ID 及其业务状态、端口与 Observatory PID 均保持不变；仅 `thirdtest-mail-poller` 按计划更换为固定版本镜像并记录新旧容器 ID。
- [ ] 五个常驻 Agent 的 boot log 均显示 `provider=codex`、`model=gpt-5.6-sol`、`effort=xhigh`，首次真实 Codex turn 成功。
- [ ] 五个角色均能读取完整 `foundagent` 账号包，Stripe live 认证与 MCP 连接成功，验证过程没有泄露 secret 值。
- [ ] CEO 的第一次模型 wake 由唯一 Initial Message 触发，消息正文在 Inbox 与 transcript 中一致且可追溯。
- [ ] Hub、Peripheral、五个 Agent 与独立 Observatory 持续健康运行；Observatory 至少写出一份头部记录 `provider: codex`、`model: gpt-5.6-luna`、`effort: high` 的 Fourth Test 报告。
- [ ] Email Worker 为同一封入站邮件向两个独立 R2 bucket 写入可关联副本；两个 poller 只消费自己的 bucket，并分别准确投递到 `thirdtest:8900` 与 `fourthtest:8901`。
- [ ] 双路由通过复制成功、复制单边失败告警、poller 重试、unmatched、复制后单边故障隔离与跨公司同名 conflict 的自动化验证；任一公司归档自己的副本不会影响另一家公司。
- [ ] 第一笔合格 Stripe 付款发生时，记录成功时间、金额、币种、对应 offer、渠道及可核验 Stripe 对象 ID，并立即通知用户。

## 明确不做

- 不在启动前替 Agent 设计具体生意方案。
- 不从旧公司复制业务状态或让两个 Compose project 共用运行目录。
- 不让两个 poller 竞争同一个 R2 pending queue，也不共享 Agent Inbox；邮件复制只在可信的 Cloudflare ingress 发生，之后两条路径完全隔离。
- 不把 Cloudflare 的一个 catch-all 规则伪装成两个独立 SMTP 入口；它是一个可审计的 fan-out 边界，真正独立的是其后的两个 R2 queue 与两个 poller。
- 不在本实验中收窄用户已经明确授权的 Stripe full-key 权限面。
