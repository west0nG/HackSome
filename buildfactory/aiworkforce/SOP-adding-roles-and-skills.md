# SOP：给 Foundagent 加"员工/技能"

> 标准作业流程。适用于：**新增一个角色 agent**（新员工），或**给现有角色加一个 skill / charter 能力**（给员工加技能）。
> 这份 SOP 是从"给 CEO 加判断力"那次（见 `ceo-judgment-design-journey.md`）抽象出来的——那次六轮纠偏，每一轮都是这里的一条原则的来源。
> 状态：**v1，草案**。带去讨论；定稿后建议固化进 `.trellis/spec/guides/`（成为开发时自动生效的规范），并可进一步做成一个 agent 能执行的 skill（→ 零人公司自我扩展）。

---

## 核心信条（贯穿全程）

1. **目标 agent 本身是 LLM。给它写泛泛的东西 = 没写。**
2. **判断力靠喂真实方法论，不靠堆告诫。** 先找现成的（开源 / gstack），别闭门造。
3. **赋能 > 限制。** 给它不知道的能力/方法；别为没发生过的失败预先设规矩。
4. **接线对 ≠ 有效。** 单测只证物化正确；判断力必须真跑一轮才算数。

---

## 流程（8 阶段，每阶段带"门禁"——过不了不往下走）

### 阶段 0 — 定范围 + 摸现状
- 这是**新角色**，还是**给现有角色加能力**？
- 摸现状：这个角色现在的 charter / skills 是什么？（`agents/<role>.yaml` + `assets/`）**别重做已有的。**
- **门禁**：能用一句话说清"要补的是什么判断/能力"，且确认它现在确实缺。

### 阶段 1 — Research 先行（别闭门造）
- 先找现成可复用的：`obra/superpowers`、`anthropics/skills`、**`~/.claude/skills/gstack/`（Garry Tan/YC 创业方法论）**、领域开源。
- **实拉真实内容**审，别信二手描述（README / awesome-list 有水分）。
- **门禁**：能回答"这块开源有没有现成可直接用的？还是本质是 gap 必须自写？"（多数判断力类是 gap，但借得到**子句和方法论骨架**。）
> 坑（轮 1）：一上来自己造 21 条"判断清单"，全是泛泛常识。

### 阶段 2 — 过"三道检验"筛每一条内容
一条 skill / charter 子句，只有满足**至少一项**才留，否则删：
- **① 系统/环境特定**：LLM 训练里不可能有的本系统机制（有哪些 role、Goal 协议、`messaging send`、DONE/KILLED、`/company` memory、验收分权）。
- **② 要专门压制的 LLM 默认**：反 helpful-assistant（不退回人审、不 hedge、heartbeat 没事闭嘴、自己拍板）。
- **③ 非平凡的具体取舍**：带阈值/反例的判断信号，不是"权衡机会成本""保持客观"这类自带美德。
- **门禁**：逐条能指认过哪道。指不出 = 泛泛 = 删。

### 阶段 3 — 赋能 vs 限制，分开处理
- **赋能**（给它不知道的系统事实/方法）→ **写**。
- **防御限制**（防某种假想的判断失误：别 hedge / 别 re-litigate / 别原样重发…）→ **只有真实运营观测到那个失误才补**，否则**押后**。
- **门禁**：清单里没有"防没发生过的事"的条目。
> 坑（轮 2-3）：为 headless 里根本不存在的"退回人审"通道写限制；为"我自己都不确定 LLM 会不会犯"的失败写规矩。

### 阶段 4 — 标定到我们的体量
- 借来的方法论（尤其 gstack 是按**十亿级 YC startup** 标定的）必须 **re-calibrate** 到"**小公司把一个真实的小东西做出来上线**"。
- 判断力的目标函数是"够不够真、能不能落地"，不是"够不够大"。砍掉 desperate-specificity / 10-star / future-fit / maximum-rigor。
- **双向门是防卡死总开关**：可逆的小决定快速动（70% 把握就够），只有大/难回头的才慢下来。
- **门禁**：这套判断力不会把每个小想法都卡死、落不了地。
> 坑（轮 5）：V5 直接用 gstack 原味，太严，什么都落不了地。

### 阶段 5 — 决定落点（charter / skill / reference）
- **charter**（每次 wake 用 `--append-system-prompt` 注入）→ 顶层取向、身份级、**精简**（每 wake 都在场，token 敏感）。
- **skill**（`resident_loadout` 从同一份角色 YAML 物化；Claude Code 落到 `~/.claude/skills/`，Codex 落到 `~/.agents/skills/`）→ 某类场景才展开的方法/清单。两边共用同一个 skill 目录，不做 provider 特供副本。
  - 顶层宿主 `SKILL.md` 是唯一可发现入口。vendored 控制层留在宿主目录内时命名为 `upstream-SKILL.md`，由宿主显式路由；不要让递归扫描把它注册成第二个 skill。
  - frontmatter 只放 `name` / `description`。`description` 要同时说清“做什么”和“什么时候用”，碰撞项还要写出边界；解析后必须是规范化单行文本。普通项以 120–180 个 Unicode 字符为目标，单项硬上限 200，同一角色的 description 总量硬上限 2000。
- **reference**（skill 的 `references/` 子目录，`copytree` 一起物化）→ 给 sub-agent 的 rubric / 模板。
- **Foundagent 硬约束**：
  - **零注释**（07-10 when-idle-rewrite 用户拍板）：SKILL.md / charter 是 agent **全文可见**的——HTML 注释一样进上下文。设计注记、机制接线、失败史（"为什么这么写"）一律落 task 工件与 git history，**不落资产文件**；把机制披露给 agent 本人违反"prompt 只定向不披露机制"（issue #207）。出处 attribution 的承载方式见 07-10-skill-source-attribution-separation。
  - **headless**：agent 是 `claude -p`，无交互端——**别写任何假设"问用户 / 等回复"的措辞**。
  - **声明式扩展**：加角色/技能 = 改 `<role>.yaml` + 加 skill 文件，**零 .py 逻辑改动**（沿用 loadout）。
  - **测组合别改基线**：想试"某 skill 关掉 / 只开一部分 / 裸 agent"，写公司 overlay（`state/<company>/config/loadout.yaml`，见 spec `loadout-overlay-contracts.md`），跑前 `make loadout-check`；**`<role>.yaml` 永远保持全量能力基线**，不为实验改它。
  - **doer≠judge**：需要独立判断的地方（审方向、验收），用**独立 sub-agent**（CEO 用 Task tool 起 `general-purpose`），**别让 agent 自审**——自己想的自己审会放水。
- **门禁**：每条内容都落到了对的载体；无 headless 违规。
> 坑（轮 4、6）：把"agent↔人类交互"的东西当判断力写；让 agent 自审而不是独立审。

### 阶段 6 — 实现 + 单测
- 加 `assets/skills/<name>/SKILL.md`（+ `references/`）、改 `<role>.yaml` 的 `skills:`、按需加 charter 段。
- 更新 `agent/tests/test_resident_loadout.py`：断言该角色物化了新 skill（+ `references/` 子目录一起进去）。
- 更新或扩展 `agent/tests/test_skill_catalog.py`：锁定角色数量、description 预算/语义边界、每棵树唯一的顶层 `SKILL.md`，以及 vendored `upstream-SKILL.md` 的完整性。
- 跑：`.venv-cua/bin/python -m pytest agent/tests/ -q`（系统 python 无 pytest/yaml）。
- **门禁**：测试绿；借用的开源内容标了来源 + 许可证。
> 坑（07-09）：skill 随"铺轨"类任务交付时容易绕过本 SOP、漏掉接线——provision-ga4
> 交付三天无人可见，deploy-site 初版同样漏接。**skill 落盘 ≠ fleet 可见**：凡新增
> `assets/skills/<name>/`，同一次交付必须改 `<role>.yaml` 的 `skills:` + 同步两个
> loadout 测试断言，缺一即为未交付。

### 阶段 7 — ⚠️ 真跑验证（e2e）—— 不能跳
- **单测只证"skill 被正确物化"，证不了这个角色真的会用它、真的做出好判断。**
- description 或 skill 路由有变化时，用固定版本的 Claude Code 与 Codex 分别跑代表性高风险碰撞场景；同一套目录应暴露同一份顶层 catalog，内部 `upstream-SKILL.md` 不应出现在发现列表里。
- `make up` 起 docker-compose（5 agent + hub + peripheral），触发一次真实 wake（`vm/seed_goal.py` / `orchestration/tests/test_e2e_real_llm.py`），观察：agent 真的加载并用了这个 skill 吗？判断/产出符合预期吗？（若涉及 sub-agent：它真的起来了吗、消耗哪份凭证、成本多少？）
- **本地 Docker 就够**（需 `vm/.env.local` 的 `CLAUDE_CODE_OAUTH_TOKEN`）；真实服务器留给"24/7 常驻真实运营"，不是开发验证的前提。
- **门禁**：至少一轮真实运行证明这个能力**在真环境里生效**。
> 当前 gap：CEO 判断力（PR #198）**尚未做这一步**——这是现在最该补的。

### 阶段 8 — 迭代
- 先写出来试试，别追求一次到位。真实运营暴露某类失误后，再回阶段 3 针对性补一条（observation-driven）。

---

## 一页速查（反模式清单）

| 别做 | 该做 | 来源 |
|---|---|---|
| 给 LLM 写泛泛的美德/常识 | 过三道检验，只写它自带能力之外的 | 轮 1 |
| 为 headless 不存在的通道（问用户）写限制 | 认清运行环境事实，别假设交互端 | 轮 2 |
| 防"没观测到、你自己都不确定"的失败 | 赋能优先；防御限制等真实暴露再补 | 轮 3 |
| 把"跟人类交互"的技能当判断力 | 发挥 agent 所长（做决策）→ 喂方法论 | 轮 4 |
| 照搬 YC 级严苛方法论 | 标定到"小公司把真实小东西做出来上线" | 轮 5 |
| 让 agent 自审自己的产出 | doer≠judge，独立 sub-agent 审 | 轮 6 |
| 单测绿就算完成 | 必须 `make up` 真跑一轮验证 | 当前 gap |

---

## 归宿建议（讨论后决定）

1. **固化为规范**：定稿后移入 `.trellis/spec/guides/`，让 `trellis-before-dev` 在每次开发前自动注入——真正做到"以后都遵循"。
2. **做成 agent skill**：把这份 SOP 写成一个 SKILL.md（触发词如"加个新角色/给 X 加技能"），先给开发用；**最终让 Foundagent 自己的某个角色（HR？CEO？）能执行它** —— 零人公司自我扩展员工与技能。这是这份 SOP 的终点形态。
</content>
