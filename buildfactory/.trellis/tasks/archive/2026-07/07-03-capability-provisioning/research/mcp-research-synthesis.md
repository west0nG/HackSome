# MCP 需求与选型综合报告（2026-07-03）

> 四路调研综合：①需求侧（仓库证据盘点）②供给侧·业务运营 MCP ③供给侧·开发基建 MCP + 集成模式 ④SEO 专项。
> 结论供「mcp-provisioning」任务立项时直接取用。

## ★ 最终版（用户三项裁决后）

用户裁决：①不从现有 skill 反推，目标栈 = GitHub / Vercel / Cloudflare / GA4 / SEO 全要；②**有 CLI 优先 CLI**，MCP 只留给无 CLI 等价物的表面；③账号注入接到常驻五角色（✅ 已交付，commit 53f9929：`x-agent` 挂 `accounts/${ACCOUNT:-${COMPANY}}/secrets.env`（optional）+ `/account:ro` 挂载，`make up` 预创建，合约测试 2 条）。

**最终 MCP 名单（仅 4-5 个）：**
| MCP | 理由 |
|---|---|
| GA4 官方 `googleanalytics/google-analytics-mcp` | 无 CLI；service-account ADC 零交互 |
| DataForSEO 官方 `dataforseo/mcp-server-typescript` | Apache-2.0、官方 Docker、Basic auth env；一个凭证覆盖关键词量/难度 + SERP + 外链 + 排名追踪，pay-as-you-go（$50 押金，低量单月几美元），全场最便宜最全 |
| GSC `AminForou/mcp-gsc`（社区最强，MIT 1.1k★，活跃） | Google 无官方 GSC MCP；`GSC_SKIP_OAUTH=true` service-account 全 headless，带 Dockerfile；GSC 索引/收录/URL 检查视图爬虫无法替代 |
| Playwright MCP（微软官方） | 待实测：微软新配套 `@playwright/cli` 省 ~4x token，CLI 先试、MCP 兜底 |
| CUA（自研，已有） | 敌对站点（KDP/Etsy 上架、Amazon 反爬）唯一路径 |

**CLI/curl 队列（token 注入即可，不装 MCP）**：gh（GitHub）、vercel、wrangler（Cloudflare）、curl PSI（性能审计）、lighthouse CLI、IndexNow（一个 POST）、linkinator/Playwright（爬站审计）、Brave/Exa 搜索 REST、Resend 发信 REST。内容优化（Surfer 类）= LLM 自己拿 SERP 数据推理，不买工具。

**`accounts/<id>/secrets.env` 凭证清单（目标栈版）**：`GITHUB_PAT`（fine-grained per-repo）、`VERCEL_API_TOKEN`、`CLOUDFLARE_API_TOKEN`、`GOOGLE_APPLICATION_CREDENTIALS=/account/google-sa.json`（GA4+GSC 共用一个 service account；GSC 需把 SA 邮箱加为 Search Console 属性用户）、`DATAFORSEO_USERNAME/PASSWORD`；可选 `BRAVE_API_KEY`/`EXA_API_KEY`/`RESEND_API_KEY`。

**SEO 域避坑（专项调研）**：Ahrefs 官方 MCP 明文禁止 custom-script/非 AI-client 使用且 Lite $129/mo 起；Semrush 实际要 ~$500/mo Business；Majestic API 档 $400/mo 且无 MCP；Google Indexing API 官方限定 JobPosting/BroadcastEvent 页面（滥用会被静默撤权），一般页面收录走 IndexNow + GSC sitemap；cnych/seo-mcp（250★）是绕 CAPTCHA 爬 Ahrefs 的 ToS 雷，勿用；结构化数据校验（Rich Results Test）无公开 API，无自动化路径。

## ★ 社交账号单子（2026-07-03 用户拍板：X 免费/自建、YouTube 要、Reddit 免费档且豁免商用风险、IG 要、LinkedIn 出局）

核实后的现状修正：X 免费档已取消（2026-02 起新开发者仅按次付费且须绑卡）→ $0 路线只有 CUA 发帖；Reddit 新增 Responsible Builder Policy（2025-11 生效）——所有 API 使用含个人非商用都要预审批，报告周期 2-4 周。

| 平台 | 路线 | 一次性人工准备 | secrets.env / /account | 成本额度 | 续期 |
|---|---|---|---|---|---|
| X | ①CUA 发帖($0) ②按次付费 API 升级(~$0.015/帖) | ①登录态 ②dev 账号+App(Read&Write)+绑卡 | ①cookies→/account ②X_CLIENT_ID/SECRET+X_OAUTH2_REFRESH_TOKEN；传图需 OAuth1.0a 四件套(v2 media 不收 OAuth2) | 无免费档 | OAuth2 refresh 自动 |
| YouTube | Data API v3 | GCP 项目+一次 OAuth | YT_CLIENT_ID/SECRET+YT_REFRESH_TOKEN | 免费，~6 视频/天 | refresh 长期 |
| Instagram | IG API with Instagram Login(2024 路线，免 FB Page) | 账号转 Business→Meta App+Instagram Platform→自己账号加 developer/tester(**Standard Access 免 App Review**)→一次授权 | INSTAGRAM_APP_ID/SECRET+ACCESS_TOKEN+BUSINESS_ACCOUNT_ID | 免费，100 帖/24h | long-lived 60 天，可程序化续（**需 30-45 天 cron，漏 60 天人工重授权**）；scope 用新名 instagram_business_* |
| Reddit | 免费档(先过预审批)；审批期 CUA 顶 | ①Responsible Builder 申请(2-4 周) ②script App ③authorization-code+duration=permanent 拿 refresh token(勿用 password grant，冲突 2FA) | REDDIT_CLIENT_ID/SECRET+REFRESH_TOKEN+USER_AGENT(格式强制) | 免费 100 QPM | refresh 自动 |
| LinkedIn | 出局 | — | — | — | — |

横切前置：①CUA 发帖线要先把住宅 IP proxy 插槽接进 compose x-agent（broker 有、常驻缺，同账号注入改法）；②IG 续期 job 挂 hub watchdog 或 cron 容器；③所有初始授权=一次性人工，符合"人类启动时备好账号"边界。

---
（以下为裁决前的原始综合，MCP 候选速查表仍有效）

## 0. 一句话结论

接入架构已就位（per-role `mcp_config` + loadout overlay 在建），缺的是内容。赚钱闭环的两个 P0 缺口里，**研究读取**可以用 MCP 补齐（搜索 + Playwright），**发布上架**恰恰是 MCP 解决不了的（Gumroad 建品无 API、KDP 无任何 API）——必须走 CUA，这反向确认了自研 CUA 桌面的战略价值。

## 1. 需求 × 供给对照表

| 优先级 | 能力缺口（角色） | 选型结论 | 关键依据 |
|---|---|---|---|
| P0 | 网页搜索/研究（researcher） | **Brave Search MCP**（官方，MIT，官方 Docker 镜像，`BRAVE_API_KEY`，免费 2k 查询/月）+ **Exa MCP**（官方，MIT，2026 最常用搜索 MCP）；Tavily 为等价备选 | 全部 API-key headless，无 OAuth |
| P0 | DOM 级浏览器读取（researcher 市场信号 / verifier 独立核验） | **Playwright MCP**（微软官方，Apache-2.0，官方 Docker 镜像仅 headless Chromium）| accessibility-tree 级，比 CUA 像素级快且稳；敌对站点除外（见 §2） |
| P0 | 发布上架 Gumroad/KDP（growth `use-accounts`） | **无 MCP 可用 → CUA 桌面 + 住宅 IP**。Gumroad API 不支持建品（antiwork/gumroad#4019 尚开着）；KDP 零 API 且社区自动化工具明确说 headless 会挂、窗口太小会挂 | MCP 只能做发布后管理（社区 gumroad-mcp 读销售/license） |
| P1 | 抓取/结构化提取（researcher） | **Firecrawl**（最活跃 6.8k★，**AGPL-3.0 需你裁决**，可自托管规避）或 **Jina Reader**（Apache-2.0，免费额度大） | |
| P1 | 图片生成（growth `gen-image`） | **不是 MCP 问题** —— skill 已写好，缺的是把 `OPENAI_API_KEY` 注入容器 env（docker-compose x-agent-env 现在没有） | |
| P1 | 站点部署（builder） | **不装 MCP，走 CLI**：`vercel`/`wrangler` via Bash + token 注入。调研数据：CLI 比 MCP 省 ~94% token、快 3.5x；Vercel/Netlify MCP 均可用但无必要 | |
| P1 | 外发邮件（growth/客服） | **Resend MCP**（官方，MIT，`RESEND_API_KEY`，免费 100 封/天，需验证域名）；AgentMail（给 agent 独立信箱，方向对但无 LICENSE 文件、51★，观察） | 外设层继续管 inbound，不冲突 |
| P1 | GitHub（builder 远端仓库） | 倾向 **gh CLI**（CLI-first 原则）；若要结构化工具再上官方 GitHub MCP（MIT，31k★，PAT env 模式 headless 干净） | |
| P2 | 社媒发布（growth） | 只有两个正规解：**X**（2026-02 新计价 $0.015/帖按次付费，适合低量；社区 MCP 包官方 API）、**YouTube**（Data API v3，一次 OAuth 换 refresh token 后全 headless）。**Reddit 商用 $12k/年起、LinkedIn/Substack 只有 session-cookie 违 ToS 方案（封号风险）、Medium API 已死** —— 这三个建议不碰或走 CUA | ToS 风险按惯例报你裁决 |
| P2 | 分析读数（growth/ceo 反馈环节） | **GA4 官方 MCP**（Apache-2.0，2.5k★，service-account ADC 全 headless 最干净）或 Plausible（社区，API key）；Gumroad 销售数据走其 API/社区 MCP | |
| P2 | 监控（verifier/运维） | **Sentry MCP**（官方，MIT，`SENTRY_ACCESS_TOKEN` env，支持自托管实例） | |
| P2 | 数据库（builder 若做 SaaS） | Supabase 官方 MCP（MIT，PAT 明确支持 CI/CD headless）；通用 Postgres 用 crystaldba/postgres-mcp（MIT，但最后 release 2025-05 偏陈旧） | 现阶段无需求，备查 |

## 2. 三个「MCP 解决不了」的硬事实

1. **Gumroad 建品无 API**（只能读销售/改已有品）→ 上架必须 CUA。
2. **Amazon KDP 零 API**，且社区自动化（auto-kdp）文档明说内容上传 headless 不行、窗口尺寸敏感 → KDP 是 CUA 桌面 + 住宅 IP 的最强用例；Amazon 有 TLS/canvas 指纹级反爬。
3. **Etsy** 有完整 API v3 但要开发者应用审核 + OAuth，且平台激进封号（datacenter IP 几十个请求就封）→ 即便 Playwright 也危险，卖家操作走 CUA + 住宅 IP，API 路线后置。

推论：**「Playwright MCP 为默认、CUA+住宅 IP 为敌对站点升级路径」**的双层浏览器策略。普通站点（自家部署的站、SaaS 后台、公开网页）走 Playwright（便宜、稳）；Amazon/Etsy 类反自动化重镇走 CUA。这与仓库里已有决策「outbound=MCP 优先、CUA 降级回退」精确互补。

## 3. 集成架构四条（来自 Claude Code 官方文档一手核实）

1. **拓扑**：短期维持 stdio-per-container（改 mcp.json 即可，loadout overlay 天然兼容）。中期一个 company 一个共享 MCP host 容器（`sparfenyuk/mcp-proxy` 做 stdio↔HTTP 桥，或借鉴 docker/mcp-gateway）：秘密只注入一处、server 版本 pin、免每次 `npx` 冷启动。没有现成的「headless agent fleet gateway」产品，要用得自己搭薄的。
2. **凭证**：mcp.json 支持 `${VAR}` 展开（command/args/env/url/headers 全支持）。官方文档明确警告别把 key 写死进 env block。标准链：容器 entrypoint → `infisical run --`（或现有 `accounts/<id>/secrets.env` source）→ `claude -p --mcp-config <role.json>`。与现有账号注入模式无缝。`headersHelper` 可在每次连接时 shell 出去取短期 token（Infisical 集成点）。
3. **per-role 限权**：标准 headless 启动 = `--mcp-config <path> --strict-mcp-config`（保证不漏加载别处配置）——loadout overlay 应该加上 `--strict-mcp-config`。工具名 `mcp__<server>__<tool>`。**Gotcha**：allow 规则里裸 `mcp__*` 无效（静默跳过），必须 `mcp__<server>__*` 逐 server 列；deny 侧通配符随意。`--tools` 只管内建工具不管 MCP。
4. **上下文成本**：Claude Code 的 MCP Tool Search 默认开启（50+ 工具场景 ~77k→~8.7k token，省 85%），不需要自己造 lazy-loading。注意：①Haiku 不支持 tool_reference，跑 Haiku 的角色会退回全量加载；②自研 MCP server 要写好 instructions 字段（ToolSearch 靠它检索，2KB 截断）。远程 OAuth-only 的 server 目前 headless 无解（Claude Code 未见支持 client_credentials 扩展，absence-based 结论），选型时一律要求有静态 token 模式。

## 4. v1 每角色最小装配建议（loadout 内容）

| 角色 | MCP | 非 MCP 补给 |
|---|---|---|
| ceo | 无（delegation 已够） | — |
| researcher | brave-search + exa + playwright（+ firecrawl 若拍板 AGPL） | curl 公开 API 继续用 |
| verifier | playwright（只读核验 live 页面/发帖） | curl |
| growth | cua（已有）+ resend | `OPENAI_API_KEY` 注入 env（修 gen-image）；`use-accounts` skill 立项（CUA 打底） |
| builder | 无 | `VERCEL_API_TOKEN` + vercel/wrangler CLI；gh CLI + PAT |

角色差异化正好由 loadout overlay 表达 —— 当前 07-03 任务是这批接入的前置条件。另外 docker-compose 目前把 `AGENT_MCP` 对所有角色硬编码同一份，接入时改为 per-role 文件。

## 5. 待裁决

1. Firecrawl AGPL-3.0（自托管内部用，按你先例应可解禁，报备）。
2. Reddit 商用 API $12k/年、LinkedIn/Substack cookie 方案 ToS 风险 —— 建议 v1 不碰。
3. 是否开「mcp-provisioning」任务落地 P0 批次（正是 growth design.md Open Q1 悬置项）。

## 6. 发现渠道备忘

选型顺序：官方 MCP Registry（registry.modelcontextprotocol.io，查正主）→ Docker MCP Catalog（300+ 已验证容器镜像，配 mcp-gateway 有 per-server 秘密隔离）→ PulseMCP（人工编辑质检）→ mcp.so（1.9 万长尾，需自审）。

## 附：候选 server 速查（license/auth/维护信号）

| Server | 官方? | License | Auth | 维护 |
|---|---|---|---|---|
| brave/brave-search-mcp-server | 官方 | MIT | API key env | 1.3k★ 活跃，官方 Docker |
| exa-labs/exa-mcp-server | 官方 | MIT | API key | 4.7k★ 极活跃 |
| tavily-ai/tavily-mcp | 官方 | MIT | API key | 2.2k★ 活跃 |
| mendableai/firecrawl-mcp-server | 官方 | **AGPL-3.0** | API key/自托管 | 6.8k★ 本域最活跃 |
| jina-ai/MCP | 官方 | Apache-2.0 | API key | 742★ |
| microsoft/playwright-mcp | 官方 | Apache-2.0 | 无外部凭证 | 极活跃，官方镜像 |
| resend/resend-mcp | 官方 | MIT | API key | 546★ 活跃 |
| agentmail-to/agentmail-mcp | 官方 | **无 LICENSE 文件** | API key | 51★ 年轻 |
| stripe/ai (Stripe MCP) | 官方 | MIT | restricted key Bearer（headless 有官方文档） | 1.6k★ 当日有提交 |
| Polar MCP | 官方托管 | n/a | Org Access Token | 活跃；MoR 替代 |
| github/github-mcp-server | 官方 | MIT | PAT env | 31k★ |
| googleanalytics/google-analytics-mcp | 官方 | Apache-2.0 | service account ADC | 2.6k★ 活跃 |
| getsentry/sentry-mcp | 官方 | MIT | token env | 活跃，支持自托管 |
| supabase-community/supabase-mcp | 官方 | MIT | PAT（CI/CD 明确支持） | 活跃 |
| browserbase/mcp-server-browserbase | 厂商 | Apache-2.0 | API key | 3.4k★（反爬场景云浏览器备选） |
| steel-dev/steel-mcp-server | 厂商 | 未核 | API key | 活跃，可自托管（反爬备选） |
| GongRzhe/Gmail-MCP-Server | 社区 | MIT | OAuth | **已 archived，勿用** |
| PostHog/mcp | 官方 | MIT | API key | **repo archived，并入主 monorepo，用前先确认新位置** |
