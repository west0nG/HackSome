# Design — 社交 MVP：agent 的浏览器 = 自己的浏览器

> PRD 见同目录 `prd.md`（2026-07-06 MVP 版）。两版旧设计（IG 续期全量版、
> 双浏览器分离版）见 git history，本文件整体替换。

## 0. 决策总览

| # | 决策 | 结论 | 备选（为何不选） |
|---|---|---|---|
| D1 | 登录态给哪个浏览器 | **就地改造现有 `playwright` server**：一个 agent 一个浏览器，默认带全部登录态（2026-07-06 用户拍板：人上网用自己的浏览器，不用隐身模式） | 双实例分离（研究净浏览器+账号浏览器）：为 proxy 流量费做的预先优化，代价是心智/配置双份；用户裁决成本痛了再收窄，不预先分裂 |
| D2 | cookies 文件粒度 | 单文件 `accounts/<id>/cookies/storage-state.json`，装整个账号身份（加平台=叠加登录态，零代码） | 每平台一文件：playwright `--storage-state` 只吃一个文件，多文件反而要合并逻辑 |
| D3 | 有头/无头 | **有 DISPLAY 就 headed**（跑在 kasm 桌面，VNC 可观察、反爬指纹更好），缺 DISPLAY 自动回退 `--headless`，不炸 | 恒 headless：X 对无头更敏感、不可观察；恒 headed：DISPLAY 缺失时直接起不来 |
| D4 | cookies 怎么来 | 宿主机 `npx playwright open --save-storage=…` 人工登录一次导出（精确语法实施 A 段钉死）；增补平台用 `--load-storage` + `--save-storage` 叠加 | 浏览器扩展导出再转格式：多一步转换，留作 README 备选 |

## 1. 边界

- **做**：wrapper 脚本、五角色 playwright 条目改接 wrapper、cookies 约定 +
  README、无 cookies dry-run、真 cookies e2e（待人工备）。
- **不做**：发帖 skill（growth use-accounts 线）、cookies 自动续期/回写
  （storage-state 是只读种子，失效=人工重导）、CUA 桌面浏览器的 cookies 导入
  （像素路线以后需要再说）。

## 2. 机制

### 2.1 wrapper：`agent/browser_mcp.sh`

MCP json 写不了条件逻辑，`command` 指向 wrapper（放 `agent/`，理由同
`proxy_env.sh`：agent/ 是 x-agent 锚点 ro 挂载进每个角色的目录）：

```sh
args=(--browser chromium)
[ -z "${DISPLAY:-}" ]                              && args+=(--headless)
[ -f /account/cookies/storage-state.json ]         && args+=(--isolated --storage-state /account/cookies/storage-state.json)
[ -n "${CUA_PROXY:-}" ]                            && args+=(--proxy-server "$CUA_PROXY")
exec playwright-mcp "${args[@]}"
```

> A 段实测修订（2026-07-06）：mcp 0.0.77 的 `--storage-state` 只对 isolated
> 会话生效，必须与 `--isolated` **成对**（in-memory profile，恰好实现只读种子
> 不回写）；DISPLAY=:1 已实测传导到 agent_loop→claude 子树，headed 分支成立。

- 三个条件互相独立，缺谁都合法降级；全缺时行为≈改造前（差别仅 headed，见 D3）。
- `CUA_PROXY` 是容器级 env（secrets.env 注入），claude 子树读得到本体
  （`proxy_env.sh` 只是不给这个子树展开 HTTP(S)_PROXY），wrapper 显式消费——
  与「账号流量显式走 proxy」的既有约定同构，且不影响 claude 本身的 LLM 流量
  （那是结构性直连，不经浏览器）。

### 2.2 MCP 接线

五个 `agents/mcp/<role>.json` 的 `playwright` 条目从
`"command": "playwright-mcp", "args": ["--headless", "--browser", "chromium"]`
改为 `"command": "/opt/foundagent-orch/agent/browser_mcp.sh"`（无 args）。
server 名不变（`playwright`），`FULL_SERVER_SET` 不变，消费方（skill/charter
里提到 playwright 的地方）零改动。

`agent/tests/test_mcp_assets.py`：playwright 条目断言改为「command=wrapper
路径且该文件存在、可执行」；新增 wrapper 参数构造测试（cookies × proxy ×
DISPLAY 三开关，直跑 shell 断 argv）。

### 2.3 cookies 生命周期

- **导出**（人工一次）：宿主机 playwright open 登录 x.com → save-storage 写
  `accounts/<id>/cookies/storage-state.json`。X 的 auth_token 长寿命
  （数月级），登出/改密会作废。
- **只读种子**：/account 是 ro 挂载，会话中新 set 的 cookies 不回写——X 场景
  可接受（核心 auth cookie 不轮换）；失效表现为「打开 x.com 未登录」，处理 =
  重导一次。README 写明。
- **失效可见性**：MVP 不做主动探测；靠消费方（未来发帖 skill）遇未登录上报。

## 3. 兼容与回滚

- 行为变化面（对现网五角色）：①浏览器从恒 headless 变为桌面内 headed；
  ②配 proxy 的账号其浏览器**全部**流量走住宅代理（含研究浏览，PRD 成本注记，
  用户知情接受）；③带登录态浏览陌生站点（人类浏览器同款风险，接受）。
- 回滚 = 五个 json 的 playwright 条目改回原 command/args + 删 wrapper；
  cookies 文件在 gitignored 数据区，无需清理。
- gitignore：确认 `accounts/<id>/cookies/` 被覆盖，不够就补。

## 4. 已知依赖 / 风险

- **e2e 依赖用户侧前置**：一个 X 账号 + 宿主机人工登录导出一次（已拍板标
  「待人工备凭证」，代码与 dry-run 不阻塞）。
- headed 窗口未来可能与 CUA 像素操作抢桌面焦点（当下 CUA 线未活跃，出现了再
  处理：如错屏/虚拟 workspace 或该会话临时 headless）。
- 五角色各起一个 chromium 实例共享同一份 cookies——X 视角=同一账号多设备在线，
  常态可接受；若触发风控再收窄（如仅 growth 挂载 cookies）。
- 首次从非常用 IP 登录导出时 X 可能弹验证——README 建议导出用日常网络，容器侧
  配 `CUA_PROXY` 再消费。
- playwright-mcp 的 `--storage-state` / `--proxy-server` / `--headless` 精确
  flag 与缺文件行为，实施 A 段对着 pin 进镜像的版本核对，不凭记忆写。
