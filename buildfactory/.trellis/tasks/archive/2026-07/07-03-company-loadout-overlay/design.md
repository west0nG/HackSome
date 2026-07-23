# Design: 公司级 Loadout Overlay

## 总览：一个解析器 + 四个消费点

```
state/<company>/config/loadout.yaml
        │  (compose 只读目录挂载 → 容器内 /opt/foundagent-config/)
        │  env: AGENT_LOADOUT=/opt/foundagent-config/loadout.yaml
        ▼
agent/overlay.py  ← 唯一的解析 + 合成逻辑（纯函数，好单测）
        │
        ├─ 消费点① agent/resident_loadout.py   容器启动：skills + hooks（materialize + reconcile）
        ├─ 消费点② orchestration/agent_loop.py  loop 启动：charter / mcp → claude argv
        ├─ 消费点③ peripheral/runner.py         服务启动：adapters 白名单过滤
        └─ 消费点④ agent/loadout_check.py       宿主机离线校验（同一解析器，warnings 升级为 errors）
```

生效语义统一为「进程启动时读一次，改文件 → 重启容器生效」。charter 现状就是 loop 启动读一次（`agent_loop.py:170`），不引入热/冷混合口径。

## Schema（v1）

```yaml
version: 1

defaults:                  # 作用于所有角色；roles.<role> 同名字段覆盖之
  hooks: off

roles:
  growth:
    skills:                # map，不是列表：天然差异语义
      de-ai-ify: off       # 关掉基线里有的
      send-goal: on        # 挂上基线里没有的（从全局池解析）
    charter: on            # on | off | <路径>
    hooks: on              # on | off
    mcp: on                # on | off | <路径>
  verifier:
    charter: assets/verifier-charter-v2.md   # 替换 = 测 prompt 变体

peripheral:
  adapters: [webhook]      # 白名单；整个键缺省 = 全开
```

规则：

- 任何字段缺省 = 按基线。空文件 / 无文件 = 全按基线。
- `skills` 里 `on` 且不在该角色基线 → 从全局池 `agents/assets/skills/<name>` 解析；解析不到 → WARN + 跳过该条。
- `charter` / `mcp` 的替换路径：绝对路径按容器内路径直接用；相对路径相对 `agents/` 目录解析（与 role YAML 的 `system_prompt` 同一规则，`assets/xxx.md` 开箱即用）。
- 未知顶层键 / 未知角色名 / 非法取值 → 运行时 WARN + 忽略；loadout-check 报错。
- `version` 非 1 → 运行时 WARN + 整份忽略（按基线）；loadout-check 报错。

## 模块：`agent/overlay.py`

```python
@dataclass
class RoleView:            # defaults + roles.<role> 合成后的单角色视图
    skills: dict[str, bool]      # {} = 不动基线
    charter: str                 # "on" | "off" | <path>
    hooks: bool | None           # None = 基线
    mcp: str                     # "on" | "off" | <path>

load(path) -> (overlay: dict | None, warnings: list[str])   # 不存在/空 → (None, [])；坏 YAML → (None, [WARN])
role_view(overlay, role) -> (RoleView, warnings)
apply_to_spec(spec, view, skill_pool_dir) -> (AgentSpec, warnings)   # 返回新 spec，不改原对象
effective_charter(view, baseline_path) -> str | None        # off → None
effective_mcp(view, baseline) -> str | None                 # off → None（不传 --mcp-config）
effective_adapters(overlay, baseline: list[str]) -> (list[str], warnings)
```

warnings 随返回值上传，由各消费点统一 `print(..., flush=True)`——解析层自身不打印、不抛（除内部 OverlayError 供 loadout-check 捕获）。

## 消费点改动

### ① resident_loadout（skills + hooks）

读 `AGENT_LOADOUT` env（缺省 `/opt/foundagent-config/loadout.yaml`）→ `load` → `apply_to_spec` → 现有 `materialize`。失败路径不变：任何异常 → log + exit 0（charter-only 兜底）。

### ①′ materialize 的 reconcile（本设计最关键的新增）

背景：state-dir 任务后 claude home 持久化到宿主机，而现有 `materialize()` 只加不删——off 掉的 skill 上次拷的目录还在，hooks 条目 merge 进 settings.json 后也没人删。

方案：**记账清单** `<claude_home>/.loadout-manifest.json`：

```json
{"skills": ["company-state", "receive-goal"], "hooks_snippet_sha": "<sha256>"}
```

每次启动 materialize 前先 reconcile：

- **skills**：`上次清单 − 本次生效集` 的差集目录从 `<claude_home>/skills/` 删除。不在清单里的目录（agent 自装 / 手装）永不动。
- **hooks**：本次 hooks 为 off、或 snippet 指纹变化时，从 `settings.json` 里移除与**上次 snippet 内容**逐值相等的 hook 条目（现有 `_merge_hooks` 的 dedup-by-value 逻辑反向使用），其余键与条目原样保留。
- 完成后写入本次清单。清单缺失（首次 / 旧数据）→ 视为空清单，只加不删，行为安全。

### ② agent_loop（charter + mcp）

`main()` 中读 overlay：`charter: off` → `charter_path=None`；替换路径 → 覆盖 `AGENT_CHARTER` 的值；`mcp` 同理（off → `mcp_config=None`，`build_claude_argv` 已天然支持不传）。`build_claude_argv` 与 `wake` 纯参数接口不变。同步更新 `agent_loop.py:29` 的注释（"expose it or not is not a capability we cap"——测试语境下这正是要 cap 的能力）。

### ③ peripheral/runner（adapters）

`_registry()` 构建时用 `effective_adapters(overlay, manifest.ADAPTERS)` 过滤；env `AGENT_LOADOUT` 同名复用。未知 adapter 名 → WARN + 忽略；空白名单合法（listener 照起，一切 POST 404）。`manifest.ADAPTERS` 仍是"代码里存在哪些 adapter"的唯一事实，overlay 只做子集选择。

### ④ loadout_check（宿主机 CLI）

`python3 -m agent.loadout_check --company <x>`（或 `--file <path>`），`make loadout-check COMPANY=<x>` 包一层。检查项：YAML 可解析、version 支持、顶层键合法、角色名 ∈ `agents/*.yaml`、skill 名 ∈（该角色基线 ∪ 全局池）、charter/mcp 替换路径存在（相对规则按 agents/ 在宿主机检查）、adapter ∈ `manifest.ADAPTERS`。每条问题一行输出，非零退出。与运行时共用 overlay.py，仅把 warnings 判为 errors——保证两边口径永不漂移。

## 挂载与 env（compose / Makefile，M4）

- `make shared`：预创建 `state/$(COMPANY)/config/`（沿用现有 chmod 方案）。
- `x-agent` anchor 与 peripheral 服务各加：
  - 挂载 `./state/${COMPANY:-foundagent}/config:/opt/foundagent-config:ro`
  - env `AGENT_LOADOUT=/opt/foundagent-config/loadout.yaml`
- 选目录挂载不选单文件挂载：vim/sed -i 等 rename 写入会换 inode，单文件 bind 下容器永远读旧内容——静默偏差不可接受。

## 兼容 / 回滚

- 无 overlay → `load` 返回 None → 所有消费点走现有代码路径，行为逐 flag 零变化（AC 第一条）。
- 功能回滚 = 删除 overlay 文件 + 重启；代码回滚 = revert（无数据迁移）。`.loadout-manifest.json` 残留无害（reconcile 差集为空）。

## 取舍记录

- **重启生效，不做热加载**：charter 本就是启动读一次；「skills 冷 + charter 热」的混合口径在测试场景比没有热加载更危险（你以为切了其实一半没切）。
- **skills 用 map 不用列表**：差异语义天然；基线新增 skill 不需要回头改任何公司的 overlay（全量声明式的最大维护成本被规避）。
- **overlay 放 `config/` 子目录**：绕开单文件挂载的 inode 坑，也给后续其他公司级配置（如 accounts 绑定）留同一落点。
- **容错折中**：运行时永不 brick（条目级降级 + 大声 WARN），确定性拦截交给启动前的 loadout-check——两者共用解析器，语义一份。
