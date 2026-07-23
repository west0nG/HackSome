# Research: CEO 判断力 — 开源 skill/charter 实拉与落地取舍

- **Query**: 实际拉取 obra/superpowers · anthropics/launch-your-agent · alirezarezvani/claude-skills 等的真实 skill/prompt 内容，逐条用 (a)/(b)/(c) 三道检验过筛，判断 CEO "判断力"开源里有没有现成可用、还是必须自写；若是 gap，给出能通过"LLM 自己不会吗"检验的具体条目清单。
- **Scope**: external（真实文件实拉，全部 WebFetch/curl raw.githubusercontent.com，已逐一标注真实路径与可访问 URL）
- **Date**: 2026-06-30
- **方法说明**: 通过 `curl` 拉 GitHub API tree + raw 文件原文审查，全部内容均来自真实文件；拉不到的如实标注。**不重复**父任务 `.trellis/tasks/06-28-role-library/research/{skill-reuse-survey,charter-prompt-survey}.md` 的二手 survey，本文是"实拉真实内容 + 三道检验落地"。

## 三道检验（用户洞察，贯穿全文）

目标 agent 本身是 LLM。给 LLM 写泛泛 skill = 没写。一条子句只有满足至少一项才保留：
- **(a) 环境/系统特定**：LLM 训练里不可能有的本系统机制（role 名单、Goal 协议、`python3 -m orchestration.messaging send`、Hub、verifier-only accept、DONE/KILLED、`/company` memory）。
- **(b) 要专门压制的 LLM 默认行为**：反 helpful-assistant（不退回人审、不 hedge、heartbeat 没事闭嘴、自己拍板）。
- **(c) 非平凡的具体取舍标准/反例**：带阈值/反例的判断信号，LLM 不会自发采用。

---

## TL;DR（重点结论先行）

1. **开源里没有一个可直接 vendor 当"CEO 判断力"用的 skill。** 三大候选各自有结构性错配，下面分别给了证据：
   - `obra/superpowers`（MIT）：真实、高质量，但是**工程 worktree + human-in-the-loop** 的 plan→execute→review 流水线。对 CEO 有价值的不是整个 skill，而是**散落的具体子句**（dispatch 自包含、doer≠judge 禁止预判、文件交接的 context 经济学、ledger 优先于记忆、连续执行不打卡、按复杂度选 role/model）。→ **借子句，不 vendor 整 skill。**
   - `anthropics/launch-your-agent`（Apache-2.0）：**最接近 CEO 生命周期形状**（idea→scope v0→launch→对二元 rubric 评分→只改一处→上 schedule），但它是**人类 founder copilot**（满屏 `AskUserQuestion`、"you drive the decisions"）且**绑死 CMA API**（Outcome/Session/Deployment/Vault 原语 + curl/ant）。→ **借生命周期形状 + rubric/eval/只改一处/三类"以后再说"纪律，丢掉 API 与人审环。**
   - `alirezarezvani/claude-skills`（MIT）：**人类 founder 的 C-suite 顾问模拟器**——"the founder decides / before reaching the founder"、董事会仪式、fundraising/runway/OKR/EOS 这些 LLM 本来就会的 MBA 知识。`ceo-advisor`/`company-os` 近乎全是泛泛常识（丢弃）。真正可借的只是几个小 shape：`decision-logger` 的两层记忆 + DO_NOT_RESURFACE、`agent-protocol` 的"suspicious consensus"触发器、"silence is an option"、按 stakes 分级验证、"never silently pick a conflict winner"——**全是 shape，且全部要把"人类决策"倒过来（CEO 自己拍板）。**

2. **因此 CEO 判断力本质是 gap，必须自写。** 开源给的是"形状 + 一把可移植子句"，没有任何模块同时满足：(i) 自治（无人类 decider）、(ii) 知道本系统 role 名单/Goal 协议/Hub/verifier-only/DONE-KILLED/`/company`、(iii) 主动压制 LLM 的 helpful-assistant 默认。这个 skill 约 **80% 原创，20% 借子句**（借的部分标了来源+许可证）。

3. **charter vs skill 落点**（本文末"落地建议"详述）：反默认的**身份级**短句（silence-is-option、decide-don't-punt、trust-the-ledger）进 **charter**（每次 wake 注入）；重的**每决策清单**（definition-of-done 怎么写、dispatch 自包含模板、冲突/迭代协议）进**渐进式披露 skill**。

---

## Findings

### 真实文件清单（实拉，均可访问）

| 来源仓库 | 许可证 | 实拉的真实文件 | 本地审查副本 |
|---|---|---|---|
| `obra/superpowers` | MIT (Jesse Vincent, LICENSE 已核) | `skills/brainstorming/SKILL.md`、`skills/writing-plans/SKILL.md`、`skills/executing-plans/SKILL.md`、`skills/dispatching-parallel-agents/SKILL.md`、`skills/subagent-driven-development/SKILL.md`、`skills/subagent-driven-development/task-reviewer-prompt.md`、`skills/using-superpowers/SKILL.md` | scratchpad `sp_*` |
| `anthropics/launch-your-agent` | Apache-2.0 (SPDX header 在 SKILL.md 内) | `.claude/skills/launch-your-agent/SKILL.md`、`.claude/skills/launch-your-agent/references/interview.md`、`.claude/skills/wrap-up/SKILL.md` | scratchpad `lya_*` |
| `alirezarezvani/claude-skills` | MIT (Alireza Rezvani, LICENSE 已核) | `c-level-advisor/skills/ceo-advisor/SKILL.md`、`.../decision-logger/SKILL.md`、`.../agent-protocol/SKILL.md`、`.../company-os/SKILL.md`、`.../chief-of-staff/SKILL.md`、`orchestration/ORCHESTRATION.md` | scratchpad `arc_*` |

URL 形如 `https://raw.githubusercontent.com/<repo>/main/<path>`，全部 HTTP 200 实拉成功。

> **拉取勘误（如实记录）**：
> - superpowers 当前 `main` 树里 **`writing-plans/SKILL.md` 存在**（HTTP 200，已拉）。父任务 survey 里提到的它仍在。
> - alirezarezvani 仓库是**多 harness 镜像**：`.gemini/skills/<name>/SKILL.md` 等是**符号链接**（52 字节，指向 `../../../c-level-advisor/skills/<name>/SKILL.md`），真实内容在 `c-level-advisor/skills/` 与顶层 `orchestration/`。任务里提到的 `c-level-advisor` 是**目录/bundle 名**（不是单个 skill）；`orchestration` 是顶层 `orchestration/ORCHESTRATION.md`（一篇人工编排 how-to，非 SKILL.md）。`decision-logger`/`company-os` 确有真实 SKILL.md。

---

## 候选逐一过筛

### A. obra/superpowers（MIT）— 工程流水线，借子句不借整 skill

#### A1. `dispatching-parallel-agents/SKILL.md` — 分派质量金矿
真实原文要点（行号对应实拉文件）：
- L10：**"They should never inherit your session's context or history — you construct exactly what they need."** → 直接对应我们 P2P 无共享记忆：**Goal 必须自包含**。**保留 (a)+(c)。**
- L36-46 "Use when / Don't use when"：3+ 独立失败、"each problem can be understood without context from others"、"No shared state"；反例 "Failures are related (fix one might fix others)"。→ **一 Goal = 一独立问题域**的判定信号。**保留 (c)。**
- L115-127 Common Mistakes ❌/✅ 表：`❌ "Fix all the tests" — agent gets lost / ✅ "Fix agent-tool-abort.test.ts"`；`❌ No constraints: agent might refactor everything / ✅ "Do NOT change production code"`；`❌ Vague output / ✅ "Return summary of root cause and changes"`。→ **具体>宽泛 + 带约束 + 指定回传格式**，带真实反例。**保留 (c)。**
- L68-77：`Multiple dispatch calls in one response = parallel execution. One per response = sequential.` → 这是 Claude Code 的 Task-tool 机制，**对我们不适用**（我们是 `messaging send` + Hub 路由），harness-bound。**丢弃此条。**

#### A2. `subagent-driven-development/SKILL.md` — 验收分权 + context 纪律金矿
- L17 **Continuous execution**：`Do not pause to check in with your human partner between tasks... "Should I continue?" prompts and progress summaries waste their time — they asked you to execute the plan, so execute it.` → 直接压制 LLM 的"打卡/求确认"默认。**保留 (b)，强。**
- L164-173 **禁止预判 reviewer**：`never instruct a reviewer to ignore or not flag a specific issue... If the prompt you are writing contains "do not flag," "don't treat X as a defect," "at most Minor," or "the plan chose" — stop: you are pre-judging.` → 对应我们 **verifier-only accept / doer≠judge**：CEO 在写验证 Goal 时**不得夹带自评、不得预设严重度**。**保留 (a)+(b)+(c)，强且独特。**
- L221-244 **File Handoffs**：`Everything you paste into a dispatch prompt — and everything a subagent prints back — stays resident in your context for the rest of the session and is re-read on every later turn. Hand artifacts over as files.` + L189-193 `Do not paste accumulated prior-task summaries... a real session's dispatch hit 42k chars of which 99% was pasted history. A fresh subagent needs its task, the interfaces it touches, and the global constraints. Nothing else.` → **context 经济学**：大件走文件路径，不贴 blob，不贴历史。带真实数字。**保留 (b)+(c)。**
- L247-264 **Durable Progress（ledger）**：`Conversation memory does not survive compaction. ... controllers that lost their place have re-dispatched entire completed task sequences — the single most expensive failure observed. Track progress in a ledger file... After compaction, trust the ledger and git log over your own recollection.` → 对应我们 **Hub 的确定性 id + reconcile 崩溃恢复**：wake/compaction 后**信 Hub ledger，不信自己的记忆**，不重发已 resolve 的 Goal。**保留 (a)+(b)。**
- L99-130 **Model Selection（T-shirt 复杂度分级）**：`Use the least powerful model that can handle each role`，按"1-2 文件+完整 spec→便宜 / 多文件集成→标准 / 设计判断→最强"。→ 对我们是**按 Goal 复杂度选 role/路径**。**保留 (c)，但偏 cost/harness，简述即可。**
- L132-148 **Handling Implementer Status（BLOCKED）**：`Never ignore an escalation or force the same model to retry without changes. If the implementer said it's stuck, something needs to change.` + `If the task is too large, break it into smaller pieces`。→ 对应**失败后别原样重发**，要么补 context、要么换 role、要么拆小、要么 KILL。**保留 (a:DONE/KILLED)+(c)。**

#### A3. `task-reviewer-prompt.md` — 验收契约 shape
- `Do Not Trust the Report... Treat the implementer's report as unverified claims... a stated rationale never downgrades a finding's severity.` + 单 verdict 输出（`✅/❌/⚠️` + Critical/Important/Minor + Task quality: Approved|Needs fixes）。→ 印证 doer≠judge 的**结构强制**与"不信自述、按证据"。**shape 有用，但我们 verifier 角色另有任务，作 (a) 印证。**

#### A4. `brainstorming` / `writing-plans` / `executing-plans` — 大部分丢弃
- `brainstorming` 有 `<HARD-GATE>`：实现前必须 human 批准设计；`executing-plans` 反复 `Raise them with your human partner before starting` / `Ask for clarification rather than guessing`（L21, L47）。→ **零人 CEO 恰恰要反过来：丢掉 human gate。** 这些 skill 整体 **human-in-the-loop，丢弃。**
- 仍可借的零散信号：`brainstorming` L68 **"if the request describes multiple independent subsystems, flag this immediately... Don't spend questions refining details of a project that needs to be decomposed first."** → **先拆分再细化**的选题信号。`writing-plans` 的 **Global Constraints 区块**（把 spec 全局约束逐字拷进、每个 task 隐含包含）→ 对应 Goal 自包含里的"全局约束"。**借这两条 (c)，不借整 skill。**

> **superpowers 小结**：对 CEO 的增量价值集中在 A1/A2 的**具体子句**（自包含分派、禁止预判 verifier、文件交接、ledger 优先、连续执行不打卡、按复杂度选 role、失败别原样重发）。这些子句很多在父任务 survey 里只是抽象提及（CrewAI "explain-don't-reference"、MetaGPT T-shirt），这里给了**真实可引原文 + 真实反例/数字**。

---

### B. anthropics/launch-your-agent（Apache-2.0）— 生命周期形状最近，但人审 + API-bound

`.claude/skills/launch-your-agent/SKILL.md`（137 行）+ `references/interview.md`（260 行）是**目前最接近 CEO lifecycle 的真实开源工件**：idea → scope v0 → launch → 对 Outcome rubric 评分 → 迭代 → schedule。

真实可借的**纪律**（形状/标准，非 API）：
- **Definition-of-done = 3-6 条二元、可独立评分的 criteria**：`interview.md` Q2 `3–6 explicit criteria; each independently gradeable. Vague criteria → noisy grading.` + `Push past "a useful summary" to "a markdown file with the 5 most important items, each with a link and one line of why".` → CEO 把**可检验验收标准写进 Goal**，verifier 才 gate 得动。**保留 (c)，强。**
- **只改一处（change ONE thing per iteration）**：SKILL.md Phase 3 `change one thing: Sharper rubric → ... / Instructions/tool change → ...`。→ 失败后重定向时只动一个变量，才能归因。压制 LLM "一次性改一堆"默认。**保留 (b)+(c)。**
- **三类"以后再说"严格不混**：SKILL.md Voice `Three different reasons, never blurred: (i) CMA can't do it at all, (ii) it needs a connector/credential they don't have on hand, (iii) it's possible but out of scope for this first iteration.` → 选题/拆分时**把"做不到/缺前置/本轮不做"分清**。**保留 (c)。**
- **smallest-core-first + 编号 v1/v2**：`v0 is the few core features that make the job work; everything else is laid out as v1, v2... a numbered sequence of planned increments... not a pile of "maybe later"` + interview "reads as a sequence of planned releases, not a list of cuts"。**保留 (c)。**
- **不要过早 fan-out / 不要过早自动化**：interview Q8 `Multiagent rules (default is NO)... Build the single most valuable subagent first; the coordinator comes after at least one subagent works alone.` + Q5 `run everything as ad-hoc sessions first; the deployment is created last, once a session has passed the rubric.` → **先证一个 role 跑通再并行/上 schedule。** 压制 LLM 爱并行的默认。**保留 (b)+(c)。**
- **eval evidence 分类法**：interview Q2b 表（golden set / 一个 artifact / 有输入无答案 / 啥都没有 / 鲜数据）→ **有/无 known-good 答案时各怎么 ground 验收**。**保留 (c)。**

**必须丢掉的**：整个 skill 是**人类 founder copilot**——`You drive the keyboard, they drive the decisions`、满屏 `AskUserQuestion`、`The founder decides`；且**绑死 CMA**（Outcome/Session/Deployment/Vault 原语、`POST /v1/agents`、curl/ant、`/mnt/session/outputs/`）。**这两层（人审 + API）对零人 CEO 编排零增量，整 skill 不可 vendor。** `wrap-up/SKILL.md` 同理（庆祝 + 给 founder 看 overview 页），丢弃。

> **launch-your-agent 小结**：**借生命周期骨架 + 上述 6 条纪律（rubric 二元化、只改一处、三类以后再说、smallest-core、先证后并行/自动化、eval 分类）**；丢掉 human-in-loop 与 CMA API。这是"借形改写"的典型——shape 有用，内容全换成本系统（Goal/role/verifier/Hub）。

---

### C. alirezarezvani/claude-skills（MIT）— 人类顾问模拟器，只剩小 shape

#### C1. `ceo-advisor/SKILL.md`（169 行）— 几乎全丢
内容是**人类公司 CEO 的 MBA 顾问**：strategic planning cycle、capital allocation、fundraising、board management、CEO metrics dashboard（ARR/runway/NPS/attrition）、"Tree of Thought: generate 3 paths, evaluate upside/downside/reversibility"。
- 这些 **LLM 本来就会**（reversibility = Bezos one-way/two-way doors；OKR；三路径权衡）。**绝大部分丢弃**（不满足 a/b/c）。
- L142-150 "Tree of Thought / reversibility / second-order effects" 是**泛泛美德**，丢弃。
- L153-158 "Internal Quality Loop... self-verify, peer-verify, critic pre-screen... tag 🟢verified/🟡medium/🔴assumed" 是**分权验证 shape**（详见 C3 agent-protocol），且**指向 human founder**。作 shape 参考。
- ⚠️ 整 skill 的隐含前提是 `before reaching the founder` / `The founder decides`——**对零人 CEO 必须倒过来。**

#### C2. `decision-logger/SKILL.md`（154 行）— 两层记忆 + DO_NOT_RESURFACE 是真 insight
- **两层记忆**：`Layer 1 stores everything. Layer 2 stores only what the founder approved. Future meetings read Layer 2 only — this prevents hallucinated consensus from past debates bleeding into new deliberations.` → **非平凡机制**：原始辩论 transcript 会污染未来决策，故把"已批决策"与"原始辩论"分层。对应我们 `/company` memory 的"决策 vs 过程"分层。**保留 (c)。**
- **DO_NOT_RESURFACE**：被否的提案打标，`🚫 BLOCKED: "[Proposal]" was rejected on [DATE]` 防重提。→ **防 LLM 反复 re-litigate 已定/已否的方向。** 但其 reopen 机制是 `founder must explicitly say "reopen"`——人审，需倒过来为"无新信息不重开"。**保留 (b)+(c)。**
- 决策条目格式（Decision/Owner/Deadline/Review/Supersedes/Superseded-by）是 shape；我们 Hub ledger 已记 Goal 状态，**条目格式作 shape 参考，不照搬**。

#### C3. `agent-protocol/SKILL.md`（451 行）— inter-agent 协议，多数我们 Hub 已覆盖，挑两条
- **Loop prevention**（No self-invoke / Max depth 2 / No circular / Chain tracking）：这是 in-context `[INVOKE:role|question]` 模型的防环。**我们是确定性 Hub 路由 + sender-identity 门**，结构上已防环防自评——所以这块是 **(a) 印证"我们设计已覆盖"，不新增。**
- **Critic Pre-Screen 触发器**含 `Any recommendation where all roles agree (suspicious consensus)` → **全体一致是危险信号，要主动 probe**，非确认。**genuinely non-obvious，保留 (c)。**
- **Conflict Resolution**：`Never silently pick one — surface the conflict.` → CEO 整合多 role 输出冲突时**不得静默选赢家**。**保留 (c)。**
- **按 stakes 分级验证**（Low/Medium/High/Critical → 要不要 peer/critic）→ **不同 Goal 配不同验证 rigor** 的 shape。**保留 (c)，但要换成我们 verifier-only 语义。**
- **Communication Rules（非常关键的反默认两条）**：
  - L448 `Silence is an option. If there's nothing to report, don't fabricate updates.` → 直接对应 heartbeat 没事**闭嘴别 busy-work**。**保留 (b)，强。**
  - L445 `Actions have owners and deadlines. "We should consider" is banned.` → 反含糊。**保留 (c)。**
  - ⚠️ L445-446 `The founder decides. Roles recommend.` / `Decisions framed as options. Not "what do you think?"` → **这是要倒过来的标本**：零人 CEO 自己是 decider，不能 punt 成 A/B 选项给人。引用它正是为了说明"要反"。**(b) 反默认。**
- **Internal Quality Loop**（self-verify checklist 里的 `"So What?" Test — if you can't answer "so what?" in one sentence → cut it`）→ 反噪声输出过滤。**保留 (b)，但偏泛。**

#### C4. `company-os/SKILL.md`（236 行）— 泛泛 EOS/ops 知识，丢弃
EOS/Scaling-Up/L10/rocks/scorecard/IDS——**人类公司管理框架，LLM 全会**。只有几条 shape 与我们机制呼应（但 LLM 自带）：`Each rock is binary: done or not done. No "60% complete."`（≈DONE/KILLED）、`One person owns each function... "Alice and Bob both own it" means nobody owns it.`（≈一 Goal 一 role）、`When everything is a priority, nothing is. Hard limit: 7.`（WIP 上限）、`Revisiting decided issues... reopen only with new information.`（≈DO_NOT_RESURFACE）。**整体丢弃，仅记这几条 shape 与我们设计同构。**

#### C5. `orchestration/ORCHESTRATION.md`（262 行）+ `chief-of-staff` — 人工编排 how-to，丢弃
`ORCHESTRATION.md` 是教**人类**怎么 `Load persona.md / Load skill/SKILL.md / 分 phase / 手动 handoff`，结尾 `The human decides. Orchestration is a suggestion.`——**手动、人审、与我们常驻-per-department + P2P + Hub 自治模型不同构。** "Personas=WHO / Skills=HOW / Task agents=WHAT" 是个干净的概念三分，但不是可执行判断。**丢弃（shape-only）。** `chief-of-staff` 是 board-meeting 后处理 + 人审日志，丢弃。

> **alirezarezvani 小结**：作为"自治 CEO 控制"零增量——它是**advisory + 人类决策 + 董事会仪式**。可借的只有**小 shape**：两层记忆 + DO_NOT_RESURFACE、suspicious-consensus、never-silently-pick-winner、silence-is-option、按 stakes 分级验证。全部需**反转人审、换本系统语义**。

---

## 重点结论：CEO 判断力是 gap，必须自写

**有没有现成可直接用的？没有。** 三类候选与"零人自治 CEO 编排"的错配是结构性的：

| 候选 | 错配 | 对 CEO 判断力的净增量 |
|---|---|---|
| superpowers | 工程 worktree + human gate | 整 skill 不可用；**散落子句**可借（自包含分派/禁预判 verifier/文件交接/ledger 优先/连续执行/失败别原样重发） |
| launch-your-agent | 人类 founder copilot + 绑 CMA API | 整 skill 不可用；**生命周期形状 + 6 条纪律**可借形改写 |
| alirezarezvani | 人类 C-suite 顾问 + 董事会仪式 + 泛 MBA | 整 skill 不可用；**几个小 shape**可借（两层记忆/DO_NOT_RESURFACE/suspicious-consensus/never-silently-pick/silence-is-option） |

没有任何模块同时具备：(i) **无人类 decider 的自治拍板**、(ii) **本系统机制感知**（role 名单 researcher/builder/growth/verifier、Goal 协议、`messaging send`、Hub、verifier-only accept、DONE/KILLED、`/company` memory）、(iii) **主动压制 LLM helpful-assistant 默认**。→ **CEO 判断力 skill 约 80% 原创，20% 借子句。**

### CEO 判断力 skill 应包含的具体条目清单（按四块；每条标 a/b/c + 证据）

> 过滤原则：下列每条都**通过"LLM 自己不会吗"检验**——要么是本系统机制(a)、要么压制具体默认(b)、要么带阈值/反例(c)。纯美德（"权衡机会成本""分步思考""保持客观"）已剔除，不列。

#### 块 1 — 方向 / 选题（dispatch 什么 Goal）
1. **先拆分再细化**：目标若横跨多个独立子系统，先拆成多个独立 Goal（各自一个 owner role），**不要发一个 mega-Goal**。 — (c)+(a)；证据：superpowers `brainstorming/SKILL.md` L68 "if the request describes multiple independent subsystems, flag this immediately... Don't spend questions refining a project that needs to be decomposed first"。
2. **smallest-core-first（v0）**：先发能交付核心职能的最小 Goal；其余拆成**带具体机制的编号后续 Goal**（v1/v2），不是含糊"以后"。 — (c)；证据：launch-your-agent SKILL.md "v0 is the few core features... everything else laid out as v1, v2... not a pile of 'maybe later'"。
3. **先证一个再 fan-out**：单 role 跑通前不要并行铺开多 role；先建最有价值的那个 worker，协调/并行在至少一个跑通后再上。 — (b)+(c)；证据：launch-your-agent `interview.md` Q8 "Multiagent default is NO... Build the single most valuable subagent first; the coordinator comes after at least one subagent works alone"。
4. **Goal 必须有可检验的 done**：值得发的 Goal 必须带可检验验收标准；"improve X / make it better" 不是 Goal。 — (c)；证据：company-os 好/坏 rock 对比（"Improve our sales process" vs "Implement Salesforce CRM... by March 31"）+ launch Q2 "push past 'a useful summary'"。

#### 块 2 — 结果后决策（accept / iterate / kill / redirect）
5. **definition-of-done = 3-6 条二元、可独立评分**，写进 Goal 让 verifier gate；CEO **绝不自评通过**（verifier-only accept，结构上由 sender-identity 门强制）。 — (a)+(c)；证据：launch `interview.md` Q2 "3–6 explicit criteria; each independently gradeable. Vague criteria → noisy grading" + 本系统 verifier-only。
6. **重定向时只改一处**（更严的验收标准 OR 重新 scope OR 换 role，不要一次改一堆），才能归因。 — (b)+(c)；证据：launch SKILL.md Phase 3 "change one thing"。
7. **结果冲突不静默选赢家**：两个 role 输出打架时显式 surface/解决（保守取差/再发一个裁决 Goal），不糊弄。 — (c)；证据：agent-protocol "Never silently pick one — surface the conflict"。
8. **可疑的全体一致**：所有信号/role 零张力地一致，当作要 probe 的危险信号，而非确认。 — (c)；证据：agent-protocol Critic Pre-Screen 触发器 "Any recommendation where all roles agree (suspicious consensus)"。
9. **失败别原样重发**：因结构性原因失败的 Goal，要么补 context、要么换 role、要么拆小、要么 **KILLED**——不要把同一 Goal 原样再丢给同一 role。 — (a:DONE/KILLED)+(b)+(c)；证据：SDD `SKILL.md` "Never... force the same model to retry without changes... If the task is too large, break it into smaller pieces"。
10. **不 re-litigate 已定/已否**：方向一旦定/否，记录之；无新信息不重提（DO_NOT_RESURFACE）。 — (b)+(c)；证据：decision-logger DO_NOT_RESURFACE + company-os "reopen only with new information"。

#### 块 3 — 优先级与节奏（heartbeat 行为）
11. **heartbeat 没事就闭嘴**：无可执行项时静默；不制造 busy-work、状态汇报、"should I continue?" 打卡。 — (b)，**最强反默认（双重证据）**；证据：SDD "'Should I continue?' prompts and progress summaries waste their time" + agent-protocol Rule 10 "Silence is an option. If there's nothing to report, don't fabricate updates"。
12. **自己拍板，不退回人审、不 hedge 成选项菜单**：开源顾问 skill 全部 `The founder decides / present options A/B`——零人 CEO **必须倒过来**，CEO 就是 decider。 — (b)+(a)，强；证据（要反的标本）：agent-protocol "The founder decides. Roles recommend." / "Decisions framed as options. Not 'what do you think?'"。
13. **WIP 上限 + 单 owner**：限制在飞 Goal 数；"everything is a priority → nothing is"；不要往一个已有未结 Goal 的 role 里再塞。 — (c)+(a)；证据：company-os "hard limit 7" + "Alice and Bob both own it means nobody owns it"（一 Goal 一 role）。
14. **先证后自动化**：一个 ad-hoc run 通过验收前，不要把周期性 Goal 上 schedule。 — (c)；证据：launch Q5 "run everything as ad-hoc sessions first; the deployment is created last, once a session has passed the rubric"。
15. **wake/compaction 后信 ledger 不信记忆**：相信 Hub 的确定性 id + reconcile，不重发 ledger 已显示 resolve 的 Goal（这是观测到的最贵失败）。 — (a)+(b)；证据：SDD Durable Progress "controllers that lost their place have re-dispatched entire completed task sequences — the single most expensive failure... trust the ledger and git log over your own recollection"。

#### 块 4 — 分派质量（Goal 怎么写）
16. **Goal 自包含（explain, don't reference）**：接收 role 与你零共享上下文——把 path/link/env/stack/验收标准**写进 Goal**。 — (a)+(c)；证据：dispatching-parallel-agents L10 "They should never inherit your session's context or history — you construct exactly what they need" + 父 survey CrewAI "explain don't reference"。
17. **一 Goal = 一问题域 + 一 owner role**：不捆绑无关工作；不发跨两个 role 域的 Goal。 — (a)+(c)；证据：dispatching-parallel-agents "Dispatch one agent per independent problem domain" + company-os 单 owner。
18. **大件走文件路径，不贴 blob/历史**：贴进 Goal 的内容会常驻你的 context 且每轮重读，并撑大接收方。 — (b)+(c)，带真实数字；证据：SDD File Handoffs "Everything you paste... stays resident... re-read on every later turn. Hand artifacts over as files" + "a real session's dispatch hit 42k chars of which 99% was pasted history"。
19. **不预判 verifier**：绝不告诉 verifier 不许 flag 什么、把严重度上限设成多少、"这是故意的"。doer≠judge 是结构强制（sender-identity 门），CEO 不得把自评夹带进验证 Goal。 — (a)+(b)+(c)，**强且独特**；证据：SDD "never instruct a reviewer to ignore or not flag... If the prompt contains 'do not flag,' 'at most Minor,' 'the plan chose' — stop" + task-reviewer "a stated rationale never downgrades a finding's severity"。
20. **具体 > 宽泛 + 带约束 + 指定回传**：`"Fix all the tests"` 会让 agent 迷路；给 scope、约束（"don't change X"）、明确回传格式。 — (c)，带真实反例；证据：dispatching-parallel-agents Common Mistakes ❌/✅ 表。
21. **按 Goal 复杂度配 role/路径**：琐碎 Goal 不走重型路径，判断密集 Goal 不走单薄路径。 — (c)（偏 cost）；证据：SDD Model Selection T-shirt 分级。

---

## 可直接 vendor / 借形改写 / 丢弃 — 文件级裁决

| 文件 | 裁决 | 理由 |
|---|---|---|
| superpowers `dispatching-parallel-agents/SKILL.md` | **借子句**（非整 vendor） | 自包含分派 + 一域一 agent + ❌/✅ 反例可借；并行机制(L68)是 Claude Code Task-tool，与我们 messaging+Hub 不符，丢 |
| superpowers `subagent-driven-development/SKILL.md` | **借子句** | 连续执行不打卡 / 禁预判 verifier / 文件交接 / ledger 优先 / 失败别原样重发——全是 CEO 判断子句；worktree/TDD/git 部分丢 |
| superpowers `task-reviewer-prompt.md` | **借形（印证）** | doer≠judge + "不信自述按证据" 印证我们 verifier 结构；verifier 角色另写 |
| superpowers `brainstorming`/`writing-plans`/`executing-plans` | **大部分丢弃**，借 2 条 | human gate 与零人 CEO 相反；仅借"先拆分再细化"+"Global Constraints 自包含" |
| launch-your-agent `SKILL.md` + `references/interview.md` | **借形改写** | 生命周期骨架 + 6 条纪律可借；human-in-loop 与 CMA API 全丢 |
| launch-your-agent `wrap-up/SKILL.md` | **丢弃** | 给人类 founder 庆祝/看页，无编排增量 |
| alirezarezvani `decision-logger/SKILL.md` | **借形改写** | 两层记忆 + DO_NOT_RESURFACE 是真 insight；人审 reopen 要反转 |
| alirezarezvani `agent-protocol/SKILL.md` | **借形（少量）** | suspicious-consensus / never-silently-pick / silence-is-option / 分 stakes 验证可借；loop-prevention 我们 Hub 已覆盖；"founder decides" 是要反的标本 |
| alirezarezvani `ceo-advisor/SKILL.md` | **丢弃** | 人类 CEO MBA 顾问（fundraising/board/runway/NPS），LLM 自带 |
| alirezarezvani `company-os/SKILL.md` | **丢弃** | EOS/L10/rocks/scorecard 泛 ops 知识；仅记几条 shape 与我们设计同构 |
| alirezarezvani `orchestration/ORCHESTRATION.md` + `chief-of-staff` | **丢弃** | 人工编排 how-to + 人审日志，与自治模型不同构 |

---

## 落地建议（charter vs skill 落点 — 供主 agent 设计参考）

> 这是研究结论的延伸，非设计/实现；主 agent 用 `update-spec`/`implement` 决定最终形态。

- **进 charter（每次 wake 注入、身份级、短句、反默认）**：条目 11（heartbeat 闭嘴）、12（自己拍板不退回人审）、15（信 ledger 不信记忆）、19 的身份化版本（doer≠judge 是铁律）、16 的一句话版（Goal 自包含）。这些是"必须每次都在场"的抗 helpful-assistant 漂移子句。
- **进渐进式披露 skill（按决策类型触发、含清单/模板/反例）**：条目 1-10、13-14、17-18、20-21。重在"出现某类决策时拉出来用"的具体清单——definition-of-done 怎么写（3-6 二元）、dispatch 自包含模板、冲突/迭代/kill 协议、suspicious-consensus 检查、文件交接规则。
- **borrowed 子句的署名**：凡借自 superpowers(MIT)/launch-your-agent(Apache-2.0)/alirezarezvani(MIT) 的原文，落地时在 skill 的 references 或注释里标来源+许可证（许可证已在上文核实）。

## Caveats / Not Found

- 未发现 superpowers 之外、专门面向"**自治零人 CEO 编排判断**"的开源 skill；VoltAgent/awesome-claude-code-subagents 等是 role 定义集合（父 survey 已覆盖），非判断力模块，本次未重复审。
- launch-your-agent 的 `references/cma-api.md`/`examples-bank.md`/`mock-connectors.md` 未逐字拉取——它们是 CMA API/连接器细节，与本任务（CEO 判断力，非 CMA 集成）无关，故略；如后续要做"外设/真实出站执行"可再拉。
- alirezarezvani 仓库的 `decide`/`hard-call`/`founder-mode`/`stress-test`/`scenario-war-room` 仅存在于 `.hermes`/`.vibe` bundle 路径（`.gemini` 与 `c-level-advisor/skills/` 下无独立 SKILL.md，按名直拉 404）。从名字看是决策类，但它们都属同一"人类顾问 + 董事会"体系，预期与 ceo-advisor/agent-protocol 同性质（人审、MBA），增量低；未逐一拉取，**如实标注未拉**。
- 本文所有引用均为真实文件原文（scratchpad `sp_*`/`lya_*`/`arc_*` 副本 + 上述 raw URL 均 200）。无任何编造内容；判断为 gap/可借/丢弃处均附了可核证据。
