# CEO 判断力 — 设计（v2：gstack 提炼 + 独立 critic）

> 依据 `prd.md` + `research/ceo-skill-reuse.md` + gstack 方法论实拉（`~/.claude/skills/gstack/` 的 `office-hours` / `plan-ceo-review`，Garry Tan / YC，MIT）。
> ⚠️ v1（防御清单版：act-on-goal-result + send-goal 增强 + charter 防御短句）**已废**——那版在"防没观测到的失败"，违反纪律。本版是**赋能方法论 + 独立审**。

## 0. 收敛后的核心

CEO 判断力 = **务实地决定追什么，重大方向经独立 critic 审**。不是自审、不是"别犯错"清单。

- **方法论源头**：gstack（Garry Tan / YC，MIT）——`office-hours` 六问 + `plan-ceo-review` 四模式 + "How Great CEOs Think" cognitive patterns。
- **标定**：从"孵化十亿级 YC startup"放松到"务实小公司把一个真实的小东西做出来上线"。V5 教训：gstack 原味太严（desperate specificity / 10-star / maximum rigor），会把每个小想法都卡死、落不了地。
- **结构（doer≠judge）**：CEO 提方向（founder），独立 sub-agent 审（partner）。gstack 那套审查姿态（anti-sycophancy / take-a-position / pushback）本就是写给 partner 的，装独立 critic 比"CEO 自审"顺。

## 1. headless 约束（保留的系统事实）

CEO 跑 `claude -p`（`orchestration/agent_loop.py`），无交互端、**不能 spawn container worker**（那是 broker 的事）。但**能用 Task tool 起 session 内 sub-agent**——这是 CEO 一次 wake 内的思考辅助，不是 container 部门，不违反"不 spawn worker"。前提已核：`ceo.yaml` 无 `allowed-tools` 限制、`permission_mode: bypass`，故 CEO 具备 Task 工具。

## 2. 落点（这一版聚焦一条主线）

| # | 落点 | 内容 |
|---|---|---|
| 2.1 | `assets/ceo-charter.md` +1 段 | 最顶层取向：务实落地优先 + 双向门快速动 + 重大方向召独立审 |
| 2.2 | `assets/skills/decide-direction/SKILL.md` | CEO 侧：务实取向 + 双向门决策流 + 何时/如何召 critic + 用 verdict |
| 2.3 | `assets/skills/decide-direction/references/direction-critic.md` | critic 的审查 rubric（gstack 提炼·务实标定）；CEO 起 sub-agent 时作 prompt |
| 2.4 | `agents/ceo.yaml` + 测试 | 挂 `decide-direction`；物化测试断言 |

**押后（不做，等真实观测）**：`act-on-goal-result`、`send-goal` 防御增强、charter 一堆防御短句（15 信 ledger / 19 不预判 verifier 等）。都是"防没观测到的失败"，等 CEO 真跑出该类失误再针对性补。

## 3. charter 增量（2.1）

`## Principles` 后新增一段 `## How you decide what to pursue`（~4-6 行，最顶层取向）：

> 你是**务实的小公司 CEO**：默认把一个真实的小东西做出来上线（SCOPE REDUCTION），不追十亿级野心。发一个小 Goal 是**双向门**——可逆，错了能 KILL 回头，所以 70% 把握就去试，别卡死在"这够不够大"上。只有**投入大、难回头**的方向，才在动手前召一个**独立视角**审一遍（见 `decide-direction` skill）。你仍是 decider——critic 是顾问不是门神。

> 借自 gstack cognitive patterns（Bezos 双向门 + 70% 决策、Jobs focus-as-subtraction），Garry Tan/YC, MIT。

## 4. skill `decide-direction`（2.2）

**触发**：heartbeat 空闲评估 / 决定下一步追什么。

**`description`（对齐 heartbeat wake 措辞）**：
> How the CEO decides what to pursue, pragmatically. Use on an idle/heartbeat wake, or whenever you must choose what work to dispatch — to pick the smallest real thing worth shipping, judge whether it is reversible enough to just try, and pull in an independent reviewer before committing to a big or hard-to-reverse bet.ke y

**body（务实取向 + 决策流，~50-70 行，风格对齐 send-goal）**：
1. **取向**：务实小公司 CEO，找**能落地的最小真实价值**（SCOPE REDUCTION）；默认想着怎么把它**做出来上线**，不是它够不够大。
2. **产出方向候选**：最窄切入优先（gstack Q4：this-week 就能做出来、能让人真用上的最小版本）。
3. **双向门判断**（决定要不要召 critic，防卡死的核心）：可逆 / 小 → **直接发 Goal**（快，错了 KILL 回头）；投入大 / 难回头 → **召独立审**。（Bezos 双向门 + 70% 信息就够决策。）
4. **召独立审**：用 Task tool（`general-purpose` sub-agent）起一个 direction-critic，把方向候选**自包含**地丢给它（sub-agent 无共享上下文），审查 rubric 见 `references/direction-critic.md`。
5. **用 verdict**：critic 戳出的是真问题（空想、无真信号、没落地路径）就改 / 弃；但 critic 是**务实标定的顾问不是门神**——你仍是 decider。

## 5. reference `direction-critic.md`（2.3）

critic 的任务 prompt（CEO 用 Task tool 传入 sub-agent 的完整指令）。gstack 提炼·务实标定：

- **角色**：一个独立的**务实产品顾问**（明确 NOT 十亿级 YC 合伙人）。fresh 视角，只审这一个方向候选。
- **姿态**（gstack anti-sycophancy，保留——这是审查者该有的）：take a position，别说"挺有意思"；分清**真信号 vs 空想**（gstack: "interest is not demand, behavior counts" / "watch, don't demo"）。
- **4 问**（office-hours 六问 → 务实标定）：① 真需求（有具体的人/场景会真的*用*吗，行为 > 我觉得）② 现状增量（现在怎么凑合、你明显好在哪）③ 最窄切入（这几天能做出来、能让人真用上的最小版本）④ 真信号非空想（靠什么验证，不是拍脑袋——可派个小 Goal 去验）。**按成熟度只问相关的**（gstack smart-routing），早期想法重点 ①③，别全套拷问。
- **务实门槛（对治太严）**：门槛 = "**真实小痛点 + 能验证有人用 + 能落地**"，不是"够大 / desperate / 10-star"。双向门方向从宽放行。
- **verdict 格式**：`GO` / `RESHAPE`（怎么改）/ `DROP`（为什么）+ 一句最关键理由。
- **署名**：借自 gstack `office-hours` + `plan-ceo-review`（Garry Tan/YC, MIT）。

## 6. 边界 / 测试 / 兼容

- **零 .py 逻辑改动**：只新增 skill + reference 文件、改 `ceo.yaml` 一行、charter 加一段、改一条测试断言。
- **Task-tool sub-agent**：用 `general-purpose` + 传入 rubric，**不新建 agent 定义**（最轻）。前提已核（§1）。
- **测试**：`test_resident_loadout.py::test_ceo_gets_send_goal` → 断言 `info.skills` 含 `decide-direction`，并 assert `SKILL.md` + `references/direction-critic.md` 物化存在。LLM 的审查行为靠 e2e / 真实运营验证，单测不覆盖。
- **物化**：`loadout.materialize` 复制整个 skill 目录（含 `references/`）——需确认 reference 子目录一并复制（若只复制 SKILL.md 则调整）。
- **回滚**：删 `decide-direction` 目录 + 还原 `ceo.yaml` / charter / 测试。

## 7. 待确认（review gate）

1. **选择性审**：只在"投入大 / 难回头"方向召 critic，双向门小方向直接发 —— design 取此（防卡死核心）。
2. **critic = `general-purpose` sub-agent + 传入 rubric**（不新建 agent 定义）—— design 取此，最轻。
3. **押后** `act-on-goal-result` / `send-goal` 防御增强 / charter 防御短句 —— 确认。
4. skill 命名 `decide-direction` —— 确认或改。
</content>
