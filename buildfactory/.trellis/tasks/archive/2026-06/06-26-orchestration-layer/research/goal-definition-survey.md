# Goal / Dispatch 协议调研：业界如何定义、分发、验证 GOAL

> 任务：`06-26-orchestration-layer`。给「Goal 跑在确定性状态机上（LLM 产出 intent，状态/输出侧标准化）」的协议设计做**参考输入**。
> ⚠️ **仅供参考，不照搬**。这些产品的设计可能是错的；本文是 input，不是 template。
> 调研日期 2026-06-28。

## 图例（来源可信度）

- ✅ **Found + source** — 有 URL / 实际 schema 文件 / 官网原文，可引用。
- 🟡 **Found, marketing-level** — 官网/产品 guide 原话，但无公开 JSON/API schema，字段名引自营销页措辞。
- ⚠️ **Inferred** — 我的推断，无直接来源。

每条尽量标注。**没找到的地方我会直说**，不编。

---

## 1. Matrix（matrix.build）— PRIMARY

> 来源：`https://matrix.build/`（首页，Playwright 渲染）+ `https://matrix.build/guide`（产品 guide，Playwright 渲染）。YC 系，Mac 桌面 app（"Matrix runs on Mac today"）。
> **关于 "OKR" 的传闻属实**：官网明确有一个叫 **"OKR System"** 的东西。但 **没有公开的 schema/API 文档** —— 以下字段名都是营销页/guide 的原话，不是 JSON schema。

### 定义 Goal/Objective 的结构
- 🟡 **三层 OKR**：guide flow 节点 "OKR System" 副标题原文 = **"Objective, key result, tasks."**，定位是 **"Priority memory"**（优先级记忆）。即 Objective → Key Result → Task 三层，作为一块"记忆"持有，而非一次性 prompt。
- 🟡 **四种角色**（guide "Product Grammar"）：**Owner**（你/人类，"sets direction"：objectives, decisions, approvals, taste）、**Lead**（常驻 agent，"owns a domain, plans the next move, keeps context across sessions"，有 memory）、**Worker**（一次性专家，"spin up with a narrow brief, use tools, return evidence, and leave cleanly"）、**System**（调度/handoff/memory/transcript）。
- 🟡 **每个 loop 都有统一的 "Operating contract" 三元组**：`Owner`（负责角色）/ `Input` / `Proof`。这是 guide 里反复出现的标准结构。例如 Worker 这一格：Owner=`Worker Agent`，Input=`Task plus allowed skills`，Proof=`Tool trace and typed result`（注意他们说 **"typed result"**）。

### "Done / 成功" 如何表达与验证
- 🟡 **"Proof of Done"**：guide 原文 "The app treats **files, tests, screenshots, and transcript evidence** as the close of work." 首页 capability 卡片 "Result Driven Autonomy — **Nothing is done until there is proof.**"
- 🟡 **不是确定性 predicate**，而是 **证据 + 人审收口**：Owner "Close each loop by **accepting, redirecting, or asking for a narrower follow-up.**" 即人类（Owner）在 review 节点 accept/redirect。
- 🟡 控制环里有显式的 **"Review and evaluate" → "OKR update"** 步骤：跑完产出 Outcome 后评估，再回写 OKR state。guide Control Loop 的 Proof = **"Synthesis plus updated objective state."**（产出综合 + 更新后的 objective 状态）。
- 🟡 旗舰 demo 里 "proof" = **真实外部 artifact**：每个 milestone 挂一个 "Open proof" 外链（live 网站 aivideopro.io、Stripe checkout、YouTube 700k 播放）。proof 是可点开的真实世界结果，不是断言。

### 如何分发 + 结果如何回流
- 🟡 **首页 9 步闭环**（"One objective becomes a company loop"）：`Intent + assets` → `CEO Office receives` → `OKR system sync` → `Route and dispatch` → `Department cells run` → `Outcome formed` → `Review and evaluate` → `OKR update` → `Priority signal loops`。注意它是**带反馈的环**：review → OKR update → priority signal 再驱动下一轮。
- 🟡 **跨 agent handoff 有结构**（guide "Coordination"，最接近 dispatch schema 的东西）：原文 "the Lead sends a **structured handoff: context summary, artifact references, exact ask, and expected proof.**" —— 即 `{context summary, artifact references, exact ask, expected proof}` 四字段。Proof = "Reply handoff with completed output."
- 🟡 **Lead/Worker 分工**：Lead 持久（含 department memory `Memory.md`），把 objective 拆成 plan 再 dispatch 给一次性 Worker；Worker 回 evidence 后干净退出，"Workers can fail or finish without corrupting the Lead memory."（失败隔离）。

### 可复用 vs 要避免
- ✅ **可借鉴**：(a) **"Operating contract" = {Owner role, Input, Proof}** 这个极简三元组很干净，每个工作单元都强制声明"谁负责 / 输入 / 什么算交付"。(b) **handoff 四字段** `{context summary, artifact references, exact ask, expected proof}` —— dispatch 时**让上游显式声明 expected proof**，正好契合你"输出侧标准化"。(c) **proof = 带 provenance 的 durable artifact + transcript**，而非自然语言"我做完了"。(d) Lead(持久 memory) / Worker(一次性、失败隔离) 的分工与你的容器编排同构。
- ⚠️ **要警惕**：(a) 验证最终靠**人 accept**（Owner review），不是机器可判定 predicate —— 你要的是确定性状态机，这点 Matrix 给不了，只能给"证据形态"。(b) OKR 作为"priority memory"是软状态，没看到 key result 的可度量字段定义（无 schema）。(c) 全是营销/guide 措辞，落地细节（字段类型、状态枚举）**未公开**。

---

## 2. Paperclip（paperclipai/paperclip）— PRIMARY（开源，有真 schema ✅）

> 来源：GitHub `paperclipai/paperclip`（Drizzle/PGlite Postgres schema，TS）。**这是金矿——能拿到真实字段。** 自我定位 "control plane for AI-agent companies"。
> 关键文件：`packages/db/src/schema/{goals,projects,issues,heartbeat_runs,approvals,issue_work_products}.ts`、`AGENTS.md`。

### 定义 Goal/Task 的结构（真实字段 ✅）
- **`goals` 表**（递归树，等价于他们的 OKR 层）：
  ```
  id, companyId, title, description,
  level   text default "task"     -- 层级判别符：mission/objective/.../task
  status  text default "planned"
  parentId  -> goals.id (self-ref)  -- 自引用，任意深度
  ownerAgentId -> agents.id
  createdAt, updatedAt
  ```
  即 **goal 是一棵自引用树，靠 `level` 字符串区分 mission/goal/.../task**，不是固定三层。营销页说的层级是 `mission → goal → project → task`（搜索结果，🟡）。
- **`projects` 表**：`id, companyId, goalId(->goals), name, description, status default "backlog", leadAgentId, targetDate, env, executionWorkspacePolicy, pauseReason/pausedAt, archivedAt`。
- **`issues` 表 = 真正的工作单元（task）**（字段很多，挑关键的 ✅）：
  ```
  id, companyId, projectId, goalId, parentId(->issues, 子任务自引用)
  title (notNull), description
  status   default "backlog"   -- 枚举见下
  workMode default "standard"
  priority default "medium"
  assigneeAgentId / assigneeUserId   -- 单一受让人（single-assignee 不变式）
  -- 原子签出 / 执行锁（dispatch 的核心）：
  checkoutRunId   -> heartbeat_runs
  executionRunId  -> heartbeat_runs
  executionAgentNameKey, executionLockedAt
  -- 来源/去重：
  originKind default "manual" (e.g. routine_execution, task_watchdog,
            harness_liveness_escalation, stale_active_run_evaluation,
            issue_productivity_review, stranded_issue_recovery)
  originId, originRunId, originFingerprint, requestDepth(委派深度)
  -- 策略/状态（jsonb，给确定性外壳挂软状态）：
  executionPolicy, executionState (jsonb)
  -- 看门狗/监控：
  monitorNextCheckAt, monitorWakeRequestedAt, monitorLastTriggeredAt,
  monitorAttemptCount, monitorNotes, monitorScheduledBy
  sourceTrust (jsonb)         -- 来源可信度
  startedAt, completedAt, cancelledAt, hiddenAt
  ```
- **status 枚举**（🟡 搜索结果确认）：`backlog, todo, in_progress, in_review, done, blocked, cancelled`。注意有 **`in_review`** 中间态。
- ⚠️ **关键空缺**：issue 上**没有** `expected_output` / `acceptance_criteria` / 验证 predicate 字段。"done" 就是 `status` 枚举值。验证靠下面这些**外部表**。

### "Done / 成功" 如何验证（✅）
- **没有单一 predicate**。验证是几张表 + 状态机组合：
  - **`issue_work_products` 表**（交付物 = "proof"）：`type, provider, externalId, title, url, status, reviewState default "none", isPrimary, healthStatus default "unknown", summary, metadata(jsonb), sourceTrust, createdByRunId`。交付物**单列成行**，带 `reviewState` 和 `healthStatus`。`AGENTS.md` 要求 agent 在置 status 前先 attach inspectable artifact（"Do not rely on local filesystem paths"）。
  - **`approvals` 表**（治理闸门 / human-in-the-loop）：`type, requestedByAgentId, status default "pending", payload(jsonb notNull), decisionNote, decidedByUserId, decidedAt`。受治理动作要人批。
  - **Watchdog / 自动评审**：`issues.originKind` 里有一组**由系统自动 spawn 新 issue 来评估卡住/低产工作**的类型：`task_watchdog`、`issue_productivity_review`、`stale_active_run_evaluation`、`harness_liveness_escalation`、`stranded_issue_recovery`。即 **"verifier" 是独立的 watchdog run**，发现异常就开新 issue 去 recover/evaluate。
- **`AGENTS.md` 的 "Definition of Done"**（针对代码贡献，✅）：`Behavior matches spec / typecheck+tests+build pass / contracts synced / docs updated / PR template filled`。注意——**真正可机器判定的 done 在"代码任务"语境里就是 `pnpm typecheck/test/build` 通过**；通用任务则退回 work product + approval + watchdog。

### 如何分发 + 结果回流（✅）
- **`heartbeat_runs` 表 = 一次 agent 执行**：`agentId, invocationSource default "on_demand"(/scheduled/wakeup), triggerDetail, status default "queued", startedAt/finishedAt, error/errorCode, exitCode, signal, usageJson, resultJson(jsonb), sessionIdBefore/After, log* (logRef/logSha256/logBytes...), stdoutExcerpt, stderrExcerpt, retryOfRunId, processLossRetryCount, scheduledRetry*, livenessState/livenessReason, continuationAttempt, lastUsefulActionAt, nextAction, contextSnapshot(jsonb)`。
- **分发 = 原子签出 + 执行锁**：agent "wake on schedule/wakeup"（`agent_wakeup_requests` 队列）→ 原子 checkout 一个 issue（写 `checkoutRunId` / `executionRunId` / `executionLockedAt`）→ 保证 **single-assignee、不重复干**（`AGENTS.md` 列为不变式 "Atomic issue checkout semantics"）。
- **结果回流**：写进 `heartbeat_runs.resultJson` + `stdoutExcerpt` + `nextAction` + `contextSnapshot`；产物写 `issue_work_products`；最后改 `issues.status` 并留 final comment。
- **liveness/续跑**：`livenessState`、`continuationAttempt`、`lastUsefulActionAt`、`processLossRetryCount` —— 进程挂了能续，卡住有看门狗升级。

### 可复用 vs 要避免
- ✅ **可借鉴**：(a) **原子 checkout + execution lock**（`checkoutRunId/executionLockedAt`）正是你 broker 多容器并发要的"任务不被两个 agent 抢"机制，纯确定性、非 LLM。(b) **goal 用自引用树 + `level` 判别符**，比写死三层灵活。(c) **交付物单列成表（work_products）带 `reviewState`/`healthStatus`**，把"证明"结构化。(d) **watchdog 作为独立 verifier run**（低产/卡死/僵尸自动开 recovery issue）——这是"分离的验证 agent"模式的真实落地。(e) **run 与 issue 解耦**：issue=任务状态，heartbeat_run=一次执行（含 resultJson/log/retry），多对一。
- ⚠️ **要警惕**：(a) issue 表**字段爆炸**（50+ 列，一堆 monitor*/origin*/execution* unique index），是长期演进堆出来的，别一上来照抄。(b) 通用任务的 done **仍无机器 predicate**，靠 status 枚举 + approval（人）+ LLM watchdog 判断 —— 和 Matrix 同样的软肋。(c) jsonb 兜底字段（`executionPolicy/executionState/contextSnapshot`）多，确定性外壳里塞了大量非结构化软状态。

---

## 3. Claude Agent SDK — subagents / task delegation（✅ 官方文档）

> 来源：`code.claude.com/docs/en/agent-sdk/subagents`、`platform.claude.com/docs/en/agent-sdk/subagents`。

- **定义**：subagent = **`AgentDefinition`**，字段：`description`（**何时用** —— Claude 据此自动决定是否委派）、`prompt`（行为/system prompt）、`tools`（可选）、`model`（可选），还支持 `disallowedTools, skills, mcpServers, maxTurns, effort, background, permissionMode`。
- **Done/验证**：**无显式 done 字段 / 无 expected_output**。subagent 跑完把结果返回给主 agent，由**主 agent（LLM）自行判断**是否满足。隔离的是 context，不是验收。
- **分发/回流**：主 agent 通过内置 **`Agent` tool** 调 subagent（要把 `Agent` 放进 allowed_tools 才能自动批）；可并行 fan-out 独立工作；各 subagent context 隔离、结果汇总回主 agent。
- **可复用 vs 避免**：✅ `description`-driven 自动路由（用"何时用"而非显式分配）很轻；context 隔离 + 并行 fan-out 与你的容器模型一致。⚠️ 验收完全交给 LLM 主 agent，**零确定性**，不满足你"输出标准化"的诉求 —— 只能当"执行原语"，验证要你自己加。

---

## 4. OpenAI Agents SDK — handoffs / output_type / guardrails（✅ 官方文档）

> 来源：`openai.github.io/openai-agents-python/{agents,handoffs}/`。

- **定义工作单元**：Agent = `instructions + tools + handoffs + guardrails + output_type`。**`output_type`**（结构化输出）——设了之后，**"final output is when the LLM returns something of that type"**，即"产出指定类型 = 完成"。这是少见的**把"done"绑到类型上**。
- **Handoff（分发）**：`input_type`（handoff tool-call 参数 schema，解析后传给 `on_handoff`）、`input_filter`（过滤传给下一 agent 的输入）。委派 = 调一个 handoff "tool"。
- **Done/验证**：(a) `output_type` 满足 = 完成（但只保证**解析**通过，不保证语义对——第三方 eval `SchemaFidelity` 专门指出 "structured-output guarantee hides semantic drift inside well-typed fields"）。(b) **guardrails**（input/output guardrail）做校验，可触发 tripwire 中止。
- **可复用 vs 避免**：✅ **`output_type` = 完成判据** 直接呼应你"输出侧标准化"：让 LLM 必须吐出符合 schema 的结构体才算 done，状态机据此推进。⚠️ 只保证 well-typed，不保证 well-valued —— **类型对 ≠ 目标达成**，需额外语义校验（见 CrewAI guardrail）。

---

## 5. AutoGPT / BabyAGI — goal→tasks 分解（✅ 概念，原始项目）

> 来源：IBM "What is BabyAGI"、autogpt.net 等二手综述。

- **定义**：单一自然语言 **objective** → LLM 生成 **task list**（队列），每个 task 就是一条字符串描述。BabyAGI 经典循环 = `pull task → execute → store result → create new tasks → reprioritize → repeat`。
- **Done/验证**：**这是反面教材**。BabyAGI 的停止条件 = **"task queue 耗尽 / 生成的新 task 已存在"**（即 LLM 想不出新 task 了），**不是目标达成判定**。AutoGPT 靠 LLM 自己判断"goal supposedly met"——文献直接用 "supposedly" 揶揄。**没有可靠的完成检测**。
- **分发/回流**：单 agent 自循环，result 存进（向量）memory 喂下一轮 task 生成。
- **可复用 vs 避免**：✅ "objective → 动态 task 队列 + 按完成结果 reprioritize" 的闭环思想是后续所有框架的祖型。⚠️ **完成判据是 anti-pattern**：用"无新 task"当 done 会导致空转/早停/跑偏（goal drift）。明确教训：**done 必须独立于"还有没有 task"来判定**。

---

## 6. CrewAI — Task 对象（✅ 官方文档，最规范的"工作单元 schema"）

> 来源：`docs.crewai.com/en/concepts/tasks`。**这是业界最接近"标准 Task schema"的引用。**

- **`Task` 字段**（✅ 完整）：`description:str`、**`expected_output:str`**（"describes what successful completion looks like"）、`name`、`agent`、`tools`、`context:List[Task]`（**依赖其他 task 的输出作为上下文**）、`async_execution`、`human_input`、`markdown`、`config`、`output_file`、`create_directory`、`output_json:Type[BaseModel]`、`output_pydantic:Type[BaseModel]`、`callback`、**`guardrail:Callable`**、**`guardrails:List[Callable]`**、`guardrail_max_retries:int=3`。
- **`TaskOutput` 字段**：`description, summary, raw, pydantic, json_dict, agent, output_format(RAW/JSON/Pydantic), messages`。
- **Done/验证（✅ 这块最有料）**：
  - `expected_output` 本身**只是 prompt 里的指导，不是 runtime validator**（"CrewAI does not enforce strict schema validation on expected_output"）。
  - **真正的验证 = `guardrail`**，签名固定：
    ```python
    def guardrail(result: TaskOutput) -> Tuple[bool, Any]:
        # (True, validated_result)  -> 通过
        # (False, "error message")  -> 失败，error 回灌给 agent 重试
    ```
    失败时 error 反馈给 agent，**重试直到 `(True, …)` 或 `guardrail_max_retries`(默认3)**。多个 guardrail 串行（前一个输出喂后一个）。给字符串则自动建 `LLMGuardrail`（LLM 判定）。
- **可复用 vs 避免**：✅✅ **这是对你最直接的参考**：`expected_output`(意图，LLM 侧) + **`guardrail: (TaskOutput)->(bool, Any)` 确定性验证函数 + 有限重试** = **"LLM 产 intent，确定性函数验收，失败回灌重试"** 的完整范式，正是你要的形状。`output_pydantic` 把输出钉成类型。⚠️ 别迷信 `expected_output` 能验收（它不验）；guardrail 才是闸门。string guardrail 又退回 LLM 判定，确定性就没了——**优先写函数 guardrail**。

---

## 7. LangGraph — state schema（✅ 官方文档）

> 来源：`docs.langchain.com/oss/python/langgraph/graph-api`。

- **定义**：没有"Task 对象"，而是**整图共享一个 State**（`TypedDict` 或 Pydantic）。每个 node 返回对 state 的更新，**reducer** `(Value, Value)->Value` 决定如何 merge（覆盖 or 累加）。
- **Done/验证**：**`conditional_edge`** —— 一个函数读当前 state、返回下一个 node 名；**done 编码成"路由到 END / 不再有出边"**。完成判定 = **检查 state 字段**（如 `task_done` / `needs_retry`）的纯函数路由。
- **分发/回流**：node 间通过共享 state 传递；并行用 reducer 合并 fan-out 结果。
- **可复用 vs 避免**：✅ **完成 = 确定性函数读 state 决定路由**，这是**最贴近"Goal 跑在确定性状态机"**的范式：LLM 写 state 字段，**非 LLM 的 conditional edge 判 done**。reducer 是标准化"输出 merge"的好抽象。⚠️ State 是全局共享、易膨胀；多 agent 时 state 边界/隔离要自己设计（不像 Paperclip 那样 issue/run 解耦）。

---

## 8. Devin（Cognition）— 自主编码 agent（🟡 二手综述，无官方 schema）

> 来源：skywork.ai / deployhq 等评测，非官方。无公开 task schema。

- **定义**：task = **"small, well-scoped, with clear acceptance criteria"**；官方建议把 Devin 当 junior eng，给 `context + constraints + done criteria`、`file paths + expected behavior + acceptance criteria`。
- **Done/验证（✅ 模式清晰）**：**靠测试**——Devin **自己写并跑自动化测试**验证正确性；团队倾向给"**有 failing test 的可复现 bug**""flag 后的小 feature""依赖升级"这类 **easy to verify + safe to roll back** 的工单。**可机器判定 = 测试通过**。架构/安全/验收仍要人。
- **分发/回流**：人给工单 → Devin 执行 + 透明进度 + 需要时 flag 求人。
- **可复用 vs 避免**：✅ **"done = acceptance test 通过"** 是编码域里**最干净的确定性验收**：把 goal 配一个可执行测试，测试绿 = done。与 Paperclip `AGENTS.md` 的 `typecheck/test/build pass` 一致。⚠️ 只在**有可执行验收**的任务域成立（写营销文案/做调研就退回人审）；任务越"软"，确定性验收越难。

---

## Patterns across sources（横向规律）

1. **层级几乎一致**：`Objective/Mission → (Key Result/Goal/Project) → Task/Issue → Sub-task`。Matrix 三层 OKR、Paperclip 自引用 `goals.level` 树、AutoGPT objective→task list 都是这个骨架。**Task 普遍携带 ancestry/"why"**（Paperclip "tasks carry full goal ancestry"、Matrix handoff 带 context summary）。
2. **"done" 的两条路，泾渭分明**：
   - **可机器判定**（少数，强）：CrewAI `guardrail:(TaskOutput)->(bool,Any)`、OpenAI `output_type`、LangGraph conditional-edge 读 state、Devin/Paperclip 代码域 `tests pass`。**共同点：有一个非 LLM 的 predicate / 类型 / 测试**。
   - **证据 + 人审**（多数，弱）：Matrix "proof of done"（artifact+transcript+Owner accept）、Paperclip `issue_work_products.reviewState` + `approvals` + watchdog。**通用/软任务普遍退回这条**。
3. **几乎都把"交付物/证据"结构化**：Matrix "expected proof"、Paperclip `work_products`(带 reviewState/healthStatus)、CrewAI `TaskOutput`(raw/json/pydantic)、Devin 测试产物。**"done" 不是一句话，是一个带 provenance 的对象。**
4. **分发普遍是"原子领取 + 单一受让人"**：Paperclip atomic checkout/execution lock、Matrix Lead→Worker dispatch、OpenAI/Claude 的 handoff/Agent-tool。
5. **任务状态 与 一次执行 解耦**：Paperclip `issues`(任务) vs `heartbeat_runs`(执行，含 resultJson/log/retry/liveness) 是最清晰的样板；利于重试/续跑/审计。
6. **独立 verifier/watchdog 是真实模式**：Paperclip 用 watchdog run 自动开 recovery issue；OpenAI guardrail tripwire；CrewAI guardrail 重试回灌。**"分离的验证 agent" 不是空想。**
7. **dispatch payload 的最小公共字段**（综合 Matrix handoff + CrewAI Task + Devin）：`{intent/description, context/ancestry, constraints, allowed tools/skills, expected_output(类型或描述), expected_proof/acceptance}`。

## Open questions for our skeleton（给我们骨架的待决问题）

1. **Goal 的"done"分级**：要不要**强制每个 goal 声明验收 mode** —— `predicate`(可执行测试/类型/断言) / `artifact+review`(证据+收口) / `human_approval`？业界教训：**软任务硬塞 predicate 会假完成；硬任务用人审是浪费**。建议状态机层支持多种 `verification_kind`，由 LLM 在产 intent 时选，状态机只认结果。
2. **"输出侧标准化"落在哪一层**：CrewAI `guardrail((TaskOutput))->(bool,Any)` + `output_pydantic` 是最贴的范式 —— **LLM 产 intent，确定性函数验收 TaskOutput，失败 error 回灌限次重试**。我们的状态机是否就以 "(typed output, guardrail verdict)" 作为唯一合法的状态推进输入？
3. **expected_proof 要不要在 dispatch 时就锁死**：Matrix handoff 把 `expected proof` 写进派单。**先声明验收、再干活**能防 goal drift（对照 AutoGPT 的反面）。代价是 LLM 得提前想清楚验收 —— 值不值？
4. **任务 vs 执行解耦**：是否照 Paperclip 把 `goal/task`(状态) 与 `run`(一次容器执行，含 result/log/retry/liveness) 拆成两层？对你的多容器 broker（OC1-OC4 已验证）天然契合，且利于"结果回收 + 重试 + 看门狗"。
5. **原子 checkout / execution lock**：并发多容器下，用 Paperclip 式 `executionLockedAt/checkoutRunId` 保证 single-assignee —— 这是纯确定性、必须放进状态机的不变式。
6. **watchdog 作为独立验证/恢复者**：低产/卡死/僵尸 run 由非 LLM 监控触发"恢复 goal"，避免把"判断 agent 是否在瞎跑"也交给被监控的 agent。
7. **避免照抄的点**：Paperclip issue 表 50+ 列的字段膨胀、Matrix/Paperclip 对"软任务"最终仍依赖人审/LLM 判定 —— 这两个是它们的**未解难题**，不是答案。
