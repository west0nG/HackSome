# Agent Layer — Technical Design

> 配套 `prd.md`。技术设计与接口契约由工程侧确定；产品/scope 决策见 prd 的 Confirmed Decisions（D1-D7）。

## 1. 架构与边界

```
          ┌─────────────────────────── 编排层 (orchestration, 后续) ─────────────────────────┐
          │  broker.py: 多容器编排 (docker run / 等就绪 / teardown / run_fleet)              │
          └───────────────┬──────────────────────────────────────────────┬──────────────────┘
                          │ 调用                                          │ 调用
          ┌───────────────▼────────────── Agent 层 (本任务, 新建 agent/) ──▼──────────────────┐
          │  spec(声明)  ·  provider(seam)  ·  credentials(seam)  ·  loadout(装载)  ·  runner  │
          └───────────────┬──────────────────────────────────────────────────────────────────┘
                          │ 复用
          ┌───────────────▼──────────────── VM 层 (已交付, 不改) ─────────────────────────────┐
          │  foundagent/cua-agent 镜像 · cua MCP · 浏览器 · 账号注入 · proxy · JSONL · resume  │
          └──────────────────────────────────────────────────────────────────────────────────┘
```

- **Agent 层只封装「单个 agent 的能力 + 执行接口」**（D4）。多 agent 调度归编排层；computer-use/浏览器/账号注入/proxy/可观测归 VM 层、复用不重造。
- broker 经重构后从「自己拼 `claude -p`」降级为「调用 Agent 层」（D7）。

## 2. 代码组织（新建）

```
agent/                       # Agent 层 Python 包
  __init__.py
  spec.py                    # AgentSpec dataclass + YAML loader + provider_for/credential_for
  credentials.py             # CredentialSource 抽象 + SubscriptionCreds + ApiKeyCreds
  provider.py                # Provider 抽象 + ClaudeCodeProvider + CodexProvider/OpenCodeProvider (stub)
  loadout.py                 # materialize(): 三类载体物化进容器 .claude/
  runner.py                  # run_task(): 组装 → docker exec claude -p → 解析 stream-json → AgentResult
  tests/                     # 单测 (spec 加载 / provider 选择 / 凭证 env / stub 抛错 / stream-json 解析)
agents/                      # 声明目录 (与 accounts/ 同级、同风格)
  operator.yaml              # 示例 agent spec (通用 operator, 无固定角色)
  assets/
    company-charter.md       # system-prompt / CLAUDE.md 注入内容 (人设/宪章, trivial)
    skills/hello-foundagent/SKILL.md   # 示例可调用 skill (trivial)
    hooks/settings.snippet.json        # 示例 hook (PreToolUse 打日志, trivial)
```

> Agent spec（能力维度）× account（账号维度）正交（D5）：运行实例 = 选一个 `agents/<role>.yaml` + 选一个 `accounts/<id>/`。

## 3. 接口契约

### 3.1 AgentSpec（声明文件 schema，AG1）

```yaml
# agents/operator.yaml
name: operator
provider: claude-code            # claude-code | codex(stub) | opencode(stub)
credentials: subscription        # subscription | api-key
system_prompt: assets/company-charter.md      # 注入 (见 loadout)
skills:                          # → .claude/skills/
  - assets/skills/hello-foundagent
hooks: assets/hooks/settings.snippet.json     # → 合并进 .claude/settings.json
mcp_config: /opt/foundagent/mcp.json          # 容器内已有 (cua-local)
permission_mode: bypass          # bypass → --dangerously-skip-permissions
```

`spec.py`：`AgentSpec.load(path) -> AgentSpec`；`provider_for(spec)`、`credential_for(spec)` 工厂。**新增 agent = 加一个 yaml，不改 .py**（AC1）。

### 3.2 Provider seam（AG2）

```python
@dataclass
class ExecPlan:
    argv: list[str]            # 容器内执行的 claude 命令
    env: dict[str, str]        # 注入的 env (含凭证)

class Provider(Protocol):
    name: str
    def build_exec(self, spec, task, creds, *, system_prompt_arg) -> ExecPlan: ...
```

- `ClaudeCodeProvider.build_exec` →
  `claude -p {task} --mcp-config {spec.mcp_config} --append-system-prompt {…} --output-format stream-json --verbose [--dangerously-skip-permissions]`；env 注入 `creds.env()`。
- `CodexProvider` / `OpenCodeProvider`：`build_exec` 抛 `NotImplementedError("provider 'codex' not implemented; seam only")`（AC2）。

### 3.3 Credential seam（AG3）

```python
class CredentialSource(Protocol):
    kind: str
    def env(self) -> dict[str, str]: ...

class SubscriptionCreds:   # kind="subscription" → {"CLAUDE_CODE_OAUTH_TOKEN": <token>}
class ApiKeyCreds:         # kind="api-key"      → {"ANTHROPIC_API_KEY": <key>}
```

与 provider 解耦：同一 ClaudeCodeProvider 可配任一 CredentialSource。默认订阅（D3），token 来源沿用 `vm/.env.local`；API key 来源 env `ANTHROPIC_API_KEY`（AC3）。

> **【spike 已验证 · 凭证互斥，必须遵守】** 容器内 `claude` 的优先级是 **`ANTHROPIC_API_KEY` > `CLAUDE_CODE_OAUTH_TOKEN`**：两者并存时 API key 胜出、订阅 token 被**静默忽略**（`claude --help`：「Anthropic auth is strictly ANTHROPIC_API_KEY or apiKeyHelper」）。因此 `SubscriptionCreds.env()` 与 `ApiKeyCreds.env()` 必须**互斥**——runner 注入前要剔除另一方的 env：订阅模式严禁残留 `ANTHROPIC_API_KEY`（否则订阅被悄悄覆盖 → 隐性 bug），切 api-key 时同时清掉 `CLAUDE_CODE_OAUTH_TOKEN`。

### 3.4 装载机制 loadout（AG4 / D6）

```python
def materialize(spec, claude_home: str) -> LoadoutInfo:
    """把声明的三类载体物化进 per-agent 的 .claude 挂载目录 (docker run 前)。
       claude_home = vm/data/<name>/claude  (已挂 /home/kasm-user/.claude, VM AC5)。"""
```

注入方式 = **运行时物化到现有 `.claude` 挂载点**（不重 build 镜像、声明驱动、可扩展）：
- **system-prompt**：内容经 provider 的 `--append-system-prompt` 传入（短）或写入 `CLAUDE.md`（长）。
- **skills**：拷 `assets/skills/<name>/` → `<claude_home>/skills/<name>/`。
- **hooks**：把 `settings.snippet.json` 的 hooks **合并**进 `<claude_home>/settings.json`（不覆盖既有键）。

三类各有可观测证据（AC4）：人设体现在输出 / skill 被识别 / hook 触发打日志。

### 3.5 执行接口 runner（AG5）

```python
@dataclass
class AgentResult:
    ok: bool
    text: str                  # final assistant text  ← 取自 result event 的 "result" 字段
    error: str | None
    cost_usd: float | None     # ← 取自 result event 的 "total_cost_usd" 字段
    raw_tail: str              # 末段原始 stream-json (排查用)

def run_task(spec, task, *, container, creds=None, timeout=300) -> AgentResult:
    creds = creds or credential_for(spec)
    plan  = provider_for(spec).build_exec(spec, task, creds, system_prompt_arg=...)
    # docker exec -e <plan.env> {container} bash -lc "<plan.argv>"
    # 解析 stream-json (NDJSON, 取末尾 type=="result" event):
    #   ok       = not ev["is_error"]          # ⚠ 必须用 is_error, 不能用 subtype
    #   text     = ev["result"]                # final assistant text
    #   cost_usd = ev.get("total_cost_usd")
    #   error    = ev.get("api_error_status") or (ev["result"] if ev["is_error"] else None)
```

> **【spike 已验证 · 字段名按实测，勿用 design 旧假设】** 实测 `result` event 真实字段 = `result`(final text) / `total_cost_usd`(cost) / `is_error`(bool)。**关键陷阱**：401 错误时 `subtype` 仍为 `"success"`，只有 `is_error=true` 才反映失败 → `ok` 判定**只能用 `is_error`**。事件序列固定为 `system/init → assistant → rate_limit_event → result`（NDJSON 每行一 event）。flag `--append-system-prompt[-file]` / `--mcp-config` / `--output-format stream-json --verbose` 全部确认有效。

## 4. 数据流（端到端，AG6）

```
agents/operator.yaml + accounts/<id>/ + task(str)
  └─ broker.spawn(op_id, task, spec):
       1. loadout.materialize(spec, claude_home)         # 写 skill/hook/CLAUDE.md 进 .claude
       2. docker run cua-agent (--env-file secrets.env, proxy, -v .claude 卷)   # VM 层不变
       3. 等 computer-server:8000 就绪                     # VM 层不变
       4. runner.run_task(spec, task, container=name)     # provider→docker exec claude -p→解析
       5. teardown (JSONL transcript 持久保留)             # VM 层不变
  └─ AgentResult { ok, text, cost, ... }
```

## 5. broker 重构方案（AG7 / D7）

- **保留**（VM 编排，broker.py 现有职责）：`docker run` 拼装（name/env-file/proxy/卷）、等 `:8000`、`teardown`、`run_fleet`。
- **移除**：`broker.py:91-105` 的 `claude -p` 命令构造 + token 注入 → 改为：`spawn()` 增 `spec` 参数（默认加载 `agents/operator.yaml`）；docker run 前调 `loadout.materialize`，就绪后调 `runner.run_task`。
- **回归**：保留 `__main__` demo（firefox / describe desktop），重构后行为不退化（AC7）。

## 6. 兼容 / 风险 / 待 spike 验证

- **R1 stream-json 结构** ✅ spike 已验证（见 `research/agent-spike.md` S1）：字段 = `result`/`total_cost_usd`/`is_error`，`ok=not is_error`（勿用 subtype）。解析逻辑已并入 §3.5。
- **R2 订阅版 skills 发现** ✅ spike 已验证（S2）：订阅版 claude 能从 `~/.claude/skills/<name>/SKILL.md` 发现并经 `Skill` 工具调用，loadout 落点 §3.4 成立、无需调整。
- **R3 容器内 API key 路径** ⚠️ 部分验证（S3）：`claude` 确认识别 `ANTHROPIC_API_KEY`（`apiKeySource` 信号 + `--help` 文档），路径成立；**优先级 api-key > 订阅、需互斥注入**（已并入 §3.3）。但**无真实 key，端到端成功调用待复核**——AC3「api-key 能跑通最小调用」这半句需有真 key 时补验。
- **R4 settings.json 合并**：hook 注入须合并而非覆盖（容器内可能已有 settings）。
- **R5 broker 重构动已验证代码**：每阶段独立 commit，broker 重构单列一次 commit 便于回退；回归 demo 必跑。
- **向后兼容**：默认订阅、token 沿用 `vm/.env.local`；`.claude` 挂载点复用、loadout 写入不破坏 VM AC5 transcript。
</content>
