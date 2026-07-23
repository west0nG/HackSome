# Design — agent 发件轨（Resend）

## 1. 组件边界

新模块 `orchestration/email_send.py`，CLI 入口 `python3 -m orchestration.email_send`。

- 不塞进 mailbox.py：mailbox 是纯本地身份注册表；发件是带外部副作用的通道 + 配额账本，关注点不同（v5 同样拆分）。发现性由 skill 承担，不靠子命令堆叠。
- 依赖方向：email_send → mailbox（复用 `reduce_mailboxes`/`read_registry` 做身份门），反向零依赖。
- 收件链路零改动。

## 2. CLI 契约

```
python3 -m orchestration.email_send \
  --from <localpart> --to <addr> --subject <s> \
  (--text <body> | --text-file <path>) [--html <h> | --html-file <path>] \
  [--from-name "<display name>"]
```

- `From:` 组装为 `"<display>" <localpart>@foundagent.net>`，display 缺省用 localpart。
- 退出码沿用 mailbox 惯例：0 成功 / 1 校验拒绝（身份门、配额、参数）/ 2 机制错误（账本不可读、HTTP 失败、缺 key）。
- 成功打印 resend id；失败如实打印 Resend 返回的错误体（agent 要靠它自诊断，不粉饰）。

## 3. 三道门（v5 移植，均结构强制）

1. **身份门**：`AGENT_KEY ∈ receivers(from)`。owner 或共享 receiver 均可发——能收到回信的身份才有资格用这个名字说话；owner-only 会废掉共享地址（hello@）的用途。未认领地址 → 拒且指引先走 claim-mailbox。
2. **公司级配额**：24h 滚动窗口内全公司 reserve 计数 < `EMAIL_SEND_DAILY_COMPANY`（默认 30）。
3. **单地址配额**：同窗口内该 from 的 reserve 计数 < `EMAIL_SEND_DAILY_PER_ADDRESS`（默认 15）。

默认值直接搬 v5（30/15），在 Resend 免费档 100/天之下留 3x 余量。拒绝文案必须给出：当前用量/上限 + 最早一条占额何时滚出窗口（何时恢复）——错误即指引，mailbox CAP 的既有姿态。

**配额 env 的落点（07-10 用户问定）**：默认值写死在 email_send.py（MAILBOX_CAP 同款形态），不进任何配置文件；运营要调时加进 docker-compose.yml 的 `x-agent-env` 锚（全 fleet 生效）；不放 secrets.env（该文件语义是凭证）。账本落 `MAILBOX_ROOT=/shared/mailboxes` 共享挂载 → 公司级配额跨容器天然一本账。

## 4. 账本（先记账再发）

`<MAILBOX_ROOT>/send_ledger.jsonl`，append-only 事件：
`{ts, event: "reserve"|"sent"|"failed", id, from, to, by, detail}`

- **占额以 reserve 计**；sent/failed 只是结果回填。失败不退额——这本身就是刹车（防重发风暴），v5 原语义。
- 锁序：`.send.lock` flock 内【reduce 配额 + append reserve】→ 出锁 → HTTP → 再入锁 append sent/failed。HTTP 永远在锁外，发件慢不阻塞他人。
- 独立锁文件，不复用 `.registry.lock`（认领与发件互不阻塞）。
- 账本不存在 = 零用量，无迁移。

## 5. Resend 调用

- `POST https://api.resend.com/emails`，`Authorization: Bearer $RESEND_API_KEY`，body `{from, to: [addr], subject, text|html}`。
- `Idempotency-Key: <reserve id>`——网络超时重试不会双发。
- stdlib `urllib.request`，timeout 30s，不引 SDK（R1）。key 只在发送函数内惰性读取（v5 惯例）。

## 6. 域名验证（一次性 provisioning，inline 不留脚本）

1. Resend API `POST /domains` `{name: "foundagent.net", region: "us-east-1"}` → 返回待写记录（`send` 子域 MX + SPF TXT、`resend._domainkey` DKIM TXT）。
2. Cloudflare API 把记录写进 zone——**全部在子域，根域 MX/SPF（CF Email Routing 收件）一条不动**。
3. `POST /domains/{id}/verify` → 轮询至 verified。
4. 过程与记录 ID 落 `research/resend-domain-setup.md`（事实存档，非脚本）。

## 7. send-email skill（三道检验落点）

- **系统特定**：确切命令；先 `mailbox mine` 确认可用身份；配额是公司共享资源（你只是 30/天里的一员）；失败也占额。
- **压制 LLM 默认**：①失败就重试/多发几封 → 禁止，先读错误体，配额不退；②为发件注册新地址 → 复用身份（claim-mailbox 既有立场）；③冷邮件冲动 → v5 坑：~15 封/天/alias 可能把整域打进垃圾箱，全公司连坐，发陌生人前想清楚必要性。
- **非平凡取舍**：对内 agent 沟通走 hub 消息、对外人类才用邮件；共享地址发信 = 以该职能口吻说话；外发内容即公司形象（关联 de-ai-ify）。
- 接线：skill 落盘 + 5 个角色 yaml `skills:` 追加（deploy-site 修过的可见面）。

## 8. 测试与 e2e

- 单测 `orchestration/tests/test_email_send.py`：tmpdir MAILBOX_ROOT（mailbox 测试形态），monkeypatch HTTP 函数；覆盖三道门、账本序、并发 flock、失败占额、拒绝文案含恢复时间。
- 真 e2e 闭环：容器内认领地址 A 发往本域认领地址 B → Resend 真实外发 → CF Email Routing 收件轨回流 → B 的 agent inbox 出现 IME。分钟级延迟正常（check-email 已教耐心等待）。
- 拒绝路径真跑：未认领 from；`EMAIL_SEND_DAILY_COMPANY=1` 压额发第二封。

## 9. 兼容与回滚

纯增量：新模块 + 新测试 + 新 skill 目录 + 5 个 yaml 各追加一行。回滚 = 删文件 + 回退 yaml。DNS 记录独立于收件轨，删除即回滚 Resend 侧，不影响收件。
