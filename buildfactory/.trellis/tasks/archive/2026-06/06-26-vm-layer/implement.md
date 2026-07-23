# VM Layer — Implement（执行计划）

> 子任务：`06-26-vm-layer`。前置：`design.md` 经 review 通过。环境：开发者 Mac + Docker Desktop。
> 原则：最小可运行先行 → 跑起来 → 看 agent 卡在哪 → 测试驱动按需补账号。每阶段产出可独立验证。

## 执行清单（有序，分阶段；每阶段映射 AC）

### Phase 0 — 环境就绪 ✅
- [x] Docker Desktop 运行（27.5.1 · linux/aarch64 · 11 CPU · 8GB）
- [x] 全程订阅确认；`computer-use-demo` 跳过（强制 API key、与订阅 OAuth 不兼容）
- [ ] Claude Code 订阅验证（`CLAUDE_CODE_OAUTH_TOKEN`）并入 Phase 2

### Phase 1 — cua 容器起步 ✅（AC1 达成）
- [x] `pip install cua-computer`（0.5.19；venv `.venv-cua`）
- [x] **自 build 固化镜像 `foundagent/cua-ubuntu:latest`**（`vm/docker/Dockerfile` + `custom_startup.sh`）：FROM `trycua/cua-ubuntu`，替换 startup 去掉每次启动的 `cua-agent[all]` 重升级（几 GB ML 依赖，曾致 100s 超时），改为直接 `python3 -m computer_server`
- [x] `vm/spike_cua.py`：SDK 起容器 + 截图验证（`CUA_IMAGE` 可配，默认固化镜像）
- **实测**：一条命令 **32s** ready（旧镜像 >100s 超时失败）；截图 1024×768/548KB；KasmVNC web `:8006`(→容器6901)；computer-server `:8000`；host SDK 0.5.19 ↔ 容器 server 0.3.17 兼容
- ✅ **AC1 达成**：一条命令起隔离容器 + Computer Use + Firefox 浏览器
- ⚠️ 待办：单容器资源占用实测（并发上限）；32s 启动后续可优化（保活/预热）

### Phase 2 — Claude（订阅）经 cua MCP 驱动容器 ✅（AC3 达成）
- [x] 自写薄 MCP `vm/cua_mcp.py`（FastMCP：screenshot/get_screen_size/left_click/double_click/type_text/press_key），内部用 cua-computer SDK 连容器 computer-server
- [x] 凭证 `vm/.env.local`（`CLAUDE_CODE_OAUTH_TOKEN` 订阅；600 + gitignored）；MCP 配置 `vm/mcp.json`
- [x] operator = `claude -p ... --mcp-config vm/mcp.json --dangerously-skip-permissions`（订阅）
- **实测**：operator（Claude 订阅）截图→认桌面→双击 Firefox→Firefox 打开（截图确认 Choose User Profile）；**零 API key**
- ✅ **AC3 达成**（Computer Use + 浏览器 + Claude 驱动打通；账号注入留 Phase 3）
- 架构 = **双层**（CEO 委托 operator；cua-agent 因锁 litellm/API key 弃用，改自编排薄 MCP）；grounding 弱项后续本地模型补
- ⚠️ 安全：`.env.local` 的订阅 token 已在对话暴露，**用完轮换**
- ✅ **Claude-in-container（终态架构）已验证**：容器内装 node20 + claude CLI（npm 装——`claude.ai/install.sh` 被 CDN 挡 403）+ cua-computer + 薄 MCP（`CUA_HOST_SERVER=1` 连 localhost:8000）；容器内 `claude -p`（订阅）自主截图→认屏→创建 Firefox profile→打开 Firefox 主窗口（截图确认）。**全程容器内、零 API key、headless、自主纠错。**
  - 关键现实：容器内 `api.anthropic.com` 可达（订阅 API 通），但 `claude.ai` 被挡 → claude CLI 必须 npm 装。
- [x] 固化镜像 `foundagent/cua-agent`（`vm/docker/Dockerfile.agent`）：base + node + claude + cua-computer + 薄 MCP + `agent-mcp.json`，开箱即用

### Phase 3 — 账号注入接口 ✅（AC2）
- [x] 可扩展 secrets 接口：`accounts/<id>/secrets.env`（KEY=VAL，gitignored）→ broker `--env-file` 注入容器 env + 挂载 `accounts/<id>:/account:ro`（cookies/keyfile）
- [x] **实测**：注入 `DEMO_ACCOUNT_EMAIL`/`DEMO_SERVICE_TOKEN`；append 一行新账号即注入、**不改代码**
- ✅ **AC2 达成**（可扩展、按需、不预配）
- 后续：Infisical 可生成同格式 env-file（接口不变）；真实账号 + 用账号登录的端到端，待有真账号时验

### Phase 4 — 静态出口 IP 接口 ✅（AC4）
- [x] broker `proxy=` / env（`PROXY_<id>`/`CUA_PROXY`）→ 容器 `HTTP(S)_PROXY/NO_PROXY`
- [x] **实测**：无 proxy curl 直连 200；设死代理后 curl 失败 = 流量走 proxy（接口生效）
- ✅ **AC4 达成**（接口成立）；真实 ISP IP（Decodo/IPRoyal）按需接
- ⚠️ 浏览器 proxy：Chromium 忽略 env proxy，接真代理时需配 `--proxy-server`（留接口）

### Phase 5 — 可观测 ✅（AC5）
- [x] 容器内 claude 的 JSONL transcript（`~/.claude/projects`，append-only，含每条 prompt/响应/工具调用）挂载到宿主卷（`-v <host>/<id>/claude:/home/kasm-user/.claude`）
- **实测**：claude 跑完，宿主卷得到完整 transcript（215KB / 19 行）；容器删除后 log 仍在宿主，可回放
- ✅ **AC5 达成**（JSONL = 真相源，已持久化可回放）；已固化进 `orchestration/broker.py`（每 operator 容器自动挂载）
- 后续加分（非 MVP）：`OTEL_LOG_RAW_API_BODIES` 全量 bodies、Docker json-file 日志驱动、自托管 Langfuse UI

### Phase 6 — Graceful shutdown ✅（AC6）
- [x] append-only JSONL：**硬 kill（SIGKILL）后 transcript 一字不丢、最后一行仍有效 JSON**（实测 19 行 / 215563 字节，kill 前后一致；容器 Exited 137 但宿主 log 完好）
- [x] 崩溃恢复：新容器挂同一 JSONL 卷 + `claude --resume <session>` 成功恢复上下文（实测答出之前的 "Purple" 壁纸）
- [x] broker teardown 改优雅：`docker stop -t <grace>`（SIGTERM + grace）再 rm（`orchestration/broker.py`）
- ✅ **AC6 达成**（日志不丢 + 可 resume 恢复）
- 后续加分（非 MVP）：tini -g PID1 + supervisor SIGTERM→interrupt→flush（常驻 agent 主动收尾用）

## 验证命令（关键）
- AC1：`docker ps` + 浏览器开 `:8006`
- AC4：容器内 `curl -s https://ipinfo.io/ip`（启用代理前后对比）
- AC5：`docker kill founder-01` 后检查宿主卷 `~/.claude/projects/*/*.jsonl` 完整；`claude --resume <id>`
- AC6：`docker stop founder-01`（计时 < grace）后检查 exit code 0 + JSONL 末尾完整

## 风险 / rollback 点
- **`supervisor.py` 是 load-bearing** → 独立单测 SIGTERM→interrupt→flush 路径，再接入
- **pin `claude-agent-sdk` 版本**（`interrupt()` 需 V1 ClaudeSDKClient + PR #642 后）
- **日志卷权限受控、绝不出网**（raw bodies 含明文凭证上下文）
- **并发上限**：Phase 1–2 实测单容器资源 → 估算这台 Mac 能并行几个身份；超限即触发「迁出本机」讨论（本期 out of scope）
- 各 Phase 独立可回滚：删对应容器/卷即可，不影响已验证的下层

## Review gate
1. `design.md` + `implement.md` 经用户 review
2. 补 `implement.jsonl` / `check.jsonl`（sub-agent 上下文清单）
3. `task.py start 06-26-vm-layer` → 进入实现
