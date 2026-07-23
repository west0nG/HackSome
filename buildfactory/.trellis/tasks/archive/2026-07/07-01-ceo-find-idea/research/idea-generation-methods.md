# Research: CEO 机会发现 / idea 生成方法论 — 实拉与三道检验

- **Query**: 给 headless 自治 CEO 一个「从 0 生成 product/business idea」的方式轮（method wheel）。实拉 idea-*生成*（非判断）方法论原文，逐条过三道检验，产出**能反空想、能喂给 `decide-direction`** 的 lens 目录。
- **Scope**: external（PG 原文 WebFetch）+ local（gstack 实拉真实文件，非二手）。
- **Date**: 2026-07-01
- **不重复**：`.trellis/tasks/06-28-role-ceo/research/ceo-skill-reuse.md`（判断侧）。本文只做**生成侧**，复用其「三道检验」定义。
- **勘误**：本任务首个 `trellis-research` sub-agent 空跑（0 tool_uses、0 文件），不予采信；以下全部为主 agent 亲自实拉。
- **⚠️ 状态降级（用户决策）**：本任务 skill 只做**骨架**（业态自觉 + 通用信号法 + 占位），**各业态「怎么找机会」的具体方法留空、单独开研究任务写**。故本文降级为那些**后续方法研究任务的种子/起点**，**不作本任务 skill 正文依据**。文中「透镜/lens」= 「**找机会的方法/角度**」的旧叫法（用户已指出是黑话）；后续任务用大白话。

## 三道检验（复用判断侧研究，逐条过筛）

目标 agent 本身是 LLM。给 LLM 写泛泛「怎么找 idea」= 没写（LLM 自带 PG 全文）。一条只有满足至少一项才保留：
- **(a) 系统特定**：headless CEO 无个人生活/无现有用户，不能「解决自己的痛」也不能「看用户用」；它的替代是**派研究 Goal 给 `researcher` 取真实信号**；idea 必须能被 `researcher`/`builder`/`growth` 部门落地；受 `/company` 记忆约束（含已否方向）。
- **(b) 压制 LLM 默认**：LLM 被要求「想 idea」时的默认 = 吐**似是而非的通用 SaaS**（"AI-powered X for Y"）＝ PG 说的 sitcom/made-up idea 陷阱；且固着第一个念头；且把野心通胀到十亿级。
- **(c) 非平凡取舍/阈值/反例**：LLM 不会自发采用的判断信号。
纯美德（"广开脑洞""第一性原理""考虑市场"）＝ LLM 自带 ＝ **DROP**。

---

## 实拉原文（真实来源）

### A. Paul Graham, *How to Get Startup Ideas*（paulgraham.com/startupideas.html，公开随笔，引作思想来源）

七条**生成**法（非评估）：
1. **解决你自己有的问题** — "look for problems, preferably problems you have yourself"（保证问题真实存在）。
2. **活在未来、造缺失的东西** — "Live in the future and build what seems interesting"。
3. **头脑风暴陷阱** — 刻意"想 idea"产出 sitcom/made-up ideas：听着合理、实则骗了你自己。**← 这正是 LLM 的默认失败模式。**
4. **站在快速变化领域的前沿** — "If you're at the leading edge of a field that's changing fast... you're more likely to be right."
5. **schlep blindness / 不性感盲区** — 关掉过滤枯燥/不光鲜机会的滤镜（Stripe 做支付这种脏活）。
6. **紧迫度测试** — "Who wants this so much that they'll use it even when it's a crappy version one made by a two-person startup?"
7. **窄而深，挖井** — "dig a hole that's narrow and deep, like a well"：为少数极度想要的人做，胜过为很多轻度感兴趣的人做。

### B. gstack `office-hours`（MIT, Garry Tan/YC；`~/.claude/skills/gstack/office-hours/SKILL.md.tmpl` 真实正文）

- **六问**（Q1 demand-reality / Q2 status-quo / Q3 desperate-specificity / Q4 narrowest-wedge / Q5 observation / Q6 future-fit）——本是**验证**姿态，但 Q2/Q3/Q4 可**倒成生成**透镜。
- **"The status quo is your real competitor. Not the other startup — the cobbled-together spreadsheet-and-Slack workaround your user is already living with."** ← 现状/凑合方案挖掘 = 需求信号源。
- **Q4 原文**：「smallest possible version someone would pay for **this week, not after you build the platform**」。红旗：「need to build the full platform first」。
- **Phase 4: Alternatives Generation (MANDATORY)**：产 2-3 个不同方案，**必须一个 minimal-viable、一个 ideal、一个 creative/lateral**。← 反固着的**发散纪律**。
- **反自嗨**：「interest is not demand」「Surveys lie. Demos are theater.」「behavior counts」。

### C. gstack `ETHOS.md` §2 Search Before Building（MIT）— 三层知识

- **Layer 1 tried-and-true**（别重造轮子）/ **Layer 2 new-and-popular**（搜但存疑，"Mr. Market too fearful or too greedy"）/ **Layer 3 first-principles**（原创观察，"Prize them above everything"）。
- **Eureka**：理解人人在做什么+为什么（L1+L2）→ 对其假设施第一性推理（L3）→ 发现约定俗成错在哪。"zig while others zag. When you find one, name it."

---

## 方式轮 lens 目录（过检验 + 标注 内省 vs 信号接地）

> 用户决策：**部分透镜信号接地**（先派研究 Goal 给 `researcher` 取真信号，反空想）；**静态清单 CEO 自选**（无有状态轮转）。

### 信号接地型（先派一个小研究 Goal 给 `researcher`，再据信号生成）

- **L1 现状/凑合方案挖掘** — 派 researcher 去某领域找「人们现在拿 spreadsheet/Slack/手工/内部工具凑合」的地方；凑合方案本身=需求信号，做掉它。〔(a)+(c)；office-hours Q2 "status quo is your real competitor"〕
- **L2 前沿/新变便宜** — 派 researcher 调研「什么能力刚变便宜/可能」（尤其 AI 让某类事新变便宜），造那个明显缺失的东西。〔(a)+(b: LLM 不会自发把 scope 收到"本季度刚可能"的窄窗)+(c)；PG#2/#4 + Search-Before-Building L3〕
- **L3 抱怨/具体的人挖掘** — 派 researcher 找**一个具体角色 + 一个反复出现的痛**（论坛/差评/招聘帖里的真人真话）。这是 CEO 对 PG#1「解决自己的痛」的系统替代（CEO 无个人痛）。〔(a)+(c)；PG#1/#6 + Q3 "name the actual human, not a category"〕

### 内省生成型（CEO 在 context 内推理，更轻；可选 Layer1/2 搜一下）

- **L4 拆解/收窄已知赢家** — 拿一个 CEO 已知的宽产品，切出部门这周能发的**最锋利一小片**。〔(c)；PG#7 挖井 + Q4 narrowest-wedge〕
- **L5 schlep/不性感** — 主动**关掉"这够不够酷"滤镜**，去够那些 LLM 因为不光鲜而跳过的枯燥高价值活。〔(b: LLM 偏好听着高大上的)；PG#5〕
- **L6 第一性/逆共识** — 搜「人人怎么做+为什么」（L1/L2），找那**一条错的约定俗成假设**（L3 zig-while-zag）。〔(c)；ETHOS 三层 + eureka〕

### 贯穿纪律（不管选哪个透镜）

- **反固着发散**：产 **2-3 个明显不同**的候选、至少一个刻意侧向的（不停在第一个似是而非的）。〔(b: LLM 固着第一念)；office-hours Phase 4 MANDATORY〕
- **命名陷阱**（skill 开篇必写）：LLM 被要 idea 的默认就是吐通用"AI-powered X for Y"（PG sitcom 陷阱）；无真信号的候选到 critic 那里必被 DROP。**所以别自由联想——跑一个透镜；信号型的先取真信号。**〔(b) 最强反默认〕

---

## 生成→判断 接缝（seam）

- **只生成、不判断**：find-idea 产候选，**不召 critic、不判 GO/DROP**——那是 `decide-direction`+`direction-critic` 的活（已存在）。职责分离（用户决策①）。产出 2-3 候选后，把每个有戏的**逐个**交给 `decide-direction`。
- **不重生已否方向（DO_NOT_RESURFACE）**：生成前先从 `/company` 记忆回忆哪些方向已试/已否，别再生成。〔(a)+(b: LLM 反复提同一个显而易见的 idea)；接判断侧研究 DO_NOT_RESURFACE〕
- **标定小而真**：候选 = 部门（researcher/builder/growth）**几天内能发**的最小真实价值，不是十亿级；匹配公司真能造的东西。〔(b) 反野心通胀；对齐 critic「务实门槛」〕

---

## DROP 清单（纯 LLM 默认美德，不写进 skill）

- 「广开脑洞 / think outside the box」— LLM 自带，且正是陷阱本身。
- 「考虑 TAM/市场规模」— 十亿级 VC 框架，已明确去标定。
- 泛泛「做点市场调研」— 太糊；被具体的「派一个带明确问题的研究 Goal」取代。
- office-hours **Q5 watch-a-user**（需现有产品+用户，CEO 还没有）、**Q6 future-fit**（是**验证**透镜，已在 critic 里）——**不作生成透镜**。
- office-hours 整套 `AskUserQuestion` / 人类 founder 交互层 — CEO headless，DROP。

---

## 业态扩展（v2）：从「只会产品」到「业态自觉」

> 用户重构决策：agent 变现不限于做产品，还有自媒体/内容、服务/信息产品、跨境电商等业态。技能升级为 `find-opportunity`：Level-1 选业态 → Level-2 业态内找机会（form-specific 透镜）。本轮充实 **内容/自媒体 + 服务/信息产品**（电商押后：基建/真金依赖重）。
> **token-ROI 归属修正（用户纠偏）**：agent 在 wake 时**看不到自己的 token 经济学**，「按 token-ROI 选业态」对 agent 是空指令。token-ROI 是 **operator（我们）排 roadmap 的标尺**——先充实哪个业态透镜、先建哪个业态执行——**不进 CEO 的 skill**。粗排（服务/信息 ≈ 自媒体 ＞ 电商 ＞ 产品）只用来定"本轮先做 service/content 透镜"，agent 侧 **Level-1 业态随便选、初期别纠结，重心全在 Level-2「在给定业态里找到真实机会」**。
> **执行层现状（已核实）**：部门全是占位骨架（`growth.yaml` 自述 placeholder，只有 company-state/receive-goal/send-goal），外设层只有入站 adapter（email/webhook）、**无出站动作**。故没有业态今天能端到端跑。→ 本任务只交付 **CEO 侧生成层**；生成层*驱动*该建哪个执行能力；一个业态的可跑=生成透镜(本任务)+执行能力(sibling)。

### D. 内容/自媒体业态 — 实拉 Kevin Kelly *1000 True Fans*（kk.org/thetechnium/1000-true-fans/）

- **真粉定义**：「a true fan is defined as a fan that will buy anything you produce」。
- **经济学**：`1000 真粉 × $100/年 = $100k/年`；**直连渠道**是关键——"they must pay you directly... you get to keep all of their support"，中间商抽成则需要的受众规模暴增。
- **窄深 > 宽浅**：不是追百万泛粉，而是深耕核心；super-fans 的热情会拉动 regular fans。

**内容/自媒体 lens 集（Level-2）**：
- **CM1 窄深赛道（1000 真粉门槛）** — 选一个窄到「~1000 人会买你产的一切」的赛道，不是泛泛"AI 资讯"。〔(c) 1000TF 数学门槛；(b) LLM 默认吐宽泛通用赛道〕内省+轻信号。
- **CM2 聚集地需求挖掘（信号接地）** — 派 researcher 找目标受众已经聚集的地方 + 哪类内容/问题高互动（内容缺口）。〔(a)+(c)；Sales Safari watering holes〕研究 Goal 样例：`"Where does <audience> already gather online, and which recurring questions/topics get the most engagement but poor existing content?"`
- **CM3 直连渠道优先** — 偏好能建**自有渠道**（newsletter/订阅）而非租来的平台流量的play。〔(c)；1000TF direct channel〕标定。
- **陷阱**（开篇必写）：LLM 默认"开个 AI newsletter/AI 资讯号"——泛、无真粉深度、无真实受众信号。→ 先取聚集地信号，选窄赛道。

### E. 服务/信息产品业态 — 实拉 Amy Hoy *Sales Safari*（solvingproduct.com/sales-safari/ + oreilly 原文摘要）

- **"Forget ideas, study a market."** 「the problems are already all out there. Instead of looking for new problems, you go and find problems people already have.」
- **net-ethnography 观察**：在 watering holes（forum/Reddit/Q&A/Amazon 差评/客服邮件）**at scale** 观察（30-50h），**listen for the nouns** + 触发词（"finally"/"easier"/"relief"/"I hate when"）。**反调研偏差**（surveys lie / self-report 不准）——纯被动观察。
- **观察→产品**：pain-killers（消除焦虑/挫败/不确定）> money-multipliers；用观察到的原话写价值主张。

**服务/信息产品 lens 集（Level-2）**：
- **SI1 Sales Safari 痛点挖掘（信号接地·主透镜）** — 派 researcher **at scale 观察一个社区**，回报反复出现的痛 + 触发词原话 + 他们已经在为什么付费/拿什么凑合。〔(a)+(b: 反凭空造=反空想)+(c)；Sales Safari〕研究 Goal 样例：`"Observe <community> at scale; report recurring pains in their own words (quote 'finally/relief/I hate when'), what they already pay for, and what they hack together."`
- **SI2 产品化重复手工活** — 找人们反复花钱请 freelancer/agency 做的活，打包成固定范围的 productized service，**agent 能亲自交付**（LLM 原生：写作/研究/分析/报告）。〔(a: LLM 原生执行=高 token-ROI)+(c)〕内省+信号。
- **SI3 教他们正搜着学的东西** — 高搜索需求 + 低质供给的主题做成 info-product/course。〔(c)〕信号接地（派 researcher 查搜索需求 + 供给缺口）。
- **标定**：pain-killer > vitamin；交付物必须是 **agent 真能产出的（文本/内容/分析）、低外部基建 → 高 token-ROI**。
- **陷阱**：LLM 默认"做个 AI 课程/泛泛咨询"——无观察到的需求。→ 先 Sales Safari 取真痛。

### Level-1 业态轮（find-opportunity 顶层，CEO 先选业态）

| 业态 | 交付什么（agent 该知道追它意味着做什么） | 透镜文件 |
|---|---|---|
| 服务/信息产品 | 产出并交付文本/内容/分析（报告/newsletter/代写/课程） | `lenses-service.md` |
| 内容/自媒体 | 持续产内容 + 发布 + 涨粉 | `lenses-content.md` |
| 产品/软件 | 造并上线软件 | `lenses-product.md` |
| 跨境电商 | 选品/铺货/投流 | 本轮未充实 |

Level-1 agent 纪律（轻）：**你不只能做产品**——挑一个业态探索本次 wake，**初期随便挑、别纠结这个选择**（会随时间试到别的）；真正重要的是选完 `Read references/lenses-<form>.md` 在该业态里找到**真实、接地**的机会（Level-2）。候选要匹配公司部门**真能造/交付**的东西（这是 agent 能判断的；token-ROI 不是，别让 agent 算）。

## 署名

| 借用 | 来源 | 许可 |
|---|---|---|
| 七生成法 / sitcom 陷阱 / 挖井 / schlep / 紧迫度 | Paul Graham, *How to Get Startup Ideas* | 公开随笔（引作思想来源） |
| 六问倒成生成 / status-quo 竞争 / Phase4 多方案发散 / 反自嗨 | gstack `office-hours` (Garry Tan/YC) | MIT |
| 三层知识 / eureka / zig-while-zag | gstack `ETHOS.md` | MIT |
| 1000 真粉 / 窄深 / 直连渠道 | Kevin Kelly, *1000 True Fans* | 公开随笔（引作思想来源） |
| Sales Safari 观察式需求挖掘 / "study a market not ideas" / 触发词 | Amy Hoy & Alex Hillman, *Sales Safari (30×500)* | 公开方法（引作思想来源；经 solvingproduct/oreilly 摘要核） |

## Caveats

- PG 随笔非代码许可；作**思想来源**引用+标明，不逐字拷贝进 skill。
- 未拉 launch-your-agent 的 idea→scope 细节——判断侧研究已覆盖其生命周期形状（smallest-core v0 / 编号增量），本任务只需其「smallest real thing」标定，已并入接缝节。
