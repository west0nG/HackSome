# BuildFactory（Foundagent）

**零人公司实验**：常驻 CEO 按需创建 Department，由临时 Worker 执行、临时 Verifier 独立验收，组成一家能自主运营的公司。人类只提供账号凭证和（可选的）初始方向。

这个仓库不是某个产品的代码，而是这家 AI 公司的**办公楼与制度**：agent 的容器化运行时、公司共享记忆系统、目标编排协议、对外感知入口。

一句话心智模型：**一个 Company Compose stack = 一家公司**。Company 状态在 `state/<公司名>/`；换个 `COMPANY` 就能开第二家公司。唯一跨公司的状态是 `state/_mail/registry.jsonl`，用于保证 `foundagent.net` 地址全局唯一。

## 新人从这里开始

📖 **[docs/overview.md](docs/overview.md)** — 项目总览：愿景、10 条设计原则、四层架构、每个核心机制的实现逻辑。

## 快速开始

```bash
# 前置：本地 Docker + vm/.env.local 中的模型登录配置
make mail-up      # 全宿主机只启动一次域名级邮件 router
make up           # 启动一家公司（CEO + 确定性内核；其他角色按需创建）
make logs-ceo    # 看 CEO 的循环日志
make down        # 停止
make mail-down    # 仅在要停止整个平台邮件接入时执行

# 单元测试
.venv-cua/bin/python -m pytest agent/tests/ orchestration/tests/ \
    peripheral/tests/

# 显式真实 E2E（启动隔离 Docker 栈并消耗真实 Worker/Verifier 模型轮次）
make e2e-native-company ACCOUNT=foundagent
```

邮件接入还需要在 `vm/.env.local` 配置 `R2_ENDPOINT`、
`R2_ACCESS_KEY_ID`、`R2_SECRET_ACCESS_KEY`；Company 发件需要
`RESEND_API_KEY`。`make mail-up` 使用独立的 `foundagent-mail` Compose
project，只运行一个 `mail-router`，不会随 `make up COMPANY=x` 被复制。
router 暂停时原始邮件继续留在 R2 `inbox/`；恢复后会按全局注册表写入
`state/<company>/mailboxes/`。不要删除 `state/_mail` 或 Company 邮件日志。

`e2e-native-company` 从空的原生 `/company` 开始，验证 Worker 浅层发现、
直接写入、`submit_result`、Verifier 只读核验，以及 Hub 重启后的文件持久性。
测试使用随机 `e2e-*` 公司名，结束后会停止容器并清理隔离状态；它不会被普通
单元测试自动执行。`ACCOUNT` 只作为 Codex 登录种子的来源；测试会创建一个不含
业务 API 密钥、Cookie 等生产凭据的临时账号包。本机存在当前
`~/.codex/auth.json` 时会优先使用它，避免复用已轮换的旧 refresh token；也可用
`E2E_CODEX_AUTH_SEED=/绝对路径/auth.json` 显式指定。

## 架构速览

自底向上四层：

| 层 | 目录 | 职责 |
|---|---|---|
| 外设层 | `peripheral/` | webhook 等外部信号归一化；平台级 mail-router 将 R2 邮件隔离写入对应 Company |
| 编排层 | `orchestration/` | 常驻循环、Goal 派活/验收状态机、非 LLM 的确定性 Hub |
| 状态面 | `state/<公司名>/company/` | Agent 原生共享文件夹：Skill 负责渐进式发现、读取与维护 |
| 执行层 | `agent/` + `vm/` | 容器镜像、角色装备（charter/skill）物化、凭证接缝 |

贯穿性原则：LLM 只做业务判断，协议与仲裁全是确定性代码；干活的不能当裁判（doer≠judge，结构性强制）；加角色/技能/账号全靠声明式配置，零代码改动。

## 深入阅读

- `.trellis/spec/backend/` — 代码级精确契约文档（信封格式、状态机、原生 Company State、装备覆盖等）
- `aiworkforce/` — 方法论：加角色/技能的 8 阶段 SOP、CEO 判断力设计全记录
- `.trellis/tasks/` — 每个特性的需求、设计与验收记录
