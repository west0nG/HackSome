# A 段事实钉死 — playwright-mcp / 导出命令 / gitignore（2026-07-06 实测）

## 镜像内 playwright-mcp（foundagent/cua-agent:latest，Version 0.0.77）

`docker run --rm --entrypoint playwright-mcp foundagent/cua-agent:latest --help` 实测：

- **headed 是默认**：`--headless  run browser in headless mode, headed by default`。
  现网五角色 json 是显式传了 `--headless`；wrapper 里"有 DISPLAY 就不传
  --headless"即可实现 D3。
- **`--storage-state <path>`**：help 原文 "path to the storage state file **for
  isolated sessions**" → storage-state 只对 isolated 会话生效，必须与
  `--isolated`（"keep the browser profile in memory, do not save it to disk"）
  成对使用。isolated + storage-state = 每次会话从文件种子、不落盘不回写——
  正好匹配 /account ro 挂载的"只读种子"语义。
- **`--proxy-server <proxy>`**：存在，示例 `http://myproxy:3128` /
  `socks5://myproxy:8080`；另有 `--proxy-bypass`。
- **`--browser chromium` 是 load-bearing**（test_mcp_assets.py 注释 + 07-03
  playwright-vs-cli 调研）：两条 playwright 路线默认 branded-chrome channel，
  容器不带 chrome，掉了这个 flag 每次导航都挂。wrapper 必须保留。
  （0.0.77 help 里 `--browser` 例举 "chrome, firefox, webkit, msedge"，但
  chromium 实测是现网在用且工作的值，勿改。）
- 无 `--save-session` 默认开启之虞（要显式传）；`--user-data-dir` 不指定时用
  临时目录——现网（非 isolated）本来也是每次 server 起来一个临时 profile，
  无跨会话持久，所以 isolated 化对无 cookies 场景无行为损失。

## 宿主机导出命令（npx playwright@latest，2026-07-06 实测 help）

- 首次导出：`npx playwright open --save-storage=accounts/<id>/cookies/storage-state.json https://x.com`
  ——浏览器弹出、人工登录、**关闭浏览器时保存**。
- 叠加新平台（不丢已有登录态）：`npx playwright open --load-storage=<同一文件> --save-storage=<同一文件> https://<新平台>`。
- 免下载浏览器：加 `--channel chrome` 直接用系统 Chrome。
- python 侧 `.venv-cua` 无 playwright CLI，README 以 npx 为准。

## gitignore 缺口（已核）

根 `.gitignore` 只挡 `*.env` / `secrets.env` / `identities/` /
`*.credentials.json` 等——**`accounts/<id>/cookies/storage-state.json`（.json）
不在覆盖内，必须补一条 `accounts/*/cookies/`**。

## 待 C 段在真容器上核verify

- DISPLAY 是否传导到 claude 子树（agent_loop → claude → mcp server）：
  hook 注释说 custom_startup 运行时 DISPLAY 已设，进容器查
  `/proc/<agent_loop pid>/environ` 确认，不猜。
