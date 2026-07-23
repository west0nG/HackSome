# Design — Continuity in memory layer, not sessions (issue 207)

## 总体形状

两个正交改动，一次交付：

1. **关死 auto-memory**：纯环境变量，零 Python 逻辑。
2. **session 策略**：AgentSpec 新增一个角色级配置字段，agent_loop 按字段走
   fresh / resume 两条分支（resume 分支 = 现行为，字节不变）。

## 1. auto-memory 关闭

**机制**：`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`（官方 env 开关）。选 env 不选
settings.json（`autoMemoryEnabled: false`）的理由：env 跟着进程走、两条调用路径
（常驻 fleet / broker docker-exec）都能从现有 env 组装点搭车；settings.json 要动
materialize_home 的合并逻辑，且 codex 侧根本没有这个文件的概念。若未来发现有
绕过 env 的 claude 调用面，再补 settings.json 作为兜底（目前没有）。

**注入点（两处，各覆盖一条路径）**：

- `docker-compose.yml` 的 `x-agent-env` 锚点加一行 → 覆盖 5 个静态 service；
  provisioner `render_role_service()` 镜像该锚点 → 未来角色自动继承
  （anti-drift 由 test_provisioner mirror test 钉住，无需改 provisioner）。
- `agent/runtimes/claude_code.py` 的 `home_env()` 返回值加一项 → 覆盖 broker
  一次性路径（`agent/runner.py` 把 `runtime.home_env()` 注入 `docker exec -e`）。
  放 adapter 而非 runner：这是 claude 专属知识（codex 无 auto-memory，其
  home_env 不加），与"provider 知识住 adapter"的 07-07 边界一致。

**注**：两处并存会让常驻容器内的 env 出现一次（compose）——resident 的 claude
子进程直接继承容器 env，不经过 home_env；broker exec 的容器 env 来自 spawn
时的 env-file，不含此变量，靠 home_env 注入。各管各的路径，不冗余。

## 2. session 策略：`session: fresh | resume`

**配置载体**：`agents/<role>.yaml` 新增 key `session`，进 `agent/spec.py`
AgentSpec：

```python
session: str = "fresh"     # fresh(默认) | resume — 跨 wake 会话连续性
```

- 默认 **fresh**（resume 是例外，与 PRD R2 一致）；`ceo.yaml` 显式写
  `session: resume`。
- 非法值 → WARN + fresh（never-brick 降级方向：宁可丢连续性，不可 brick）。
- 未知 key 向前兼容忽略的既有机制保证老 worktree/旧 yaml 不受影响。
- 不进 loadout overlay（overlay 管 skills/hooks/mcp/charter 的开关组合实验，
  连续性不是 capability，暂不给覆盖面；需要时再加）。

**agent_loop 改动**（`orchestration/agent_loop.py`）：

- `_role_config()` 返回值加 `session_mode`（roleless / 坏 yaml → "fresh"）。
- `agent_loop()`：
  - `resume` 模式：现行为字节不变（load_session → wake(resume) → save_session）。
  - `fresh` 模式：不 load、不 save；每次 `wake(session_id=None, ...)` —— wake()
    现有逻辑自动为 claude 预铸新 uuid（`session_hint`），codex 则由 CLI 自行
    分配 thread id。`AGENT_SESSION_FILE` 完全不触碰。
- compose 里各 service 的 `AGENT_SESSION_FILE` **保留不删**：CEO 在用；fresh
  角色留着无害（不读不写），provisioner 模板也不用动。boot 日志打印
  `session=fresh|resume` 便于 e2e 断言。

**wake prompt（fresh 角色的定向指令，R3 后半）**：

`build_wake_prompt(events, objective, fresh=False)` 加第三参；`fresh=True` 时在
objective 块之前加一行**定向指令**（不做"你是全新会话"之类的机制说明——全新
会话本来就没有"以前"可记，说了是废话；prompt 的职责是让它去获取信息）：

> Before acting, orient yourself: read the relevant parts of /company (its
> MAP.md is the index) — it is the company's shared state and the only record
> of what has happened so far. Write durable results back under /company
> before you finish.

"the only record of what has happened so far" 一句顺带排除了虚构"我上次做过X"
的空间，无需谈 session。`fresh=False` 输出与现版本字节一致（golden/现有单测
不动）。措辞只指 /company 与其现存的 MAP.md 惯例（company_state_kit 已有），
不预设其他内部路径（D5）。

## 3. charter 强调（R3 前半，5 个文件）

每个 charter 加一小节（英文，具体措辞按角色微调），要点：

- 你产出的任何耐久结论/交付物/教训，必须写到 /company 下（位置和组织方式
  你自己定）——不写下来的东西等于没发生。
- fresh 角色版：你的会话不跨 wake，下次醒来只有 /company、你的 objective 和
  收件箱可依赖。
- CEO 版（resume 但会被 auto-compact）：会话可能被压缩，承重结论只活在
  /company 里才算数。

按"三道检验"写（系统特定：点名 /company 与 wake 机制；压制 LLM 默认：
"把结论留在对话里"就够的错觉；取舍标准：写盘 vs 省时间——写盘赢）。

## 数据流 / 兼容性

- 遥测不动：`_record_wake` 已按 wake 记 session_id/cost；fresh 角色每行
  session_id 各异，成为 AC2 的审计面。
- Hub/ledger/inbox 全不感知 session，零改动。
- 存量 `/sessions/<role>/session_id` 文件：fresh 角色的变成死文件，留着
  （下次真跑新公司 state 目录本来就是新的；firsttest 归档不动 = D4）。
- 存量 auto-memory 目录：开关只是不读不写，不删除 —— firsttest 归档天然保留。
- 回滚：单 commit revert 即可（env 一行 + yaml 一行 + spec/loop 小改 +
  charter 文案），无数据迁移、无状态破坏。

## 风险与观察点

- CEO 之外的判断退化风险（verifier 也 fresh 了）：verifier 的评审是单次
  goal 级、无跨 wake 依赖（07-06 设计如此），风险低；下次长跑以 AC4 的
  telemetry + 抽查 verdict 质量验证。
- fresh 角色"忘记写盘"风险：charter 强调 + wake prompt 机制告知双保险；
  长跑后审计 /company 的增长 vs 交付物是否闭环。
- codex fresh：本来就不能 resume（uses_session_hint=False），fresh 反而是
  其自然形态；AC3 钉住。
