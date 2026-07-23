# 社交账号轨道 MVP：agent 的浏览器 = 自己的浏览器（cookies 搞定 X）

> 父任务：`07-03-capability-provisioning`。社交单子见父任务 research/ ★社交账号单子一节。
>
> **沿革**：2026-07-06 用户两次拍板——①砍成 MVP：第一版只做「X 用 cookies 登录态
> 跑起来」，IG 续期 job、YT/IG/Reddit 铸 token helper、四平台全量清单**全部推迟**
> （旧版规划见 git history）；②否决双浏览器分离：**agent 只有一个浏览器，就是带
> 自己全部登录态的那个**——人每次上网用的也是自己的浏览器，不是隐身模式。

## 目标

人工导出一次 X 登录态 cookies 放进账号包，agent 现有的浏览器（playwright MCP）
从此默认带登录态、并在配了 `CUA_PROXY` 时走账号 IP——growth 未来的发帖 skill
直接消费它，本任务不写发帖 skill。

## 需求

1. **cookies 约定**：账号包新增 `accounts/<id>/cookies/storage-state.json`
   （Playwright storage-state 格式，装整个账号身份——今天只有 X，以后
   Gumroad/KDP 等直接往同一文件叠加登录态，零代码变更）。
2. **现有 `playwright` server 就地改造成账号浏览器**：五个角色共用的
   playwright MCP 改经 wrapper 启动——cookies 文件存在就加载、`CUA_PROXY`
   存在浏览器流量就走它、有 DISPLAY 就有头跑在 kasm 桌面上（可从 VNC 观察）。
   **不加第二个浏览器实例**。
3. **导出文档**：`accounts/README.md` 新增 X / cookies 一节——宿主机一次性
   导出步骤、失效重导流程、代理与只读语义；proxy 一节补一句「浏览器属账号面，
   CUA_PROXY 存在时全部浏览器流量走它」。

## 约束

- 不动镜像、不加依赖：playwright-mcp 已 pin 进 cua-agent 镜像，改动 =
  一个 wrapper 脚本 + 五个 role json 改 playwright 条目 + README。
- cookies 不落 git 可见路径（确认 gitignore 覆盖 `accounts/<id>/cookies/`）。
- 缺 cookies / 缺 proxy / 缺 DISPLAY 都是合法状态，逐项优雅降级，不炸容器。
- **成本注记（知情接受）**：配了 `CUA_PROXY` 后研究浏览也走住宅代理烧流量——
  这是「人用自己家网上网」模型的代价；流量费真痛了再后置收窄（如重爬取
  改走 curl 直连），不预先分裂浏览器。

## 验收标准

- [x] 单测：wrapper 参数构造覆盖（有/无 cookies × 有/无 CUA_PROXY × 有/无
      DISPLAY）；五个 role json 的 playwright 条目指向 wrapper 且 MCP 资产
      契约测试同步更新不回归。
- [x] 容器 dry-run（无 cookies）：playwright MCP 正常连接、能浏览公开页面，
      与改造前行为无回归。
- [x] 真 cookies e2e（**待人工备 X 账号**）：growth 容器内浏览器打开 x.com
      为登录态；发一条测试帖（发前向用户确认）。
- [x] README：照 X 一节从零完成「导出 → 放置 → 容器内验证」，无需读代码。
