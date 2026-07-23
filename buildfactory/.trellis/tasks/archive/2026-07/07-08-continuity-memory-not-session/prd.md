# Continuity in memory layer, not sessions (issue 207)

## Goal

落实 issue #207 的讨论结论：agent 的连续性从"终身 resume 的 session"搬到 memory 层。
持久状态只有一个家 —— `/company`（格式由 agent 自生长）；Claude Code 的 auto-memory
私有记忆用官方开关关死；除 CEO 外 session 不再承担跨 wake 连续性。

价值：
- 消掉 resume-forever 的三大代价（context 只增不减的重读成本、跨业务转向的旧包袱、
  不受控的 auto-compact）。首跑实测：一次空转心跳 $12.57，尾部 4h 空转 41 次唤醒烧 $67.76。
- 消掉私有记忆黑盒：首跑实锤 CEO 把"KYC 墙"行动结论和"误杀先查 /company"教训只写进了
  自己的 auto-memory（`state/firsttest/sessions/ceo/projects/-home-kasm-user/memory/`），
  其他角色学不到。
- 收敛 provider 不对称：codex 无法预设 session id（`uses_session_hint=False`）、
  也没有 auto-memory——改动后除 CEO 外 claude/codex 的连续性语义完全一致。

## 已拍板的决策（2026-07-08 用户确认）

- D1 换会话时机：**除 CEO 外所有角色每 wake 全新会话**；CEO 保留 resume-forever。
- D2 所有角色（含 CEO）的提示词要强调：**耐久的东西必须落盘到 /company 下面**。
- D3 auto-memory 对**所有角色（含 CEO）**关死，用官方开关（不靠提示词规范去顶）。
- D4 firsttest 老数据不迁移，原样归档。
- D5 公司 wiki 格式由 agent 自生长，代码不预设任何 /company 内部结构（延续既有立场）。

## 已确认的代码事实

- 连续性现状：`orchestration/agent_loop.py` — `load_session()` → `wake(resume_token=session_id)`
  → `save_session()`；首个 wake 由 `session_hint`（预铸 uuid）建会话。session 文件
  `AGENT_SESSION_FILE=/sessions/<role>/session_id`（docker-compose.yml 各 service，
  provisioner 渲染新角色时同样注入，provisioner.py:321）。
- auto-memory 落盘点：`CLAUDE_CONFIG_DIR=/sessions/<role>` → 记忆写进
  `/sessions/<role>/projects/-home-kasm-user/memory/`。
- 官方开关：settings.json `autoMemoryEnabled: false`，或环境变量
  `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`（docs: code.claude.com/docs/en/settings.md）。
  关闭后不读不写 memory 目录、MEMORY.md 不注入、系统提示不再出现记忆引导。
- 环境注入面有两个：①常驻 fleet：docker-compose.yml `x-agent-env` 锚点——provisioner
  `render_role_service()` 从加载的 compose 文档镜像该锚点，未来角色自动继承（anti-drift
  由 test_provisioner 的 mirror test 钉住）；②broker 一次性路径：`agent/runner.py`
  `docker exec -e`（env 由 `injection_env` + `runtime.home_env` + `extra_env` 组装）。
- 角色配置载体：`agents/<role>.yaml` → `agent/spec.py` AgentSpec（provider/model/effort
  等，未知 key 向前兼容忽略）；agent_loop `_role_config()` 每次 boot 读取。
- charter 已指向 /company（ceo-charter.md:74 "Deliverables live in /company"；
  builder/growth 有 company-state skill），本任务在此基础上按 D2 加强。
- 遥测：`_record_wake()` 每 wake 记 session_id/cost_usd —— 改动后仍按 wake 审计。

## Requirements

- R1 关死 auto-memory（对应 D3）：常驻 fleet 与 broker 一次性路径下的 claude 调用均
  不再读写 auto-memory；未来 provisioner 创建的角色自动继承。
- R2 session 策略（对应 D1）：除 CEO 外每 wake 全新会话；CEO 行为不变（resume +
  session 文件持久化）。策略必须是**角色配置**而非硬编码角色名，未来可按角色调整；
  默认值 = fresh（resume 是例外）。对 claude/codex 两个 provider 语义一致。
- R3 提示词强调（对应 D2）：所有角色被明确告知耐久产出必须写 /company；fresh 角色
  的 wake prompt 另加一条定向指令——先读 /company 获取上下文再行动（不做
  "你是全新会话"式的机制说明，prompt 的职责是让 agent 去获取信息）。措辞不预设
  /company 内部结构（对应 D5）。
- R4 遥测连续性：wake 级 session_id/cost 审计不因换会话而丢失。
- R5 never-brick 延续：坏 yaml / 缺配置降级到默认策略（fresh）+ 响亮 WARN，不 brick 循环。

## Acceptance Criteria

- [x] AC1 真跑（e2e207 公司，ceo+builder 两轮心跳）：memory 目录 0 个（claude 连目录
      都没建）；builder 转写中 auto-memory 引导文本 0 次出现。证据：research/e2e-evidence.md。
- [x] AC2 builder 两次 wake 两个不同 session id（cec97df6→63f22f68）且 session 文件
      从未创建；CEO 两次 wake 同一 id（722e93a7）且落盘。telemetry 每行含
      session_id 与 cost_usd。
- [x] AC3 codex fresh 语义由单测钉住（test_wake_provider_codex_*：无 hint 持久化、
      thread id 由 CLI 分配）；fresh 分支传 None 对 codex 即"每 wake 新 thread"。
      （无现成 codex 角色可真跑，单测覆盖视为达标——codex 本就不能 resume 预设。）
- [x] AC4（方向性证据，正式验证留下次长跑）：fresh 空转心跳 $0.25 vs 首跑肥会话
      $12.57，两个数量级；且按构造不随 wake 数增长。
- [x] AC5 五个 charter 含落盘强调（verifier 为只读适配版）；fresh wake prompt 含
      orient 指令；单测钉住（test_fresh_prompt_* / test_compose_kills_auto_memory_*）。
- [x] AC6 单测全过（468 passed）：spec session 字段、fresh/resume 分支、orient
      前缀、home_env/compose 锚点注入、provisioner mirror 自动继承。

## Out of Scope

- firsttest 旧数据迁移（D4：`state/firsttest/sessions/*/memory/` 原样归档）。
- memory-layer skeleton 的完整实现（读/写/重整工具等）——本任务只做"连续性搬家 +
  关私有记忆"，不新建记忆机制。
- 心跳间隔/成本治理本身（heartbeat-governance 是另一个 issue）。
- inbox 中途传入 / mid-wake delivery（issue #206 已明确推迟）。
- CEO 的 resume 轮换/交接策略（本次保留原样，观察下次长跑后再议）。
