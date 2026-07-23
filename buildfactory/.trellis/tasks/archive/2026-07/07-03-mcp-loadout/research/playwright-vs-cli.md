# Research: Playwright MCP vs Playwright CLI（researcher 场景实测）

- **Query**: researcher 场景下 Playwright MCP vs 微软 Playwright CLI，赢者进 researcher 的 MCP 配置（PRD AC5，时间盒 ~40 min）
- **Scope**: mixed（npm registry 核实 + foundagent-researcher 容器内实测）
- **Date**: 2026-07-03

## 结论（TL;DR）

1. **「CLI 省 ~4x token」传闻未复现**：本次实测 CLI 路线仅省 ~28% 新增 input token、总成本便宜 ~14%（$0.274 vs $0.319），而 MCP 路线反而快 33%（14.1s vs 21.2s）。
2. 原因是 **2026 年两条路线的省 token 机制已趋同**：claude CLI 2.1.x 用 ToolSearch 按需加载 MCP 工具 schema（不再全量预载 ~25 个工具），且 `@playwright/mcp` 0.0.77 也改成把页面快照写入文件（`.playwright-mcp/page-*.yml`）让模型按需 Read，不再把 accessibility tree 硬塞进每个 tool response。4x 传闻对应的是旧版行为。
3. **建议**：Playwright MCP 进 `researcher.json`（加 `--headless --browser chromium` 参数）；`@playwright/cli` 记入 CLI/skill 队列备用——若未来 researcher 出现长浏览会话（几十次页面操作），CLI 的文件快照 + 无 schema 开销优势会随会话长度放大，届时可切换。

## 包名核实（2026-07-03，npm registry）

| 包 | 最新版 | 说明 |
|---|---|---|
| `@playwright/mcp` | 0.0.77（2026-07-03 更新） | 官方 Playwright MCP server，bin 入口 `cli.js` |
| `@playwright/cli` | 0.1.15（2026-06-30 更新） | 官方新 CLI，bin 名为 `playwright-cli`；父任务说的包名正确 |
| `playwright-cli`（旧包） | 0.262.0 | 已弃用，README 指向 `@playwright/cli` |

两者依赖同一 playwright 版本（`1.62.0-alpha-2026-06-29`），共享同一份 chromium 下载。

官方 README 对二者的定位（`@playwright/cli` README 原文大意）：CLI 面向 coding agents，"token-efficient, does not force page data into LLM"；MCP 适合需要持久状态、富自省的长自治循环。官方未给出 4x 数字。

## 实验设置

- 环境：`foundagent-researcher` 容器（kasm 镜像，uid1000，实测有免密 sudo），claude CLI 2.1.197（subscription 认证），node 20.20.2 / npm 10.8.2
- 安装位置：`/tmp/node_modules`（不动镜像与仓库）
- 统一任务：「打开 https://news.ycombinator.com ，报告 top 5 故事的标题与分数」
- 模型：两路线均不加 `--model`。⚠️ 容器默认解析为 **claude-sonnet-5**（不是任务假设的 opus），但两路线一致，对比仍公平。另有极小量 haiku 内部调用（~600 tok，两边都有）。
- 路线 A（MCP）：`claude -p "<task>" --mcp-config /tmp/pw-mcp.json --strict-mcp-config --output-format json --dangerously-skip-permissions`，pw-mcp.json 内 playwright server 为 `node /tmp/node_modules/@playwright/mcp/cli.js --headless --browser chromium`
- 路线 B（CLI）：同上 claude 命令但 `--mcp-config /tmp/empty-mcp.json`（零 MCP），prompt 指明用 `/tmp/node_modules/.bin/playwright-cli`（`--browser chromium`）
- 各跑 1 次（N=1）；两路线输出完全一致故未复跑

## 实测数字（sonnet-5 主模型部分）

| 指标 | 路线 A：Playwright MCP | 路线 B：playwright-cli | 差异 |
|---|---|---|---|
| 成败 | ✅ 成功 | ✅ 成功 | 输出的 5 条标题+分数**完全一致**（互为验证） |
| 时长 duration_ms | **14.1s** | 21.2s | MCP 快 33% |
| turns | 4（3 次工具调用） | 6（5 次工具调用） | MCP 少 2 轮 |
| input_tokens（非缓存） | 3,275 | **2,706** | |
| cache_creation | 44,228 | **31,699** | CLI 少写 ~12.5k（≈省掉的 schema/响应开销） |
| 新增 input 合计（input+cache_creation） | 47,503 | **34,405** | CLI 省 28% |
| cache_read | **118,134** | 216,513 | CLI 轮次多、重读多 |
| output_tokens | **503** | 699 | |
| total_cost_usd | $0.3188 | **$0.2745** | CLI 便宜 14% |

工具调用序列：

- A（MCP）：`ToolSearch("playwright browser navigate")` → `mcp__playwright__browser_navigate` → `Read /tmp/.playwright-mcp/page-*.yml`（1043 行快照文件）
- B（CLI）：`playwright-cli --help` → `open <url> --browser chromium` → `snapshot` → `Read <tool-results 溢出文件>`（同样 1043 行快照）→ `close`

即：**两条路线最终都是"快照落文件、模型按需读"**，读进 context 的页面数据量相同；差距只剩交互轮数与残余 schema 开销。

## 安装成本（容器内冷启动实测）

| 步骤 | 耗时 | 备注 |
|---|---|---|
| `npm install @playwright/mcp @playwright/cli` | 6.6s | ~18MB node_modules |
| `npx playwright install chromium` | **12 min** | 容器网络慢；下载 chromium(633MB 解压) + headless shell(341MB 解压) + ffmpeg，磁盘 ~1GB。**不需要 `--with-deps`**——kasm 镜像 X 库齐全，headless 直接能跑 |

踩坑记录：

1. `~/.npm` 缓存目录 root 属主 → npm 装包报错。容器内实测 kasm-user **有免密 sudo**（与任务假设"无 sudo"不符），`sudo chown -R 1000:1000 ~/.npm` 即解；无 sudo 时 `npm --cache /tmp/npm-cache` 也能绕过。
2. 两者默认都用 **`chrome` channel**（找 `/opt/google/chrome/chrome`），容器里没有 branded Chrome → 必须显式 `--browser chromium`（CLI 的 `open --help` 里没列出 chromium 这个值，但实测接受）。MCP 侧同理在 server args 加 `--browser chromium`。
3. `playwright-cli` 会在 cwd 留 `.playwright-cli/` 快照目录、并有常驻 daemon（`close-all`/`kill-all` 清理）；MCP 留 `.playwright-mcp/`。

## 与「CLI 省 ~4x token」传闻的对照

- 本测：新增 input token 比 1.38x（47.5k vs 34.4k），成本比 1.16x——**远不到 4x**。
- 传闻的来源语境应是旧版组合：MCP 全量预载 ~25 个工具 schema（万级 token）+ 每次操作把整棵 accessibility tree 塞进 tool response。在 claude 2.1.x（ToolSearch 按需加载）+ `@playwright/mcp` 0.0.77（快照落文件）下，这两项开销已被官方自己消掉大半。
- 预期例外：**长会话**（一次 session 内几十次导航/点击）下 MCP 每步响应的固定开销与 CLI 的差距会累积；单页任务两者接近。

## 建议（按现有证据）

1. **进 `researcher.json`**：`@playwright/mcp`，args 含 `--headless --browser chromium`。理由：速度更快、轮次更少；与本任务正在建设的 per-role mcp.json + `--strict-mcp-config` 机制零成本对接；token 差距已缩小到 ~14% 成本。
2. **`@playwright/cli` 进 CLI/skill 队列**（不阻塞本任务）：镜像里预装二进制 + chromium 后，可作为长浏览会话的备选（`playwright-cli install --skills` 可装成 Claude Code skill）。切换触发条件：researcher 实际工作负载中出现单会话大量页面操作导致 context 压力。
3. 镜像构建注意：chromium 下载 12 min/1GB，应烘进镜像层而非运行时装。

## Caveats / Not Found

- N=1 单次运行，token 数字有随机波动（模型措辞、快照大小随 HN 页面变化）；但两路线结论方向（无数量级差距）对波动不敏感。
- 默认模型是 sonnet-5 而非任务假设的 opus；若 researcher 生产配置用别的模型，绝对数字会变，比例结论大概率仍成立。
- 未测长会话（多页连续操作）场景——这是 4x 传闻最可能部分成立的场景，留待有真实负载后验证。
- 路线 B 的 prompt 给了 CLI 路径与 `--browser chromium` 提示（否则会撞 chrome-not-found 坑），比路线 A 的 prompt 略多引导；生产中该引导可由 skill 承担。
- 容器内遗留：`/tmp/node_modules`、`/tmp/pw-mcp.json`、`/tmp/empty-mcp.json`、`/tmp/route-{a,b}.json`、`~/.cache/ms-playwright/`（按任务要求不清理，容器可重建）。
