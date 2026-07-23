# Domain rail：foundagent.net 子域名自助 + GSC/GA4 属性接线

> 父任务：`07-03-capability-provisioning`。承接 `07-03-mcp-loadout`（已归档）移交的 AC2-GSC 半场。

## 背景（2026-07-04 已核实）

- 用户已备根域名 **foundagent.net**：DNS 托管 Cloudflare（zone `fde57901…`，active），apex A 记录指向 Vercel（76.76.21.21）。
- 账号包 `accounts/foundagent` 的 `CLOUDFLARE_API_TOKEN` **已能读到该 zone**——子域名 DNS 自动化路径通（写权限待任务内核实）。
- 用户裁决：**子域名每个 agent 随便用**（权限从宽，先给足）。
- mcp-loadout 遗留：researcher 的 gsc server 已 pin 进镜像 + 配置，只等一个已验证 GSC 属性做真凭证 e2e。

## 目标

把 foundagent.net 变成 fleet 自助能力：agent 可自助开子域名部署站点；Google 数据回路接通（gsc/ga4 server 已全量铺给所有角色——2026-07-06 用户拍板 MCP 不做角色预设，全员全量集）。

## 需求（research 已核实定稿，见 research/google-programmatic-verification.md）

1. **子域名自助**：agent 用账号包 CF token（API/wrangler）自助建/删 DNS 记录；约定最小化（不建登记册——DNS 本身就是登记册），用法写进 accounts/README.md。CF token 写权限已实测通过（2026-07-04 建/删 TXT 成功）。
2. **GSC 属性验证（2026-07-06 用户拍板改线：UI 一次性验证，不留脚本工件）**：一次性动作人工做——用户在 Search Console UI 添加 Domain property `foundagent.net`，把 TXT 贴到 Cloudflare apex（可由本 session 代放）后点验证，再把 SA 邮箱加为该属性的 Full 权限用户（供 mcp-gsc 读数据）。Domain property 覆盖全部子域，开新子域无需任何 Google 侧动作。程序化路线（Site Verification API，research 已核实可行）留档 research/ 作 fallback，不实现。
3. **补跑 GSC e2e**（mcp-loadout AC2 移交项）：researcher 容器内经 MCP 取回真实 GSC 响应。
4. **GA4 路线（research 定稿：半人工；2026-07-06 用户拍板改形态：skill 而非脚本）**：account 创建含 ToS 人工接受，SA 无法代签 → 人工一次（建 account + SA 邮箱加 Editor + `GA4_ACCOUNT_ID` 入 secrets.env）；之后 property/data stream 用 Admin API 全程序化（返回 measurementId）。反复用的能力归 fleet：交付形态 = `agents/assets/skills/` 下的 skill（过「三道检验」），由 agent 在首个站点上线时自己执行；不交付 repo 脚本、本任务不执行。
5. **人工前置（用户侧，2026-07-06 随改线更新）**：
   - `google-sa.json`：GCP 项目 + SA + 启用三个 API（`searchconsole` / `analyticsadmin` / `analyticsdata`；UI 验证路线不再需要 `siteverification`）+ JSON key → `accounts/foundagent/google-sa.json`。SA 不需要任何 GCP IAM 角色。
   - GSC UI 验证 + SA 邮箱加 Full 权限（见需求 2，~5 分钟）。与 google-sa.json 一起构成 GSC 线的阻塞门。
   - GA4 account 人工建 + SA 加 Editor（GA4 线，不阻塞 GSC 线，可后置）。

## 约束

- 凭证走账号包契约（secrets.env + `/account:ro`），不写死。
- agent 权限从宽（先给足，安全收窄后置）。
- CF token 权限不足（如缺 DNS edit）时报用户升级 token，不绕路。
- 与 per-role mcp.json 机制零改动衔接（gsc/ga4 server 配置已就位且自 2026-07-06 起全角色全量铺开，本任务只补 Google 侧资产）。

## 验收标准（草案）

- [ ] agent 容器内经 MCP 取回一次真实 GSC 响应（承接 mcp-loadout AC2，不可 mock；gsc 已全员铺开，任一角色容器均可，默认沿用 researcher）。
- [ ] foundagent.net 成为 Search Console 已验证属性且 SA 有读权限；人工步骤最小化并全部记录在 accounts/README.md。
- [ ] 任一 agent 容器内用账号包 token 新建 + 删除一条子域名 DNS 记录成功（e2e）。
- [ ] 子域名使用约定 + Google 侧前置清单写入 accounts/README.md。
- [ ] GA4 skill 交付（`agents/assets/skills/`，过三道检验）+ 人工前置清单落盘；执行等首个站点上线，不在本任务验收。
