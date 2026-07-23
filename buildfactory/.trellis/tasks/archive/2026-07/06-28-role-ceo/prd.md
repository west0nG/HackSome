# CEO 判断力（务实创业方法论 + 独立 critic）

> 父任务：`../06-28-role-library`。交付 CEO 的**判断力**层。
> ⚠️ 边界：唤醒循环机制（inbox / heartbeat / Hub / `--resume`）归**已 done** 的 ceo-loop（PR #195）；本任务只碰 **charter 内容 + skill loadout**——声明式，**零 .py 逻辑改动**，仅物化测试断言更新。
> ⚠️ **v2 修订**：从"判断力 = 一堆自审 / 防御条目"改为"**务实创业方法论（gstack 提炼）+ 重大方向经独立 sub-agent critic 审（doer≠judge）**"。防御性条目全押后。

## 现状（已存在，不重做）

- CEO = 常驻 `claude -p` session（`agents/ceo.yaml`），charter `assets/ceo-charter.md`，挂 1 个 skill `send-goal`。
- charter 已覆盖：机制（wake/sleep、`messaging send`、DONE/KILLED、`/company`）+ 部分判断（heartbeat 没事就一句话停）。
- 物化机制 `agent/resident_loadout.py` 容器启动把 yaml 声明的 skills 物化进 `~/.claude/skills/`。

## Goal

给 CEO 一套**务实的"决定追什么"判断力**：

- **内核 = gstack（Garry Tan / YC，MIT）创业方法论提炼**——`office-hours` 六问 + `plan-ceo-review` 四模式 + "How Great CEOs Think" cognitive patterns，**标定到"小公司把一个真实的小东西做出来上线"**（V5 教训：gstack 原味按十亿级 YC startup 严苛度要求，会把每个小想法卡死、落不了地）。
- **结构 = doer≠judge**：CEO 提方向（founder），**重大方向**动手前用 Task tool 起一个**独立 sub-agent**（拿务实标定的审查框架）审（partner）。

**核心纪律**：**赋能（给方法论 / 能力）> 限制（防假想失败）**。只写 ①系统特定 / ②要压制的 LLM 默认 / ③gstack 提炼的非平凡方法论；**防御"没观测到的失败"一律押后**（见 `research/ceo-skill-reuse.md` 的教训）。

## Requirements

- **R1 charter 顶层取向一段**：务实落地优先（SCOPE REDUCTION）+ 双向门快速动（可逆就试、70% 把握够）+ 重大方向召独立审。
- **R2 skill `decide-direction`**（CEO 侧，触发 heartbeat / 决定追什么）：务实取向 + 最窄切入 + 双向门决策（要不要召 critic）+ 如何召 critic + 用 verdict。
- **R3 reference `decide-direction/references/direction-critic.md`**：critic 审查 rubric（gstack 提炼·务实标定：务实 4 问 + 反自嗨姿态 + 务实门槛 + `GO/RESHAPE/DROP` verdict）。CEO 用 Task tool 传入 `general-purpose` sub-agent。
- **R4 选择性审 + 务实门槛（防卡死）**：双向门决定要不要召 critic；critic 门槛 = 真实小痛点 + 能验证有人用 + 能落地，**非 YC 严苛**（desperate / 10-star / future-fit 已砍）。
- **R5 gstack 借用署名**（MIT，Garry Tan / YC）。
- **R6 声明式**：零 .py 逻辑改动；仅 `agent/tests/test_resident_loadout.py` 断言更新。

## Acceptance Criteria

- [ ] **AC1**：`ceo.yaml` skills 挂 `send-goal` + `decide-direction`；`test_resident_loadout` 断言含 `decide-direction` 且 `SKILL.md` + `references/direction-critic.md` 物化存在；`pytest` 绿。
- [ ] **AC2（纪律）**：skill / critic 每条内容能指认来源（①/②/③ 或 gstack 提炼），**无泛泛常识、无"防没观测失败"的防御条目**。
- [ ] **AC3（务实标定）**：critic 门槛可核为"真实小痛点 + 能验证 + 能落地"，YC 严苛件（desperate-specificity / 10-star / future-fit / maximum-rigor）已砍；双向门小方向明确"直接发、不召 critic"。
- [ ] **AC4**：gstack 借用标来源 + 许可证。
- [ ] **AC5**：风格与现有 skill 一致（祈使 / 具体 / 渐进披露）；决策流可独立跑通（CEO 产出候选 → 双向门判断 → 起 sub-agent 审 → 用 verdict，路径完整、headless 不假设交互端）。

## Out of Scope（押后 / 不做）

- **押后**（等真实运营暴露某类失误再针对补）：`act-on-goal-result`（结果后决策防御清单）、`send-goal` 分派防御增强、charter 防御短句。
- 唤醒机制 / inbox / Hub（已 done）；其他角色；prompt "最优化"（第一版立可迭代骨架）。
- 新建自定义 `direction-critic` agent 定义（用 `general-purpose`，最轻）。

## 依据

- `research/ceo-skill-reuse.md`（本任务）+ gstack 实拉（`~/.claude/skills/gstack/` 的 `office-hours` / `plan-ceo-review`）。
- 折中标定（V5 gstack 太严教训）+ 独立 critic 结构（doer≠judge）：本 session 讨论收敛。
</content>
