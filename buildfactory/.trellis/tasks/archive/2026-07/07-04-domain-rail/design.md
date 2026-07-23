# Design — Domain rail：foundagent.net 子域名自助 + GSC/GA4 接线

> 依据：prd.md + research/google-programmatic-verification.md（三问题全核实：GSC 全程序化可行、GA4 半人工、CF token 读写删实测通过）。

## 0. 全景（2026-07-06 改版：一次性动作人工做不留脚本、反复动作交付 skill）

```
人工一次（用户）                      本任务交付（程序化/资产）
────────────────                     ─────────────────────────────────────────
google-sa.json（GCP SA + 3 API）      GSC MCP e2e（researcher 容器真凭证，
GSC UI 验证 + SA 加 Full 权限          承接 mcp-loadout AC2）
（TXT 可由 session 代放 CF apex）      子域自助：README 约定 + 容器内 DNS e2e
GA4 account + SA=Editor               agents/assets/skills/provision-ga4/
+ GA4_ACCOUNT_ID 入 secrets.env       （skill，交付不执行，首个站点上线时
                                       agent 自己跑：property + stream → G-XXXX）

之后每个 agent：CF token 自助开子域（CNAME→Vercel 等）——与 Google 侧完全解耦
```

## 1. 关键决策

### D1 一次性动作不留脚本工件（2026-07-06 用户拍板）

GSC 验证是一辈子一次的动作，不值得一个入库脚本。改用户 UI 路径，步骤（进 accounts/README.md）：

1. search.google.com/search-console → 添加资源 → **域**（Domain property）→ `foundagent.net`
2. 复制给出的 TXT（`google-site-verification=…`）→ 贴 Cloudflare apex（name=`foundagent.net`）——可由 session 用 CF token 代放
3. 回 UI 点验证（Cloudflare 权威 NS 秒级生效，一般一次过）
4. 设置 → 用户和权限 → 添加 SA 邮箱 → **Full** 权限（mcp-gsc 读数据够用）

相对原程序化方案的额外收益：属性 owner 直接是用户人类账号（UI 天然可见），原「SA 当 owner + delegation API 把用户加回来」步骤及其格式坑整体消失；SA 只是读数据的 user，权限语义更干净。程序化五步（research §1）留档作 fallback，不实现。

### D2 SA 权限核验（代替原脚本冒烟）

用户完成 D1 后，session 侧用 SA 凭证调一次 `GET webmasters/v3/sites`（scope `auth/webmasters.readonly` 即可）确认回包含 `sc-domain:foundagent.net`——这是 Step 2 e2e（researcher 容器 MCP）之前的快速门检。host 侧跑，`google-auth`/`requests` 在 `.venv-cua` 已有，不引入依赖、不留文件（inline 一次性）。

### D3 apex TXT 是永久资产

Google 周期性复查 ownership，删 TXT = 属性失效。写进 accounts/README.md 子域约定的第一条禁则；provision 脚本对该记录只增不删。

### D4 子域自助约定（README 章节，不建代码/登记册）

- DNS 即登记册：agent 用 `CLOUDFLARE_API_TOKEN` 直接建/删记录（API 或 wrangler），命名建议 `<product>.foundagent.net`。
- 两条禁则：①不动 apex 的 `google-site-verification=` TXT；②不动别的 agent 已占用的名字（先 `GET dns_records` 查再建）。
- Domain property 覆盖 `*.foundagent.net` 全部子域 ⇒ 开新子域零 Google 侧动作，GSC 数据自动归入同一属性。

### D5 GA4 = skill 交付、执行后置（2026-07-06 用户拍板：反复用的能力归 fleet，用 skill 不用 repo 脚本）

落点 `agents/assets/skills/provision-ga4/SKILL.md`（可带内嵌 python/curl 片段，参考 design-asset 带 scripts/ 的先例）。内容照 research §2：`properties.create`（parent=`accounts/$GA4_ACCOUNT_ID`）+ `dataStreams.create` → measurementId 交给建站流程埋 gtag。**本任务交付 skill、不执行**（无站点时 property 无意义）。

三道检验（[[skill-design-no-generic-for-llm]]）：
- ①系统特定：SA key 恒在 `/account/google-sa.json`、`GA4_ACCOUNT_ID` 读 secrets.env、measurementId 的去向（建站流程 gtag 埋码）。
- ②压制 LLM 默认：**不要**试图程序化建 account（ToS 必须人工签，见 research §2）、不走 OAuth 流、不每站开新 account；缺 `GA4_ACCOUNT_ID` 时报人工前置清单而不是绕路。
- ③非平凡取舍：站点可公网访问后才建 property（不提前占位）；timeZone/currencyCode 用公司约定而非 API 默认。

人工前置（建 account 接受 ToS + SA 加 Editor + `GA4_ACCOUNT_ID` 入 secrets.env）写 README，与 GSC 线并行不阻塞。

### D6 e2e（AC 对应）

- **GSC e2e**（承接 mcp-loadout AC2）：D1/D2 完成后，researcher 容器 `claude -p` 经 gsc MCP 列出属性，断言含 `sc-domain:foundagent.net`。新属性无流量数据，「真实响应」以 list_properties 为准（Search Analytics 空结果是正常态，不作断言）。
- **子域 e2e**：researcher 容器内用容器 env 的 CF token 建 + 删一条 `_domain-rail-e2e.foundagent.net` TXT（证明 agent 自助路径通，用完即删——与 D3 的永久 TXT 无关）。

### D7 测试姿态：无单测，e2e + skill review 即验收

不再有任何入库脚本；skill 是文档资产（现有 `agents/assets/skills/` 无单测惯例），验收 = 两个 e2e（D6）+ skill 过三道检验的 review。repo 现有单测不受影响（零 runtime 代码改动）。

## 2. 风险

- **SA 权限不够 mcp-gsc 读**（UI 加的权限级别选低了）：D2 的门检会当场暴露；升到 Full/Owner 即解。
- **UI 验证一次不过**（TXT 未生效就点验证）：Cloudflare 秒级生效，等 1-2 分钟重点即可；极端情况 fallback 程序化路线仍在 research/ 留档。
- **CF token 泄漏面扩大**（所有 agent 容器都能改 DNS）：与用户既定 permissions stance（先给足）一致；域名本身是给 agent 随便用的资产，接受。

## 3. 兼容 / 回滚

- 零 runtime 代码改动：mcp.json / agent_loop / overlay 全不动（gsc server 配置在 mcp-loadout 已就位）。
- 回滚 = 删 Search Console 属性 + 删 apex TXT（人工决策，任何自动化不碰）；子域记录随建随删。
