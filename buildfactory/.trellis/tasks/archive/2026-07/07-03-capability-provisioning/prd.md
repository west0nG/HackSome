# 外部能力供给（父任务）：CLI-first 工具链 + MCP loadout + 社交账号轨道

## 背景

四路调研（需求盘点 / 业务运营 MCP / 基建与集成模式 / SEO 专项 + 社交平台核实）结论见 `research/mcp-research-synthesis.md`。用户已做出的裁决，全部子任务必须遵守：

1. **有 CLI 优先 CLI**：MCP 只留给没有 CLI 等价物的表面（依据：CLI 比 MCP 省 ~17x token）。
2. **目标栈定调**（不从现有 skill 反推）：GitHub / Vercel / Cloudflare / GA4 / SEO 全要。
3. **社交名单**：X（$0 走 CUA、按次付费留升级）、YouTube、Instagram（Standard Access 免审路线）、Reddit（免费档，商用 ToS 风险用户已知情豁免，需过 2025-11 起的 Responsible Builder 预审批）；LinkedIn 出局。
4. 发布上架（Gumroad/KDP/Etsy）无 API 可用，归 CUA + 住宅 IP，不在本父任务范围（属 use-accounts skill 线）。

已就位的前置：账号注入已通（commit 53f9929：`accounts/<id>/secrets.env` + `/account:ro` 进常驻五角色）；公司 loadout overlay（07-03-company-loadout-overlay）提供 per-company 的 MCP 开关。

## 子任务地图

| 子任务 | 交付物 | 优先级 |
|---|---|---|
| `07-03-cli-toolchain` | 镜像烧 gh/vercel/wrangler、凭证键名合约、人工 provisioning 清单 | P1 |
| `07-03-mcp-loadout` | per-role mcp.json（GA4 / DataForSEO / GSC）、`--strict-mcp-config`、与 loadout overlay 对齐 | P1 |
| `07-03-social-rail` | ~~IG token 续期 job、一次性授权 helper、社交 provisioning 清单~~ → 2026-07-06 用户砍成 MVP：agent 浏览器=自己的浏览器（X cookies 登录态，`browser_mcp.sh` wrapper）；IG 续期 / 三平台授权 helper 全推迟，proxy 插槽已由 `07-03-proxy-slot` 交付 | P2 |

执行顺序：①→②→③（②依赖①的凭证合约；③依赖①②的注入/配置模式）。

## 跨子任务验收标准

- [ ] **优雅缺省**：`accounts/<id>/` 缺失或空时，`make up` 与五角色启动完全不受影响（CLI 存在未认证、MCP server 起不来都不得导致 agent_loop 崩溃）。
- [ ] **凭证单一来源**：所有新增凭证只经 `accounts/<id>/secrets.env`（env 变量）或 `/account`（key 文件）进入容器，不出现第三条路径、不硬编码。
- [ ] **e2e（真凭证冒烟）**：注入真实 token 后，容器内 `gh auth status`、`vercel whoami`、`wrangler whoami` 通过；researcher 通过 MCP 拿到一次真实 DataForSEO / GSC 响应。
- [ ] **人工清单可执行**：一个新公司从零 provisioning（领 token → 填 secrets.env / 放 key 文件）只依赖清单文档即可完成，无需读代码。
