# 真实链路验证（plumbing live，2026-07-08）

> M6 第一阶段：云端 provisioning + 全链路真邮件验证。AC1 完整 agent 场景（任务中途 peek + 非首条）与 AC2 fan-out 见后续记录。

## 云端 provisioning（全 API，零 dashboard 点击）

- Global API Key + `westonguo@outlook.com` 验证通过；只读核对纠正了用户口头映射：**account=106cf78c…、zone=fde57901…**（用户原话记反了），已修正 `vm/.env.local`。
- Email Routing on foundagent.net：**已是 enabled+ready**（v5 遗产），MX/SPF/DKIM 齐全（dig + `/email/routing/dns` 双验证）。
- R2 bucket `foundagent-mail`：wrangler 创建成功。
- Worker `foundagent-mail-ingress`：`wrangler deploy` 成功（version `1ba83a2f`）；修了一处——邮件 Worker 无 HTTP 面须 `workers_dev: false`，否则 deploy 在 workers.dev 发布步骤报错（commit `0231e43`）。
- catch-all `*@foundagent.net` → worker：REST `PUT .../rules/catch_all` 成功并 GET 回读验证。
- R2 S3 凭证冒烟：put/list/get(+customMetadata)/delete 全过。
- **代理虚惊**：此前 R2 端点 TLS 全挂是因为在探记反的账号子域；正确子域下走代理/直连都通，**poller 容器无需代理配置**。

## 真邮件全链路（外部 → agent inbox）

1. 用户从 Gmail（westongu@usc.edu）发真邮件 → `plumbing-test@foundagent.net`（主题 "hey"）。
   - 注：用户发的第一封始终未达（疑发件侧问题/greylist，未见 worker 事件），第二封 1.2s 内走完 worker。
2. `wrangler tail` 抓到事件：`outcome: ok`、无异常、`rcptTo: plumbing-test@foundagent.net`、rawSize 8980。
3. R2 出现 `inbox/1783504980333-….eml`（8980B，metadata `{from: westongu@usc.edu, to: plumbing-test@foundagent.net}`）。
4. 宿主机半段（隔离环境：scratchpad 注册表 + 本地 peripheral runner :8911）：
   - `AGENT_KEY=growth mailbox claim plumbing-test` → `resolve()` 返回 `['growth']`；
   - 真 R2 `run_once` → `{'processed': 1, 'unmatched': 0, 'deferred': 0}`；
   - growth inbox 收到 IME：id=`<message_id>:growth`、text=`新邮件：westongu@usc.edu · hey`、body 首行不可信标注 + `（发往 plumbing-test@foundagent.net）`；
   - R2 对象移入 `processed/`，`inbox/`、`unmatched/` 均空；
   - agent 视角 `receive_tool --peek` 原样看到该 IME（只读）。

## 结论

外部邮件 → MX → catch-all → Worker → R2 → poller → `/ingest/email` → adapter → agent inbox → peek，**每一段都在真实环境验证通过**。剩余：AC1 完整 agent 场景（fleet 内、任务中途、非队列首条、真实服务 magic-link）与 AC2 双接收者 fan-out。

## 遗留提醒

- scratchpad 临时注册表里的 `plumbing-test` 认领是一次性验证用，不进生产注册表；生产 fleet 的 `state/<company>/mailboxes/` 仍是空的。
- Cloudflare 凭证（Global Key）只在 host 侧 `vm/.env.local`；agent 容器只拿 R2 S3 密钥对（mail-poller 服务），符合隔离承诺。
