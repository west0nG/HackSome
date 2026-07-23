# MCP loadout：per-role mcp.json（GA4 / DataForSEO / GSC）

> 父任务：`07-03-capability-provisioning`。选型依据见父任务 `research/mcp-research-synthesis.md`（★最终版一节）。

## 目标

把 CLI 覆盖不了的三个表面用 MCP 接进来，并把「每角色一份 mcp.json」从单文件常量升级为可组合的配置资产，与 07-03-company-loadout-overlay 的 `mcp: on|off|<path>` 开关衔接。

## 需求

1. **三个 server**（均为调研核实过的 headless 路线）：
   - GA4：官方 `googleanalytics/google-analytics-mcp`（service-account ADC，key 文件走 `/account/google-sa.json`）。
   - DataForSEO：官方 `dataforseo/mcp-server-typescript`（`DATAFORSEO_USERNAME/PASSWORD` Basic auth）。
   - GSC：`AminForou/mcp-gsc`（`GSC_SKIP_OAUTH=true` service-account 模式，与 GA4 共用同一个 SA；SA 邮箱需加为 Search Console 属性用户——写进人工清单）。
2. **per-role 配置文件**：`vm/docker/mcp/<role>.json`（或与 loadout overlay 对齐的落点，design 阶段定）。基线分配：researcher = cua + dataforseo + gsc；growth/ceo = cua + ga4；builder/verifier = cua（维持现状）。所有凭证用 `${VAR}` 展开，不写死。
3. **启动加固**：agent_loop 拼 argv 时加 `--strict-mcp-config`（防止漏加载别处配置——Claude Code 官方 headless 推荐组合）。
4. **Playwright 对比实验**（时间盒，不阻塞交付）：researcher 场景下 Playwright MCP vs 微软 `@playwright/cli`，赢者进 researcher 配置，结论记 research/。

## 约束

- 与 loadout overlay 完全兼容：overlay 的 `mcp: <path>` 换的就是这些文件；`mcp: off` 语义不变。
- 凭证缺失时该 server 连接失败即可，agent_loop 与其余 server 不受影响（优雅缺省）。
- MCP server 版本 pin（npx 指定版本或 vendor 进镜像，design 阶段定，倾向后者以免每次冷启动 npm install）。
- 不给任何角色跑 Haiku 的假设引入（tool search 依赖 tool_reference）。

## 验收标准

- [x] 五角色 argv 各自指向正确的 per-role mcp.json 且带 `--strict-mcp-config`（单测断言 argv）。
- [x] 注入真凭证后，researcher 容器内经 MCP 取回一次真实 DataForSEO 响应 + 一次 GSC 响应（e2e，不可 mock）。
  - DataForSEO ✅ 2026-07-04：真凭证注入 secrets.env，researcher 经 MCP 实取 "coffee" 月搜索量 6,120,000（DFS_OK）。
  - GSC ⏭ 半场移交后续 domain-rail 任务（用户裁决 2026-07-04）：前置是已验证的 Search Console 属性，域名 foundagent.net 已备，属性验证 + SA 授权 + GSC e2e 并入新任务。
- [x] `mcp: off` / 替换路径经 loadout overlay 仍按 07-03-company-loadout-overlay 的 AC 生效（回归其测试）。
- [x] 凭证键与领取步骤并入 `accounts/README.md`（含 SA 邮箱加 GSC 属性这步）。
- [x] Playwright vs CLI 对比结论落盘 research/（含 token 消耗数字；MCP 胜出已进 researcher.json）。
