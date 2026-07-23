# Design — MCP loadout：per-role mcp.json（GA4 / DataForSEO / GSC）

> 依据：prd.md + 父任务 `research/mcp-research-synthesis.md`（★最终版）。
> 相关 spec：`agent-execution-contracts.md`、`resident-agent-contracts.md`、`loadout-overlay-contracts.md`。

## 0. 现状（改动前）

- 五角色 compose 在 `x-agent-env` 里硬编码同一份 `AGENT_MCP: /opt/foundagent/mcp.json`（cua-local only，镜像内烘焙自 `vm/docker/agent-mcp.json`）。
- `agents/<role>.yaml` 已有 `mcp_config` 字段（`AgentSpec`，默认 `/opt/foundagent/mcp.json`），但常驻路径 `agent_loop.main()` 只读 env，不消费它；只有休眠的 broker 路径（`agent/provider.py`）在用。
- loadout overlay 已支持 `mcp: on|off|<path>`，相对替换路径 resolve 到 `AGENTS_DIR`。
- `build_claude_argv` 不带 `--strict-mcp-config`。

## 1. 关键决策

### D1 落点：`agents/mcp/<role>.json`（不是 vm/docker/mcp/）

五份 per-role 配置放 `agents/mcp/{ceo,researcher,builder,growth,verifier}.json`，经既有 `./agents:/opt/foundagent-orch/agents:ro` 挂载进容器。理由：

- 与角色 yaml 同一棵 capability 树、同一个挂载——**改 MCP 配置不需要 rebuild 镜像**（烘焙进镜像的方案每改一次配置要全量 rebuild 五容器）。
- overlay 的相对替换路径本来就 resolve 到 `AGENTS_DIR`，per-role 基线与公司级替换文件同根同语义。
- 角色 yaml 的 `mcp_config` 字段正是「per-role 配置资产」的声明位——延续「加/改角色 = 改 yaml 不改代码」的既有原则（AC1 血统）。

镜像内烘焙的 `/opt/foundagent/mcp.json` **保留不动**，作为 roleless fallback（`DEFAULT_MCP_CONFIG`，never-brick 兜底）。

### D2 baseline 解析优先级（agent_loop.main）

```
AGENT_MCP env（显式设置时）＞ agents/<key>.yaml 的 mcp_config ＞ DEFAULT_MCP_CONFIG
```

- `_role_model_effort` 扩展为一次 yaml 解析同时返回 model/effort/mcp（改名 `_role_config`）；`mcp_config` 相对路径按 `spec.resolve()` 语义（相对 yaml 所在目录，即 `AGENTS_DIR`）。
- compose 从 `x-agent-env` **删除 `AGENT_MCP` 行**，让 yaml 生效；env 保留为手动调试/覆盖插槽。
- overlay 继续在这个 baseline 上套 `on|off|<path>`（`_overlay_charter_mcp` 不改语义）。
- 解析失败 → WARN + fallback（与 model/effort 同一 never-brick 姿态）。

### D3 版本 pin：pin 版本装进镜像（无运行时 npx/pip install）

Dockerfile.agent 按 gh/vercel/wrangler 的既有 ARG-pin 模式加装（全部已核实正主 + 分发渠道，2026-07-03）：

| server | 安装 | 入口命令 | 已核实 |
|---|---|---|---|
| DataForSEO | `npm i -g dataforseo-mcp-server@2.9.11` | `dataforseo-mcp-server` | 官方，Apache-2.0，2026-06-30 发版 |
| GA4 | `pip install analytics-mcp==0.6.0` | `google-analytics-mcp` | PyPI 正主（repo=googleanalytics/google-analytics-mcp），Requires-Python ≥3.10 |
| GSC | `pip install mcp-gsc==0.1.0` | `mcp-gsc` | AminForou 本人 PyPI 包；**已拆 wheel 核实**含 `GSC_CREDENTIALS_PATH` + `GSC_SKIP_OAUTH` service-account 模式；Requires-Python ≥3.11（容器 Python 3.12.12，满足） |

冷启动零 npm install，版本可复现——满足 PRD「倾向 vendor 进镜像」。

### D4 五份 json 内容

所有角色保留 `cua-local`（computer-server 对所有人 ON，现状不变）：

| 角色 | servers |
|---|---|
| researcher | cua-local + dataforseo + gsc |
| ceo / growth | cua-local + ga4 |
| builder / verifier | cua-local（与现状等价） |

凭证一律 `${VAR}` 展开（Claude Code mcp.json 原生支持，含 `${VAR:-default}`）：

```jsonc
// researcher.json（示意）
"dataforseo": {
  "command": "dataforseo-mcp-server",
  "env": {
    "DATAFORSEO_USERNAME": "${DATAFORSEO_USERNAME}",
    "DATAFORSEO_PASSWORD": "${DATAFORSEO_PASSWORD}",
    "ENABLED_MODULES": "SERP,KEYWORDS_DATA,DATAFORSEO_LABS,BACKLINKS"
  }
},
"gsc": {
  "command": "mcp-gsc",
  "env": {
    "GSC_CREDENTIALS_PATH": "${GOOGLE_APPLICATION_CREDENTIALS:-/account/google-sa.json}",
    "GSC_SKIP_OAUTH": "true"
  }
}
// ceo/growth 的 ga4：
"ga4": {
  "command": "google-analytics-mcp",
  "env": {
    "GOOGLE_APPLICATION_CREDENTIALS": "${GOOGLE_APPLICATION_CREDENTIALS:-/account/google-sa.json}"
  }
}
```

- `ENABLED_MODULES` 按 PRD 需求收敛为 4 模块（关键词量/难度 + SERP + 外链 + Labs 排名/竞争）；是能力配置不是凭证，写死无碍。
- GA4/GSC 共用同一个 SA 文件路径（`/account/google-sa.json`，账号包契约已有此键）。
- **优雅缺省**：凭证 env 缺失 → 该 server 启动失败，Claude Code 对失败 server 是降级继续（其余 server 与会话不受影响）；冒烟步骤显式验证。

### D5 `--strict-mcp-config` 恒加（不只 mcp_config 非空时）

`build_claude_argv` 无条件追加 `--strict-mcp-config`：

- 有 `--mcp-config` 时：只加载我们给的文件（官方推荐 headless 组合）。
- overlay `mcp: off`（mcp_config=None）时：**真 off**——没有 strict 的话 `~/.claude.json`、工作目录 `.mcp.json`（agent 自己写的、或落在 /company 里的）仍可能被捡起来，off 语义漏气。

### D6 人工清单入 accounts/README.md

- 新键：`DATAFORSEO_USERNAME` / `DATAFORSEO_PASSWORD`（Basic auth，控制台生成）。
- Google SA 三步扩写：GA4 property 加 SA 邮箱（Viewer）→ **GSC 属性把 SA 邮箱加为用户（Full/Restricted）**→ `google-sa.json` 落位。
- 验证命令（容器内 claude 会话 `/mcp` 或日志）。

### D7 e2e（AC2）

真凭证注入 `accounts/foundagent/secrets.env` + `google-sa.json` 后，researcher 容器内 `claude -p` 经 MCP 取回一次真实 DataForSEO 响应 + 一次 GSC 响应（不可 mock）。**外部依赖**：DataForSEO 账号（$50 押金）、GCP SA、GSC 属性授权——人工备好后才能跑，实现顺序上放最后、不阻塞其余交付。

### D8 Playwright MCP vs @playwright/cli 对比实验

时间盒（≤半天）、不阻塞交付：researcher 场景同一组任务（打开页面→提取结构化内容）分别走 Playwright MCP 与微软 `@playwright/cli`，记录 token 消耗与成功率，结论 + 数字落 `research/playwright-vs-cli.md`；赢者进 researcher.json（或 CLI 队列）。作为独立收尾步骤。

> **实验结果（2026-07-03，已执行）**：MCP 胜——快 33%、轮次更少；「CLI 省 4x token」未复现（实际成本差仅 14%，claude 2.1.x ToolSearch + mcp 0.0.77 快照落文件已把旧开销消掉）。`@playwright/mcp@0.0.77` 进 researcher.json（args 必须带 `--headless --browser chromium`，容器无 branded Chrome）；chromium 烘进镜像 `PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright`（免 12 min 冷下载）；`@playwright/cli` 记入 CLI 队列备长会话场景。数字详见 research/playwright-vs-cli.md。

## 2. 数据流（改动后）

```
agents/<role>.yaml (mcp_config: mcp/<role>.json)     ← per-role 基线（本任务新增资产）
        │ _role_config() resolve（相对 AGENTS_DIR）
        ▼
AGENT_MCP env（显式设置时优先）                        ← 调试/覆盖插槽
        ▼
_overlay_charter_mcp()：loadout.yaml 的 mcp: on|off|<path>  ← 公司级 diff（语义不变）
        ▼
build_claude_argv：--mcp-config <path>（若非 off）+ --strict-mcp-config（恒有）
        ▼
claude 子进程展开 ${VAR}（继承容器 env = secrets.env 注入）→ 起 stdio server
```

## 3. 兼容性 / 回滚

- **overlay 回归**：`mcp: off|<path>` 语义不动，`test_agent_loop_overlay.py` 原样通过（AC3）。
- **broker 休眠路径**：`agent/provider.py` 读同一个 `spec.mcp_config`，yaml 改指 per-role 文件后自动一致，无需改码。
- **roleless / 缺 yaml**：fallback `DEFAULT_MCP_CONFIG`（镜像内 cua-only），行为与今天完全一致。
- **回滚点**：compose 恢复 `AGENT_MCP` 行即回到全员同配置；镜像回退上一 tag 即卸三个 server；每步独立 commit。

## 4. 风险

- `mcp-gsc==0.1.0`（2025-09 发版）落后 repo main（后者工具更多）。够用先用；不够时升级路径 = vendor repo 单文件进 `vm/`（同 cua_mcp.py 模式，MIT + ATTRIBUTION）。
- `analytics-mcp` 依赖 `google-adk` 较重：镜像体积上涨 + pip resolver 冲突风险——build 一次性验证，冲突则退 `pipx` 隔离安装。
- DataForSEO 是计费 API：agent 滥刷会烧钱。v1 靠 4 模块收敛 + charter 判断力；预算护栏是后续任务（不进本任务范围）。
- 工具数上涨的上下文成本：Claude Code MCP tool search 默认开启兜底；fleet 全员 opus（无 Haiku 假设，PRD 约束成立）。

## 5. 测试设计

单测（无网络、无真凭证）：
1. `build_claude_argv`：恒含 `--strict-mcp-config`；`mcp_config=None` 时无 `--mcp-config` 但 strict 仍在。
2. `_role_config`：yaml 相对路径 resolve 到 AGENTS_DIR；`AGENT_MCP` env 显式设置时胜出；无 yaml → DEFAULT。
3. 配置资产测试（新 test 文件）：五份 json 存在且可解析；全员含 cua-local；researcher 含 dataforseo+gsc、ceo/growth 含 ga4、builder/verifier 仅 cua；凭证值必须是 `${...}` 形态（防写死）；五份 yaml 的 `mcp_config` 指向存在的文件（AC1 的 per-role argv 断言）。
4. 回归：`test_agent_loop*.py`、`test_overlay.py`、`test_loadout_check.py`、`test_spec.py`、`test_provider.py` 全绿。

e2e：见 D7；另加无凭证冒烟（`make up` 后 researcher 日志确认 dataforseo/gsc 连接失败但会话可用、cua-local 正常）。
