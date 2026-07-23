# Agent Handbook（公民技能 + Goal 数据契约）

> 父任务：`.trellis/tasks/06-26-foundagent-v6`。与 `06-28-role-library` **平级（兄弟）**：
> role-library 写**角色专属** skill，本任务写**横切所有角色的公民技能（civic skills）**——
> 不属于任何单个角色，是 role-library 4 个角色 skill 的**前置**。
> 状态：**in_progress**。机制前提（doer≠judge、worker→verifier 路由）已由 child②
> (`06-29-p2p-goal-passing`) 的 **Hub（PR#195）** 定型。2026-06-30 用户追加关键设计决策（B，见下「已决议」）：
> **判定标准（proof / acceptance criteria）只交给 verifier、对 worker 蒙眼**（防 Goodhart）。
> 这给本任务加了一层小机制增量（Phase A：Hub verifier-only accept 通道），其上才是文案（Phase B：R1–R4 + e2e）。

## Goal（目标）

给零人公司里**每一个 agent（不论角色）**一套必备的「公民技能」：横切的方法论 + 契约，
让任意角色都用同一套规矩**发 Goal、收 Goal、声明完成**。第一版只立**可演化骨架**，
调优靠后续真实运营迭代（沿用 role-library 方法论：不追求一次写到最优）。

载体与角色三要素一致：**charter 引用 + skill（SKILL.md）+（必要时）hook**。
关键价值是**消除重复**：现状 `builder`/`growth` charter 把"收 task→做→落 /company→report"
**逐字各抄一遍**（`agents/assets/builder-charter.md:10`、`growth-charter.md:11`），
公民技能层把这段抽成一处权威来源，charter 只 `see also`。

## 第一版范围（已与用户收敛）

**只做两件事**，其余明确后置：

1. **Goal 写法规范** —— 一份「一个好 Goal 长什么样」的内容契约（result-not-steps、可验收、给够 context、单一职责…）。
2. **主回路公民技能** —— 发送 / 接收 / 声明完成 这条回路的统一 skill（尤其补上现在缺的 **worker 侧**）。

## 背景与现状（confirmed facts，代码已证）

角色 = 声明式 `agents/<role>.yaml`（charter + skills + hooks），已有 ceo/builder/growth/verifier charter。

主回路的**底层机制已存在**，本任务大部分是给它们写「agent 面向的契约 + skill」，不是从零造管道：

- **发送**：`orchestration/messaging.py:41` `send(to, intent, reply_to)` —— 把一条 IME 投到 peer inbox；
  body 里内嵌 reply_to + goal_id + "report 命令" + "先把 deliverable 落 /company 再 report"。
  `send` 自带 8 位 goal_id 但**当前不写 ledger**（`messaging.py:46` 注释："for later ledger side-logging"——尚未接上）。
- **接收**：resident `orchestration/agent_loop.py:161` `agent_loop(key=…)` 用 `inbox.poll` 取事件，
  `build_wake_prompt`（`agent_loop.py:38`）渲染成 wake prompt；或 `orchestration/receive_tool.py` 的 `receive()` 一条一条取。
- **IME 信封**：5 字段 `{id,time,to,text,body}`（`orchestration/inbox.py:37`）。**设计红线 §2.3：不加新信封字段，一切塞 body。**
- **声明完成（现状三条路径并存）**：
  - (a) worker `messaging.report --to <reply_to>`（`messaging.py:61`）—— "我做完了 + 结果"，投回发起者 inbox。
  - (b) verifier 输出 `VERDICT: PASS / FAIL`（`agents/assets/verifier-charter.md:19`）—— 验收判断。
  - (c) `goal_ledger` 状态机 `open→claimed→running→reported→verifying→done/killed`（`orchestration/goal_ledger.py`）
    + `goal_inbox.py` 把终态事件转 IME 投回发起者 —— 上一代中心 pump 时代的确定性追踪。
- worker 侧 charter 现为 **placeholder**（`builder-charter.md:1`/`growth-charter.md:1` 自述"真内容来自 role-library，别过度投入"），
  已雏形教了"收→做→record→report"，但**各 charter 各抄、未抽公共层、未成文规范**。

## Requirements（第一版）

> 两层：**Phase A = Hub 机制增量**（verifier-only 判定标准通道）；**Phase B = 文案**（skill/charter/yaml）。
> A 先做、B 依赖 A。A 动 child② 已交付的 Hub，但仍守 IME §2.3（accept 走 DISPATCH body，不加信封字段）。

**Phase A — 机制增量（防 Goodhart：判定标准对 worker 蒙眼）**

- **R0 verifier-only 判定标准通道**：让 caller 可在派活时附一份**只给 verifier、对 worker 蒙眼**的「判定标准（acceptance criteria）」。
  - **可选**：省略 = verifier 自行从 goal 推导（旧行为，向后兼容）；提供 = verifier 按它判。
  - **载体**：`send` 加 `--accept`，criteria 编码进 **DISPATCH body** 的独立分段（守 §2.3，不加信封字段）；
    Hub `parse_body` 解出 → `goal_ledger` 存 `accept`（默认 None，不破现有测试）→ `hub._verify_ime` 注入给 verifier。
  - **worker 蒙眼是结构性的**：`hub._work_ime` 只用 `intent` 现造工单，**永不携带 accept**——worker 无从获取。
  - verifier-charter 更新：有 accept 按它判、没有才自推导。

**Phase B — 文案（两个公民 skill：`send-goal` + `receive-goal`，写人话）**

> 总纲：skill/prompt 必须**写人话**——自然、清楚的英文，逻辑顺，别诡异、别堆术语。篇幅不长，**Goal 写法直接写进 skill 本体，不单开 reference 文件**。
> **拆两个 skill（用户 2026-06-30 定）**：发 Goal 与做 Goal 是两个时刻、两个受众，各一个聚焦 skill 触发更准、按角色最小装载——
> **CEO 只装 `send-goal`（只发不收）、部门只装 `receive-goal`（只收不发，本版无递归）**；上递归时部门再加 `send-goal`。

- **R1 Goal 写法（写进 `send-goal/SKILL.md`）**：教发起者写一个好 Goal：
  - **真实、具体、可执行**——是想要的**结果**，不是含糊口号、也不是逐步流程。
  - **必须给充分 context**：为什么要这个 goal、它在更大图景里的位置、相关背景，全都塞进 `--intent`，让执行者读得懂、能直接当一个明确任务去做（goal 可能很宏大，信息要给够）。
  - **可选判定标准 → `--accept`**（给 verifier 用、执行者看不到）：怎么写一条可独立核验的成功口径。
  - **载体**：goal+context 走 `--intent`、criteria 走 `--accept`，都不加 IME 结构化字段（守 §2.3）。
- **R2 worker 侧（写进 `receive-goal/SKILL.md`，现状缺）**：收到 Goal 后——读懂 goal 和它的 context → **专注把这件事做好**（deliverable 可能是产物、**也可能是对外操作，不强制落 /company**）→ 做完用 `report --goal-id <id>` 报一句 done。
  - **就这么简单**：不提"判定标准"、不提"自评"——评价是 verifier 的事，执行者只管做好、做完说 done（"OK, I'm done"）。
- **R3 charter 去重**：`builder`/`growth`/`researcher` charter 改为**引用**该公民 skill，删掉各自逐字重复的主回路段落（charter 只留角色独有内容）。
- **R4 一致性**：skill 遵循 SKILL.md 规范（frontmatter `description` 写清"何时用"）；与 role-library 的「通用 charter 结构」对齐，不冲突。

## Acceptance Criteria

- [x] **AC0（Phase A 机制）**：`send --accept` → criteria 进 ledger `accept`、由 `_verify_ime` 投给 verifier；`_work_ime` 结构性不含 criteria。
      `send` 拒收含保留分隔符的 payload（防泄漏/截断，code-review 抓出）。单测：`test_accept_criteria_hidden_from_worker_shown_to_verifier`、
      `test_send_without_accept_is_backward_compatible`、`test_reconcile_reissued_verify_keeps_accept_criteria`、`test_send_rejects_reserved_delimiter_in_{accept,intent}`。
- [x] AC1：`send-goal/SKILL.md` 含 Goal 写法：真实/具体/可执行 + 必给 context(why) + 可选 `--accept` + 好/坏对照例；人话。
- [x] AC2：`receive-goal/SKILL.md` worker 侧："收懂 goal+context → 把事做好（含对外操作，不强制落 /company）→ report done"；全程不提自评/判定标准。
- [x] AC3：`builder`/`growth`/`researcher` charter 已改为引用公民 skill（grep "When you receive a task" = 0）；181 测试全绿。
- [x] AC4（Tier-A 确定性 e2e）：`test_e2e_8` 全栈走真协议——caller `send --intent --accept` → Hub → worker 收到（工单**无 criteria**）→ report → Hub 转 verifier（verify 工单**有 criteria**）→ PASS → done → 通知 caller。
- [x] **AC4（Tier-B 真 LLM 容器 e2e，2026-06-30 已跑通）**：`docker compose up hub builder verifier` + 注入 `send --to builder --accept "..."`。零人闭环 ~60s、attempts=0：builder（真 LLM）工单**无 criteria**、写 `/company/working_hours.md` 真产物 → verifier（真 LLM）工单**有 criteria**、据其判 PASS → done → harness 收 `goal … DONE`。防 Goodhart live 生效（builder 不知考点仍命中）。

## Out of Scope（第一版不做，留后续 increment）

- 外部信号处理（peripheral inbox 收到外部信号怎么判断/路由）。
- 「如何编写 Skill」「如何编写 Wiki」等元技能（应在写过几个真 skill 后反向提炼，硬写必空）。
- Reach-Goal 的角色专属方法论、各角色专属 skill（归 role-library）。
- 验收的**强制性**（本版 accept 可选；"必须写 criteria 才能派活" 留后续按真实运营决定）。
- 任务分解 / 递归（大 Goal 拆子 Goal）——留后续 increment。

## 已决议：完成/验收路径（2026-06-30，用户定 B —— 判定标准对 worker 蒙眼）

**核心设计原则（用户提出，防 Goodhart / teaching-to-the-test）**：worker 一旦知道判定标准，会为「通过检查」做表面工作，
而非真把事做好。所以**判定标准（proof / acceptance criteria）只交给 verifier、对 worker 蒙眼**；worker 收到的只有 goal 本身、专注把事做好。

调和「防 goal drift」与「worker 蒙眼」：
- **「什么算做成」由 Goal 名词本身承载**（caller 写精确无歧义的结果，worker 看得到，锚定意图）。
- **「怎么验证 / 判定标准」是 verifier 私有**（caller 写、只投 verifier，worker 看不到 → 防表面工作）。
- 好 Goal = 精确的结果，**不是**给 worker 的检查清单。

固定回路（从 agent 视角）：

1. **caller** `send --to <dept> --intent "<goal + 充分 context/why>" [--accept "<verifier-only criteria>"]` → 经 Hub。
   Hub 建 + claim goal、**存 accept 进 ledger**，用 `_work_ime`（**只含 intent，即 goal+context**）把活路由给 `<dept>`。
2. **worker** 收到 goal + context（拿不到 accept）→ 读懂、专注把事做好（产物或对外操作）→
   `report --goal-id <id> --text "<what you did>"` 报一句 done（goal 进 RUNNING → Hub 自动转交验收）。
3. **verifier**（独立角色）从 Hub `_verify_ime` 拿到 **goal + accept**（有则按它判、无则自推导）→ 核查成果出 verdict →
   `report`（goal 在 VERIFYING）→ Hub 据 verdict 走 done / retry / kill。
4. Hub 把终态通知投回 `reply_to`（caller 的 inbox）。

**两条结构强制、不靠 agent 自觉**：doer≠judge 由 Hub `from`-gate；worker 拿不到判定标准由 `_work_ime` 只携带 intent。
所以 worker 侧 skill **无需也不该**提"自评/判定标准"——它结构上就接触不到，提了反而误导。

## 本版范围锁定（2026-06-30，用户确认）

- 交付 = **Phase A（Hub 机制增量：R0 verifier-only accept 通道）+ Phase B（R1–R4 文案）+ 一条真实零人 e2e**。
  A 动 child② 的 Hub（约 5 文件 + 测试），仍守 IME §2.3；折进本任务、分两阶段（也可拆独立机制子任务）。
- 公民 skill 内容边界 = **caller 侧发 Goal（+ 可选私有 accept）** + **worker 侧收/做好/report work-done（蒙眼、不自评）**两块。
- accept **可选**（省略=verifier 自推导）；强制性、任务分解/递归本版不做。

## Open Questions

- （无阻塞项。）accept 是否最终强制、强制性怎么把关——留真实运营迭代。skill/Goal 规范细节同此，第一版只立可演化骨架。
