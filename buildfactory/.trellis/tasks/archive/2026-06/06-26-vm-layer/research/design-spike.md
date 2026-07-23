以下是 VM 层选型设计报告(Markdown,中文)。这是交付物本身。

---

# Foundagent v6 — VM 层选型设计报告 (Design Selection)

> 范围:本报告只覆盖 **VM 层(沙箱运行时)**,即「在一台开发者 Mac(macOS + Docker Desktop)上,给单个 founder-agent 一个隔离、可观测、可优雅关停的运行环境,内含 Computer Use 桌面 + 浏览器,并能按需注入账号与静态出口 IP」。
> 已在 infra-research(`/Users/weston/dev/BuildFactory/.trellis/tasks/06-26-foundagent-v6/research/infra-research.md`)中**定稿、本报告直接复用**的部分:账号/secrets = 自托管 [Infisical](https://infisical.com/pricing);静态出口 IP = 独享 ISP 代理 [Decodo](https://decodo.com)/[IPRoyal](https://iproyal.com);Web 强 stealth 层 = [Browser Use](https://browser-use.com/pricing)/[Steel](https://steel.dev/)。
> 硬约束:无生产环境,全部跑在这一台 Mac 上;**能用容器(Docker)就不用重型 VM**;「最好配 + 最好用」;账号注入必须是「按需扩展」接口;新增两条硬需求 **VM7(全量可观测/记录/回放/持久化)** 与 **VM8(优雅关停)**。

---

## 1. 选型结论(TL;DR)

| 模块 | 选型(一句话) |
|---|---|
| **容器沙箱方案** | [trycua/cua](https://github.com/trycua/cua) 的 `trycua/cua-ubuntu` 容器跑在 Docker Desktop 上(MIT、原生 arm64、专为 computer-use 而造);用 [Anthropic computer-use-demo](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo) 做 Day-0 一行命令冒烟。**不上重型 VM**——Mac 上容器本就跑在 LinuxKit hypervisor VM 里,已白送一层 VM 级隔离边界。 |
| **Computer Use(桌面级「手」)** | cua 容器内置的 `computer-server`(screenshot/click/type/scroll)+ XFCE 桌面;Claude(Agent SDK / Claude Code)经 **cua MCP server** 当大脑驱动。Claude = 脑,cua = 手。 |
| **浏览器层** | 容器内自带 Firefox/Chromium 满足桌面级 web;高风控注册/登录走已定稿的 [Browser Use](https://browser-use.com/pricing)/[Steel](https://steel.dev/),通过同一静态 IP 代理出网。 |
| **账号/secrets 注入接口** | 「一身份一具名容器」:每个身份 `docker run --name founder-<id>` + 独立 `--env-file` + 挂载 `./identities/<id>` 卷,值在启动时从自托管 [Infisical](https://infisical.com/pricing) 拉取。**按需新增,不预配**。 |
| **静态 IP 接口** | 容器层透明注入:`HTTP_PROXY/HTTPS_PROXY/NO_PROXY`(指向 [Decodo](https://decodo.com)/[IPRoyal](https://iproyal.com) 独享 ISP IP),桌面与浏览器流量全部继承固定出口;需更强隔离时用 proxy sidecar 网关。 |
| **可观测(VM7)** | 「防御纵深」分层:**L0** 文件系统 JSONL transcript(`~/.claude/projects/<proj>/<session>.jsonl`,append-only,ground truth)+ **L1** `OTEL_LOG_RAW_API_BODIES=file:<dir>`(每条请求/响应全量落盘)+ **L2** Docker `json-file`/`local` 日志驱动 + 轮转(stdout 兜底);**好用层**叠自托管 [Langfuse](https://langfuse.com/integrations/frameworks/claude-agent-sdk)(检索/回放/成本 UI)。 |
| **优雅关停(VM8)** | `tini -g`(PID1,回收僵尸 + 进程组转发 SIGTERM)→ 自写 supervisor(捕获 SIGTERM → `interrupt()` → 有界 drain → `disconnect()` flush JSONL → exit 0)→ 挂载 JSONL + `resume(session_id)` 做崩溃恢复;`stop_grace_period: 60s` + HEALTHCHECK 心跳 + `restart: unless-stopped`。 |

**一句话架构**:Claude Agent SDK = 编排大脑(在宿主或一个 supervisor 容器内);cua-ubuntu 容器 = 可被替换的「手」(Docker 今天,需要硬隔离/macOS guest 时一行参数升级到 Lume micro-VM);可观测以 append-only 文件为唯一真相源,Langfuse 仅作锡上添花;关停走程序化 interrupt+drain+flush,而非裸信号。

---

## 2. 容器沙箱方案

### 2.1 对比表

| 方案 | 维护 / 许可 | Mac (Apple Silicon) | 能力面 | 隔离 | 起步成本 | 适配本项目 |
|---|---|---|---|---|---|---|
| **[trycua/cua](https://github.com/trycua/cua)** (cua-ubuntu 容器) | 活跃 (推送 ≈当天)、MIT、专为 computer-use | 原生 arm64(`docker manifest inspect` 已验证,无 Rosetta) | **完整 Linux 桌面**(任意 GUI)+ Firefox/Chromium + 自启 `computer-server` + KasmVNC 浏览器实时画面 `:8006` | Docker 标准容器隔离(Mac 上= 容器套 LinuxKit VM,白送 VM 边界);可一行升级 Lume micro-VM | 3 步(装 Docker → `pip install cua-computer cua-mcp-server` → `Computer(...).run()`) | **最佳**:原生 MCP 入 Claude Code/Agent SDK;一身份一容器=天然账号注入接口 |
| [Anthropic computer-use-demo](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo) | Anthropic 官方、MIT | 原生 arm64(已验证) | 完整 Linux 桌面 + Firefox + 组合 chat+desktop UI `:8080` | 单容器、共享内核(官方明确要求跑在专用 VM/容器、白名单出网) | **1 行 `docker run`** | **Day-0 冒烟最快**;但是 demo 非框架(无任务库/回放库/多账号接口) |
| [browser-use/web-ui](https://github.com/browser-use/web-ui) | 活跃、MIT、100k★ | 需确认 arm64 | **仅浏览器**(无通用桌面)+ noVNC `:6080` + CDP | 单容器 | `docker compose up -d` | 与已定稿 web 层重叠,非桌面沙箱需求 |
| [Steel](https://github.com/steel-dev/steel-browser) | 活跃、Apache-2.0 | ARM 有已知问题,需官方 ARM 镜像/本地构建 | **仅浏览器** + CDP + 代理 + session viewer | 单容器 | `docker run`/compose | 已是定稿 web 层,作浏览器切片而非桌面 |
| [Bytebot](https://github.com/bytebot-ai/bytebot) | **已 ARCHIVED**(archived:true,末次推送 2025-09-12)、Apache-2.0 | 无 Mac 专属文档 | 最 turnkey:Tasks UI + Live View + Takeover + 桌面应用 | 每桌面独立容器 | 一条 compose | **不可作长期底座**(无安全/Apple-Silicon 维护)——这是对早期研究的最大修正 |
| [cua + Lume/Lumier](https://cua.ai/blog/lume-to-containerization) (Apple Virt VM) | 活跃、MIT | Apple Silicon 原生但重型 | 完整 VM(可跑 **macOS guest**) | **最强**:每 guest 真 VM、独立内核 | 重(下载+启动整 VM 镜像) | **仅在需要 macOS-only 应用或硬隔离时**才用;用户已明确「重型 VM 短期无优势」,跳过 |

### 2.2 推荐与理由

**选 cua 的 `trycua/cua-ubuntu` 容器,Docker Desktop 运行,经 cua MCP server 接 Claude;用 computer-use-demo 做一行冒烟。**

- 唯一同时满足:(a) 活跃维护且**专为 computer-use agent 而造**(MIT);(b) **一个容器 = 完整 Linux 桌面 + 浏览器 + 自启 screenshot/click/type server + 浏览器实时画面 `:8006`**;(c) **原生 arm64**(无模拟);(d) **原生 MCP** 直接落进 Claude Code/Agent SDK,保持 Claude 为脑、cua 为手。
- **关键认知**:Docker Desktop 在 Mac 上把每个 Linux 容器都跑在 LinuxKit hypervisor VM 内,所以「容器」本就是「容器套 VM」——**已白送一层 VM 级宿主隔离**,这正好印证用户「单独重型 per-agent VM 短期无优势」。需要更硬隔离或 macOS guest 时,**同一行 cua API 改 `provider_type='lume'` 即升级到 Apple-Virtualization micro-VM,agent 代码零改动**。
- 旧 turnkey favorite **Bytebot 已 archived**,不能作长寿命项目底座(只能硬 fork 自维护)。

### 2.3 搭建步骤草图(几条命令到可用桌面)

```bash
# 0) Day-0 冒烟(1 行,确认这台 Mac 上 Computer Use 可用)
docker run \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $HOME/.anthropic:/home/computeruse/.anthropic \
  -p 8080:8080 -p 6080:6080 -p 8501:8501 -p 5900:5900 -it \
  ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest
# 打开 http://localhost:8080 → chat+desktop 合并 UI

# 1) 装 Docker Desktop,并在 Resources 调高 CPU/RAM
brew install --cask docker        # 启动后到 Settings → Resources 提配额

# 2) 装 cua SDK + MCP server
pip install cua-computer cua-mcp-server   # 或 cua-agent[all]

# 3) 启一个 founder 沙箱(首次自动拉原生 arm64 镜像 + 起 XFCE+Firefox+computer-server)
python - <<'PY'
import asyncio
from computer import Computer
async def main():
    c = Computer(os_type='linux', provider_type='docker',
                 image='trycua/cua-ubuntu:latest', name='founder-01')
    await c.run()        # 启动桌面
asyncio.run(main())
PY
# 4) 浏览器看/接管:http://localhost:8006 (KasmVNC,无需 VNC 客户端)

# 5) 在 Claude Code / Agent SDK 注册 cua MCP server,Claude 即可把
#    screenshot/click/type/scroll 当工具调用(Claude=脑, cua=手)
```

---

## 3. 可观测性方案(VM7:全部输出可记录、可回放、持久化)

### 3.1 设计原则

> **真正的 ground truth 是文件系统 JSONL transcript,不是任何第三方平台。** OTel/UI 靠批量 flush,被硬杀会丢 buffer;只有 append-only 文件在硬 kill/断电下不丢已写数据。所以「保证记录+回放」用零依赖的文件底座达成,Langfuse 只作「好用」层。

### 3.2 推荐组合(防御纵深,从下到上)

| 层 | 机制 | 抓什么 | 为何必需 | URL |
|---|---|---|---|---|
| **L0 真相源** | `~/.claude/projects/<proj>/<session-id>.jsonl`(默认开启,append-only)bind-mount 到宿主卷 | prompt + thinking + 每个 tool input/output + 每轮 token/model/git state,`parentUuid` 串链 | 内容最全、append-only、`claude --resume <id>` 原生回放;**硬 kill 不丢已写**(直接服务 VM8) | https://code.claude.com/docs/en/sessions |
| **L1 全量证据** | `CLAUDE_CODE_ENABLE_TELEMETRY=1` + `OTEL_LOG_RAW_API_BODIES=file:/logs/api` | 每次 API attempt 未截断的 `<uuid>.request.json` + `<request_id>.response.json`(完整 system prompt + 全部 messages + tools + content blocks + usage) | 「每一条发给 Claude / Claude 返回的」字面全量(注意历史轮 thinking 被 redact;落盘含凭证上下文,目录须受控) | https://code.claude.com/docs/en/monitoring-usage |
| **L1' headless 事件流** | `claude -p "<task>" --output-format stream-json --verbose --include-partial-messages \| tee /logs/run-$(date +%s).jsonl` | 实时 token delta / tool call / retry / 终态 cost+session_id | 后台/编排 agent 的实时可观测 + 可回放落盘(`--verbose` 是拿全中间事件的必需项) | https://code.claude.com/docs/en/headless |
| **L2 stdout 兜底** | Docker 日志驱动 `--log-driver json-file --log-opt max-size=20m --log-opt max-file=10 --log-opt compress=true`(或 `local`) | 容器一切 stdout/stderr(带时间戳+来源) | 应用零改动的安全网;**务必显式 max-size/max-file 否则撑爆磁盘** | https://docs.docker.com/engine/logging/drivers/local/ |
| **好用 UI** | 自托管 [Langfuse](https://langfuse.com/integrations/frameworks/claude-agent-sdk):`git clone langfuse && docker compose up -d` → `:3000`;接入用 `openinference-instrumentation-claude-agent-sdk` 一行 `ClaudeAgentSDKInstrumentor().instrument()` | 逐 step 看 prompt/response/tool-call、跨 session 聚合、multi-agent 委派链、成本 | MIT 自托管、数据全留本机、对 Agent SDK 一等集成(Helicone 已进维护模式,不作首选) | https://langfuse.com/integrations/frameworks/claude-agent-sdk |

### 3.3 最少配置(挂 2 个卷 + 几个 env + 1 行 log-opt)

```bash
docker run \
  -v cc_sessions:/root/.claude \                 # L0: JSONL transcript(全量真相源)
  -v $PWD/logs:/logs \                           # L1: raw API bodies + stream-json
  -e CLAUDE_CODE_ENABLE_TELEMETRY=1 \
  -e OTEL_LOG_RAW_API_BODIES=file:/logs/api \    # L1: 每条请求/响应全量落盘
  --log-driver json-file --log-opt max-size=20m --log-opt max-file=10 --log-opt compress=true \
  <agent-image>
# 容器内固定 HOME/工作目录,保证 ~/.claude/projects/<proj>/<session-id>.jsonl 路径可预测
```

可选的 native OTel(发到 Langfuse/Collector,正文需显式 opt-in):
```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1 CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
export OTEL_TRACES_EXPORTER=otlp OTEL_LOGS_EXPORTER=otlp OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_LOG_USER_PROMPTS=1 OTEL_LOG_TOOL_DETAILS=1 OTEL_LOG_TOOL_CONTENT=1   # 记正文
# VM8 减少 flush 丢失窗口:
export OTEL_METRIC_EXPORT_INTERVAL=1000 OTEL_LOGS_EXPORT_INTERVAL=1000 OTEL_TRACES_EXPORT_INTERVAL=1000
```

> **像素级回放(可选)**:用 ffmpeg 录制 cua 的 KasmVNC `:8006` 画面流写宿主卷,得到与 transcript 对齐的视频回放。cua 的 agent trajectory(screenshots+actions)也可写到挂载的 `./trajectories` 卷。

---

## 4. Graceful shutdown 方案(VM8)

### 4.1 信号流(docker stop → SIGTERM → agent 优雅退出)

```
docker compose stop founder-agent
        │  (默认 STOPSIGNAL=SIGTERM,grace=stop_grace_period:60s)
        ▼
PID1 = tini -g  ──(进程组转发 SIGTERM,杀掉被 reparent 的 Bash/浏览器孤儿子进程)
        ▼
supervisor.py (捕获 SIGTERM)
        ├─ client.interrupt()                 # 立即中止在途轮次(Python/V1 一等方法,立即返回但不清 buffer)
        ├─ await wait_for(drain, timeout=30)  # 有界 drain receive_response() 直到 ResultMessage
        ├─ flush 应用日志 / 写 session_id / 写 heartbeat
        └─ 退出 async with → disconnect()/__aexit__  # 等 CLI 子进程最多 ~5s flush 它的 JSONL (PR #642)
        ▼
exit 0  (若 60s 内没完成 → 收 SIGKILL 不 flush,但 append-only JSONL + resume 仍可恢复)
```

### 4.2 为什么不能裸跑 `claude -p` 当 PID1(反模式)

- 直接对 `claude` 发 SIGTERM **不 flush 会话状态、不触发 SessionEnd hook、并把所有 Bash-tool 子进程变孤儿**([claude-code #29096](https://github.com/anthropics/claude-code/issues/29096));SIGKILL 则任何 hook 都不触发。官方至今**没有**程序化的 `/exit` 等价优雅信号。
- 正确路径是**程序化**而非信号驱动:用 SDK 自带的 `interrupt()` → drain → `disconnect()` flush 链路。

### 4.3 退出前刷写什么

| 刷写项 | 落点(挂载卷) | 保证 |
|---|---|---|
| 会话 transcript JSONL | `~/.claude/projects/...`(append-only) | 最后一条**完整**轮次必在卷上;mid-write 的那一轮才会丢 |
| `session_id` 指针 | `/state/session.json`(每轮 checkpoint) | 重启时 `ClaudeAgentOptions(resume=session_id)` 恢复全上下文 |
| raw API bodies + stream-json | `/logs/...` | VM7 全量证据 |
| 应用级业务状态 | `/state/...`(Stop/SessionEnd hook + supervisor 双保险) | 业务记忆/当前任务/在制品;**SessionEnd 不是 Python SDK 回调、且 raw kill 不触发,故 supervisor 必须也 flush** |
| heartbeat 时间戳 | `/state/heartbeat` | 配合 HEALTHCHECK 检测「卡死在 Working」并自愈重启 |

### 4.4 关键配置(Dockerfile + compose)

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends tini nodejs npm \
 && npm i -g @anthropic-ai/claude-code \
 && pip install --no-cache-dir 'claude-agent-sdk>=<pin 含 PR #642 的版本>' \
 && rm -rf /var/lib/apt/lists/*
COPY supervisor.py /app/supervisor.py
STOPSIGNAL SIGTERM
ENTRYPOINT ["tini","-g","--"]            # -g 转发到整个进程组(--init 不带 -g)
CMD ["python","-u","/app/supervisor.py"]
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD [ $(( $(date +%s) - $(cat /state/heartbeat 2>/dev/null || echo 0) )) -lt 90 ]
```

```yaml
services:
  founder-agent:
    build: .
    init: false                 # 自带 tini -g,勿双 init
    stop_signal: SIGTERM
    stop_grace_period: 60s      # 留足 interrupt+drain+flush(默认 10s 太短)
    restart: unless-stopped     # 崩溃自愈,supervisor 自动 resume
    volumes:
      - claude-sessions:/root/.claude/projects
      - ./state:/state
volumes: { claude-sessions: {} }
```

> **Mac 注意**:Docker Desktop 引擎是 Linux VM,信号语义与 Linux 一致;唯二坑在 CLI 层——`docker kill` 与 Cmd-Q 退出 Docker Desktop 会跳过 grace 期(走 SIGKILL,不 flush;但 resume 仍能恢复)。**优雅停一律用 `docker compose stop`**。SDK 注意:`interrupt()` 仅 `ClaudeSDKClient`(非一次性 `query()`),V2 `unstable_v2_createSession` 仍缺 `interrupt()`([sdk-ts #120](https://github.com/anthropics/claude-agent-sdk-typescript) 开放);旧 SDK 有 flush race([python #625](https://github.com/anthropics/claude-agent-sdk-python),已由 PR #642 修复),**务必 pin 新版**。

---

## 5. 账号/secrets 可扩展注入接口 + 静态 IP 接口

> 复用 infra-research 定稿:secrets = 自托管 [Infisical](https://infisical.com/pricing)(MIT 核心、无限免费 machine identity);静态 IP = 独享 ISP 代理 [Decodo](https://decodo.com)/[IPRoyal](https://iproyal.com)。两条铁律:**凭证永不进 LLM context、白名单出网**。

### 5.1 账号/secrets 注入接口(「一身份一容器」,按需扩展、不预配)

设计:**注入点 = 容器边界**(env + 挂载卷),而非把所有账号烤进镜像。新增一个身份 = 启一个新具名容器,值在启动时从 Infisical 拉。

```bash
# 接口契约:identities/<id>/ 是该身份的持久卷;Infisical 提供该身份的 machine identity
ID=founder-02
# 1) 用该身份的 machine identity 登录 Infisical,导出该身份 scope 的 secrets 到运行时 env-file
infisical export --projectId=$PROJ --env=prod --path="/identities/$ID" --format=dotenv > /run/$ID.env
# 2) 启该身份的具名沙箱:独立 env + 独立卷 + 独立出口 IP(见 5.2)
docker run -d --name $ID \
  --env-file /run/$ID.env \
  -v $PWD/identities/$ID:/identity \
  -v cc_sessions_$ID:/root/.claude \
  trycua/cua-ubuntu:latest
shred -u /run/$ID.env          # 用完即焚,secrets 不落明文盘
```

- **可扩展性**:加账号 = 在 Infisical 新建一个 path/machine identity + 跑一次上面的脚本。无需改镜像、无需改编排代码。
- **隔离**:每身份独立容器 + 独立卷 + 独立 session,互不串台;cua 容器在 Mac 上又套在 LinuxKit VM 内。
- **更硬的注入(可选)**:把 agent 容器 `--network none`,所有出网经一台「出站代理 sidecar」(Envoy credential_injector / Squid / LiteLLM),代理在网络层注入凭证 + 域名白名单——agent 永不接触 secret(infra-research 的 secure-deployment 模式)。

### 5.2 静态 IP 接口(对 agent 透明)

```bash
# 最小实现:容器层 env,桌面 + 浏览器流量全部继承固定出口
docker run -d --name founder-02 \
  -e HTTP_PROXY="http://user:pass@<decodo-isp-ip>:port" \
  -e HTTPS_PROXY="http://user:pass@<decodo-isp-ip>:port" \
  -e NO_PROXY="localhost,127.0.0.1,langfuse-web,infisical" \
  ... trycua/cua-ubuntu:latest
```

- **一身份一独享 ISP IP**(非轮换),Computer Use 与浏览器对网络层完全无感、自动继承固定出口,符合「养号需稳定出口」。
- **可扩展为 proxy sidecar 网关**:每身份一个 proxy 容器持有该身份的 ISP IP,agent 容器 `--network container:<proxy>` 或 compose 网络指向它——便于审计与按域名白名单。
- 已定稿 web 层 [Browser Use](https://browser-use.com/pricing)/[Steel](https://steel.dev/) 同样走这个代理出口,保证「桌面动作」与「stealth 浏览器动作」同一出口 IP。

---

## 6. 最小可运行架构总览(映射 VM 层 PRD AC1–AC6)

**叙述**:宿主 Mac 上跑 Docker Desktop;一个 **supervisor**(`claude-agent-sdk`)作大脑,持有 cua MCP server 连接到 **一个具名 cua-ubuntu 容器**(=该 founder 身份的「手」:完整 Linux 桌面 + Firefox + computer-server,`:8006` 实时可视/接管)。该容器:env 注入来自 Infisical 的账号 secrets + 指向 Decodo/IPRoyal 的代理出口;`~/.claude`、`/logs`、`/state` 三个卷落到宿主做持久化与回放;PID1 是 `tini -g`,关停走 `docker compose stop`(SIGTERM→interrupt→drain→flush)。可观测旁路一个自托管 Langfuse 容器(`:3000`)。加新身份 = 复制这一套具名容器 + 卷。

```
host Mac (Docker Desktop = LinuxKit VM,白送一层隔离)
├─ supervisor (claude-agent-sdk)  ── 大脑 / 编排 / SIGTERM handler / resume(session_id)
│     └─(cua MCP server)→ founder-01 容器
├─ founder-01  [trycua/cua-ubuntu]  ── 手:XFCE + Firefox/Chromium + computer-server + KasmVNC:8006
│     ├─ env: Infisical secrets(per-identity) + HTTP(S)_PROXY → Decodo/IPRoyal ISP IP
│     ├─ PID1 = tini -g  / stop_grace_period 60s / restart unless-stopped / HEALTHCHECK
│     └─ volumes → host:  ~/.claude(JSONL) · /logs(raw bodies+stream-json) · /state(session_id+heartbeat) · /trajectories
├─ langfuse (compose)  ── 好用层 UI :3000(检索/回放/成本)
└─ identities/<id> + cc_sessions_<id> ── 按需新增身份(复制 founder-01 这套)
```

| AC(VM 层验收,按本报告约束推导) | 由什么满足 |
|---|---|
| **AC1 — Mac 上几条命令起一个隔离沙箱(含桌面)** | §2.3:Docker Desktop + cua `Computer(...).run()`,`:8006` 可视;Day-0 用 computer-use-demo 一行冒烟 |
| **AC2 — Computer Use + 浏览器可被 agent 驱动** | §1/§2:cua computer-server(screenshot/click/type)经 MCP 接 Claude;容器内 Firefox + 已定稿 Browser Use/Steel |
| **AC3 — 账号/secrets 可扩展注入(按需、不预配)** | §5.1:一身份一具名容器 + env-file/卷,值取自自托管 Infisical;加账号=跑一次脚本 |
| **AC4 — 静态出口 IP 接口(对 agent 透明)** | §5.2:`HTTP(S)_PROXY` → Decodo/IPRoyal 独享 ISP IP;桌面+浏览器流量继承,可升级 proxy sidecar |
| **AC5 — VM7 全量可观测/记录/回放/持久化** | §3:L0 JSONL transcript(真相源)+ L1 raw API bodies + L2 docker 日志 + Langfuse UI;卷持久化 |
| **AC6 — VM8 优雅关停不丢日志/状态** | §4:tini -g + supervisor interrupt→drain→flush + append-only JSONL + resume + grace 60s |

---

## 7. 风险与开放问题

1. **VM7/VM8 没有任何容器是开箱 turnkey 的**——都是「拼装」:可观测靠 JSONL+rawbodies+docker-log+Langfuse 四件套,关停靠 tini+supervisor+resume。落地工作量集中在 **supervisor.py(~40 行,load-bearing)** 与卷/env 编排,需当作正经组件维护和测试。
2. **OTel flush 在硬 kill 下丢 buffer**(metrics 60s/logs+traces 5s 默认):必须以 append-only JSONL 作唯一真相源,OTel/Langfuse 只作好用层;并调小 export interval + 留足 grace 期。
3. **敏感数据落盘**:开 `OTEL_LOG_RAW_API_BODIES` / `OTEL_LOG_USER_PROMPTS` 后,落盘的是含完整对话 + 凭证上下文的明文;日志卷必须仅本机、访问受控、**绝不随 agent 出网**(与 infra-research 的「凭证永不进 LLM context」一致)。
4. **SDK 版本依赖**:`interrupt()` 只在 `ClaudeSDKClient`(V1/Python),V2 仍缺;flush race 需 PR #642 后的版本——**pin 版本**,V2 不要用于关停关键路径。
5. **Docker Desktop 在 Mac 是共享内核容器**(套 LinuxKit VM,已有一层边界):处理不可信 web 动作仍有 prompt-injection 风险;若单容器被攻破后横向移动是顾虑,再升级到 cua + **Lume Apple-Virtualization micro-VM**(一行参数,agent 代码零改),代价是重型 VM 的启动/footprint。
6. **macOS guest 是 Docker 唯一给不了的**:若业务必须用 Mac-only 应用,只能走 Lume/Apple Virtualization(每台物理 Mac 约 2 个 macOS guest 的 Apple 许可上限)。默认 Linux 桌面容器。
7. **arm64 验证**:cua-ubuntu 与 computer-use-demo 已验证原生 arm64;但 Steel 在 ARM 有已知问题,Browser Use web-ui 的 arm64 镜像需在采用前 `docker manifest inspect` 确认或本地构建。
8. **单 Mac 并发上限**:每个 founder 容器是完整桌面(XFCE+浏览器),内存/CPU 占用不低;一台开发者 Mac 上能并行几个身份需实测,Docker Desktop Resources 配额是硬瓶颈——这影响「多身份 fleet」何时必须迁出这台 Mac。
9. **待决**:VM 层 PRD 的 AC1–AC6 精确措辞我未见到(本报告按任务给定的约束推导映射),正式 design.md 落稿前应与 PRD 逐条核对编号与验收口径。

---

相关文件:本报告复用的已定稿研究在 `/Users/weston/dev/BuildFactory/.trellis/tasks/06-26-foundagent-v6/research/infra-research.md`(Infisical / Decodo-IPRoyal / Browser Use-Steel 的定稿依据)。