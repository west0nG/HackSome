# Agent Handbook — 技术设计

> 任务：`.trellis/tasks/06-29-agent-handbook`。范围 = **Phase A（Hub 机制增量）+ Phase B（R1–R4 文案）+ e2e**（见 prd）。
> 核心设计决策（用户 2026-06-30）：**判定标准只交给 verifier、对 worker 蒙眼**（防 Goodhart）。
> 机制基线：child② Hub 已交付（`orchestration/hub.py`，`spec/backend/resident-agent-contracts.md`）。

## 0. 设计原则：worker 蒙眼判定标准

worker 知道 proof → 为通过检查做表面工作（teaching-to-the-test）。所以：

- **goal 名词**（精确结果）→ 给 worker，锚定「做什么」、防 goal drift。
- **acceptance criteria**（怎么验）→ caller 写、**只给 verifier**、worker 结构性拿不到 → worker 专注把事做好。
- 两条结构强制、不靠自觉：doer≠judge 由 Hub `from`-gate；worker 蒙眼由 `_work_ime` 只携带 intent。

## 1. Phase A — Hub 机制增量（verifier-only accept 通道）

**目标**：caller `send` 时可附一份可选的 `accept`，全程对 worker 蒙眼、只到 verifier。守 IME §2.3（不加信封字段，accept 走 DISPATCH body 分段）。

改动点（约 5 文件 + 测试，**契约级最小**）：

| 文件 | 改法 | 兼容性 |
|---|---|---|
| `orchestration/messaging.py` | `send(to, intent, *, accept=None, reply_to=None)`；body = `DISPATCH …:: {intent}`，若 accept 追加分段（见下）。CLI 加 `--accept` | accept 默认 None → 旧调用 body 不变 |
| `orchestration/hub.py` `parse_body` | DISPATCH 解析：从 body 切出可选 accept，返回 dict 多一个 `"accept"` 键（无则 None） | 无 accept 分段 → accept=None，旧 DISPATCH 照常 |
| `orchestration/hub.py` dispatch handler | 把 `parsed["accept"]` 透传给 `ledger.add_goal(..., accept=…)` | — |
| `orchestration/goal_ledger.py` `add_goal` | 新增可选参 `accept=None`，存进 goal dict `goal["accept"]` | 默认 None，现有 142 测试不传 → 不破 |
| `orchestration/hub.py` `_verify_ime` | 新增可选参 `accept`；非空则在 verifier prompt 注入 `ACCEPTANCE CRITERIA (judge against THIS): …`。调用处（RUNNING→VERIFYING）读 `goal.get("accept")` 传入 | 默认 None → 旧 prompt 不变 |
| `orchestration/hub.py` `_work_ime` | **不改** —— worker 工单永远只含 intent，accept 不出现 | worker 蒙眼 |
| `agents/assets/verifier-charter.md` | 加一句：有 ACCEPTANCE CRITERIA 按它判；没有才从 goal 自推导 | — |

**DISPATCH body 编码**（守 §2.3：一切进 body，IME 仍 5 字段）：

```
DISPATCH to=<dept> reply_to=<caller> :: <intent>
===ACCEPT===
<verifier-only acceptance criteria, 可多行>
```

- `parse_body`：先按现有 `_DISPATCH_RE` 取 to/reply_to/intent；再对 group(3) 按 `\n===ACCEPT===\n` 分割——
  前段 = intent、后段 = accept（无分隔符则 accept=None）。delimiter 选不易撞用户文本的串，撞了走转义/兜底（实现时定）。
- 红线：**不**新增 IME 信封字段；accept 只活在「DISPATCH IME body（Hub inbox）」+「ledger goal.accept」+「verify IME body（→verifier）」三处，
  worker 的 `_work_ime` 不在其中 → worker 无从获取。

**信息可见性矩阵**（设计要点）：

| | goal intent | accept criteria |
|---|---|---|
| caller | 写 | 写 |
| Hub / ledger | 存转 | 存转 |
| **worker** | ✅ 见 | ❌ 结构性看不到 |
| verifier | ✅ 见 | ✅ 见（有则按它判） |

## 2. Phase B 载体分层：charter（prompt）↔ skill（渐进式披露）

「同时进 prompt 和其他环节」= 两层分工，避免把整套协议塞进每个 charter（现状重复根源）：

| 层 | 载体 | 装什么 | 何时被读 |
|---|---|---|---|
| 常驻（prompt） | 各角色 charter（`--append-system-prompt`） | 角色身份/边界 + **一句指针**「收到 Goal / 要派活或上报时，遵循 `goal-protocol` skill」 | 每次 wake 在 system prompt |
| 详尽（skill） | `goal-protocol/SKILL.md` + `reference/` | 完整回路：caller 发 Goal(+accept)、worker 收/做好/report、Goal 写法规范 | frontmatter `description` 触发，按需下钻 |

`company-state` skill 已验证「charter 引用 + skill 详写」模式容器内可工作。这正是 R3 去重的落点。

## 3. 公民 skill 结构 —— 两个 skill（用户 2026-06-30 定）

> **写人话。** 内容是给真人/agent 读的自然英文散文，不是术语碎片。篇幅短 → Goal 写法直接写进 skill 本体，**不开 reference 子文件**。仿 `company-state/SKILL.md` 质感。
>
> **拆两个单一职责 skill**（发 Goal / 做 Goal 是两个时刻、两个受众 → 触发更准、按角色最小装载）：
> - `agents/assets/skills/send-goal/SKILL.md` —— 「What a Goal is」+「Sending a Goal」（caller 侧 = R1）。装到 **CEO**。
> - `agents/assets/skills/receive-goal/SKILL.md` —— 「What a Goal is」+「Doing a Goal」（worker 侧 = R2）。装到 **builder/growth/researcher**。
> - 共享的「What a Goal is」一句话两边各写一遍（一句重复，胜过耦合）。本版部门只收不发；递归落地时部门再加 `send-goal`。
>
> 下面三段是两 skill 的合并内容（send-goal=段1+2，receive-goal=段1+3）：

**frontmatter**（触发覆盖三时机）：

```yaml
---
name: goal-protocol
description: How agents hand work to each other. Use this whenever you receive a
  Goal in your inbox, want to send a Goal to another department, or have finished a
  Goal and need to report it back.
---
```

**body 三段（人话、逻辑顺）：**

1. **What a Goal is（一句话奠基）**：一个 Goal 是「你想要做成的一件事（一个结果）」。有人把 Goal 发给你、你去把它做成；或你把 Goal 发给别人、让别人做成。

2. **Sending a Goal to someone（caller 侧 = R1 写法）** —— 把 R1 直接写在这：
   - `python3 -m orchestration.messaging send --to <department> --intent "<the goal>"`
   - 写好一个 Goal（人话讲清，配 1 组**好/坏对照例**）：
     - **真实、具体、可执行**——说清你要的**结果**，不是模糊愿望、也不是分步指令。
     - **给足背景**：为什么需要这件事、它属于哪个更大的目标、相关上下文——全写进 `--intent`。执行者只看得到你写的这些，背景越全、做得越对。假设这可能是一件很大的事，信息别吝啬。
   - **可选**：要让验收有明确标准时，加 `--accept "<how someone should check it's truly done>"`。这条**只给验收方**、执行者看不到——所以放心把检查口径写具体。
   - `reply_to` 默认你自己（结果回到你），要改才加 `--reply-to`。
   - 红线：goal+背景进 `--intent`、验收口径进 `--accept`，别自己发明别的字段。

3. **Doing a Goal someone sent you（worker 侧 = R2）** —— 简单直接：
   - 读懂收到的 Goal 和它的背景（body 里有 `goal_id`，report 时带上）。
   - **把这件事做好。** 产物可能是一份成果，也可能是一次对外操作（发邮件、上线、发帖…）——做真的，不是描述。
     （有值得留存的公司状态就用 `company-state` skill 记一笔；但这不是每个 Goal 的必经步骤。）
   - 做完报一句完成：`python3 -m orchestration.messaging report --goal-id <id> --text "<what you did>"`。
   - 就到这。验收由别人来做，你不用评判自己——**skill 里不出现"自评/判定标准"任何字样**（执行者结构上也接触不到 accept）。
   - HEARTBEAT 唤醒（没有新消息）：看一眼有没有待办，没有就一行带过、停下。

> 取舍：原 §0「worker 蒙眼」是**内部机制语言**，落到 SKILL.md 时**只表现为"skill 不提验收标准"**——
> 不写"你被蒙眼了""别揣测标准"这类反而把"标准"塞进它脑子的句子。蒙眼靠 Phase A 的 `_work_ime` 结构保证，不靠 skill 说教。

## 4. charter 去重（R3）

builder / growth / researcher 三个 charter 的「When you receive a task: … Persist … report …」整段（各自第 10–23 行）逐字重复，删掉，换成一句引用（人话、不提自评/标准）：

```
When you receive a Goal, follow the `goal-protocol` skill: understand the goal and
its context, do the real work to achieve it, then report that you're done.
```

charter 只留**角色独有**内容（身份段 + heartbeat 行）；placeholder 抬头注释保留（真内容仍归 role-library）。

## 5. yaml 接线

各参与角色 yaml 的 `skills:` 加 `assets/skills/goal-protocol`：

- `builder.yaml` / `growth.yaml`：已有 `skills: [company-state]` → 追加 `goal-protocol`。
- `researcher.yaml` / `ceo.yaml`：**当前无 `skills:` 字段** → 新增（researcher: `company-state`+`goal-protocol`；CEO: 纯 caller，至少 `goal-protocol`，company-state 只读按 ceo-charter 现状决定）。
- verifier / company-operator：本版不动（verifier 语义特殊——它收 accept、报 verdict；不纳入公民 skill）。

零 `.py` 改动——`agent_loop` loadout 已支持 `skills:`（`builder.yaml`/`company-operator.yaml` 已在用）。

## 6. 验证与 e2e

- **单测**：现 142 基线（`pytest orchestration/tests/`）。Phase A 加新单测：messaging body 带 accept 分段；`parse_body` 解 accept（有/无）；
  `add_goal` 存 accept；`_verify_ime` 含/不含 criteria；`_work_ime` **永不含** accept（蒙眼断言，AC0 关键）。所有改动向后兼容 → 142 不回归。
- **AC4 真实零人 e2e**：复用 compose + `companies/e2e-*`，跑：caller `send --intent --accept` → 经 Hub → builder 收（**工单里无 criteria**）、
  把事做好落 `/company`、report work-done → Hub 转 verifier（**verify 工单含 criteria**）→ verdict → done → 终态回 caller inbox。
  优先看 `test_hub_e2e.py` 能否承载断言；真容器 run 需要新夹具就最小化（一个 goaltest company）。

## 7. 风险 / 决策记录

- **改 child② 的 Hub**：用户接受（任务标题含「Goal 数据契约」，accept 即数据契约扩展）。改动向后兼容、§2.3 安全、加测试守回归。
- **accept 可选 + 自推导兜底**：B 是 A 的超集，不丢能力；强制性留后续。
- **不暴露机制细节给 agent**：agent 只认 `send/receive/report(+--accept)`；DISPATCH/REPORT/ledger 状态机对 agent 透明（呼应「只暴露 4–5 原语」）。
- **delimiter 撞文本（code-review 抓出，已修）**：in-band fence + rpartition 无法区分「结构 fence」与「payload 里的 fence」——
  若 accept 含 fence 会**泄漏**给 worker（违反蒙眼），若 intent 含 fence 且无 accept 会**截断**。修法 = `send` 端 **fail-loud 守卫**：
  payload 含 `ACCEPT_DELIM` 直接 `ValueError`，保证 body 里至多一个结构 fence（存在 ⟺ 有 accept）。单测锁两条泄漏/截断场景。
- **与 role-library 不冲突**：本任务写横切公民 skill + Goal 数据契约，是 role-library（角色专属 skill）的前置；charter 去重后留的身份段正是 role-library 填真内容处。
