# @stripe/mcp 0.3.3 机制取证（07-09 实施）

来源：npm tarball `https://registry.npmjs.org/@stripe/mcp/-/mcp-0.3.3.tgz`
（实施当天下载，逐行核对 dist/）。

## key 传递选 env 而非 args 的依据

`dist/cli.js` 第 32 行：

```js
const apiKey = options.apiKey || process.env.STRIPE_SECRET_KEY;
```

server 原生支持 `STRIPE_SECRET_KEY` env var（`--api-key` 缺席时的 fallback），
所以 role json 用 `env` 块传 key，与 dataforseo 完全同模式——不需要验证
claude 是否会展开 `args` 里的 `${VAR}`（现有五个 json 只在 `env` 值里用过
`${VAR}`，args 展开无既有先例可背书）。

用 `${STRIPE_SECRET_KEY:-}`（带空默认，`:-` 语法在 gsc/ga4 条目已有先例）而非
裸 `${STRIPE_SECRET_KEY}`：存量 secrets.env 里没有这一行时容器内 var 完全未
定义，空默认保证 mcp-config 展开永不失败；server 进程拿到空值后自己抛
`Stripe API key not provided` 退出 → `/mcp` 显示未连接，其余 server 不受
影响（AC1 语义）。

## bin 冲突与 `stripe-mcp` 符号链接的依据

`package.json` 的 `bin = { mcp: 'dist/index.js' }`——bin 名字面上是 `mcp`。
Dockerfile.agent 的 `pip install ... mcp ...`（pip `mcp` 包）也装一个叫
`mcp` 的 console script 到 `/usr/local/bin`，PATH 上排在 npm 全局 bin
（`/usr/bin`）之前，裸 `mcp` 会解析到 pip 版。因此 Dockerfile 里
`ln -sf /usr/lib/node_modules/@stripe/mcp/dist/index.js /usr/local/bin/stripe-mcp`
造一个无冲突名（仿 `fdfind→fd` 先例）；`dist/index.js` 带
`#!/usr/bin/env node` shebang，npm 装 bin 时会给目标文件加执行位。
role json 一律用 `stripe-mcp`，永不裸调 `mcp`。

（没选 `npx -y @stripe/mcp`：npx 对全局安装包的解析行为随 npm 版本变化，
"零冷下载"无法离线确证；直链路径与 Dockerfile 第 88 行已依赖的
`/usr/lib/node_modules/...` 布局一致。）

## 其他核对结果

- `--tools` 参数在 0.3.x 已移除（cli.js 里遇到只打 warning）：工具面完全由
  key 权限决定，与 PRD"工具面 = 密钥权限面"的理解一致。
- `dist/index.js`：本地进程是 stdio→HTTP 转发器，目标写死
  `https://mcp.stripe.com`，Authorization header 带 key——确证"本地进程实为
  mcp.stripe.com 转发器"。
- key 校验：必须 `sk_` 或 `rk_` 前缀；`sk_` 会打一条建议用 restricted key
  的 warning（stderr，无害）。

## Live e2e results (2026-07-09, AC2)

One-shot builder container (`docker compose run --rm --no-deps --entrypoint bash builder`,
isolated `CLAUDE_CONFIG_DIR=/tmp/e2e-claude`, real `agents/mcp/builder.json` +
`--strict-mcp-config --dangerously-skip-permissions`), live sk_live key from
`accounts/foundagent/secrets.env` (HKD account):

- stripe MCP connected; full flow pure-MCP, zero fallbacks: create product →
  price (hkd 8800) → payment link → deactivate link → archive product →
  re-fetch shows `active: false`. Host-side API re-verification confirmed both
  objects `livemode: true, active: false`. No charge ever possible (link died
  minutes after creation).
- `plink_1TrJIYIRw93begpcvrV5axyI` / `prod_Ur1KTowiHgCPik` (kept as archived
  tombstones; payment links cannot be deleted, only deactivated).

**Tool-surface finding**: the hosted server (0.3.3 forwarder) exposes META
tools, not per-object CRUD: `stripe_api_read/write/search/details`,
`stripe_implementation_planner`, `search/fetch_stripe_resources`,
`get_stripe_account_info`, `search_stripe_documentation`, plus a dedicated
`create_refund`. Consequences: (a) `stripe_api_write` is a generic escape
hatch to ANY API mutation the key allows — the "tool surface = key permission
surface" statement is literal; (b) `create_refund` being first-class confirms
the full-key risk noted in the PRD constraints.
