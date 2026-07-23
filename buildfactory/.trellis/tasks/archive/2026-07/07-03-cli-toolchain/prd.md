# CLI 工具链：镜像烧入 gh/vercel/wrangler + 凭证合约

> 父任务：`07-03-capability-provisioning`（裁决与调研背景见父任务 prd + research/）。

## 目标

让常驻角色（首先是 builder，其余角色同镜像自然获得）在容器内直接用 CLI 操作 GitHub / Vercel / Cloudflare——CLI-first 裁决的落地第一步，同时定下全部外部凭证的键名合约和人工领取清单。

## 需求

1. **镜像**：`foundagent/cua-agent` 烧入 `gh`、`vercel`、`wrangler`（辅助：`lighthouse`、`linkinator` 视镜像体积增量决定，超过约 200MB 则砍）。版本 pin，不用 latest。
2. **通用开发工具包**（2026-07-03 盘点镜像后补充，与上条同一次 rebuild）：apt 装 `jq`、`ripgrep`、`fd-find`、`zip`、`unzip`、`sqlite3`、`tree`、`imagemagick`，合计增量约 80MB，计入 200MB 红线。Ubuntu 的 fd-find 二进制名为 `fdfind`，需 symlink 成 `fd`。背景：镜像现有 Node 20 / Python 3.12 / git / gcc / ffmpeg / pandas / playwright(Firefox build)，但缺这批 shell 层常用件；gh/vercel/wrangler 之外不再新增语言运行时。
3. **认证走 env，零交互**：`GH_TOKEN`（GitHub fine-grained PAT）、`VERCEL_TOKEN`、`CLOUDFLARE_API_TOKEN` 从 `accounts/<id>/secrets.env` 注入即认证生效（取 CLI 原生识别的变量名，不写包装脚本）。
4. **凭证键名合约**：在 `accounts/README.md` 定死每个键的名字、用途、领取步骤（`GH_TOKEN` / `VERCEL_TOKEN` / `CLOUDFLARE_API_TOKEN` / 可选 `CLOUDFLARE_ACCOUNT_ID` / `GOOGLE_APPLICATION_CREDENTIALS=/account/google-sa.json` 预留给子任务②共用）。这份文档就是「人工 provisioning 清单」的第一部分。
5. **agent 可见性**：builder charter 或相应 skill 里一句话级别告知有哪些 CLI 可用（遵守 [[skill-design-no-generic-for-llm]]：只写系统特定事实，不写 CLI 常识）。
6. **链接检查**（2026-07-03 用户裁决）：尽管核心 CLI 已超过原约 200MB 体积红线，仍把 `linkinator` 作为发布前 broken-link 检查工具烧入镜像；继续不加入 `lighthouse`。

## 约束

- 无 token 时 CLI 保持未认证状态即可，任何启动路径不得因此失败（父任务「优雅缺省」AC）。
- 不引入 MCP（本子任务纯 CLI）；不动 loadout overlay 的语义。
- 镜像构建时间与体积增量在 PR 里记录。

## 验收标准

- [ ] 注入真 token 后，容器内 `gh auth status`、`vercel whoami`、`wrangler whoami` 全部通过（e2e 冒烟，不可 mock）。
- [ ] 空 accounts 包时 `make up` 与五角色启动无回归（existing 162 tests + compose 合约测试全绿）。
- [ ] `accounts/README.md` 覆盖本子任务全部键：一个新公司照文档领 token、填文件即可跑通上一条 AC，无需读代码。
- [ ] 镜像 rebuild 后 CLI 版本可复现（pin 生效）。
- [ ] 通用工具包冒烟：容器内 `jq --version`、`rg --version`、`fd --version`、`zip -v`、`unzip -v`、`sqlite3 --version`、`tree --version`、`convert -version` 全部可用。
- [ ] `linkinator --version` 可用。
