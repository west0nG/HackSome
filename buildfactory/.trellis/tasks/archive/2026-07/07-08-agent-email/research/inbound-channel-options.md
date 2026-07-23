# Research: 入站邮件物理通道选型（issue #208, agent email v1 只收不发）

- **Query**: 外部邮件 → foundagent.net 地址 → 本地 compose 集群 `POST /ingest/email` 的通道方案调研
- **Scope**: mixed（外部为主：Cloudflare / AgentMail / 替代品官方文档；内部：消费端接口确认）
- **Date**: 2026-07-08

---

## TL;DR 推荐

**Cloudflare Email Routing catch-all → Email Worker（哑巴：只把 raw MIME 流式写进 R2）→ 宿主机 Python poller 轮询 R2（list → get → stdlib `email` 解析 → POST `/ingest/email` → delete）。**

- 全链路 $0（Email Routing 入站免费无限量 + Workers/R2 免费额度远超邮件量级）
- 不需要公网入站端点、不需要隧道：poller 只发出站 HTTPS
- R2 强一致（含 list），delete-after-read 语义干净，天然是个持久缓冲队列
- 除 1-2 次 dashboard 点击（Email Routing 开域 + R2 API token），全部可 wrangler/REST API 脚本化
- 插拔性：邮件后端 = "一个 Worker + 一个 bucket + 一个 poller 脚本"，换后端只动 poller 一个文件（`/ingest/email` 契约不变）

**重要意外发现**：Cloudflare 已把 Email Routing 并入新产品 **"Cloudflare Email Service"**（收+发一体，旧 `developers.cloudflare.com/email-routing/*` 文档 301 到 `email-service/*`）。接收路由仍免费；只有**发送**需要 Workers Paid（$5/mo，v1 用不到）。另外 **Queues 现在有免费档**了（历史上要 Workers Paid），但消息上限 128 KB 放不下 raw MIME，只能当升级路线。

---

## 0. 前提约束（每个方案都按此评估）

- fleet 跑在操作员本机 docker-compose，**无稳定公网入站端点** → 任何 "provider webhook POST 给我们" 的方案都要么加隧道（cloudflared tunnel / ngrok，多一个常驻运维件），要么改成"云端暂存 + 本地轮询/长连接"。
- 消费端已存在：peripheral 常驻容器 `POST /ingest/email`（`peripheral/runner.py:77`），native dict `{from, subject, preview, link, message_id, to?}` → IME（`peripheral/adapters/email.py`）。缺的只是"外部邮件 → 宿主机上某个东西调这个端点"。
- 硬要求：邮件后端整体可插拔。v5 的 Gmail 中间层（app password + IMAP:993 防火墙 + 共享收件箱）是复杂度根源，应淘汰。
- v1 只收不发。地址形态：扁平 `name@foundagent.net`，catch-all 式申领，自建 registry 做 address → agent 映射。

---

## 1. 方案一：Cloudflare Email Routing + Email Workers（主候选）

### 1.1 免费额度与限制（2026-06 现行文档）

| 项目 | 数值 | 来源 |
|---|---|---|
| 入站路由费用 | **Workers Free / Paid 均 Unlimited、免费** | [Pricing](https://developers.cloudflare.com/email-service/platform/pricing/) |
| catch-all | 支持（dashboard 开关 / API `PUT .../rules/catch_all`，matcher `type:"all"`，action 可选 `drop/forward/worker`） | [Rules & addresses](https://developers.cloudflare.com/email-service/configuration/email-routing-addresses/), [REST API](https://developers.cloudflare.com/api/resources/email_routing/) |
| routing rules | 200 条/域 | [Limits](https://developers.cloudflare.com/email-service/platform/limits/) |
| destination addresses | 200 个/账户（**catch-all→Worker 模式完全用不到**，那是转发到外部邮箱才需要验证的） | 同上 |
| 域数量 | 30 domains/zone（含 apex + 子域） | 同上 |
| 入站单封上限 | **25 MiB**，超则拒收 | 同上 |
| 子域名路由 | dashboard Settings 里加子域即可，**无套餐门槛**（详见 §5 声明核验） | [Subdomains](https://developers.cloudflare.com/email-service/configuration/subdomains/) |
| subaddressing | 支持 `user+detail@`（RFC 5233），Settings 开关，`+detail` 保留在 `message.to` | [Rules & addresses](https://developers.cloudflare.com/email-service/configuration/email-routing-addresses/#subaddressing) |

### 1.2 Email Worker：能拿到什么

`email()` handler 收到 `ForwardableEmailMessage`（[Workers API](https://developers.cloudflare.com/email-service/api/route-emails/email-handler/)）：

```ts
interface ForwardableEmailMessage {
  readonly from: string;         // envelope MAIL FROM
  readonly to: string;           // envelope RCPT TO ← 这就是 resolved recipient localpart 的来源
  readonly headers: Headers;     // Subject / Message-ID / Date ...
  readonly raw: ReadableStream;  // 整封 raw MIME 流
  readonly rawSize: number;
}
```

- **完整 raw MIME 可得**，且是流 → 可直接 `env.BUCKET.put(key, message.raw)` 不占内存。
- Workers Free 额度：**100,000 requests/天**（email 触发按此计），**10ms CPU/次**（[Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/)）。邮件量级（每天几十几百封）对 100k/天九牛一毛。
- 官方明示：Free 档上复杂 email handler 可能 `EXCEEDED_CPU` 失败（[Limits — Routing to Workers on the Workers Free plan](https://developers.cloudflare.com/email-service/platform/limits/#routing-to-workers-on-the-workers-free-plan)）→ 又一个"Worker 保持哑巴"的理由。流式写 R2 是 IO-bound，CPU 占用极小。
- 本地可测：`wrangler dev` 支持模拟入站邮件（[Local development](https://developers.cloudflare.com/email-service/local-development/routing/)）。

### 1.3 Worker → 本地宿主机的暂存选型（核心对比）

无公网端点 → Worker 把邮件放进 Cloudflare 某个存储，宿主机 Python 出站轮询拉取。四个候选：

| | **R2**（推荐） | KV | Queues | D1 |
|---|---|---|---|---|
| 免费额度 | 10 GB 存储、**1M Class A/月**（put+list）、10M Class B/月（get）、**delete 免费** | 读 100k/天、**写 1k/天、list 1k/天** | **10k ops/天**（1 op = 64KB 读/写/删各计一次） | 5M 行读/天、100k 行写/天、5 GB |
| 单条大小 | 无实际限制（≫25 MiB） | 25 MiB（与入站上限恰好持平，顶界） | **128 KB ← 放不下 raw MIME** | 行级，不适合 blob |
| 一致性 | **强一致，含 list-after-write / delete**（[Consistency](https://developers.cloudflare.com/r2/reference/consistency/)） | 最终一致（秒~分钟） | 队列语义（ack/visibility timeout） | 强一致 |
| Python 侧 API | **S3 兼容 → boto3 标准姿势**；也有 CF REST API | REST API（list 受 1k/天卡死） | HTTP pull consumer（`POST .../messages/pull` + ack，官方支持任意语言）（[Pull consumers](https://developers.cloudflare.com/queues/configuration/pull-consumers/)） | REST query API（要 SQL/schema） |
| delete-after-read | `DeleteObject`（免费 op），干净 | delete 计入 1k 写/天 | **ack 原生**，最优雅 | DELETE 行 |
| 30s 轮询的月开销 | list ≈ 87k Class A/月 + 每封 1 put + 1 get，1M 额度内绰绰有余 | **list 2,880/天 > 1,000/天，直接爆额度** | 每次 pull 计 ops，10k/天够用但保留期仅 24h（Free 档不可调）——poller 宕机一天就丢信 | 读写额度够，但复杂度不值 |

**结论：R2 单件套。** 对象即消息、key 前缀即队列（如 `inbox/<ts>-<rand>.eml` + 自定义 metadata 存 envelope to/from）、delete 即 ack。Queues 的 pull-consumer 语义更漂亮，但 128 KB 上限逼出 "R2 存体 + Queue 传指针" 两件套，且 Free 档 24h 保留期是硬伤；等有 Workers Paid（发送邮件本来就要）时可平滑升级。KV 被 list 1k/天直接淘汰。

Worker 全文示意（真的就这么点）：

```ts
export default {
  async email(message, env, ctx) {
    const key = `inbox/${Date.now()}-${crypto.randomUUID()}.eml`;
    await env.MAIL_BUCKET.put(key, message.raw, {
      customMetadata: { to: message.to, from: message.from },
    });
  },
};
```

### 1.4 MIME 解析位置：Worker 还是宿主机

**推荐宿主机解析（Worker 保持哑巴）**：

- Python stdlib `email`（`message_from_bytes` + `policy.default`）足以取 subject/text 正文/Message-ID，零外部依赖，正好产出 `/ingest/email` 需要的 native dict；`to` 从 R2 customMetadata 拿（envelope RCPT TO，比解析 To: header 更可靠——BCC/别名场景 header 里根本没有本地址）。
- Worker 端解析的方案是 [postal-mime](https://www.npmjs.com/package/postal-mime)（官方文档推荐，v2.7.5，2026-06-25 仍在更新，MIT-0）。但 Free 档 10ms CPU 解析大邮件有 `EXCEEDED_CPU` 风险，且解析放云端会把"格式知识"锁进 Worker，违背可插拔。留作未来 Worker 需做内容路由时的选项。

### 1.5 部署故事（CLI-first 核验）

可脚本化的部分（全部有官方 CLI/API）：

| 步骤 | 工具 |
|---|---|
| 建 R2 bucket | `wrangler r2 bucket create foundagent-mail` |
| 部署 email Worker | `wrangler deploy`（email handler 不需要特殊路由声明，普通 Worker 即可） |
| 开启 Email Routing / 加 DNS | REST：`POST /zones/{zone_id}/email/routing/enable`、`POST /zones/{zone_id}/email/routing/dns`（[API](https://developers.cloudflare.com/api/resources/email_routing/)） |
| 设 catch-all → Worker | REST：`PUT /zones/{zone_id}/email/routing/rules/catch_all`，body `{"matchers":[{"type":"all"}],"actions":[{"type":"worker","value":["<worker-name>"]}],"enabled":true}` |
| 查状态 | REST：`GET /zones/{zone_id}/email/routing`（`status: ready/unconfigured/misconfigured`） |

注意：**wrangler 没有 email-routing 子命令**，routing 部分只能 REST API 或 dashboard；MX/SPF 记录在 dashboard "Onboard Domain" 流程中自动添加（zone 已在 CF 上，5-15 分钟生效，[Domain configuration](https://developers.cloudflare.com/email-service/configuration/domains/)），API 路径也有 dns 端点可全自动。**catch-all→Worker 不需要任何 destination address 验证**（那是 forward 到外部邮箱才要的人工点邮件环节）——这条帮我们消掉了 v5 式的人工验证。

### 1.6 方案一风险清单

1. **25 MiB 入站上限**：超限直接拒收（发件人收 bounce）。对 agent 用例可接受，需在 spec 里写明。
2. **Workers Free 10ms CPU**：Worker 里绝不做解析/转码，只 stream；若未来加逻辑，先测 CPU。
3. **产品重组进行时**：Email Routing 已并入 Email Service（文档 2026-06 大改版），REST 路径 `/email/routing/*` 目前未变，但需留意后续 deprecation 公告。
4. **轮询延迟**：收件延迟 = 轮询间隔（建议 30-60s；agent 邮件场景无实时性要求）。
5. **poller 宕机**：邮件积压在 R2——这其实是优点（10 GB ≈ 几十万封的持久缓冲，恢复后补拉），对比 Queues Free 的 24h 上限。
6. **R2 凭证**：S3 access key 要在 dashboard 手工创建一次（R2 → Manage API Tokens），属一次性人工操作。
7. **无内建垃圾邮件过滤**：catch-all 会收到全部投向该域的 spam；v1 可靠 IME 的 preview 让 agent 自行忽略，后续可在 Worker 加关键词/信誉过滤（官方有 [spam-filtering 示例](https://developers.cloudflare.com/email-service/examples/email-routing/spam-filtering/)）。

---

## 2. 方案二：AgentMail（agentmail.to）

v5 时代 `peripheral/adapters/email.py` docstring 里点过名（"IMAP/AgentMail fetch is wired in the runner as creds arrive"）。

### 2.1 现状（2026-07）

- 产品活跃：YC 系、**$6M seed**（官网横幅）、SOC 2 Type I/II、自称 100M+ 邮件投递，Garry Tan 站台背书。定位就是"给 AI agent 发邮箱"——inbox 即 API 资源。（[agentmail.to](https://agentmail.to/)）
- 能力面：inboxes/messages/threads/labels/attachments API、Python/TS SDK、MCP server、CLI、webhooks、**WebSockets**、IMAP/SMTP 兼容层。（[docs](https://docs.agentmail.to/llms.txt)）

### 2.2 定价（[pricing](https://agentmail.to/pricing)）

| | Free | Developer $20/mo | Startup $200/mo |
|---|---|---|---|
| inboxes | 3 | 10 | 150 |
| emails/月 | 3,000（100/天） | 10,000 | 150,000 |
| **custom domains** | **0（只能 @agentmail.to）** | 10 | 150 |
| webhook endpoints | 2 | 2 | 10 |

**要挂 foundagent.net 必须 Developer $20/mo 起。**

### 2.3 关键机制

- 自定义域：`client.domains.create("foundagent.net")` 一行 → 返回需配置的 DNS records（**MX 指向 AgentMail = 收件全托管给它**）。（[Custom domains](https://docs.agentmail.to/custom-domains.md)）
- 地址申领：`client.inboxes.create(username=..., domain=...)` 毫秒级建 inbox。**文档全文搜不到 catch-all**——地址必须显式创建，发往未创建地址的邮件预期被拒。我们的 registry 申领时多调一个 API 即可，不算硬伤但语义与"catch-all 兜底"不同。
- 到达本地的方式（这是它的亮点）：**WebSockets——出站长连接订阅 `MessageReceivedEvent`，官方明确"不需要公网 URL/ngrok"**，Python SDK 原生 async/sync 支持（[WebSockets](https://docs.agentmail.to/websockets.md)）；也可 REST 轮询 list messages 或 IMAP。完全适配我们"无公网端点"的约束。

### 2.4 评估

- **插拔性**：API 极干净，"channel 模块"会比 Cloudflare 版更薄（不用自己写 Worker）。但**反向耦合更深**：域名 MX、地址存在性、消息存储全在 vendor 手里，换掉它 = 换 MX + 重建全部 inbox。
- **vendor 风险**：种子期创业公司；定价/免费额度随时可变；倒闭或被收购时收件通道整体中断。把公司域名的 MX 交给它，比把 MX 交给 Cloudflare（域名本来就在人家 DNS 上）风险高一档。
- **成本**：v1 只收不发花 $240/年，买到的（webhook/websocket/线程模型/发送能力）大半用不上。
- 结论：**v1 不选，但它是"发送 + 双向对话"阶段最值得重估的候选**——届时 threads/drafts/deliverability 托管的价值才兑现。适配器接缝里保留它的位置。

---

## 3. 方案三：快速扫描（rule in/out）

- **ForwardEmail**（forwardemail.net）：开源可自托管、免费档即支持自定义域转发/wildcard/catch-all，有 REST API 与 webhook（alias 可直接指到 http URL），付费 ~$3/mo 有加密 IMAP/POP3 存储。但"到本地"只有两条路：webhook（**要公网端点**）或 IMAP 轮询（**回到 v5 的 IMAP:993 痛点**），没有"云端暂存+API 拉取"形态。排除；若哪天想彻底去 Cloudflare 化，它是转发层的开源备胎。（[forwardemail.net/en/faq](https://forwardemail.net/en/faq)）
- **ImprovMX**：纯转发起家（2013 年，自负盈亏）。Free：1 域、25 alias、500 封/天、含 API；**webhook 投递要 Premium $9/mo 且仍要公网端点**；无存储拉取 API。排除。（[improvmx.com/pricing](https://improvmx.com/pricing)）
- **Mailgun / SendGrid inbound parse**：Mailgun routes 有 `store()` 动作，raw MIME 存 ~3 天可经 Events API 拿 storage URL 拉取（理论上可轮询、不需 webhook，[Storing and Retrieving Messages](https://documentation.mailgun.com/docs/mailgun/user-manual/receive-forward-store/)），但要把 MX 指给 Mailgun、免费额度近年大幅收缩、计费面向发送方业务；SendGrid inbound parse 纯 webhook。两者都是"发送厂商的附赠品"，只收不发场景过重。排除。
- **自托管（Mailu / maddy / Postal）**：与"本地无公网"前提正面冲突——收 25 端口需要公网 IP + ISP 不封（住宅网络普遍封）、PTR/rDNS 不可控；即使只收不发也躲不开公网 SMTP 监听。除非未来整体迁 VPS，否则排除。

---

## 4. 汇总对比表

| 方案 | 成本 | 地址申领机制 | 邮件如何到本地 | 运维负担 | 插拔适配 |
|---|---|---|---|---|---|
| **CF Email Routing + Worker + R2** | **$0** | catch-all 全收，registry 只管映射（申领=改自家表） | Worker 写 R2，宿主 poller 出站轮询拉取后 delete | Worker+bucket 一次性部署；日常零维护 | ★★★ 后端=1 Worker+1 bucket+1 poller 文件；契约=R2 里的 .eml |
| AgentMail | $240/年起（custom domain） | registry 调 API 建 inbox（秒级，无 catch-all） | WebSocket 出站长连接（无需公网）或 REST 轮询 | 零基础设施，纯 SaaS | ★★ API 最薄但 MX/存储/地址全耦合 vendor |
| ForwardEmail | $0–36/年 | catch-all/wildcard | webhook（要公网/隧道）或 IMAP 轮询（v5 痛点回归） | 低 | ★★ 开源备胎价值 |
| ImprovMX | $0（webhook 要 $108/年） | catch-all | webhook（要公网/隧道） | 低 | ★ |
| Mailgun 等 | 计费复杂 | routes 表达式 | store+API 拉取 或 webhook | 中 | ★ 面向发件人的产品 |
| 自托管 | VPS 费用 | 全自由 | 本机即服务器 | **高**（deliverability/port 25/信誉） | ★★★ 但前提不成立 |

---

## 5. 声明核验：「CF 免费版 Email Routing 只覆盖 apex，子域名要付费/enterprise」

**结论：不成立，需要纠正。**

- 现行文档（2026-06-09 更新）：子域名在 dashboard **Email Routing → Settings → Subdomains** 直接添加，Cloudflare 自动加 DNS 记录，全文无任何套餐门槛表述。（[Subdomains](https://developers.cloudflare.com/email-service/configuration/subdomains/)）
- 上线公告（2023-10-26 博客）明说：*"You can use Email Routing with any subdomain of any zone in your account"*，并强调 *"there are no changes in pricing, and Email Routing is still free for Cloudflare customers"*。（[Email Routing subdomain support, new APIs and security protocols](https://blog.cloudflare.com/email-routing-subdomains/)）
- 追溯核验：Wayback Machine 2023-12-11、2024-05-20、2025-04-07 三个历史快照的 `email-routing/setup/subdomains` 文档均无 Enterprise/paid 限制，即该功能自 2023-10 上线起就是全套餐可用，不存在"曾经收费后来放开"的历史。
- 唯一确实收费的相邻事实，别混淆：**Email Sending**（出站，2025 年并入 Email Service 的新能力）需要 Workers Paid（$5/mo，含 3,000 封/月）；入站 routing 两档套餐都免费无限量。（[Pricing](https://developers.cloudflare.com/email-service/platform/pricing/)）

对我们的影响：`name@foundagent.net` 扁平地址本来就只用 apex，无所谓；但这意味着未来若想给 agent 发 `x@dept.foundagent.net` 之类的子域地址，同样免费可行（30 domains/zone 上限内）。

---

## 6. 推荐方案的最小人工操作清单（操作员）

前提：foundagent.net zone 已在 Cloudflare（active）。v5 用过 Email Routing 的话 MX 可能已存在——先跑 `GET /zones/{zone_id}/email/routing` 看 `status` 是否 `ready`。

1. **（可能可跳过）dashboard 一次点击**：Compute → Email Service → Email Routing → "Onboard Domain" 选 foundagent.net（自动加 MX/SPF，5-15 分钟生效）。API 党可改用 `POST .../email/routing/enable` + `.../email/routing/dns` 全脚本化。
2. **创建 R2 API token 一次**（dashboard → R2 → Manage API Tokens → Object Read & Write，限定 bucket）：拿 `access_key_id` / `secret_access_key` 给宿主机 poller（boto3，endpoint `https://<account_id>.r2.cloudflarestorage.com`）。
3. **创建 Cloudflare API token 一次**（scope: Zone → Email Routing Rules: Edit），供部署脚本设 catch-all。
4. 其余全自动：`wrangler r2 bucket create` → `wrangler deploy` → `PUT .../rules/catch_all`（action `worker`）。
5. 验收：给 `anything@foundagent.net` 发一封真邮件 → R2 出现 `.eml` → poller 打进 `/ingest/email` → agent inbox 出现 IME → R2 对象被删。

**人工操作合计：dashboard 2-3 次点击（域开通 + 两个 token），均为一次性动作**——符合 provisioning 纪律（一次性动作人工做，不留 repo 脚本）。

---

## 内部相关文件

| 文件 | 说明 |
|---|---|
| `peripheral/runner.py:77` | 常驻 HTTP listener，`POST /ingest/<source>`，本方案 poller 的投递目标 |
| `peripheral/adapters/email.py` | native email dict → IME 纯变换；docstring 名点 IMAP/AgentMail（本调研的 AgentMail 线索来源）；`message_id` 用于去重 → poller 应从 MIME `Message-ID` header 提取传入 |

## Caveats / Not Found

- AgentMail 文档中**未找到 catch-all** 的任何记载（llms-full.txt 全文搜索无结果）——按"无此功能"处理，但未经客服确认。
- AgentMail WebSockets 在哪个套餐档可用：pricing 页表格标注不清（文本抽取丢失勾选态），未能确认 Free 档是否含 WebSockets；反正 custom domain 已经要 $20/mo，不影响结论。
- Mailgun 当前免费档的入站额度细节未深挖（已因"MX 交给发送厂商 + 计费复杂"排除，不值得继续）。
- Cloudflare `POST .../email/routing/enable` 与 `POST .../email/routing/dns` 两组端点并存（疑似新旧两代 API），实际开通时以哪组为准需要实测；最坏情况退回 dashboard 点一次。
- 空的 Queues pull（无消息时的轮询请求）是否计入 10k ops/天免费额度，文档未写明——Queues 已非首选，仅升级路线时需澄清。
