# 执行清单：CLI 工具链

前置事实：镜像 `foundagent/cua-agent`（5.39GB，本地 build）由 `vm/docker/Dockerfile.agent` 定义，构建命令在其头注释（`docker build -f vm/docker/Dockerfile.agent -t foundagent/cua-agent:latest vm/`）；`make up` 不自动 rebuild 它。镜像已有 Node 20 / Python 3.12 / git / gcc / ffmpeg / playwright(Firefox)。

## 步骤

1. **Dockerfile.agent 增补两层（同一次 rebuild）**
   - apt 通用工具层：`jq ripgrep fd-find zip unzip sqlite3 tree imagemagick`，并 `ln -s $(which fdfind) /usr/local/bin/fd`；清 apt lists。
   - CLI 层：`gh`（官方 apt repo 或 release 二进制，**版本 pin**）+ `npm install -g vercel@<pin> wrangler@<pin> linkinator@<pin>`（选当前 stable，写死版本号）。
   - `lighthouse`：先算增量，200MB 红线内则加，超则砍并在 PR 记录。`linkinator` 后续由用户明确要求加入，即使体积超过原红线。
2. **核实各 CLI 原生凭证 env 变量名**（PRD 要求零包装脚本）：`gh`→`GH_TOKEN`；`vercel`→核实 `VERCEL_TOKEN` 是否免 `--token` 直接生效；`wrangler`→`CLOUDFLARE_API_TOKEN`。以核实结果为准写进 README，PRD 中的键名字段随核实结果对齐。
3. **`accounts/README.md`**：凭证键名合约 + 每个 token 的人工领取步骤（GitHub fine-grained PAT 按 repo 限权；Vercel token；Cloudflare API token；预留 `GOOGLE_APPLICATION_CREDENTIALS=/account/google-sa.json` 给 mcp-loadout 子任务）。明示 secrets.env 已 gitignore。
4. **builder charter 一句话级告知**（`agents/assets/builder-charter.md`）：容器内已装 gh/vercel/wrangler、凭证来自环境变量、缺凭证时 CLI 未认证属正常。只写系统特定事实。
5. **rebuild + 冒烟**：
   - rebuild 镜像，记录构建耗时与体积增量（`docker images` before/after）。
   - 工具冒烟：`docker run --rm --entrypoint bash foundagent/cua-agent:latest -lc 'jq --version && rg --version && fd --version && zip -v | head -1 && unzip -v | head -1 && sqlite3 --version && tree --version && convert -version | head -1 && gh --version && vercel --version && wrangler --version && linkinator --version'`。
   - 真 token 冒烟（AC1）：若 `accounts/<id>/secrets.env` 已有真凭证则容器内跑 `gh auth status` / `vercel whoami` / `wrangler whoami`；无真凭证则此条标记「待人工 provisioning 后补验」，不得 mock 充数。
6. **回归**：`/opt/homebrew/bin/pytest -q agent/tests orchestration/tests` 全绿；`docker compose config` 通过；空 accounts 包 `make up` 语义无变化（不必真起栈，config 校验 + 现有合约测试覆盖）。

## 校验命令

```bash
/opt/homebrew/bin/pytest -q agent/tests orchestration/tests
docker compose config >/dev/null && echo compose-ok
docker build -f vm/docker/Dockerfile.agent -t foundagent/cua-agent:latest vm/
# + 上面第 5 步的两条冒烟
```

## 执行记录（2026-07-03）

- 版本 pin：`gh 2.96.0`、`vercel 54.20.0`、`wrangler 4.86.0`、`linkinator 7.6.1`。`wrangler 4.107.0` 已验证要求 Node `>=22`，不符合本任务“不新增语言运行时 / 保持 Node 20”的约束，因此 pin 到 4.x 中最高的 Node 20 兼容版本（engine `>=20.3.0`）。`linkinator 7.6.1` 要求 Node `>=20`，与镜像兼容。
- 镜像构建：最终 `docker build -f vm/docker/Dockerfile.agent -t foundagent/cua-agent:latest vm/` 通过；加入 `linkinator` 后的缓存构建耗时约 `49s`。
- 镜像体积：构建前 `5.39GB`，加入核心 CLI 后 `5.85GB`，加入 `linkinator` 后 `5.86GB`。增量主要来自核心 npm CLI 层（`vercel` 约 `195MB`、`wrangler` 约 `198MB`，其中 `workerd` 约 `128MB`）；临时容器验证 `npm install --omit=optional` 未降低体积。用户随后明确要求仍加入 `linkinator`；`lighthouse` 继续不加入。
- 工具冒烟通过：`jq`、`rg`、`fd`、`zip`、`unzip`、`sqlite3`、`tree`、`convert`、`gh`、`vercel`、`wrangler`、`linkinator`、`node` 全部可执行。
- 真 token e2e 通过：`accounts/foundagent/secrets.env` 注入容器后，`gh auth status`、`vercel whoami`、`wrangler whoami` 全部通过。GitHub/Vercel/Cloudflare token 均不写入 git，仅本地 secrets env 使用。
- 空账号/缺 token 状态：`accounts/demo/secrets.env` 不含 `GH_TOKEN` / `VERCEL_TOKEN` / `CLOUDFLARE_API_TOKEN`；已验证无 token 时 CLI 保持未认证状态。
- 回归验证通过：`/opt/homebrew/bin/pytest -q agent/tests orchestration/tests` 为 `222 passed`；`docker compose config` 与 `ACCOUNT=empty-e2e-check docker compose config` 均通过。

## 回滚点

改动纯增量（Dockerfile 两层 + 两份文档 + charter 一行）。回滚 = revert 提交后按原 Dockerfile rebuild 一次。
