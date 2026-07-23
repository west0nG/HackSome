# PRD — agent 发件轨（Resend）

## 背景

- 07-08 邮件轨 v1 只做收件（CF catch-all → Worker → R2 → poller → IME），D1 决策明确「发件后置独立任务，届时搬 v5 的 Resend+配额设计」。本任务就是那个任务。
- 已有基础：mailbox 注册表（认领地址、owner/receivers、AGENT_KEY 身份门）、claim-mailbox / check-email 两个 fleet skill、`RESEND_API_KEY` 已入 `accounts/foundagent/secrets.env`（2026-07-10 用户提供，docker-compose env_file 自动注入容器）。
- v5 发件设计已调研（archive/07-08-agent-email/research/v5-email-stack.md）：三道门 + 先记账再发 + 配额是 deliverability 刹车。

## Requirements

- R1 发件通道：agent 能以自己认领的 `<name>@foundagent.net` 为 From，向任意外部邮箱发件（Resend API，纯 stdlib 调用，不引 SDK）。
- R2 身份门（结构强制，非文案）：From 地址必须在注册表中存在，且调用者（AGENT_KEY）是该地址的 receiver（owner 或共享 receiver 均可发）；否则拒绝。
- R3 配额刹车：公司级 24h 滚动配额（默认 30）+ 单地址 24h 滚动配额（默认 15），env 可调；账本先 RESERVE 再调 HTTP——发送失败也占额、不漏记，防重发风暴。
- R4 fleet skill：`send-email` 落盘 `agents/assets/skills/` 且接进全部 5 个角色 yaml（skill 落盘≠可见的既有坑）；内容过三道检验（系统特定命令与语义、压制 LLM 默认、非平凡取舍——deliverability 连坐、配额是共享资源、发件=对外动作）。
- R5 域名一次性开通：foundagent.net 在 Resend 完成验证（DNS 记录经 Cloudflare API 写入）；**不动根域 MX/SPF**，收件轨零影响；provisioning inline 做、不留 repo 脚本。

## Constraints

- 收件链路（catch-all/Worker/R2/poller/注册表语义）原样不动。
- key 直接进容器 env（Stripe 先例、permissions stance）：CLI 配额门是 deliverability 刹车，不当安全墙设计。
- 代码形态对齐 mailbox.py 既有惯例：append-only jsonl + reduce-on-read + flock + 身份门 + fail-closed。

## Acceptance Criteria

- AC1 CLI 单测：身份门（未认领/非 receiver 拒）、双配额（到线拒且提示还剩什么额度/何时恢复）、RESERVE→HTTP→回填账本序、并发 flock，Resend HTTP 全 mock。
- AC2 真 e2e 闭环：域名在 Resend 显示 verified；容器内以认领地址真实发一封到本域另一认领地址，经收件轨回流进目标 agent inbox（IME 可见）——全程无人工收信。
- AC3 skill 可见性：5 个角色 yaml 均含 send-email；容器内 agent 实际可见（对齐 deploy-site 修过的接线面）。
- AC4 拒绝路径真跑（非单测）：容器内用未认领地址发→拒；把配额压到 1 再发第二封→拒且文案给出指引。

## Out of scope

- 群发/营销序列、退订管理、bounce/complaint webhook 处理（后置，Resend 侧数据在，需要时再接）。
- 发件历史查询界面/命令（账本 jsonl 本身可读，够用）。
- 收件方为本域时走内部短路（照样走真实 SMTP 外环，闭环测试正好依赖这一点）。
