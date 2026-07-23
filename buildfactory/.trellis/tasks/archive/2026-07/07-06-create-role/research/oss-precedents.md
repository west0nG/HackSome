# OSS 先例调研：CEO 运行时创建新角色（charter / skills / MCP）

- 调研日期：2026-07-06
- 任务：`.trellis/tasks/07-06-create-role`
- 方法：web search + 官方文档/源码抽取 + 本机 skill-creator 插件源码通读
- 结论先行（TL;DR）：
  1. **"agent 在运行时创建 agent" 有成熟先例**：AutoGen AutoBuild（LLM 生成整队 agent 配置）、AG2 CaptainAgent（对话中 retrieval-selection-generation 组队 + reflection）、AgentVerse（recruiter 生成专家 + evaluation 反馈重组队伍）。机制上早已被验证可行。
  2. **质量是普遍短板**：AutoBuild 生成 persona 全靠一次 LLM 调用、无 critic/评分；有质量门的先例是 Voyager（run-and-verify 才入库）、skill-creator（baseline 对比 + 独立 grader + 人审循环）、AgentVerse（evaluation 不达标就重组）。我们的差异化应放在质量门，不是生成机制。
  3. **对我们而言 role config schema 不用发明**：Claude Code subagent 的 `.claude/agents/*.md` frontmatter 已原生支持 `tools` / `mcpServers` / `skills` / `model` / `memory` / `permissionMode` 等字段——"创建新角色"在机制上就是 CEO 写一个 md 文件（+ 可选 per-role MCP json，与本项目已有 `agents/mcp/<role>.json` 约定吻合）。难点全部在生成质量与验收。

---

## 领域 1：多 agent 框架的运行时角色创建

### 1.1 AutoGen AutoBuild / `AgentBuilder`（★ 最直接的先例）

- 链接：[AutoBuild 博客](https://microsoft.github.io/autogen/0.2/blog/2023/11/26/Agent-AutoBuild/) · [源码 agent_builder.py（0.2 分支）](https://github.com/microsoft/autogen/blob/0.2/autogen/agentchat/contrib/agent_builder.py) · [AG2 notebook](https://docs.ag2.ai/latest/docs/use-cases/notebooks/notebooks/autobuild_basic/)
- License：microsoft/autogen 仓库现为 **CC-BY-4.0**（0.2 时代代码曾以 MIT 发布）；活跃维护的 fork **ag2ai/ag2 为 Apache-2.0**。要 vendor 代码走 ag2。
- 机制：用户给一句 `building_task`，一个 "build manager" LLM 依次完成：
  1. 生成专家名单（`AGENT_NAME_PROMPT`）
  2. 逐个生成 system message（`AGENT_SYS_MSG_PROMPT`，往默认模板里填）
  3. 把 system message 压缩成一句 description（`AGENT_DESCRIPTION_PROMPT`，供 GroupChat speaker 选择用）
  4. 判断任务是否需要写代码（`CODING_PROMPT`，决定是否加 user proxy / code executor）
  5. 组装 GroupChat，配置可存为 JSON 复用
- 关键提示词（源码原文，节选）：

```text
AGENT_NAME_PROMPT:
  Suggest no more than {max_agents} experts with their name according to the following user requirement.
  - Expert's name should follow the format: [skill]_Expert.
  - Only reply the names of the experts, separated by ",".

AGENT_SYS_MSG_PROMPT:
  - According to the task and expert name, write a high-quality description for the expert
    by filling the given template.
  # Task {task} / # Expert name {position} / # Template {default_sys_msg}

AGENT_DESCRIPTION_PROMPT:
  Summarize the following expert's description in a sentence.

CODING_PROMPT:
  Does the following task need programming (i.e., access external API or tool by coding)
  to solve ... Answer only YES or NO.
```

- 保存的 config schema：

```json
{
  "building_task": "...",
  "agent_configs": [
    {"name": "...", "model": "...", "system_message": "...", "description": "..."}
  ],
  "manager_system_message": "...",
  "code_execution_config": {},
  "default_llm_config": {}
}
```

- `build_from_library()` 变体：先从预置 agent library 里检索（`AGENT_SEARCHING_PROMPT`：按 name+profile 匹配任务、"less is better"），选不到才现场生成——**先复用后生成**的两级策略。
- 评价：机制清晰、prompt 可直接抄；但**没有任何质量门**——system message 一次生成即用，没有 critic、没有 e2e 试跑。生成的 persona 容易泛泛（正好踩中我们记忆里 "No generic skills for LLM agents" 的反面）。

### 1.2 AG2 CaptainAgent（对话中自适应组队，AutoBuild 进化版）

- 链接：[博客](https://docs.ag2.ai/latest/docs/blog/2024/11/15/CaptainAgent/) · [论文 Adaptive In-conversation Team Building, arXiv:2405.19425](https://arxiv.org/pdf/2405.19425) · [notebook](https://github.com/ag2ai/ag2/blob/main/notebook/agentchat_captainagent.ipynb)
- License：Apache-2.0（ag2ai/ag2）
- 机制（两步循环）：
  1. **组队**：拆解任务→为每个子任务推荐角色→每个角色"从 agent library 检索选择，或现场生成"（retrieval-selection-generation），并从 tool library 检索预置工具装配给 agent；
  2. **执行+反思**：nested chat 协作解子任务→触发 summarization + reflection 生成报告→CaptainAgent 据报告决定**调整子任务和队伍**（回到第 1 步）或终止输出。
- 库格式：`agent_lib="captainagent_expert_library.json"`、`tool_lib="default"`，均为可选 JSON；可作为 `AssistantAgent` 的 drop-in 替代。
- 评价：比 AutoBuild 多了 **reflection→重组** 这个反馈环，是"生成的角色不好用就换"的先例；工具从 tool library 检索装配的做法与我们 per-role MCP loadout 同构。

### 1.3 CrewAI

- 链接：[Agents 概念文档](https://docs.crewai.com/en/concepts/agents) · [Processes](https://docs.crewai.com/en/concepts/processes) · [仓库](https://github.com/crewAIInc/crewAI)
- License：MIT
- Role schema（核心三元组 + 配置项）：`role`（职能）、`goal`（个体目标）、`backstory`（人格/上下文），另有 `llm`、`tools: List[BaseTool]`、`allow_delegation`（默认 False）、`max_iter`、`system_template`/`prompt_template`/`response_template`（自定义提示结构）、`knowledge_sources`、`reasoning` 等。配置落盘为 `agents/<name>.jsonc`（新）或 `config/agents.yaml`（旧），支持 `{placeholder}` 模板插值。
- 运行时创建：`Agent()` 构造器可在执行期任意实例化（无需配置文件），hierarchical process 下 manager agent 动态分派任务；但**框架没有让 LLM 生成 Agent 定义的内置管线**——动态的是"任务分派"，不是"角色铸造"。
- 评价：role/goal/backstory 三元组是最广为流传的 persona 最小 schema，值得作为 charter 生成 prompt 的骨架之一；机制本身对我们没有增量。

### 1.4 MetaGPT

- 链接：[role.py](https://github.com/geekan/MetaGPT/blob/main/metagpt/roles/role.py) · [论文 ICLR 2024](https://arxiv.org/pdf/2308.00352) · [多 agent 教程](https://docs.deepwisdom.ai/main/en/guide/tutorials/multi_agent_101.html)
- License：MIT（FoundationAgents/MetaGPT）
- Role schema：`name` / `profile` / `goal` / `constraints`，提示模板即 `"You are a {profile}, named {name}, your goal is {goal}. the constraint is {constraints}."`；行为面由 `actions`（可执行动作集）+ `_watch`（订阅上游消息类型）组成——**角色 = 人设 + 动作集 + 触发订阅**，用 SOP 把角色串成流水线。
- 运行时创建：角色是 Python 类，需要人写代码；无 LLM 铸造角色的管线。
- 评价：`constraints` 作为一等字段、`watch`（角色何时被激活）值得吸收进我们的 charter schema——对应我们编排层里"角色何时 wake"的问题。

### 1.5 CAMEL

- 链接：[论文 NeurIPS 2023](https://proceedings.neurips.cc/paper_files/paper/2023/file/a3621ee907def47c1b952ade25c67698-Paper-Conference.pdf) · [role_playing.py](https://github.com/camel-ai/camel/blob/master/examples/ai_society/role_playing.py) · [role_assignment_agent.py](https://github.com/camel-ai/camel/blob/master/camel/agents/role_assignment_agent.py)
- License：Apache-2.0
- 机制：inception prompting 三件套——task specifier prompt（把模糊任务具体化）、assistant system prompt、user system prompt；`RoleAssignmentAgent` 可以按任务生成 N 个角色名+描述（这是一个小型"角色铸造" agent）。
- 评价：**task specifier**（先把任务写具体，再据此生成角色）这个前置步骤值得抄——CEO 铸造角色前先把 workflow 需求规格化，能显著减少泛泛 persona。

### 1.6 LangGraph

- 链接：[仓库](https://github.com/langchain-ai/langgraph) · [Send API / map-reduce 讨论](https://aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization)
- License：MIT
- 现状：没有"角色"一等概念；Send API 支持运行时动态并行 task、Command 支持动态路由，社区有 meta-agent 拼装教程，但**没有内置的 agent-definition 生成器**。
- 评价：对本特性无增量，仅作覆盖记录。

### 1.7 AgentVerse（★ 质量反馈环先例）

- 链接：[论文 ICLR 2024, arXiv:2308.10848](https://arxiv.org/pdf/2308.10848) · 仓库 OpenBMB/AgentVerse（Apache-2.0）
- 机制：四阶段闭环——**expert recruitment**（recruiter agent 按目标动态生成专家描述，不靠预定义）→ collaborative decision-making → action execution → **evaluation**（评估现状与目标差距，不达标就把 reward 反馈回第一阶段，**重新调整队伍构成**再来一轮）。
- 评价：这是"生成的角色受验收驱动而迭代"的最干净学术表述，直接对应我们 doer≠judge 文化：评估者不满意→重铸角色。

---

## 领域 2：meta-agent / persona 工厂与质量

### 2.1 PersonaHub（Tencent AI Lab）

- 链接：[仓库](https://github.com/tencent-ailab/persona-hub) · [论文 arXiv:2406.20094](https://arxiv.org/html/2406.20094v1) · [HF 数据集](https://huggingface.co/datasets/proj-persona/PersonaHub)
- License：**仓库无 OSI license；数据明确 "research purposes only"**——不可 vendor 进商业自治系统。
- 方法论（可抄思路不抄数据）：Text-to-Persona（任意网页文本→"谁会读/写这段文本"→persona）与 Persona-to-Persona（由已有 persona 沿人际关系推导相邻 persona，跑 6 跳）两条扩产管线；用 MinHash 按描述去重。
- 评价：它解决的是"多样性规模化"，不是"单个 persona 的质量"；对我们只有一个启示——**从真实材料（workflow 的实际产物/工单）出发生成 persona，比凭空想更具体**。

### 2.2 生成 persona 的质量控制现状

- AutoBuild：无 critic、无评分，一次生成即用（前述缺陷）。
- CaptainAgent：靠事后 reflection 报告驱动重组，粒度是"队伍"不是"单个 persona 的文本质量"。
- AgentVerse：evaluation 阶段给 reward 反馈，重组 recruiter 输出。
- disler meta-agent（下文 4.3）：靠"生成时先抓最新官方文档 + 固定输出模板"保底，无评测。
- **结论：没有任何一家有"persona 质量评分 rubric + 不过关不上岗"的硬门**。我们记忆里的三道检验（①系统特定 ②压制 LLM 默认 ③非平凡取舍）+ objective propose 式评审门是真实空白，值得作为差异化实现。

---

## 领域 3：agent 自建 skill 库

### 3.1 Voyager（MineDojo）

- 链接：[仓库](https://github.com/MineDojo/Voyager)（**MIT**）· [论文 arXiv:2305.16291](https://arxiv.org/abs/2305.16291)
- Skill 即代码：技能 = 可执行 JavaScript 函数（控制 Minecraft bot），由 GPT-4 迭代生成。
- **验证故事（核心）**：iterative prompting 循环 = 环境反馈 + 执行错误 + self-verification。critic 是另一个 GPT-4 调用，输入游戏状态，输出：

```json
{"reasoning": "...", "success": bool, "critique": "feedback for improvement"}
```

  只有 critic 判 success 的程序才入库（run-and-verify before commit）。注意社区共识：这种"再问一次 LLM 成没成"的自验对高正确性要求领域**不够强**——我们应以真实 e2e 产物验收替代。
- 存储/检索（`voyager/agents/skill.py`）：三层——① Chroma 向量库存 description embedding；② 文件系统存 `.js` 代码 + `.txt` 描述；③ `skills.json` 主索引。description 由 GPT-3.5 读代码自动生成（"给这个函数写注释"）。检索用 `similarity_search_with_score(query, k=5)` 返回代码。重名技能：向量索引覆盖、旧代码保留为 `{name}V2/V3` 版本文件。
- 评价：**"技能描述由模型读实现自动生成 + 向量检索 + 版本化不删旧"** 三个工程决策都可直接借鉴；MIT 可 vendor，但代码强绑 Minecraft，实际是 pattern 级复用。

### 3.2 Anthropic skill-creator（本机已装，源码已通读）

- 位置：`/Users/weston/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/SKILL.md`；公共仓库 [anthropics/skills](https://github.com/anthropics/skills)（skills/ + template/ + spec/；skill 内自带 **Apache-2.0** LICENSE.txt，仓库另有 THIRD_PARTY_NOTICES）。
- 完整流程（这是目前看到的最完善的"造能力→验证→迭代"闭环）：
  1. **Capture intent**：4 个定题问题（做什么/何时触发/输出格式/是否需要 test cases——客观可验的技能才配 assertion）。
  2. **写 SKILL.md**：progressive disclosure 三层（metadata 常驻 / body 触发加载 <500 行 / scripts+references 按需）；description 是唯一触发机制，要写得"pushy"对抗 under-trigger。
  3. **测试（doer≠judge 已内建）**：每个 test case **同回合**起两个 subagent——with-skill 与 baseline（无 skill 或旧版 skill 快照），互为对照；产物按 `iteration-N/eval-N/` 落盘。
  4. **评分**：独立 grader subagent 按 assertions 打分（能写脚本判定的必须写脚本判定），聚合成 benchmark.json（pass_rate/time/tokens、mean±stddev、delta），再跑一个 analyzer pass 找"永远通过的无区分度断言/高方差 flaky eval"。
  5. **人审 + 迭代**：eval viewer 收集人的逐例 feedback→改 skill→重跑全部 case 进新 iteration，直到满意。改进哲学明确写着："Generalize from the feedback"（禁止 overfit 少数样例）、"如果发现自己在写全大写 ALWAYS/NEVER，是黄旗——改成解释 why"。
  6. **Description 触发优化**：生成 20 条真实感 trigger evals（8-10 正例 + 8-10 **near-miss 负例**，明确禁止"太容易的负例"），60/40 train/test 切分，每条 query 跑 3 次取触发率，循环让 Claude 改 description，**按 test 分选优防过拟合**（`scripts/run_loop.py`，用 `claude -p` 子进程实测触发）。
  7. 还有 blind A/B comparator（不告诉评审哪个是新版）作为高严格度选项。
- 评价：**这就是我们 create-role 质量门的模板**。把"skill"换成"role charter"，同一套结构成立：draft → 造 2-3 个真实 workflow 试题 → 新角色 vs 现有最接近角色（baseline）各跑一遍 → 独立 grader 按 AC 打分 → 不达标重铸。Apache-2.0，流程文档和脚本均可 vendor/改造。

---

## 领域 4：Claude Code subagent 规范（我们的落地载体）

### 4.1 官方 `.claude/agents/*.md` frontmatter 全字段

来源：[官方文档 sub-agents](https://code.claude.com/docs/en/sub-agents)。仅 `name`、`description` 必填：

| 字段 | 语义 |
|---|---|
| `name` | 唯一 id（小写+连字符），hooks 里即 `agent_type` |
| `description` | **自动委派的唯一依据**——何时该用这个 agent |
| `tools` / `disallowedTools` | 允许/剔除的工具列表；省略=继承全部 |
| `model` | `sonnet`/`opus`/`haiku`/`fable`/完整 model id/`inherit`（默认 inherit） |
| `permissionMode` | `default`/`acceptEdits`/`auto`/`dontAsk`/`bypassPermissions`/`plan` |
| `mcpServers` | 该 subagent 可用的 MCP server：名字引用已配置 server，或**内联完整 server config** |
| `skills` | 启动时**全文预载**的 skills（不是只载 description） |
| `hooks` | 作用域限于该 subagent 的生命周期 hooks |
| `memory` | `user`/`project`/`local`——跨 session 学习 |
| `maxTurns` / `effort` / `background` / `isolation`(worktree) / `color` / `initialPrompt` | 运行控制杂项 |

- 加载优先级：managed > `--agents` CLI JSON > `.claude/agents/`(项目) > `~/.claude/agents/`(用户) > plugin。**文件热加载**：session 中新写入/修改的 agent 文件几秒内生效（新建首个 agents 目录才需重启）——对"CEO 运行时铸造角色立即可用"至关重要。
- ⚠️ 安全限制：**plugin 分发的 subagent 会忽略 `hooks`/`mcpServers`/`permissionMode`** 三个字段。我们的角色若要带 per-role MCP，必须落在项目 `.claude/agents/` 而非 plugin。
- `--agents` flag 接受同 schema 的 JSON（`prompt` 字段=md 正文），适合一次性/测试性角色，不落盘。

### 4.2 社区最佳实践（多篇指南收敛的共识）

- description 决定自动委派质量：写明"是什么 + 何时用 + 触发条件"，像给别人的编排器写说明书。
- **job-shaped 名字**（repo-explorer、test-runner）比 generic 名字（frontend-engineer）路由更可靠。
- 工具按职责最小化：读向角色只给 Read/Grep/Glob，执行角色才给 Edit/Bash。
- system prompt 明确"是什么 + 不负责什么"（"You do not modify the source code itself — only test files"）。
- 参考集合：[VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)（100+，MIT）、[wshobson/agents](https://github.com/wshobson/agents)（多 harness 插件市场，MIT）、[0xfurai/claude-code-subagents](https://github.com/0xfurai/claude-code-subagents)——可作为"角色写法语料库"喂给铸造 prompt，但注意这些集合里大量正是我们要避免的 generic persona。

### 4.3 生成器先例：disler 的 meta-agent（agent 生成 agent 的最小实现）

- 链接：[meta-agent.md](https://github.com/disler/claude-code-hooks-mastery/blob/main/.claude/agents/meta-agent.md)（仓库无 license——**只学思路，别拷文本**）
- 本身就是一个 subagent（`model: opus`, tools: Write/WebFetch/...），流程：先 WebFetch 抓最新官方 sub-agents 文档 → 分析用户描述 → kebab-case 命名 → 写 action-oriented description → 推断最小工具集 → 按固定模板组装 md 文件直接落盘。
- 评价：证明"一个 subagent 负责铸造其他 subagent"在 Claude Code 里开箱即用；但它生成即交付、无验收，质量上限低。

---

## 领域 5：License 汇总（gh api 实测 SPDX）

| 项目 | License | 可用性 |
|---|---|---|
| ag2ai/ag2（AutoBuild/CaptainAgent 现役版） | Apache-2.0 | ✅ 可 vendor 代码/prompt |
| microsoft/autogen | CC-BY-4.0（现状） | ⚠️ 抄 prompt 需署名；建议从 ag2 取 |
| crewAIInc/crewAI | MIT | ✅（但无增量代码可抄） |
| FoundationAgents/MetaGPT | MIT | ✅ schema 思路 |
| camel-ai/camel | Apache-2.0 | ✅ task-specifier / role-assignment prompt |
| MineDojo/Voyager | MIT | ✅ pattern 级复用 |
| tencent-ailab/persona-hub | 无 license，research only | ❌ 数据不可用；方法论可参考 |
| anthropics/skills（skill-creator） | skill 内 Apache-2.0 | ✅ 流程+脚本可改造（本机已有全套源码） |
| VoltAgent/awesome-claude-code-subagents | MIT | ✅ 语料 |
| wshobson/agents | MIT | ✅ 语料 |
| disler/claude-code-hooks-mastery | 无 license | ⚠️ 只学流程，不拷文本 |

---

## Adopt / Adapt / Avoid（对准本特性：CLI-first、质量门、doer≠judge）

| 结论 | 对象 | 具体做法 |
|---|---|---|
| **Adopt** | Claude Code subagent frontmatter 作为 role schema | 不自造 schema。角色 = `.claude/agents/<role>.md`（name/description/tools/model/skills/mcpServers）+ 沿用已有 `agents/mcp/<role>.json` 约定。热加载让新角色即造即用；铸造动作本身就是写文件，天然 CLI-first |
| **Adopt** | skill-creator 的验收闭环（Apache-2.0，本机有源码） | 角色铸造后必过：真实试题 × (新角色 vs 最接近现有角色 baseline) → 独立 grader 按 AC 打分 → benchmark（含无区分度断言检查）→ 不过关重铸。脚本结构（run_loop/aggregate_benchmark/grader.md）可直接改造 |
| **Adopt** | AutoBuild 的分步铸造管线（从 ag2 Apache-2.0 版取） | 命名→system message→一句话 description→能力判定（要不要代码/哪些 MCP）分四次小调用，比一发生成整文件可控；saved-config JSON 思路 = 我们的角色注册表 |
| **Adapt** | CaptainAgent 的 retrieval-selection-generation | 铸造前先查已有角色库："现有角色能不能用？改 charter 能不能用？都不行才新建"。AGENT_SEARCHING_PROMPT 的 "less is better" 原则照搬，防角色爆炸 |
| **Adapt** | CAMEL task specifier | CEO 铸角色前先产出一份"岗位需求规格"（workflow 缺口的具体化），作为铸造 prompt 的输入，替代直接从模糊意图生成 persona |
| **Adapt** | AgentVerse evaluation→recruitment 反馈环 | 与我们 doer≠judge 对齐：验收 agent（非铸造者）给出的不通过报告，作为下一轮重铸的输入；上岗后表现差也可触发 charter 修订（复用 objective propose 评审门模式） |
| **Adapt** | Voyager 技能库三层存储 | 角色/技能注册表：描述由模型读 charter 自动生成、旧版本不删（V2/V3）、检索按 description。向量检索可降级为文件 + grep（CLI-first，角色数量级用不上向量库） |
| **Adapt** | MetaGPT 的 `constraints` + `watch` | charter schema 里保留 constraints（角色不做什么）和触发条件（何时 wake/被路由），后者接我们 Hub 编排层 |
| **Avoid** | AutoBuild 式"生成即上岗"（无 critic） | 所有先例中最大的坑：一次 LLM 调用产出的 persona 泛泛且无验证。必须过我们的三道检验 rubric（①系统特定 ②压制 LLM 默认 ③非平凡取舍）+ e2e 试跑 |
| **Avoid** | PersonaHub 数据、disler meta-agent 文本 | license 不允许（research-only / 无 license）；且 PersonaHub 解决的是多样性不是质量，方向不同 |
| **Avoid** | 用 plugin 分发带 MCP 的角色 | Claude Code 明确忽略 plugin subagent 的 `mcpServers`/`hooks`/`permissionMode`；角色必须落项目 `.claude/agents/` |
| **Avoid** | 社区 100+ subagent 集合直接当角色库 | 大多是 generic persona（frontend-engineer 类），正是社区公认路由效果差、也违反我们 no-generic 原则的写法；只可当反例/语料 |

## 主要参考链接

- AutoBuild 博客：https://microsoft.github.io/autogen/0.2/blog/2023/11/26/Agent-AutoBuild/
- AutoBuild 源码（prompt 原文）：https://github.com/microsoft/autogen/blob/0.2/autogen/agentchat/contrib/agent_builder.py
- CaptainAgent 博客：https://docs.ag2.ai/latest/docs/blog/2024/11/15/CaptainAgent/ ；论文：https://arxiv.org/pdf/2405.19425
- CrewAI Agents 文档：https://docs.crewai.com/en/concepts/agents
- MetaGPT role.py：https://github.com/geekan/MetaGPT/blob/main/metagpt/roles/role.py ；论文：https://arxiv.org/pdf/2308.00352
- CAMEL 论文：https://proceedings.neurips.cc/paper_files/paper/2023/file/a3621ee907def47c1b952ade25c67698-Paper-Conference.pdf
- AgentVerse 论文：https://arxiv.org/pdf/2308.10848
- Voyager：https://github.com/MineDojo/Voyager ；论文：https://arxiv.org/abs/2305.16291
- PersonaHub：https://github.com/tencent-ailab/persona-hub ；论文：https://arxiv.org/html/2406.20094v1
- Claude Code subagents 官方文档：https://code.claude.com/docs/en/sub-agents
- anthropics/skills（skill-creator 公共仓库）：https://github.com/anthropics/skills ；本机源码：`/Users/weston/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/`
- disler meta-agent：https://github.com/disler/claude-code-hooks-mastery/blob/main/.claude/agents/meta-agent.md
- 社区集合：https://github.com/VoltAgent/awesome-claude-code-subagents · https://github.com/wshobson/agents
