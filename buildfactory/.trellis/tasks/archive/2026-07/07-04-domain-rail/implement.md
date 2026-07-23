# Implement — Domain rail

> 前置：design.md 已按 2026-07-06 用户裁决改版（一次性动作人工做不留脚本、GA4 交付 skill），待用户审。Step 0 是用户侧人工门；GSC 线（Step 1-3）等 Step 0 前两项，GA4 线（Step 4）可后置。

## Step 0 人工前置（用户）｜阻塞门

- [x] `google-sa.json`：GCP 项目 + SA + 启用 `searchconsole` / `analyticsadmin` / `analyticsdata` 三个 API + JSON key → `accounts/foundagent/google-sa.json`（SA 不需要 GCP IAM 角色）
- [x] GSC UI 验证（design D1 四步）：添加 Domain property `foundagent.net` → TXT 贴 CF apex（可由 session 代放）→ 点验证 → SA 邮箱加 Full 权限
- [x] （GA4 线，可后置）analytics.google.com 人工建 account（接受 ToS）→ SA 邮箱加 Editor → `GA4_ACCOUNT_ID=` 写入 secrets.env

## Step 1 SA 权限门检（design D2）

- [x] host 侧用 SA 凭证 inline 调 `GET webmasters/v3/sites`，确认含 `sc-domain:foundagent.net`（不留文件）

## Step 2 GSC MCP e2e（承接 mcp-loadout AC2）

- [x] researcher 容器 `claude -p` 经 gsc MCP 列属性，回包含 `sc-domain:foundagent.net`（GSC_OK 断言式 prompt）

## Step 3 子域自助：README 约定 + e2e

- [x] accounts/README.md 新章节：GSC 人工验证四步记录（已完成态）、子域自助用法（CF API/wrangler）、命名建议、两条禁则（apex 验证 TXT 不许删；先查再建）、Domain property 覆盖全子域说明
- [x] e2e：researcher 容器内 CF token 建 + 删 `_domain-rail-e2e.foundagent.net` TXT

## Step 4 GA4 skill（design D5，交付不执行）

- [x] `agents/assets/skills/provision-ga4/SKILL.md`：properties.create + dataStreams.create → measurementId 去向；三道检验内容齐备（系统特定路径/压制默认/取舍标准）
- [x] README GA4 章节：人工前置三步 + 「首个站点上线时由 agent 用 skill 执行」触发条件

## 收尾

- [x] journal + spec 触点检查（补充 backend account-package contract，记录 domain rail env/权限/验证契约）
- [ ] commit + 归档

## Review gates

- design 改版审阅（用户）→ 才 task.py start
- Step 0 前两项 → 才能跑 Step 1-2
- Step 1 门检结果向用户报告（属性验证 + SA 权限生效）
- Step 4 skill 按三道检验 review
