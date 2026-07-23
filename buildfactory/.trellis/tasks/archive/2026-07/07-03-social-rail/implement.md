# Implement — 社交 MVP：agent 的浏览器 = 自己的浏览器

> 顺序执行；每步验证过了再走下一步。E 段（真 cookies e2e）标「待人工备凭证」，
> 与前面解耦交付。

## A. 事实钉死（对着镜像里的版本核对，落 research/）

- [x] 镜像内 `playwright-mcp --help`（或源码）核对：`--storage-state`、
      `--proxy-server`、`--headless` 精确 flag、不传 --headless 时是否需要
      DISPLAY、storage-state 文件缺失/损坏时的行为。
- [x] 确认 claude 子树（agent_loop → claude → mcp server）确实继承 DISPLAY
      （进容器看 environ，不猜）。
- [x] 宿主机导出命令精确语法：`npx playwright open --save-storage` /
      `--load-storage` 叠加；结论写 `research/account-browser-facts.md`。
- [x] 确认 `.gitignore` 是否已覆盖 `accounts/<id>/cookies/`（不够就在 B 段补）。
- [x] 与 design §2 有出入 → 先改 design.md 报用户，再继续。

## B. wrapper + 接线 + 单测

- [x] `agent/browser_mcp.sh`（design §2.1：cookies/proxy/DISPLAY 三条件拼参，
      缺谁都合法降级）。
- [x] 五个 `agents/mcp/<role>.json` 的 `playwright` 条目改指 wrapper
      （server 名不变，FULL_SERVER_SET 不变）。
- [x] `.gitignore` 补 cookies 覆盖（若 A 段确认需要）。
- [x] 测试：`test_mcp_assets.py` playwright 条目断言改 wrapper 路径+文件存在
      可执行；新增 wrapper 参数构造测试（cookies × proxy × DISPLAY 组合，
      直跑 shell 断 argv）。
- [x] 验证：`.venv-cua/bin/python -m pytest agent/tests/ -q`

## C. 容器 dry-run（无 cookies，AC2）

- [x] `make up` 后任一角色容器内 claude 会话 `/mcp` 看 playwright 连接状态；
      无 cookies 时浏览一个公开页面成功（与改造前无回归）。
- [x] headed 确认：VNC 看得到浏览器窗口出现在 kasm 桌面。
- [x] 有测试代理就顺手验出口 IP；没有留到 E 段。

## D. README（AC4）

- [x] `accounts/README.md`：文件布局节补 `cookies/storage-state.json`；新增
      「X / 登录态 cookies」一节（导出步骤、--load-storage 叠加新平台、失效
      重导、只读种子语义、导出用日常网络的提醒）；proxy 节补一句「浏览器属
      账号面：CUA_PROXY 存在时全部浏览器流量走它（含研究浏览，知情成本）」。

## E. 真 cookies e2e（AC3，待人工备凭证）

- [x] 用户侧前置：一个 X 账号 + 宿主机人工登录导出一次 storage-state。
- [x] growth 容器内浏览器打开 x.com 为登录态。
- [x] 发一条测试帖（发前向用户确认）。

## F. 收尾

- [x] 全量测试：`.venv-cua/bin/python -m pytest agent/ orchestration/ -q`
- [x] spec 更新：`resident-agent-contracts.md` 记「agent 浏览器=账号浏览器」
      契约（wrapper 三降级 + cookies 只读种子 + 成本注记）。
- [x] 父任务 prd 的 scope 描述与本任务 MVP 裁决对齐（一句话沿革即可）。
- [x] 提交（多 session 共享工作树：commit 前查分支、只 add 本任务文件）。

## 回滚点

- B 纯声明式：五条 json 还原 + 删 wrapper + 还原测试即回滚。
- cookies 数据在 gitignored 区域，与 git 无关。
