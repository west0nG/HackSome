# v5 邮件栈调研（origin/v5）

> 调研时间：2026-07-08。目的：为 issue #208（agent 邮件身份）设计做参考。
> 源码位置：`origin/v5:solvo/skills/email_{identity,receive,send}/`，设计文档 `origin/v5:docs/{archive/,}superpowers/`。

## 整体链路

```
外部邮件 → Cloudflare Email Routing catch-all (*@foundagent.net)
        → 转发到一个共享 Gmail 收件箱（operator 的 Gmail + app password）
        → 容器内 scheduler poller 每 tick 走 IMAP 轮询 Gmail
        → 按 To: localpart 精确匹配本 workspace 的 identity registry
        → 命中的写入 .solvo/inbox/pending/<uid>.json
        → inbox bridge 在每个 production tick 把 pending 文件变成 DAG 节点
        → agent 在正常执行循环里看到并处理

agent 发信 → email_send skill（三道门）→ Resend API（From: <localpart>@foundagent.net）
```

## 三个 skill

### email_identity（身份注册）
- agent 自助 `claim(localpart)`，完全自选名字（`hello`、`founder`、`support`…），不再是早期的 `<purpose>-<4hex>` 随机别名。
- 校验：小写字母/数字/`-_.`，2-32 字符，首尾必须字母数字，禁 `+` 别名（路由会当成不同 localpart）。
- 保留名单：`postmaster/abuse/mailer-daemon/noreply/no-reply/donotreply/do-not-reply`。
- 双注册表：per-workspace（`.solvo/email_identities.json`，上限 5 个，`SOLVO_MAX_EMAIL_IDENTITIES` 可调）+ 全局（`~/.solvo/email_registry.json`），全局唯一，flock 锁防两容器并发抢同名。claim 幂等。

### email_receive（收件）
- stdlib `imaplib` 封装；后期演进为**容器内** poller（默认 60s 间隔），只按 To/Cc/Delivered-To 的 localpart 精确匹配，**无内容过滤**——OTP/magic link/验证链接全部原样落盘。
- 状态文件：`.solvo/state/inbox_poller.json`；投递 `.solvo/inbox/pending/`，处理后挪 `processed/`，不匹配的进 `unmatched/`。
- Iron Law（SKILL.md）：容器内 egress 防火墙 RST TCP:993，agent 绝不能直接 IMAP，只能读 pending 文件。
- 光写 JSON 不够：必须有确定性的 inbox bridge 在 tick 里把 pending 变成工作节点，否则 agent 永远看不到（v5 曾经踩过这个洞）。bridge 按 UID 去重（`.solvo/state/inbox_bridge.json`）。

### email_send（发件）
- Resend API，`RESEND_API_KEY` 只在 `send()` 内读取（import 时惰性）。
- 三道门：① localpart 必须在本 workspace registry；② per-workspace 滚动 24h 配额（默认 30，`SOLVO_RESEND_DAILY_PER_WS`）；③ per-identity 配额（默认 15，`SOLVO_RESEND_DAILY_PER_IDENTITY`）。
- 配额账本先 RESERVE 再调 HTTP（发送后失败也不会漏记 → 防重复发送），成功后回填 resend id；flock 串行化并发 lane。
- 发送成功自动 `touch()` registry（v5 教训：靠 agent 自觉 touch 会忘）。

## 演进史（Phase A→D + 2026-06-02 重设计）
1. **Phase A**：identity registry（PR #44）。
2. **Phase B**：host 端 inbox_poller 改为 registry-aware 路由（PR #47）。
3. **Phase C**：outbound 配额 + 强校验（email_send）。
4. **2026-06-02 workspace-email-identities**：随机别名 → 自选专业 localpart；host 端共享 poller → 容器内 poller；补 inbox bridge。

## v5 自己记录的坑（直接影响 v6 设计）
1. **随机 hex 别名发冷邮件不专业**（`evidence-packet-outreach-f3ae@` 一眼机器人）→ 自选 localpart。
2. **host 端 poller = `solvo run` 之外的运维状态**，host 跑法和 Docker 跑法行为不一致 → 收件路径必须归属 agent 运行时自己。
3. **Haiku 内容分类会丢 OTP**（`inbox_match.txt` 关键词/正则 + 廉价分类，两个 workspace 撞词、非标准 OTP 排版漏掉）→ 只做 localpart 精确匹配，零内容过滤。
4. **单域名 deliverability 连坐**：Gmail 2025+ 启发式约 ~15 封冷邮件/天/alias 就可能把整个域打进垃圾箱 → per-identity/per-ws 配额是刹车，Resend 免费档 100/天还是 operator 级共享。
5. **容器 egress 封 993**：曾让 agent 直连 IMAP 挂死 → 明确写进 SKILL.md 的 Iron Law。
6. **收到邮件 ≠ agent 看到邮件**：pending JSON 必须有确定性 bridge 进执行循环。

## 对 v6 的映射
- **v6 已有落点**：`peripheral/adapters/email.py` 的 `to_ime()` 就是为这条链路留的 seam；IME/收件箱事件机制 = v5 inbox bridge 的等价物，且已经比 v5 的 DAG 注入更规整。缺的只是「路由 → 存储 → poller」的上游。
- **v5 链路里最可疑的一环是 Gmail 中间层**：catch-all → Gmail → IMAP 引入了 app password、993 防火墙坑、共享收件箱。issue #208 讨论点 1 提示可以用 Cloudflare Email Routing 直接处理（Email Workers 可把入站邮件交给 worker → 写入自有 store → agent/harness poll），有机会整层去掉 Gmail。
- **身份模型基本可以照搬**：claim 语义、localpart 校验、保留名单、全局唯一注册表、per-agent 上限。v6 的对应物是 per-agent 而非 per-workspace；全局注册表的落点要对齐 v6 的 company-state/registry 形态。
- **v1 receive-only 与 v5 经验一致**：解锁 magic-link/验证流只需要收件；发件的全部难点（deliverability、配额、RESERVE-先行账本）v5 有完整设计，后置时可直接搬。
