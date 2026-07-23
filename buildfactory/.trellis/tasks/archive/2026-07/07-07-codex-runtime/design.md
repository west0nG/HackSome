# Design: Runtime abstraction（claude-code / codex 可切换）

> 输入：`research/claude-coupling-map.md`（六层耦合清单）+ `research/codex-cli-capability-map.md`（能力映射与缺口）。
> 本文只写设计与取舍；执行清单在 implement.md。

## 1. 架构总览

**核心原则：所有调用方只面对中性模型，runtime 差异只存在于两个 adapter 文件里。**

```
调用方（全部 runtime 无感知）              中性契约 (agent/runtimes/base.py)      adapter（唯一知道 CLI 细节处）
────────────────────────────            ─────────────────────────────        ────────────────────────────
orchestration/agent_loop.py  ─┐          RunRequest  (一次唤醒/任务的意图)      agent/runtimes/claude_code.py
agent/runner.py (broker 路径) ─┼───────→  RunResult   (结构化结果+续接令牌) ───→  agent/runtimes/codex.py
agent/resident_loadout.py    ─┘          Runtime     (protocol：五个方法)
orchestration/provisioner.py             runtime_for(spec) 工厂
```

现有 `agent/provider.py` 的 Provider seam **升级吸收**为 Runtime 协议（provider.py 删除，引用方迁移）；`orchestration/agent_loop.py` 的 `build_claude_argv`/`wake` 内部改走 adapter——两份 claude 知识合并成一份，这是"改一份代码两边自适应"的落点。

## 2. 中性契约（`agent/runtimes/base.py`）

```python
UNSET = object()   # yaml 里"没写这个键"（≠ 显式 null）

@dataclass
class RunRequest:
    prompt: str
    charter: str | None = None          # 追加 system prompt 内容（非路径）
    mcp_config: str | None = None       # agents/mcp/<role>.json 的解析后路径；None = 该 runtime 的"无 MCP"
    model: str | None | UNSET = UNSET   # UNSET→adapter 默认；None→省略 flag（CLI 默认）；str→透传
    effort: str | None | UNSET = UNSET  # 中性词表 = 现 fleet 词表 (low|medium|high|xhigh|max)，adapter 负责翻译
    resume_token: str | None = None     # 上一轮 RunResult.session_token；None = 新会话
    bypass_permissions: bool = True
    workdir: str | None = None

@dataclass
class RunResult:
    ok: bool
    text: str                    # 最终 assistant 消息
    error: str | None
    session_token: str | None    # 下一轮的 resume_token（语义见 §5）
    cost_usd: float | None       # codex 恒 None（无美元字段）
    usage: dict | None           # token 计数（两侧都填，口径为各 CLI 原生字段）
    raw_tail: str                # 调试尾巴

class Runtime(Protocol):
    name: str
    def build_argv(self, req: RunRequest) -> list[str]: ...
    def parse_output(self, stdout: str, returncode: int) -> RunResult: ...
    def materialize_home(self, spec, home_root: str) -> LoadoutInfo: ...   # skills/hooks/mcp 落盘
    def credential_kinds(self) -> dict[str, type[CredentialSource]]: ...   # "subscription"/"api-key" → 类
    def home_env(self, home_root: str) -> dict[str, str]: ...              # CLAUDE_CONFIG_DIR / CODEX_HOME
```

工厂 `runtime_for(spec) -> Runtime` 放在 `agent/runtimes/__init__.py`（替代 `spec.provider_for`），未知 provider 报错不变，opencode 保持 raise NotImplementedError 的 stub。

**扩展规约（可维护性的操作定义）**：
- 加"两边都要"的能力 → 改 `RunRequest`/`RunResult` + 两个 adapter 各实现一处，调用方零改动或只改一处。
- 加 runtime 特有 flag → 只碰对应 adapter 文件。
- 调用方新增（未来第三条路径）→ 只依赖 base.py，不 import 具体 adapter。

## 3. Claude adapter（合并两条旧路径）

现两条路径 argv 有三处不一致，合并时统一为**超集**并作为 deliberate 变更记录：

| 差异点 | agent_loop 旧行为 | runner 旧行为 | 合并后 |
|---|---|---|---|
| `--output-format stream-json --verbose` | 无（只看 exit code） | 有 | **恒有**。常驻路径由此获得结构化 error/cost/usage（此前瞎的）；wake 日志从裸 stdout 改打 `RunResult.text`+status 行 |
| `--strict-mcp-config` | 恒有（07-03 决策） | 无 | **恒有**（broker 路径补齐 07-03 决策） |
| `--resume` | 有 | 无（只 `--session-id`） | RunRequest.resume_token 有值→`--resume`，无值→`--session-id <新uuid>` |

其余 flags（`-p`、`--append-system-prompt`、`--mcp-config`、`--model`、`--effort`、`--dangerously-skip-permissions`）语义不变。`parse_stream_json` 从 runner.py 原样迁入（含 `is_error` 而非 subtype 的坑注释），补充：从自己预设的 uuid 返回 `session_token`。

**默认 model/effort 移入 adapter**：`AgentSpec.model/effort` 改为 UNSET 语义（yaml 没写→adapter 默认；显式 null→省略 flag）。claude adapter 默认保持 `claude-opus-4-8` + `xhigh`（现 fleet 行为）；`agent_loop.py:36` 的重复 fallback 删除，never-brick fallback 改为 import adapter 失败时直接用字面 argv 兜底不变。

## 4. Codex adapter（新增）

### argv

```
首轮:  codex exec  "<prompt>" --json --skip-git-repo-check \
         -c developer_instructions="<charter>" \
         [-m <model>] [-c model_reasoning_effort="<effort>"] \
         --dangerously-bypass-approvals-and-sandbox
续轮:  codex exec resume <thread-id> "<prompt>" --json ... (同上)
```

- `--dangerously-bypass-approvals-and-sandbox`（`--yolo`）对应 `permission_mode: bypass`——容器内官方推荐姿势（Landlock 在无特权容器不可用）。
- `--skip-git-repo-check` 恒带（agent 工作目录不是 git repo）。
- effort 词表翻译：中性 `max`→codex `xhigh`；`low|medium|high|xhigh` 透传；（codex 的 `minimal` 无中性对应，不产出）。
- **默认 model/effort（用户拍板 07-07）：`gpt-5.5` + `xhigh`**——与 claude 侧（opus-4-8 + xhigh）对称显式 pin。确切模型 id（`gpt-5.5` vs `gpt-5.5-codex`）在 stage 2 用真实 CLI 验证后钉死；角色 yaml 随时可覆盖。
- MCP 不走 flag（codex 无 per-invocation MCP 文件），走 CODEX_HOME 渲染（见下）。

### 输出解析（JSONL）

- `thread.started` → `session_token`（thread id）。
- `item.completed` 且 `item.type=="agent_message"` → `text`（取最后一条）。
- `turn.completed.usage` → `usage`；`cost_usd=None`。
- 失败判定（stage 2 实证修订）：`ok = 见到 turn.completed 且无 turn.failed/顶层 error 事件`——退出码**不参与** ok 判定（codex 无退出码枚举表、SIGINT 曾返回 0，与 claude 侧 is_error-不看-subtype 同一立场），rc 只用于兜底错误文案。`item.type=="error"` 的 item 可为非致命警告（fixture 实证），不算失败。
- 崩溃边界：进程死在 `thread.started` 之前 → `session_token=None`，调用方（agent_loop）看到 None 不覆盖 session_file，下轮开新会话——与 claude 路径 wake 超时的现有语义一致。

### session 续接语义统一（缺口①的消化）

把"session id"重定义为 **adapter 返回的续接令牌**：claude adapter 返回自己预设的 uuid（行为不变），codex adapter 返回 CLI 分配的 thread id。`agent_loop` 的 `load_session`/`save_session` 逻辑不改——只是从"保存我预设的 id"变成"保存 RunResult.session_token"。抽象接口从此不假设"调用方能指定 id"。

对 memory 层的影响：`COMPANY_SESSION_ID` 与 claude `--session-id` 的关联（broker 路径）在 claude 侧不变；codex 侧 record hook 属范围外（prd）。

### home 物化（缺口②⑤的消化）

per-role `CODEX_HOME = /sessions/<role>/codex`（嵌套子目录，与 claude 的 `/sessions/<role>` 零文件名冲突；同卷持久化 → codex 的 sessions/ rollout 跨重启存活，resume 才可用）：

1. **config.toml 渲染**：读 `agents/mcp/<role>.json`（唯一 source of truth）→ 翻译为 `[mcp_servers.*]`（command/args/env → 同名键；json 里的 `${VAR}` / `${VAR:-default}` 引用在渲染时用容器 env 展开——codex 不支持 config 内 env 展开）。独立 CODEX_HOME 天然等价 strict 语义（不会捡到别的 config）。
   - ⚠️ 已知取舍：展开后的凭证值落在持久化卷的 config.toml 里（claude 侧是 CLI 运行时展开不落盘）。与现有 permissions stance（先能力后收窄）一致，接受；文件 chmod 600。
2. **auth 预置**：`accounts/<id>/codex-auth.json`（用户 `codex login --device-auth` 一次产出，沿用 accounts=身份轴模式）→ 启动物化时若 `CODEX_HOME/auth.json` 不存在则拷入。此后 token 刷新由 codex 就地写回 per-role 副本（共享只读会破坏刷新，故必须 per-role 拷贝）。
3. **skills**：与 claude 同一份 skill 目录，拷到 `~/.agents/skills/<name>/`（SKILL.md 开放标准，格式兼容，零转换）。复用 loadout.py 的 manifest reconcile 机制——把"拷 skills + manifest 记账"抽成与目标目录无关的中性核心，claude 的 settings.json hooks 合并、codex 的 hooks.json（骨架，本期只留 TODO 位）作为各 adapter 的 runtime-specific 步骤。
4. **hooks**：本期不实现（prd 范围外），adapter 留空实现 + 注释指向 codex hooks.json 的同构事件模型。

`resident_loadout.materialize_for` 改为按 `spec.provider` 分发 `runtime.materialize_home`；never-brick 契约不变（任何物化失败 → WARN + charter-only 降级）。

## 5. 凭证（`agent/credentials.py` 扩展）

yaml 的 `credentials: subscription | api-key` 词表**不变**（runtime 相对语义），解析改为 provider-aware：`runtime.credential_kinds()[spec.credentials]`。

| provider × credentials | 注入 | 说明 |
|---|---|---|
| claude-code × subscription | `CLAUDE_CODE_OAUTH_TOKEN` | 现状不变 |
| claude-code × api-key | `ANTHROPIC_API_KEY` | 现状不变 |
| codex × subscription | （无 env）依赖 `CODEX_HOME/auth.json` 预置 | env() 返回 {}，主用形态 |
| codex × api-key | `CODEX_API_KEY` | e2e 阶段实测它 vs auth.json 的优先级并把结论写进 spec |

`ALL_CREDENTIAL_VARS` 扩为 `("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "CODEX_API_KEY", "OPENAI_API_KEY")`——互斥清零逻辑不变，防止跨 runtime 凭证串台（OPENAI_API_KEY 虽不主动注入，但列入清零集）。

## 6. 调用方改造

- **agent_loop**：`_role_config` 增返 provider → 构造 adapter 一次；`build_claude_argv` 删除（ceo_loop 兼容 shim 同步清理）；`wake()` 改为 `adapter.build_argv(RunRequest(...))` + `adapter.parse_output(...)`，日志行打 `RunResult` 摘要。leading-dash prompt 防护保留在 wake prompt 构造处（对 codex 同样有效——positional arg 同病）。
- **runner.run_task**：`provider.build_exec` → `runtime.build_argv` + `runtime.parse_output`；`docker exec` 组装与凭证互斥注入逻辑不变；`ExecPlan` 概念并入（env 部分由 credentials + home_env 提供）。
- **broker**：`__main__` 的 `CLAUDE_CODE_OAUTH_TOKEN` 硬校验改为按目标 spec 的凭证类校验。
- **compose / provisioner**：`x-agent-env` 与 `render_role_service` **恒注入两个 env**（`CLAUDE_CONFIG_DIR: /sessions/<role>`、`CODEX_HOME: /sessions/<role>/codex`）——模板不感知 provider，adapter 各用各的。`Makefile shared` 目标顺带 mkdir codex 子目录。
- **role.py lint**：`provider` 值加白名单校验（claude-code|codex；opencode 拒绝——stub 不该被 provision 出来）。

## 7. 兼容性 / 回滚

- **stage 1（收敛重构）行为零变化**：默认 fleet 全部 claude-code，argv 语义等价由 golden test 锁定（对比重构前两条路径的 argv 快照，仅允许 §3 表格里三处 deliberate 差异）。回滚 = revert 单个 commit。
- **stage 2（codex adapter）纯增量**：不改 claude 路径任何行为；没有角色声明 `provider: codex` 时，镜像里多一个二进制而已。回滚 = revert。
- **stage 3（e2e）只改测试角色 yaml + 文档**。
- 镜像层：`@openai/codex` ARG-pinned（0.142.5，musl 静态二进制约 293MB——镜像体积 +~300MB，接受）；`@anthropic-ai/claude-code` 同步补 pin（现浮动 latest 是既有缺陷）。codex self-update 在容器内天然无效化（镜像只读层）。`--strict-config`（stage 2 拍板）**不上 argv**：它与 never-brick 冲突（codex 升版后不识别渲染 config 里的键会拒跑而非降级），且版本已 pin、漂移只发生在有意升级时——升级验证靠 fixture 单测兜。

## 8. 已知风险

| 风险 | 缓解 |
|---|---|
| codex auth.json 刷新写回失败/过期 → 角色静默失能 | wake 失败日志已有；e2e 验证 `codex login status` 可作健康检查，写进 runbook |
| codex JSONL schema 漂移（周更节奏） | 版本 pin + fixture 单测（真实捕获的 JSONL） |
| `-c developer_instructions` 对超长 charter 的 shell/长度边界 | charter 走 argv 与 claude `--append-system-prompt` 同级；e2e 用真实 ceo charter 长度验证 |
| effort/model 词表漂移（OpenAI 改名） | 翻译表集中在 codex adapter 一处 + 单测锁定 |
| config.toml 内落盘的展开态凭证 | chmod 600 + 已在 §4 记录为 deliberate tradeoff |
