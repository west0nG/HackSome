# Design: codex hooks translation + runtime-neutral marker keying

依据：research/codex-hooks-contract.md（0.142.5 本机实测，与容器 pin 版本一致）。PRD 开放问题全部有实测答案，不确定性已清零（仅剩两条容器内保险性复核，见 §6）。

## 1. 核心事实（决定设计形状）

- codex Stop hook 契约与 claude **逐字段同构**：stdin 有同名 `stop_hook_active`/`session_id`，阻断= `{"decision":"block","reason":...}` + exit 0，放行= exit 0 无输出。**`record_stop_hook.py` 零改动**，R4 的"垫片"不需要。
- hooks.json 的形状与 claude settings.json 的 `hooks` 键**同形**（事件 → matcher 组 → handlers）→ claude adapter 现有的 `_snippet_hooks/_merge_hooks/_remove_hooks` 可以**原样复用**。
- 不加 `--dangerously-bypass-hook-trust` 时 hooks 被**静默跳过**（headless `--json` 下无任何提示）；trust 无法非交互预置；requirements.toml 路线粒度是全 fleet，会波及 verifier，走不通。
- hook 崩溃 = fail-open（正常停止），never-brick 天然满足；block-续跑不产生第二对 turn 事件，`parse_output` 零改动。
- codex 的 session_id（=thread id）跨 wake 不变 → 按 session_id 键控 marker 在 codex 下必然失效（第一次 record 后终身免检）；claude resident 侧本就没人 export `COMPANY_SESSION_ID`（R5 既有错位）。**per-wake nonce 是两个 runtime 共同的正解**，且 hook 子进程继承父 env（两侧实测/已知成立）。

## 2. 改动清单（按模块）

### 2a. 中性核心：hooks merge/remove helpers 上移

`agent/runtimes/claude_code.py` 的 `_snippet_hooks/_merge_hooks/_remove_hooks` 移入 `agent/loadout.py`（两 adapter 共用——它们操作的都是含顶层 `hooks` 键的 JSON 文件，claude 是 settings.json、codex 是 hooks.json）。claude adapter 改为引用，行为逐字节不变（golden test 锁定）。

### 2b. codex adapter（`agent/runtimes/codex.py`）

- `materialize_home` 第 4 步：与 claude 完全对称的 hooks reconcile——读 snippet → 与上次 manifest diff → `_remove_hooks`（撤销上次 merge 且本次不再要的）→ `_merge_hooks` 进 `CODEX_HOME/hooks.json` → manifest hooks 槽记录本次条目。agent 自加的 hooks 条目永不触碰（与 claude 同语义）；无 hooks 声明时不创建文件、不清别人的。失败降级 WARN（never-brick，与 config.toml/auth 同姿态）。
- `build_argv`：**恒加** `--dangerously-bypass-hook-trust`（与 `--yolo` 并列）。取舍见 §4。
- `parse_output`：零改动（flag 带来的 2 条非致命 error item 已被"error item 不算失败"立场覆盖，加一条注释说明）。

### 2c. hooks snippet（`company_state_kit/hooks/settings.snippet.json`）

条目加 `"timeout": 30`（秒）。两侧语义一致（claude 默认 60s、codex 默认 600s——600s 的默认值在卡死时会吃掉整个 wake 预算，必须显式收紧）。单一 snippet 喂两个 runtime，不复制。

### 2d. marker keying（runtime 中性，R5）

- `orchestration/agent_loop.py` `wake()`：每次 wake 造一个 nonce（uuid4），以 `env={**os.environ, "COMPANY_WAKE_ID": nonce}` 传给子进程。claude/codex/fallback 三条路径一致。
- `company_state_kit/company.py` `session_marker_path` 优先级改为：
  `COMPANY_RECORD_MARKER`（显式文件，不变）＞ **`COMPANY_WAKE_ID` env（新，CLI 与 hook 都继承同一值 → 结构性对齐）** ＞ 现状（hook 的 stdin session_id / CLI 的 `COMPANY_SESSION_ID` env）＞ `default`。
- `record_stop_hook.py`：**零改动**（仍传 stdin session_id，作为无 nonce 时的 fallback）。
- 兼容性：broker 路径不设 `COMPANY_WAKE_ID` → 走现状分支，行为不变（它的 env `COMPANY_SESSION_ID` 与 claude 预设 session id 本就一致）；resident claude 从"每次白拦一轮"修复为真正对齐；resident codex 获得正确的 per-wake 强制。

## 3. 数据流（resident codex 一次 wake）

```
agent_loop.wake()
  ├─ nonce = uuid4() → 子进程 env COMPANY_WAKE_ID=nonce
  ├─ argv = codex exec ... --yolo --dangerously-bypass-hook-trust
  └─ codex 子进程
       ├─ agent 干活；跑 company.py record → marker: <dir>/<nonce>.marker（env-first）
       └─ Stop → CODEX_HOME/hooks.json → record_stop_hook.py（继承 env）
            ├─ marker 存在 → exit 0 放行
            └─ 不存在 → {"decision":"block","reason":...} → 模型补 record → 第二次 Stop（stop_hook_active=true）放行
```

## 4. 关键取舍

- **trust flag 恒加 vs 仅有 hooks 时加**：恒加。理由：①静默跳过是本任务要消灭的头号失效模式，条件判断（读 env+磁盘定 argv）引入的任何 bug 都会退回静默跳过且不可观测；②豁口（workdir `.codex/hooks.json` 一并放行 = agent 可自加 hooks）与 claude 现状对等——claude agent 本来就能改自己的 settings.json 加 hooks，两 runtime 姿态一致，符合"先给权限、安全收窄后置"的既定立场；③verifier 无 hooks 声明 → CODEX_HOME 无 hooks.json → 恒加 flag 也不会给它装任何东西。豁口记录在案。
- **hooks.json 单一表示**：不用 config.toml `[hooks]`（两处共存会 merge + 启动警告，且 config.toml 是每次全量重渲的生成物，hooks 需要 merge 语义，二者生命周期不同）。
- **timeout 放 snippet 而非 adapter 注入**：单一来源；manifest 值相等性 dedup 对此天然兼容（snippet 变更 → reconcile 撤旧 merge 新）。
- **nonce 新变量 `COMPANY_WAKE_ID` 而非复用 `COMPANY_SESSION_ID`**：broker 路径的 `COMPANY_SESSION_ID` 语义是"= claude session id"，resident 的 nonce 语义是"= 本次 wake"，混用会把两个不变式搅在一起；新名字各表其义，优先级链清晰。

## 5. 兼容 / 回滚

- compose、镜像、hub、verifier、broker：零改动（flag 在 0.142.5 已实测存在）。
- 回滚点独立：2a-2c（hooks 翻译）与 2d（marker keying）可各自单独 revert；2d 回滚后退回"每次白拦一轮"的现状，无数据损坏。
- marker 目录内容形状不变（仍是 `<key>.marker` 文件），无迁移。

## 6. 容器内待验证（保险性质，随 AC1 真跑一并做）

- 镜像内确认 `/etc/codex/`（managed 层）不存在。
- 容器内复跑一次 run2 式冒烟（block → 补 record → 放行全链路）。
