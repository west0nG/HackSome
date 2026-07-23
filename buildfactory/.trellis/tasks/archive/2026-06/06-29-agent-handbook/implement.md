# Agent Handbook — 执行计划

> 见 `prd.md`（需求/AC）+ `design.md`（设计）。**Phase A = Hub 机制增量（动 .py）**，**Phase B = 文案（skill/charter/yaml）**。
> A 先做、B 依赖 A。基线：`.venv-cua/bin/pytest orchestration/tests/ -q` = **142 passed**。每步后跑相关验证。

## Step 0 — 基线（rollback point）

- [x] `.venv-cua/bin/pytest orchestration/tests/ -q` → 142 passed（基线）。
- [x] 重复 charter = builder/growth/researcher 三处（`grep "When you receive a task" agents/assets/`）。
- [x] 无测试断言这三个 placeholder charter 文本（`test_goal_runtime.py` 只断言 `/company`/`company-operator`/VERDICT，不碰）。

---
## Phase A — Hub 机制增量（verifier-only accept 通道）

### A1 — messaging：caller 写 accept ✅
- [x] `messaging.send(to, intent, *, accept=None, reply_to=None)`：accept 非空时 body 追加 `\n===ACCEPT===\n{accept}`。
- [x] CLI `send` 加 `--accept`（默认 None）。
- [x] **守卫（code-review 抓出）**：intent/accept 含 `ACCEPT_DELIM` → `ValueError`（防泄漏/截断）。
- 验证：`test_send_with_accept_*`、`test_send_without_accept_is_backward_compatible`、`test_send_rejects_reserved_delimiter_in_{accept,intent}`、`test_cli_send_accept_flag_reaches_body`。

### A2 — hub.parse_body：解出 accept
- [ ] DISPATCH 分支：对 intent 段按 `\n===ACCEPT===\n` 切，前=intent、后=accept（无则 None）；返回 dict 加 `"accept"`。
- [ ] 边界：intent 文本里含 `===ACCEPT===` 的兜底（实现时定 sentinel/转义），单测覆盖。
- 验证：`test_hub_handler` —— DISPATCH 带/不带 accept 各解析正确；空 intent 仍报 `HubParseError`。

### A3 — ledger.add_goal：存 accept
- [ ] `add_goal(self, intent, parent=None, role=None, accept=None, ...)` → `goal["accept"] = accept`。
- 验证：`test_goal_ledger` —— add_goal 带 accept → `_load` 回来有；不带 → 键存在且为 None（或缺省一致）。

### A4 — hub dispatch handler + _verify_ime：透传 + 注入 verifier
- [ ] dispatch handler 把 `parsed["accept"]` 传给 `add_goal`。
- [ ] `_verify_ime(goal_id, intent, dept_summary, mid, accept=None)`：accept 非空则插 `ACCEPTANCE CRITERIA (judge against THIS): {accept}`。
- [ ] RUNNING→VERIFYING 调用处读 `goal.get("accept")` 传入。
- [ ] **`_work_ime` 不改** —— 加断言锁死：worker 工单文本里查不到 accept（AC0 关键）。
- 验证：`test_hub_handler` —— `_verify_ime` 含/不含 criteria；**`_work_ime(...)` 永不含 accept 文本**。

### A5 — verifier-charter
- [ ] 加一句：给了 ACCEPTANCE CRITERIA 按它判；没有才从 goal 自推导。

### A6 — Phase A 回归（review gate）
- [ ] `.venv-cua/bin/pytest orchestration/tests/ -q` → **142 + 新增全绿**，旧 142 零回归（accept 全程默认 None 向后兼容）。
- 对照 **AC0**。红了回对应 Ax。

---
## Phase B — 文案（公民 skill + charter + yaml）

### B1 — 两个公民 skill（写人话，Goal 写法并进本体）✅
- [x] `send-goal/SKILL.md`（装到 CEO）：frontmatter `name: send-goal` + description（想派活时）。body = What a Goal is + Sending（`send --to --intent`，真实/具体/可执行 + 给足背景 why，1 组好/坏对照例，可选 `--accept` 只给验收方、执行者看不到，`reply_to` 默认自己）。
- [x] `receive-goal/SKILL.md`（装到部门）：frontmatter `name: receive-goal` + description（收到 Goal 时）。body = What a Goal is + Doing（读懂 goal+context 取 `goal_id` → 把事做好，产物**或对外操作、不强制落 /company** → `report --goal-id` 报 done；**不出现自评/判定标准字样**）。
- 验证：对照 **AC1 + AC2**；frontmatter 合法；通读是"人话"、无自评/criteria 字样、无"必须落 /company"。
- ⚠️ 不建 `reference/` 子文件（篇幅短，并进本体）。

### B3 — yaml 接线（按角色最小装载）✅
- [x] ceo：`skills: [send-goal]`（只发不收）。
- [x] builder/growth：`skills:` 追加 `receive-goal`（与 company-state 并列）。
- [x] researcher：新增 `skills: [company-state, receive-goal]`。
- 验证：yaml 全可解析；`test_civic_goal_skills_wired_and_resolvable`（builder→receive-goal、ceo→send-goal 路径解析 + SKILL.md 存在）；无 `goal-protocol` 残留引用。

### B4 — R3：charter 去重
- [ ] builder/growth/researcher charter：删逐字重复段，换一句引用（人话、不提自评/标准）：
      `When you receive a Goal, follow the goal-protocol skill: understand the goal and its context, do the real work to achieve it, then report that you're done.`
      （保留身份段 + heartbeat + placeholder 抬头）。
- 验证：`grep "When you receive a task" agents/assets/` = 0 处；charter 里无 `/company` 强制句、无自评句；对照 **AC3**。

### B5 — 全套单测（review gate）
- [ ] `.venv-cua/bin/pytest orchestration/tests/ -q` → 与 A6 同绿（**AC3 后半不回归**）。

---
## Step C — AC4：真实零人 e2e
- [ ] 选最省入口（先 `test_hub_e2e.py`，否则 compose 真容器 + goaltest 夹具）。
- [ ] 跑通：caller `send --intent --accept` → 经 Hub → builder 收（**工单无 criteria**）、做好落 /company、report work-done →
      Hub 转 verifier（**verify 工单含 criteria**）→ verdict → done → 终态回 caller inbox。零人。
- [ ] 记证据（日志/ledger 终态/`/company` 产物 + 「worker 工单确无 criteria」），对照 **AC4**。四 AC 全打勾。

## Step D — 收尾（Phase 3）
- [ ] spec 更新 `.trellis/spec/backend/`：①公民 skill 分层契约 ②Hub accept 通道（信息可见性矩阵）+ 更 index。
- [ ] commit（中文沟通/英文 message）：messaging+hub+ledger+charter / skill+charter+yaml / spec 分组。
- [ ] 更 MEMORY（orchestration-protocol：B 决策——判定标准 worker 蒙眼 + accept 通道；handbook 公民 skill 分层）。

## Rollback points
- Step 0 = 干净基线（142）。
- Phase A 出错：改动集中在 messaging/hub/goal_ledger/verifier-charter，`git checkout --` 这几个文件即退回；A 全程向后兼容，回归红=多半 `_work_ime` 误带 accept 或 add_goal 签名漏 default。
- Phase B 出错：改动全在 `agents/`，`git checkout -- agents/` 退回。yaml 红多半 `skills:` 路径写错（应 `assets/skills/goal-protocol`，相对 `agents/`）。
