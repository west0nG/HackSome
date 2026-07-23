All facts verified against the live system:
- Docker Desktop **4.38.0** (server confirmed), runc 1.1.12 — below 4.44.3, so CVE-2025-9074 applies.
- No `~/.docker/sandboxes/sandboxd.sock` → the 4.58 microVM path is NOT available on this machine.
- cua docker provider is pure `docker` CLI subprocess (lines 280+ confirm `docker run -d --name`, plus `inspect`/`stop`/`rm`/`ps`).
- The agent image has `claude` + `node` but **no `docker` CLI** (confirmed: only claude and node resolve).
- No ECI active (Security Options empty).

I have everything needed. Here is the deliverable.

---

# Foundagent v6 编排层：要不要「容器套容器」(DinD)？

> 适用范围：v6 零人公司 / serving-orchestration 层。约束＝每 agent 一独立容器、运行时宿主零 Claude 进程、CEO（容器内）需驱动 operator 容器、测试期＝一台开发 Mac + Docker Desktop。
> 本机实测：Docker Desktop **4.38.0** / Engine 27.5.1 / runc 1.1.12；`~/.docker/sandboxes/` 不存在（无 4.58 microVM API）；`foundagent/cua-agent:latest`（5.39GB）含 `claude`+`node`、**无 `docker` CLI**；ECI 未开启。

---

## 1. 直接回答：要不要 DinD？

**不要。** 一句话：你需要的是「**兄弟容器 (siblings)**」而不是「嵌套容器 (nesting)」——宿主上同一个 `dockerd` 在 CEO 容器**旁边**创建 operator 容器，二者同级。这同时满足两条硬约束（每 agent 一容器、宿主零 Claude），又避开了 DinD 的两大代价：`--privileged` 逃逸面、以及嵌套 overlay 存储/镜像重复拉取的开销。DinD 唯一多给你的是「拆掉 CEO 即连带拆掉子树」这点便利——而这用控制面**记录 owner 关系**就能复刻，不值得用 privileged 去换。

---

## 2. 机制对比表

| 机制 | 隔离强度 | 要 `--privileged`？ | Mac (Docker Desktop) 可行性 | 复杂度 | 满足「每 agent 独立容器 + 容器外零 Claude」 |
|---|---|---|---|---|---|
| **DinD**（容器内跑第二个 `dockerd`，operator = 子容器） | 中：内层 daemon 与宿主 daemon 隔离，但 `--privileged` 是真实逃逸面（cgroup `release_agent`、`/sys` 写、内核模块加载） | **是** | 可行（`docker:dind` 在 LinuxKit VM 内跑） | 中（dind 镜像 + privileged + 存储驱动调优 + **每个 CEO 自带镜像缓存→重复拉取/磁盘膨胀**） | 满足，但用 privileged 换来的 |
| **DooD / 裸 `docker.sock`**（挂宿主 socket，operator = 兄弟容器） | **极弱**：持 sock = 对该 daemon 的 **root 等效**；可 `docker run --privileged -v /:/host` 拿下整个 daemon + 所有兄弟。只读挂载也无效（create/exec API 仍在） | 否，但**等价于 privileged**（能按需造 privileged 兄弟，blast radius 更大） | 可行（本机 `/var/run/docker.sock` → `~/.docker/run/docker.sock`），失陷点是 LinuxKit VM 而非 macOS | 最低（1 行挂载 + docker CLI） | 满足，但安全上不可接受 |
| **Sysbox**（`--runtime=sysbox-runc`，无 privileged 无 sock 的安全 DinD） | **强**（共享内核里最佳）：user-ns 映射，容器 root→宿主非特权 UID，内层 Docker 完全隔离 | **否**（这正是卖点） | **不可行**：sysbox-runc 必须装进 Linux 宿主的 dockerd；Docker Desktop 的 daemon 在不可改的 LinuxKit VM 内，无法安装 | 用起来低、装起来在 Mac 上=不可能 | Linux 上满足，Mac 测试期出局 |
| **Kata Containers**（每容器一个轻量 VM，独立 guest kernel） | **最强**（硬件虚拟化边界，逃逸需 hypervisor escape） | 否（但需嵌套虚拟化 VT-x/AMD-V） | **不可行**：LinuxKit VM 不暴露嵌套虚拟化，且无法装 Kata runtime。*概念上的 Mac 等价物＝Docker 4.58 microVM / Apple Containerization，但本机 4.38 无此 API* | 高 | Linux/上云满足，Mac 测试期出局 |
| **podman rootless/nested**（daemonless，无 sock，nested rootless 子容器） | 较好（rootless + 无 daemon socket，共享内核） | 理想路径否；Mac 上常退化为给外层加 `--privileged`，优势尽失 | **脆弱**：需 `/dev/fuse` + LinuxKit VM 内开启 unprivileged user-ns（不保证）；且现有镜像是 Docker 构建，换 podman=移植成本 | 中-高（fuse-overlayfs ~2x I/O 开销） | 满足，但 Mac 上不顺手 |
| **宿主非-Claude 守护进程 / broker**（宿主一个非 Claude 进程持 docker 访问，对 CEO 只暴露窄 API，operator = 兄弟容器） | **本项目最强实务姿态**：CEO 不持 docker 能力，只能调白名单动词；危险权限被隔离在小而可审计的 broker 里 | 否（agent 容器全部无 privileged） | **最佳契合**：纯宿主进程 + 兄弟容器，今天就能跑 | 中（要自写并测试 broker：队列/超时/回收/鉴权/崩溃恢复） | **完美满足**：broker 是非-Claude 进程（约束本就允许它在宿主），CEO/operator 全在容器内 |

**核心事实补充（已实测）：** cua 的 docker provider（`/Users/weston/dev/BuildFactory/.venv-cua/lib/python3.13/site-packages/computer/providers/docker/provider.py`）是**纯 `docker` CLI subprocess**（`docker run -d --name` / `inspect` / `stop` / `rm` / `ps`）。所以**只要 CEO 容器内能触达 daemon**（挂 sock 或 `DOCKER_HOST=tcp://proxy:2375`），host 上跑通的 spike 路径在容器内可逐字复用——这是 DooD 系方案改动极小的根因，也是 broker 后端能复用 cua provider 的原因。

---

## 3. 推荐的编排拓扑（针对 Foundagent）

### 选型：分两步走，用同一个 `orchestrator MCP` 抽象桥接

- **测试期主架构（今天就落地）：Topology A-hardened —— DooD + docker-socket-proxy 收敛权限。**
- **生产/演进终态：Topology B —— 宿主非-Claude broker 守护进程。**

不直接上裸 DooD（A）：因为本机 **4.38.0** 受 **CVE-2025-9074**（CVSS 9.3，4.44.3 才修）影响——任意容器**无需挂 sock**即可经 `192.168.65.7:2375` 无认证直达 Engine API，升级前「容器隔离」是假象。不直接上 B：B 是正解但要自写并测一个真 daemon，违背「先最小可运行、再测试驱动扩展」。A-hardened 当天可复用已验证的 cua provider + 已验证的 cua-agent 镜像。

### 落地形态（CEO → 部门 → 执行者）

```
┌─────────── 宿主 Mac（运行时零 Claude 进程）───────────┐
│  一次性 launcher（非 Claude，启完即退）                 │
│        │ docker run                                    │
│        ▼                                               │
│   ┌──────────────┐   DOCKER_HOST=tcp://docker-proxy:2375
│   │  CEO 容器     │ ───────────────┐                   │
│   │ cua-agent     │                ▼                   │
│   │ + docker CLI  │        ┌──────────────────┐        │
│   │ + orchestrator│        │ docker-socket-   │        │
│   │   MCP         │        │ proxy (持真 sock)│        │
│   └──────────────┘        │ 仅放行 CONTAINERS│        │
│        │ spawn_operator()  │ /POST/START/STOP │        │
│        │                   │ /IMAGES(读)；拒  │        │
│        │                   │ EXEC/privileged/ │        │
│        │                   │ host-bind        │        │
│        │                   └────────┬─────────┘        │
│        │                            ▼ docker run        │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  (兄弟容器)    │
│   │operator1│  │operator2│  │operator3│  各自 Claude-in-│
│   │cua-agent│  │cua-agent│  │cua-agent│  container 自跑 │
│   └─────────┘  └─────────┘  └─────────┘  CU 循环        │
└────────────────────────────────────────────────────────┘
```

**CEO 如何下达「起 operator」：**
- CEO 镜像 = `foundagent/cua-agent` **+ docker CLI**（operator 镜像不动），设 `DOCKER_HOST=tcp://docker-proxy:2375`。
- CEO 内的 Claude（订阅）调一个薄 `orchestrator MCP` 的 `spawn_operator(identity, task)`：内部走 `Computer(provider_type="docker", image="foundagent/cua-agent", name="op-<id>").run()`（逐字复用 spike）。operator 起为 CEO 的兄弟容器，自跑 Claude-in-container CU 循环（你已有的 `CUA_HOST_SERVER=1` 接 `localhost:8000` computer-server）。

**结果如何回收：**
- 命名卷 `results/op-<id>/`：operator 落盘 JSONL transcript + 结果文件 + 终态截图。
- operator **退出码**＝成败信号；CEO 经 `docker inspect`/`ps`（经 proxy）轮询状态。
- CEO 只收「成败 + 摘要 + 终态截图」，符合已定的双层 computer-use（不让 CEO 逐帧看 operator 屏幕）。
- teardown：MCP 调 `docker stop` + `docker rm`；卷/命名按 `op-<id>` per-identity 便于回收。

**现有镜像怎么配（复用最大化）：**
- `operator` 镜像 = **现状 `foundagent/cua-agent` 不动**（已含 claude + node + cua_mcp.py，实测无需 docker CLI）。
- `CEO` 镜像 = 在 `vm/docker/Dockerfile.agent` 基础上**仅多装 docker CLI** + 把 `cua_mcp.py` 扩出一个 `spawn_operator` 工具（`/Users/weston/dev/BuildFactory/vm/cua_mcp.py` 已支持 host/container 双模式，扩 spawn 顺理成章）。
- 升级到 B：把 `orchestrator MCP` 后端从「走 proxy 的 docker CLI」换成「向宿主 broker 投递 job」，**CEO 侧 MCP 接口不变 → 零返工**。

> 否决 Topology C（同容器多 Claude 会话）：直接违反「每 agent 一容器」，且无身份/出口 IP/secrets/桌面隔离，与「每身份固定独享 IP 是养号命脉」结论正面冲突。C 仅适合「同身份内纯文本子任务扇出」（如 Trellis subagent 规划/写码，不需独立桌面+身份）。

---

## 4. 安全模型（跑不可信 web + 真实账号资金）

这是本项目最关键的一节：CEO/operator 会**读取不可信网页**（indirect prompt injection）且**持有真实凭据/钱**。

### `docker.sock = root` / `--privileged` 的风险
- **裸挂 `docker.sock` = 把宿主 root 交出去。** Docker daemon 以 root 跑；任何能写该 socket 的进程都能 `docker run --privileged -v /:/host`，一次 prompt injection 即挂载宿主全盘提权。**只读挂载不防护**（create/exec API 仍暴露）。OWASP / Quarkslab / Datadog 均明确反对。对一个会读不可信网页又持真钱的 agent，这是灾难级。
- **`--privileged` DinD 逃逸不需要内核 0-day：** privileged 容器可 `init_module` 加载内核模块、直接访问宿主设备和 host-facing 内核文件系统，属「简单逃逸」而非「需要 0-day」。2024-2025 已有 8 个容器逃逸 CVE（Leaky Vessels、runc race、NVIDIAScape），privileged 放大全部。
- **本机当前真实风险 CVE-2025-9074**（CVSS 9.3，4.44.3 修复）：Docker Desktop < 4.44.3 上任意容器**无需挂 sock**即可经 `192.168.65.7:2375` 无认证直达 Engine API。本机 4.38.0 中招 → **落地前第一步必须升级 Docker Desktop ≥ 4.44.3**，否则隔离是假象。
- **macOS 边界事实（缓解但非豁免）：** 容器跑在 LinuxKit Linux VM 内，VM 本身是 host 安全边界——容器 root ≠ macOS root，sock escape 落点是 LinuxKit VM 而非 Mac。所以 Mac 测试期「宿主沦陷」风险低于 Linux 裸机，但 **VM 内横向污染（控制所有兄弟容器 + 凭据）仍真实存在**。

### 防逃逸纵深（按有效性排序）

1. **网络出口白名单（对抗注入数据外泄最有效的单点）。** Simon Willison 的 "lethal trifecta"＝私有数据 + 不可信内容 + 对外通信，三者齐备即可被利用。砍掉第三条——operator 容器走 egress 代理/防火墙，**只放行任务必需域名**——注入即使成功也无法把凭据/数据发给攻击者域名，外泄即失败。
2. **凭据隔离 + per-identity 最小权限。** 每个 operator 只拿它身份对应的、最小权限、**可即时吊销**的凭据；绝不共享一个「全能」凭据；运行时短期 token 注入，**不写进 image**；operator 之间无横向移动路径（一个失陷不应能拿到其它身份凭据或访问其它容器）。这是「持真钱」场景的硬性要求。
3. **容器加固模板（broker/MCP 强制）：** 非 root 用户（cua-agent 已 `USER 1000`）、`--cap-drop ALL`、`--security-opt no-new-privileges`、只读 rootfs + tmpfs、seccomp 默认 profile、不允许任意 bind-mount、不允许 privileged、不允许改 network mode。
4. **能力面收敛（A-hardened 的核心）：** 用 `tecnativa/docker-socket-proxy`（arm64 可用）把「持 sock = root 等效」收敛为「只能管 operator 生命周期」——`POST` 默认关，按端点显式放行 `CONTAINERS/ALLOW_START/ALLOW_STOP/IMAGES(读)`，拒 `EXEC/privileged/host-bind`。
   - ⚠️ **proxy 的上限缺陷：它无法过滤 `POST /containers/create` 的请求体参数**——一旦放开 create，仍可被注入 `-v /:/host` 或 privileged 配置。**高安全场景必须用自写语义化 broker**（只接受 image + 固定安全模板，拒绝任意 mount/privileged），proxy 只能当过渡/补充，不能当终态主防线。这正是 Topology B 优于 A 的根本原因。
   - 同样，proxy 防不住 CVE-2025-9074（绕过 sock 直连 Engine API）——只能靠**升级 Docker Desktop ≥ 4.44.3 + 开 ECI**。
5. **Docker Desktop Enhanced Container Isolation (ECI)（Mac 期最高性价比纵深防御）：** 底层就是 **Sysbox**，跑在 LinuxKit VM 内——容器 root→VM 内非特权 UID（user-ns），**默认阻止挂 docker.sock**，即使 `--privileged` 也无法加载内核模块/改宿主网络/访问宿主设备。这是 macOS 上唯一现成的 Sysbox 级加固（Sysbox 本身不单独支持 Mac）。**代价：需 Docker Business 付费订阅。** 本机当前未开启（Security Options 为空）。

---

## 5. Mac 测试期落地 vs 未来生产（分阶段）

### Phase 0 — 立即（落地前的硬前置）
1. **升级 Docker Desktop ≥ 4.44.3**（修 CVE-2025-9074）。本机 4.38.0 升级前任何隔离都是假象。
2. （可选，Business 订阅）开 **ECI**：默认堵死 docker.sock 滥用，即使 privileged 也无法逃逸到 VM。

### Phase 1 — Mac 测试期（A-hardened，今天就能跑通）
- 形态：CEO 容器（cua-agent + docker CLI，`DOCKER_HOST=tcp://docker-proxy:2375`）→ `tecnativa/docker-socket-proxy` sidecar（持真 sock，最小放行）→ 兄弟 operator 容器（现状 cua-agent 镜像，加固模板）。
- 编排：CEO 内 Claude 调 `orchestrator MCP.spawn_operator()` → cua docker provider 逐字复用。
- 纵深：egress 白名单 + per-identity 凭据 + cap-drop/no-new-privileges/只读 rootfs。
- 一次性非-Claude launcher 起 CEO 容器后退出 → 运行时宿主零 Claude 进程。
- 复用：operator 镜像不动；CEO 镜像仅加 docker CLI + 扩 `spawn_operator` 到 `vm/cua_mcp.py`。

### Phase 2 — 仍在 Mac，安全升级（同 broker 契约，换后端）
- 用**自写语义化 broker**（宿主非-Claude 守护进程）替换 docker-socket-proxy，堵住 `POST /containers/create` 参数注入这个 proxy 无法覆盖的缺口。CEO 侧 MCP 接口不变。
- broker 成为放配额/审批/审计/kill-switch/可观测聚合的天然落点（契合 v6「CEO→部门→执行者 + 自主 kill 决策」）。
- （若届时升到 Docker Desktop 4.58+ 且 `~/.docker/sandboxes/sandboxd.sock` 出现）broker 可改调其 microVM API，给每 agent 一个 Apple virtualization.framework microVM（≈「Kata for macOS」）。但该 API 未文档化/不稳定且为宿主调用（VM 内回调起兄弟 VM 未确认），故**只让 broker 当唯一调用方并 pin 版本**。本机当前**无此 socket**，不能依赖。

### Phase 3 — Linux / 生产（broker 契约不变，换隔离 runtime）
- 密度优先：**Sysbox**（`--runtime=sysbox-runc`，无 privileged 无 sock，内层 Docker 完全隔离，root-in-container→宿主非特权）。
- 不可信代码 gold standard：**Firecracker microVM**（E2B / Vercel Sandbox 用，每 session 独立 guest kernel，~125ms 启动，~5MB 开销，逃逸需 hypervisor escape）或 **Kata Containers**（Daytona 的 optional 强隔离档）。
- 因为 CEO 永远只跟 broker 对话，从 docker-socket-proxy → 自写 broker → Sysbox → Kata/Firecracker 全程**零 CEO 改动**。这就是「现在就用 broker 抽象」的无死角价值。

---

## 关键引用（工具 / runtime / URL）

- Docker socket = root：OWASP Docker Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
- CVE-2025-9074（Docker Desktop < 4.44.3，容器直达 Engine API）：https://nvd.nist.gov/vuln/detail/CVE-2025-9074
- `tecnativa/docker-socket-proxy`（API 端点白名单，arm64 可用）：https://github.com/Tecnativa/docker-socket-proxy
- Enhanced Container Isolation（底层 Sysbox，需 Business）：https://docs.docker.com/security/for-admins/hardened-desktop/enhanced-container-isolation/
- Sysbox（Linux-only 安全 DinD runtime，Docker 收购 Nestybox）：https://github.com/nestybox/sysbox
- Kata Containers：https://katacontainers.io/
- Firecracker microVM（E2B / Vercel Sandbox 用）：https://firecracker-microvm.github.io/ ；Vercel Sandbox：https://vercel.com/docs/vercel-sandbox
- "Lethal trifecta"（prompt injection 数据外泄）— Simon Willison：https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
- DinD vs DooD 背景（jpetazzo, "Do not use Docker-in-Docker for CI"）：https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/
- cua docker provider（纯 CLI subprocess，已读源码）：`/Users/weston/dev/BuildFactory/.venv-cua/lib/python3.13/site-packages/computer/providers/docker/provider.py`

**相关项目文件（绝对路径）：**
- `/Users/weston/dev/BuildFactory/vm/cua_mcp.py`（薄 MCP，已支持 host/container 双模式，扩 `spawn_operator` 的落点）
- `/Users/weston/dev/BuildFactory/vm/docker/Dockerfile.agent`（operator 镜像；CEO 镜像在此基础上加 docker CLI）
- `/Users/weston/dev/BuildFactory/vm/docker/agent-mcp.json`（container-side MCP 配置）