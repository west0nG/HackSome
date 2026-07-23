# Resend 域名开通事实存档（M1，2026-07-10）

## 结论：零操作完成

foundagent.net 在本 Resend 账号早已注册并 verified（v5 时代 2026-05-16 创建），DNS 记录一直留在 Cloudflare 未删。本次 M1 只做了核验，未写任何 DNS。

## Resend 侧

- domain id: `a393db4e-315d-48e7-a5e1-2faf58a742f4`
- status: verified；region: us-east-1；capabilities: sending=enabled, receiving=disabled
- 记录（全部 verified）：
  - DKIM TXT `resend._domainkey.foundagent.net`
  - MX `send.foundagent.net` → feedback-smtp.us-east-1.amazonses.com (pri 10)
  - SPF TXT `send.foundagent.net` → `v=spf1 include:amazonses.com ~all`
- open_tracking / click_tracking: 均 false（保持——追踪重写链接会毁验证类邮件的观感）

## 收件轨核验（2026-07-10 dig 实测）

- 根域 MX：route1/2/3.mx.cloudflare.net（CF Email Routing，收件轨完好）
- 根域 SPF：`v=spf1 include:_spf.mx.cloudflare.net ~all`（未动）
- Resend 记录全在 `send` 子域与 `resend._domainkey`，与根域零冲突——design §6 的「不动根域」约束天然满足

## API key

- `RESEND_API_KEY` 已入 `accounts/foundagent/secrets.env`（2026-07-10 用户提供；该文件 gitignored，经 docker-compose env_file 注入全部 agent 容器）
- key 可用性已验证（domains list/get 调用成功）
