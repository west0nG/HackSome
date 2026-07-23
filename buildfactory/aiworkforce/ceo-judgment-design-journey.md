# CEO 判断力 (decide-direction) — 设计过程、分析与 e2e 验证

> 面向公司讨论的记录。主题：给 Foundagent 的 CEO agent 加"判断力"，从最初想法一路收窄到交付（PR #198），再真跑验证。
> 关联：task `06-28-role-ceo`（父任务 `06-28-role-library`）；分支 `feat/ceo-decide-direction`；PR https://github.com/SolvoHQ/BuildFactory/pull/198
> 姊妹文档：`SOP-adding-roles-and-skills.md`（把这条路抽象成的标准流程）。
> 日期：2026-06-30 ~ 07-01

---

## 0. 一句话结论

CEO 判断力 = **务实地决定追什么，重大/难回头的方向动手前用一个独立 sub-agent（拿 gstack 提炼、务实标定的审查框架）审一遍**。
不是"让 CEO 自审"、不是堆一堆"别犯错"的规则。方法论借 **gstack（Garry Tan / YC，MIT）**，标定到"小公司把一个真实的小东西做出来上线"，结构是 **doer≠judge**。

这是**六轮纠偏收窄**后的产物。每一次纠偏本身就是这个项目对"给 AI agent 写判断力该怎么做"的方法论——比最终代码更值得讨论。**并且：真跑 e2e 发现了设计与真实行为的一个 gap（见 §4）。**

---

## 1. 起点与背景

- **Foundagent = 零人公司**：AI 自主创办并运营公司。四层：信息层（company memory）/ 编排层（Goal + Hub）/ 执行层（5 个常驻 agent）/ 外设层。
- **CEO** = 执行层顶端的**持久化、可 resume 的 `claude -p`（headless）session**，只 **think + dispatch，不亲自干活**（连 docker.sock 都不给）。靠 wake/sleep 循环：被 heartbeat 或 inbox 事件（goal DONE/KILLED）唤醒。
- **改动前**：charter 几乎全是**机制**，只挂一个 `send-goal` skill；"该追什么、怎么排、什么时候动"这些真正的**判断几乎是空的**。
- **任务**：给 CEO 加判断力 skill 和 prompt。团队信条：**判断力 = skill/hook，不是堆 prompt**。

---

## 2. 六轮纠偏（讨论重点）

| 轮 | 用户的纠偏 | 沉淀的原则 |
|---|---|---|
| 1 | "你也是 LLM，给它写泛泛的 skill = 它自己也会 = 没写" | **三道检验**：①系统特定 ②要压制的 LLM 默认 ③非平凡取舍。泛泛=删。 |
| 2 | "CEO 是 `claude -p`，本身不带回复/问问题" | headless 下"问用户/退回人审"是**物理上不存在的通道**，为它写限制无意义。 |
| 3 | "别为没发生过的事加限制，你自己都不确定它会犯" | **赋能 > 限制**。防御性条目 **observation-driven**：真实运营暴露了才补，否则押后。 |
| 4 | "Agent 自身的 skill ≠ 人机交互 skill；让它发挥所长（做决策）→ 喂方法论（创业方法论）" | 从"防御"彻底转向**赋能一套真实创业方法论**。可搜 gstack。 |
| 5 | "V5 试过 gstack，太严——按 YC 十亿级要求，我们没那么大，会卡死落不了地" | **折中标定**：默认 SCOPE REDUCTION、门槛=真实小痛点+可验证+可落地、双向门=防卡死总开关。 |
| 6 | "自审不如让 sub-agent 以独立视角审" | **doer≠judge**：CEO 提方向、独立 sub-agent 审。gstack 的审查姿态本就是写给"审查者"的。CEO 用 Task 起 `general-purpose` sub-agent（**轻路径**）。 |

**关键收尾（防卡死）**：不是每个方向都召 critic。**双向门原则同时决定"要不要审"和"审多严"**——可逆小方向直接发（错了 KILL），只有大/难回头的才召独立审。

方法论源头 gstack：`office-hours`（YC 六问）+ `plan-ceo-review`（四 scope 模式 + "How Great CEOs Think" 认知模式，含 Bezos 双向门/70% 决策）。三步改造：① 剥交互层 ② 砍 YC 严苛标定 ③ 倒成自治/doer≠judge。

---

## 3. 最终交付（PR #198）

- `agents/assets/skills/decide-direction/SKILL.md` — CEO 侧决策流：最窄切入 → 双向门（可逆就 70% 直接发）→ 只有大/难回头才召审 → `GO/RESHAPE/DROP`。CEO 仍是 decider。
- `agents/assets/skills/decide-direction/references/direction-critic.md` — critic 审查 brief（CEO 用 `Agent` 工具传给 sub-agent），务实标定（砍了 desperate/10-star/future-fit）。
- `agents/assets/ceo-charter.md` +1 段顶层务实取向；`agents/ceo.yaml` 挂载；测试断言更新。
- **刻意不做**：防御性"别做 X"条目——等真实运营暴露再补。
- 验证（当时）：37 单测绿 + trellis-check AC1–AC5 全过。

---

## 4. ⭐ e2e 验证结果（阶段 7 真跑，2026-07-01）

> 方法：容器内两轮真实 `claude -p` wake（`foundagent/cua-agent:latest` 镜像 + 真 `CLAUDE_CODE_OAUTH_TOKEN`，物化 skills 后跑真 LLM）。这是单测覆盖不到的部分。

### ✅ 判断力本身：真生效
- **物化在真容器生效**：`decide-direction` + `send-goal` + `direction-critic.md` 都落到 `/home/kasm-user/.claude/`。
- **CEO 真的在用这套框架**（两轮都验证）：
  - 输出直接用它的语言——*"clear pain, clear user, **shippable in days, two-way door**"*、MVP scope、**pilot-first**。
  - **务实标定生效**：两轮都选**小而能落地**的方向。big-bet 那轮没直接砸一个月，而是*"先上 single-view MVP 给 3 家 pilot，只有 pilot 主动回来才付费上线"*。
  - 双向门防卡死、结果后决策（solid→build / gap→**KILL**）、Goal 写得务实自包含带 `--accept` —— 都对。

### ✅ 独立审也落地了（doer≠judge 一直在工作）
CEO **每轮都起了独立 sub-agent** 拿 `direction-critic.md` 审——stream-json 抓到 `Agent` 工具调用 2 次，rubric 路径就在 sub-agent 的 input 里（命中 6 次）。CEO 自己不审，交给一个 fresh sub-agent，用它返回的 `GO/RESHAPE/DROP` 定夺。**设计里的"轻路径"（CEO 自觉起 sub-agent）真的 work，从第一轮就 work。**

### ⚠️ 真正的教训：一个测量 bug 让我误判了三轮
我一度得出"独立审没触发 → CEO 退化自审 → 轻路径不可靠 → 该上结构强制"的结论——**全错，根因是我 grep 错了工具名**。这个 claude 版本（2.1.195）spawn sub-agent 的工具叫 **`Agent`**，我却一直 grep `"name":"Task"` → 永远 0 → 误判成"没起 critic"。当时 `direction-critic` / `GO` / `RESHAPE` / `DROP` 明明都在输出里（那**正是** sub-agent 的 prompt 和它的返回），我却读成了"CEO 自读自审"。

为这个**不存在的 gap**，我折腾了三轮改 skill（全审 / 动作硬门 / 明确措辞），还一度建议上"结构强制（动 Hub）"的重路径——全是白费，甚至差点动错架构。是用户从头坚持"还是能用 sub-agent"、并追问"是不是 skill 没写好"，才逼我回去查根因。

**真教训（比原先那条更重要）**：e2e 跑出"异常"时，**第一件事是自证测量本身对不对**（工具名、grep 关键词、断言逻辑），别急着归因模型能力 / 环境 / 架构。不同 claude 版本 spawn sub-agent 的工具名会变（这版是 `Agent`），这类基础事实要先核。**一个错误的观测比没有观测更危险——它会驱动你去做错误的"修复"。**

> 遗留待办：`decide-direction/SKILL.md` + charter 里写的是"call the **Task** tool"，实际工具名是 `Agent`。模型能自行映射（e2e 证明它照起了 sub-agent），但用词应更正为 `Agent` / "spawn a subagent" 以求准确。

---

## 5. 沉淀的方法论（可复用到其它角色）

见姊妹文档 `SOP-adding-roles-and-skills.md`（8 阶段 + 反模式速查表）。核心五条：
1. 给 LLM agent 写 skill 不能泛泛（三道检验）。
2. 赋能 > 限制；防御限制 observation-driven。
3. judgment 靠喂真实方法论（gstack），但需剥交互层 / 砍 YC 严苛 / 倒成自治。
4. doer≠judge 用独立审——e2e 证明**轻路径（CEO 自觉起 sub-agent）真的 work**；别把"没观测到"当成"不 work"（见 §4 测量 bug）。
5. 双向门 = 防卡死总开关。
6. **接线对 ≠ 有效：必须真跑**（阶段 7）——但真跑的**观测本身也要自证**（§4 的测量 bug：grep 错工具名，把 work 的东西误判成 gap，还差点驱动错误的架构改动）。

---

## 6. 待讨论 / 开放问题（带去公司）

1. **§4 的"gap"已澄清是测量 bug**——独立审（轻路径）本来就 work，无需修，也不用上 Hub 结构强制。剩下的只是把 `SKILL.md`/charter 里"Task tool"用词更正为 `Agent`。
2. **本地 vs 真服务器**（用户提的问题，已在 e2e 中回答）：**开发验证本地 Docker（`docker run` / `make up`）就够**——这次两轮真跑就是纯本地 Docker + token 跑的，没上服务器。**真实服务器留给"24/7 常驻真实运营"**（agent 是 long-lived，要一直醒着等 heartbeat/外部信号；真做生意+真外联+账号可扩展需要稳定常驻）。
3. **完整编排 e2e 还没跑**：这次是"CEO 单容器单 wake"聚焦真跑（绕过了 kasm 桌面/hub）。完整 `make up`（5 agent + hub + peripheral，CEO 派 Goal → worker 产物 → verifier 验收 → 回 CEO）这条零人闭环**尚未真跑**。
4. **其它角色**（builder/verifier/growth/researcher）判断力同样走这套 SOP，但都还没做，也都要真跑验证。

---

## 附：关键文件索引

- 实现：`agents/assets/skills/decide-direction/{SKILL.md, references/direction-critic.md}`、`agents/assets/ceo-charter.md`、`agents/ceo.yaml`
- 调研（gstack 实拉 + 三道检验逐条过筛 + 21 条清单）：`.trellis/tasks/06-28-role-ceo/research/ceo-skill-reuse.md`
- 规划三件套：`.trellis/tasks/06-28-role-ceo/{prd.md, design.md, implement.md}`
- 方法论源头（本地）：`~/.claude/skills/gstack/{office-hours,plan-ceo-review}/SKILL.md`
- 真跑方式：`docker run --env-file vm/.env.local ... foundagent/cua-agent:latest`（物化 + `claude -p` 一次 wake）；完整编排 `Makefile` (`make up`) + `docker-compose.yml`
</content>
