# VM Layer — Design（技术设计）

> 子任务：`06-26-vm-layer`。详细选型依据见 `research/design-spike.md`，上游基础设施依据见父任务 `research/infra-research.md`。
> 对应 PRD：`prd.md`（需求 VM1–VM8 / 验收 AC1–AC6）。
> 环境：开发者本机 Mac + Docker Desktop，全程验证阶段，无生产环境。

## 1. 选型总览

| 模块 | 选型 | 依据 |
|---|---|---|
| 容器沙箱 | **trycua/cua** 的 `trycua/cua-ubuntu`（MIT、原生 arm64、专为 computer-use）跑在 Docker Desktop（冒烟默认用 cua + Claude Code 订阅；`computer-use-demo` 需 API key，可选跳过） | Mac 上最好配最好用；Docker Desktop 容器已套 LinuxKit hypervisor VM = 白送一层隔离；需硬隔离/macOS guest 时一行切 cua Lume micro-VM |
| Computer Use（**双层**） | CEO（订阅）委托 → operator = 独立 Claude Code 实例（订阅）+ 薄 cua MCP（`vm/cua_mcp.py`，暴露 screenshot/click/type）→ 容器 computer-server。operator 自跑 CU 循环，CEO 只收成败+摘要。grounding 弱项后续用本地免费模型（GTA1/UI-TARS）补 | 上下文隔离 + 分层自治 + 零 API key；**不用 cua-agent**（它锁 litellm/API key，用不了订阅）。详见 §7 |
| 浏览器 | 容器内 Firefox/Chromium（桌面级）；高风控注册/登录走 Browser Use/Steel，同一代理出口 | 复用 infra 定稿 |
| 账号/secrets 注入 | **一身份一具名容器**：`--name founder-<id>` + `--env-file`（启动时从自托管 Infisical 拉）+ 挂载 `accounts/<id>` 卷；按需新增、不预配 | 加账号 = 跑一次脚本，不改镜像/代码（满足「账号可扩展性」核心目标） |
| 静态出口 IP | 容器层透明注入 `HTTP(S)_PROXY/NO_PROXY` → Decodo/IPRoyal 独享 ISP IP；可升级 per-account proxy sidecar | 桌面 + 浏览器流量继承固定出口，养号需稳定出口 |
| 可观测（VM7） | **L0** JSONL transcript（`~/.claude/projects`，append-only，真相源）+ **L1** `OTEL_LOG_RAW_API_BODIES=file`（全量请求/响应）+ **L1'** headless `stream-json --verbose` + **L2** Docker `json-file`/`local` 日志驱动 + 自托管 **Langfuse**（好用 UI 层） | append-only 文件硬 kill 不丢；Langfuse 仅锡上添花 |
| 优雅关停（VM8） | `tini -g`(PID1) → supervisor（SIGTERM→`interrupt()`→有界 drain→`disconnect()` flush JSONL→exit 0）→ append-only JSONL + `resume(session_id)` 崩溃恢复；`stop_grace_period 60s` + HEALTHCHECK + `restart unless-stopped` | 程序化 interrupt+drain+flush，而非裸信号 |
| **凭证 / 运行时** | **CEO 与 operator 都用 Claude 订阅**（Claude Code + `CLAUDE_CODE_OAUTH_TOKEN`）—— 已验证 operator 经薄 MCP 驱动容器、**零 API key**；grounding 本地模型免费。**不走 cua-agent 的 litellm/API key 路径**（订阅 OAuth 调 Anthropic API 被拒，官方 #37205） | 全订阅 + 本地，零按量 API；订阅程序化用量受 2026-06 新政约束 |

## 2. 架构

```
host Mac (Docker Desktop = LinuxKit VM,白送一层隔离)
├─ supervisor (默认 Claude Code 订阅 / 可切 Agent SDK)  ── 大脑 / 编排 / SIGTERM handler / resume
│     └─(cua MCP server)→ founder-01 容器
├─ founder-01  [trycua/cua-ubuntu]  ── 手:XFCE + Firefox/Chromium + computer-server + KasmVNC:8006
│     ├─ env: Infisical secrets(per-account) + HTTP(S)_PROXY → Decodo/IPRoyal ISP IP
│     ├─ PID1 = tini -g  / stop_grace_period 60s / restart unless-stopped / HEALTHCHECK
│     └─ volumes → host:  ~/.claude(JSONL) · /logs(raw bodies+stream-json) · /state(session_id+heartbeat)
├─ langfuse (compose)  ── 好用层 UI :3000(检索/回放/成本)
└─ accounts/<id> + cc_sessions_<id> ── 按需新增身份(复制 founder-01 这套)
```

**组件职责：**
- **supervisor**（默认 Claude Code + 订阅 OAuth；可切 Agent SDK + API key）：编排大脑；持有 cua MCP server 连接；捕获 SIGTERM 走优雅退出；崩溃后 `resume`（`claude --resume` 或 SDK `resume(session_id)`）。
- **founder-<id> 容器**（cua-ubuntu）：agent 的「手」——XFCE 桌面 + 浏览器 + computer-server + KasmVNC `:8006`（实时可视/接管）；env 注入 per-account secrets + 代理出口；三卷落宿主持久化；PID1 = `tini -g`。
- **langfuse**：可观测 UI（检索/回放/成本），好用层、非真相源。
- **accounts/<id> + cc_sessions_<id>**：每身份一套，按需新增。

## 3. 关键契约 / 接口

### 3.1 账号/secrets 注入接口（可扩展，VM4）
- 注入点 = **容器边界**（env + 挂载卷），不把账号烤进镜像。
- 加身份 = Infisical 新建 path/machine account → 跑启动脚本（`infisical export → /run/<id>.env → docker run --env-file + 挂载卷 → shred`）。详见 spike §5.1。
- 铁律：**凭证永不进 LLM context**；更硬可选 `--network none` + 出站代理 sidecar 在网络层注入凭证。

### 3.2 静态出口 IP 接口（对 agent 透明，VM5）
- `HTTP(S)_PROXY/NO_PROXY` env → 独享 ISP IP；桌面与浏览器流量自动继承。
- 可升级为 per-account proxy sidecar（`--network container:<proxy>`），便于审计 + 按域名白名单。详见 spike §5.2。

### 3.3 可观测层（VM7）
- 四层防御纵深（L0 JSONL 真相源 / L1 raw API bodies / L1' headless stream-json / L2 Docker 日志）+ Langfuse UI。详见 spike §3。
- **真相源 = L0 append-only JSONL**（硬 kill 不丢已写）。

### 3.4 Graceful shutdown 信号流（VM8）
- **默认（Claude Code 订阅）**：`docker stop` → SIGTERM → `tini -g` 转发进程组 → claude 进程优雅退出；JSONL 实时 append-only 已持久化（硬 kill 不丢已写）；崩溃恢复 `claude --resume <session>`。
- **备选（Agent SDK / API key）**：supervisor `interrupt()` → 有界 drain → `disconnect()` flush JSONL → exit 0；`resume(session_id)` 恢复。
- 两路径共用：`stop_grace_period 60s` + HEALTHCHECK + `restart unless-stopped`。详见 spike §4。

## 4. 关键权衡

- **容器 vs VM**：Mac 上 Docker 容器已套 LinuxKit VM，隔离足够；重型 per-agent VM 短期无优势（用户已确认）。保留「一行切 cua Lume micro-VM」的升级路径，应对硬隔离 / macOS guest 需求。
- **VM7/VM8 无 turnkey，靠拼装**：`supervisor.py`（~40 行）是 load-bearing 组件，必须当正经组件维护 + 单测 SIGTERM 路径。
- **敏感数据落盘**：开 raw bodies 后落盘含明文凭证上下文 → 日志卷仅本机、访问受控、**绝不随 agent 出网**。
- **SDK 版本依赖**：`interrupt()` 仅在 `ClaudeSDKClient`（V1/Python），flush race 需 PR #642 后版本 → **pin 版本**，V2 不用于关停关键路径。

## 5. 风险与缓解（精选自 spike §7）

| 风险 | 缓解 |
|---|---|
| VM7/VM8 无开箱方案 | 以 append-only JSONL 为唯一真相源；supervisor 当正经组件测试 |
| OTel 硬 kill 丢 buffer | 真相源用 JSONL，不依赖 OTel；调小 export interval + 留足 grace |
| 敏感数据明文落盘 | 日志卷本机受控、不出网 |
| SDK interrupt 版本限制 | pin claude-agent-sdk 版本，关停走 V1 ClaudeSDKClient |
| 单 Mac 并发上限 | Phase 1–2 后实测单容器内存/CPU，估算并发；Docker Desktop Resources 配额是硬瓶颈 |
| arm64 兼容 | cua-ubuntu / computer-use-demo 已验证；Steel/Browser Use 镜像采用前 `docker manifest inspect` 确认 |

## 6. PRD 验收映射

| AC | 由什么满足 |
|---|---|
| AC1 起隔离容器（含桌面+浏览器） | §2.3 spike：Docker Desktop + cua `Computer(...).run()`，`:8006` 可视；Day-0 computer-use-demo 一行冒烟 |
| AC2 账号可扩展注入 | §3.1：一身份一具名容器 + env-file/卷 + Infisical；加账号=跑脚本 |
| AC3 Computer Use+浏览器+账号打通 | §3.1/§2：cua computer-server 经 MCP 接 Claude + 容器浏览器 |
| AC4 静态 IP 接口 | §3.2：`HTTP(S)_PROXY` → 独享 ISP IP |
| AC5 全量可观测/记录/回放 | §3.3：L0 JSONL + L1 raw bodies + L2 docker 日志 + Langfuse |
| AC6 优雅关停 | §3.4：tini -g + supervisor interrupt→drain→flush + resume + grace 60s |

## 7. Computer-use 架构（双层，已验证）

> 研究依据 `research/computer-use-architecture.md`；Phase 2 已实测验证。

**结论**：采用**双层** —— CEO 委托完整电脑任务给专门 operator 执行，而非 CEO 自己循环点像素。理由是**结构性**的（非「Claude 点击差」——Claude OSWorld 端到端 61.4% 是 SOTA）：上下文隔离（operator 的截图/重试/多轮 vision 不污染 CEO 长程规划）、分层自治、成本/失败收敛、并发。

**落地（全订阅、零 API key，已验证）**：
- **CEO**：Claude Code 订阅，下达「在 X 完成 Y」并验收（收成败+摘要+终态图）。
- **operator**：独立 Claude Code 实例（订阅，`CLAUDE_CODE_OAUTH_TOKEN`）+ 薄 cua MCP（`vm/cua_mcp.py`：screenshot/get_screen_size/left_click/double_click/type_text/press_key），自跑 CU 循环。
- **grounding 弱项**（高分屏/专业软件像素定位，Claude ScreenSpot-Pro ~17%）：后续在薄 MCP 加 `click_element(description)`，内部调**本地免费**专门模型（MLX UI-TARS-7B / GTA1）转坐标 —— 仍零 API key。
- **不用 cua-agent**：它走 litellm 只认 API key，订阅 OAuth 调 Anthropic API 被拒（#37205）。故走自编排薄 MCP 路线。

**Phase 2 实测**：operator（Claude 订阅）截图→识别桌面→双击 Firefox→Firefox 打开（截图确认 "Choose User Profile" 对话框）。零 API key。

**Claude-in-container（终态，已验证）**：agent 不在宿主、而是**整个跑在容器内**——镜像 `foundagent/cua-agent`（`vm/docker/Dockerfile.agent`）内置 node + claude CLI（npm 装；`claude.ai/install.sh` 被 CDN 挡）+ cua-computer + 薄 MCP（`CUA_HOST_SERVER=1` 连 localhost:8000）。容器内 `claude -p`（订阅 `CLAUDE_CODE_OAUTH_TOKEN`）自主操作容器桌面（实测：创建 Firefox profile + 打开主窗口）。宿主 Mac 完全不参与。容器内 `api.anthropic.com` 可达（订阅 API 通），`claude.ai` 被挡（故 claude CLI 走 npm）。这取代了早期「Claude 在宿主、伸手进容器」的过渡形态。

> 完整对比表、搭建命令、信号流见 `research/design-spike.md` 与 `research/computer-use-architecture.md`。
