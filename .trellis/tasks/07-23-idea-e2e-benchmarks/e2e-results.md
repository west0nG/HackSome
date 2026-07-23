# Idea Workflow E2E 结果

## 结论

当前 Idea-only Workflow 已证明可以稳定执行大规模并行 Session、持久化完整
Prompt/输出/决策链，并从真实赛题走到可验证的 Idea Card。但本轮的主要问题不是
运行稳定性，而是质量门槛过松：

- 米哈游 16 个 Problem 全部通过 Gateway；
- 105 个 Idea 只有 4 个被 Red Team 淘汰；
- 最终 101 张 Idea Card 中存在大量近重复方案和边缘赛题方案。

这说明“动态数量、只淘汰不排名”的产品原则可以保留，但 `pass` 的绝对质量标准
需要明显提高。当前 Gateway 更接近“有证据就通过”，Red Team 更接近“有 User
Flow 就通过”，还没有稳定判断一个方向是否强到值得进入黑客松产品构思。

## 运行输入

两个 fixture 的运行前 SHA-256 与归档 manifest 一致：

| 基准 | SHA-256 |
| --- | --- |
| `PAWN` | `b633531592c2c9e88b7037edc7328bbb3642255d771e9508d4b845d7c7ae03a2` |
| 米哈游全球发行 | `7d7008936a85ff3199a1696ae21578d37bae8792916db5ed624545ef4fba5a57` |

两者使用独立 Run 和独立 Session。Session ID 交集为 0，交叉 Prompt 关键词污染
检查为 0。

## 首轮失败与修复

第一轮 `v1` 的两个 Run 都在 Problem Writer 阶段失败。原因是 Candidate JSON
同时要求模型生成 `title` 和 Markdown H1，Hub 又要求两者逐字相同，但 Prompt
没有声明这条要求。

最终修复不是继续强迫两个标题一致，而是删除重复的 `title` 字段：

```json
{"candidates": [{"markdown": "# 唯一标题\n..."}]}
```

Markdown H1 现在是标题的唯一事实来源，Hub 在需要索引标题时自行提取。

失败证据保留在：

- `runs/pawn-e2e-v1-20260723/`
- `runs/mihoyo-e2e-v1-20260723/`

## 米哈游完整 Run

运行目录：`runs/mihoyo-e2e-v2-20260723/`

运行时间为 2026-07-23 11:03:39 至 11:40:25（Asia/Shanghai），约 36 分 46 秒。
运行时使用 Codex CLI 0.142.5；虽然 Run 配置未显式 pin 模型，但真实 Session
元数据显示全部任务实际使用 `gpt-5.5`。

### 数量漏斗

| 阶段 | 数量 | 结果 |
| --- | ---: | --- |
| Challenge Parser | 1 | 成功 |
| Audience Expander | 1 | 产出 5 个人群 |
| Research | 5 | 全部成功，仅此阶段开启 Web Search |
| Problem Writer | 5 | 产出 16 个 Problem |
| Problem Gateway | 16 | 16 pass，0 reject |
| Idea Generator | 48 | 每个 Problem 3 个全新 Session |
| Idea | 105 | 每个 Generator 可返回动态数量 |
| Idea Red Team | 105 | 101 pass，4 reject |
| Idea Card | 101 | 全部通过确定性校验 |

共执行 181 个模型任务，181 个 Session ID 全部唯一，所有任务成功。离线
`hacksome validate` 通过。

### 模型用量

持久化 Result 汇总值：

| 指标 | 数量 |
| --- | ---: |
| Input tokens | 1,742,840 |
| Cached input tokens | 687,488 |
| Output tokens | 189,058 |
| Reasoning output tokens | 35,283 |
| 各 Session 执行时长之和 | 64,959.9 秒 |

执行时长之和约 18 小时，但由于并行执行，实际墙钟时间约 37 分钟。

### 产出的人群

1. Global game publishing teams
2. Game localization professionals
3. Regional community managers
4. Live operations and release managers
5. miHoYo game fan communities

### 内容质量观察

较强的方向包括：

- `Monetized Copy Risk Simulator`：把付费文案的跨语言承诺偏差提前模拟成发布事故，
  由发布团队直接修正文案、支持话术和审核包，用户价值与闭环清楚。
- `42-Day Community Risk Simulator`：用公开历史社区讨论预演地区化公告的误读，
  直接产出可使用的 FAQ、Moderator briefing 和回复模板。
- `Launch State Twin`：把维护、版本、活动、公告和补偿建模成可执行发布图，并从
  玩家视角模拟发布，Pitch 力较强。

暴露的问题包括：

- Problem Gateway 淘汰率为 0，无法区分“有公开证据”和“值得做产品”。
- Red Team 淘汰率仅 3.8%，对完整但普通、赛题相关性偏弱的方案也普遍放行。
- 多个独立 Generator 产生高度相似甚至同名方案，例如 `Launch State Twin`、
  `LoreLock Localization Workbench`、`Patchline Canon Companion`。
- 命名大量集中在 `Simulator`、`Control Room`、`Agent`、`Workbench`、`Twin`，
  组合起来有明显的 AI 模板感。
- 对私有数据/业务权限的判断不稳定：部分依赖内部发布资产的 Idea 被拒绝，另一些
  相似 Idea 因声称可用 synthetic demo 而通过。
- `Dialogue Friction Replay Lab` 等玩家侧工具本身 User Flow 完整，但与“重做全球
  发行链条”的关系偏弱，仍然通过。

### 被 Red Team 淘汰的 4 个 Idea

- `[Zenless Zone Zero] Version Gatekeeper for Client-Server Launch Readiness`
- `[Genshin Impact / Honkai: Star Rail / Zenless Zone Zero] Compensation Sandbox for Release War Rooms`
- `[Zenless Zone Zero] Player-Loss Twin for Platform-Specific Update Incidents`
- `[Genshin Impact / Honkai: Star Rail / Zenless Zone Zero] Launch State Twin`

共同原因是核心价值依赖真实内部遥测、账号权益、发布配置或写入权限，公开数据和
本地 Demo 无法完成真实闭环。

## PAWN 部分 Run

运行目录：`runs/pawn-e2e-v2-20260723/`

`PAWN` 被解析为一个完全开放的单词，扩散到棋手、国际象棋教练、典当行从业者、
典当顾客和游戏设计师。Research 产出 19 个 Problem，其中 18 个通过 Gateway，
随后开始大规模 Idea fanout。

观察中已经出现大量语义分叉和同质 Idea。用户据此明确要求停止 `PAWN`，只继续
米哈游赛题。进程已经终止，没有残留 Codex 子进程；所有已完成的 Prompt、Research、
Problem 和 Idea 保留。由于当前 CLI 对人工 `Ctrl-C` 没有 Run-level interrupted
终态，持久化状态仍显示 `running`，这是后续可修的生命周期问题。

## E2E 后的运行时配置

E2E 完成后，本地 Codex CLI 从 0.142.5 更新到 0.145.0。新版模型目录已提供
`gpt-5.6-terra`，后续 Run 的默认配置已改为：

```text
model = gpt-5.6-terra
reasoning_effort = high
```

模型和 reasoning effort 会显式写入启动参数与 Run 元数据，不再依赖 CLI 的动态
默认值。

## 下一轮应讨论的问题

本轮不直接修改 Gateway/Red Team 产品标准。下一轮应基于这些真实输出讨论：

1. Problem Gateway 除了“真实、有证据”，还必须满足什么绝对门槛才值得进入 Idea？
2. Red Team 是否只判断 Felt Value/User Flow，还是也应判断赛题题眼、公开数据可交付性
   和产品机制是否形成质变？
3. 保留相似方案时，如何识别“都有成功可能”与“只是同一模板换名字”？
