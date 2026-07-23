# Design — info-product 找机会方法（headless CEO）

> 本文是 R1+R2+R3 三份研究的综合（即计划里的 R4）+ 落地设计。说明用中文（供审阅），内嵌的 skill 正文草稿用英文（最终交付物语言）。

## 一、脊柱洞见（整个方法的一句话）

对一个 headless LLM agent，人类创业者的核心约束——**"我会不会做/我懂不懂这个"**——**消失了**，因为 agent 能写任何文本产品。于是找机会的全部重量压到**需求侧**：

> **能写任何东西 ⇒ 难的不是"能不能做出来"，而是"有没有人肯掏钱"。所以把全部力气花在证明"钱已经在流动"上。**

一切都归结为：**派研究 Goal 把"钱已经在动"的痕迹捞出来，再用能区分"真金付费 vs 只是兴趣"的纪律阈值去读它。** 人类靠沉浸/品味/受众做的三件事，分别替换成：
- 沉浸 → **派 researcher 取 at-scale 逐字语料**（禁摘要）；
- 品味/直觉 → **显式阈值**（触发词、≥5 作者、销量代理分档、饱和闸）；
- 自有受众/presell → **观察市场里已经发生的付费**（marketplace 销量/评论/报名/BSR、付费推荐）。

这条脊柱是本 skill 区别于"通用找机会"的地方，也是它对 `decide-direction` 反空想标准的承接。

## 二、合并去重后的 7 步 pipeline

三份研究里 10+ 条方法合并成一条线性 pipeline（标注来源 R#-M#/信号#）。每步 = 一个 agent 可执行操作（研究-Goal 模板 / LLM 原生扫描 / 决策阈值）。

| 步 | 名称 | 来源 | 操作类型 | keep/drop 闸 |
|---|---|---|---|---|
| 0 | 别凭空造 + 查记忆 | 骨架 | 查 `/company` | 已否方向不重生 |
| 1 | 找市场说话的地方（+ 可读性硬门） | R1-M1 | 研究-Goal | <2 个公开可读社区 → 弃这个市场 |
| 2 | 逐字采集抱怨（at-scale，禁摘要） | R1-M2 | 研究-Goal | 目标 ~40-60 条原话带 URL；返回摘要/<30 条 → 重派 |
| 3 | 找到尖锐 + 复现的痛 | R1-M3+M4 | LLM 原生扫描 | 触发词/问题命中；且 ≥5 个不同作者、≥2 个社区 |
| 4 | 证明已经有人**付费**（主闸） | R1-M5 + R3信号1/2/3 + R2-M2/M3 | 研究-Goal + 分档 | 只有 Tier-1 已发生付费才算 GO；无付费痕迹 → DROP |
| 5 | 查饱和 + 找楔子（诚实闸） | R3信号4 + R1-M6 | 研究-Goal + LLM 原生 | 饱和(头部全 ≥4.5★/百评/低价/无未满足抱怨)→DROP；"已证明但可打"窄窗→KEEP |
| 6 | 定义 2-3 个候选 | R2-M1/M4/M5 | 结构化生成 | 每个=1 买家+1 灼痛+最小文本交付物；LLM 原生可写、无重基建；明显互异 |
| 7 | 交 decide-direction，不自判 | 骨架接缝 | 逐个 send | 只生成不判 GO/DROP |

**关键阈值锚**（研究出处见 r1/r2/r3；skill 正文措辞用"约/数量级"，不写死）：
- 可读性门：<2 个公开可读社区 → 弃市场。
- 语料量：~40-60 条逐字原话（agent 对人类"30-50 小时沉浸"的规模替代）。
- 复现门：≥5 个不同作者、跨 ≥2 个社区。
- 付费三档（R2-M3/R3）：Tier-1 已发生付费(购买/预购/付费订阅/持续经营的付费竞品/"take my money") = 唯一 GO 依据；Tier-2 waitlist/搜索量 = 弱；Tier-3 点赞/"好主意" = 忽略。
- 付费代理读数（R3信号1）：Amazon 品类 BSR（<10k 强销 / <100k 稳动 / >500k 稀少，看**品类榜**非总榜）；Udemy 报名（中位仅 ~217，报名>千才算持续买；评论数少的高星无意义）；Substack 付费订阅徽章 100/1,000/10,000；Gumroad ratings 数 / Etsy "X sold"。
- 竞品数量：**≥3 个付费竞品且卖得动 = 需求已证明**（"没竞品=蓝海"是陷阱，常=没人肯付费）。
- 饱和 DROP：≥5 个付费品、头部全 ≥4.5★/评论上百/低价/无未满足抱怨。
- "已证明但可打"窄窗：有真实销量 **但** 头部平庸/过时/单薄/有复现抱怨 → 有更小更好更便宜的楔子。

## 三、交付物形态（挂进 skill 的方式）—— 三层"渐进式披露"（用户决策 2026-07-02）

用户观察：**每个平台策略不一样**（亚马逊看 BSR/关键词、Substack 看付费订阅、Gumroad/Etsy 看销量/模板）。用户决策：不拆成多个独立 skill，而是**一个 skill 内部分层文件**（father 说明 + 各平台子说明，靠渐进式披露路由；仿 `decide-direction/references/` 先例）。三层：

```
find-opportunity/
├─ SKILL.md                                     ← 爷爷：选业态（已存在，小改）
└─ references/
   ├─ finding-info-product-opportunities.md     ← 父：共通 7 步 + "在哪个平台找？读对应子说明"
   ├─ platform-gumroad.md                        ← 子（首批）
   ├─ platform-amazon-kdp.md                     ← 子（首批）
   └─ platform-etsy.md                           ← 子（首批）
   （platform-substack.md / platform-udemy.md = 后续任务补）
```

**分工原则（父 vs 子）**：
- **共通、写在父说明一次**：脊柱洞见（能写任何东西⇒难在"有没有人付钱"）+ 第二节 7 步里**平台无关的部分**——步 0 查记忆、步 1-3 找社区/采集原话/找复现痛、步 6 定义候选、步 7 交接。父说明末尾放"平台菜单 + 路由"：列出各平台一句话适配（谁适合文本原生 agent）+ "选定后去读 `platform-<x>.md`"。
- **平台特有、各子说明具体化**：主要是**步 4（证明付费）和步 5（饱和/找缝）**——因为"销量信号在哪看、什么算有缝、平台脾气/工具"正是平台差异所在。每个子说明 = 针对该平台把步 4-5 落成具体的研究-Goal 模板 + 读数 + 阈值 + 该平台适合的产品形态。子说明依据各自平台研究（`research/gumroad.md`/`amazon-kdp.md`/`etsy.md`）。

**首批范围（用户决策）**：父说明 + Gumroad + 亚马逊 KDP + Etsy 三个子说明。Substack / Udemy 在父说明的平台菜单里列出、标"playbook 待补"，排后续 child 任务。

1. **新增 父** `references/finding-info-product-opportunities.md`：大白话、第二人称（同 `direction-critic.md` 风格），**撤所有"lens/透镜"黑话**。开篇脊柱洞见 → 7 步（平台无关步给全，步 4-5 写共通逻辑 + "平台细节见对应子说明"）→ 平台菜单+路由 → 标定说明 + provenance 脚注（Amy Hoy/Alex Hillman、Nathan Barry、Ramit Sethi、Justin Welsh、Pieter Levels、Daniel Vassallo、Indie Hackers）。

2. **新增 3 个子** `references/platform-{gumroad,amazon-kdp,etsy}.md`：各自把步 4-5 平台化——该平台的需求信号在哪看（研究-Goal 模板）、什么算可打的缝、平台机制/工具/价格锚、适合的产品形态。大白话、带该平台 provenance。

3. **编辑 爷爷** `find-opportunity/SKILL.md`（小改，不动骨架）：line 46-48 占位注释改为"info-product 已有具体方法 → 见 references/finding-info-product-opportunities.md；其余业态仍在做"；业态表/信号节附近加一句路由：选了 service/info-product 就读父说明。通用信号法作其它业态回退保留。

4. **命名与边界**：父文件名 `finding-info-product-opportunities.md`（info-product 专名）；子文件 `platform-<name>.md`。SKILL.md "A service / info-product" 行当前只 info-product 子形态有方法；done-for-you 服务 / RaaS 是已登记 follow-up，父说明顶部注明。

## 四、约束与纪律（承接父 PRD + 本任务决策）

- **零 .py / 声明式**：只加/改 markdown skill 文件，不写代码（对齐骨架"声明式零 .py"）。
- **职责边界**：本方法只到"定义候选 + 交 decide-direction"。执行（造/发布/收款/搭渠道）不在本 skill——但候选的**可造性闸**（LLM 原生可写、无重基建）保证不产空中楼阁。
- **agent 可执行 > 哲学**：每步必须有可执行操作，不能只有哲学（本任务第一要求）。审阅时逐步核这一点。
- **命令真实性**：研究-Goal 命令 `python3 -m orchestration.messaging send --to researcher --intent "…"`（可选 `--accept "…"`）已被 R3 核到 `orchestration/messaging.py`；正文用真实命令。
- **标定措辞**：所有数字（BSR 分档、报名中位、竞品数）写成"约/数量级/例如"，不写死为硬性阈值。

## 五、验证方式（AC 如何被核）

- **静态核**：reference 文件存在、7 步齐全、每步有"研究-Goal 模板 + 读数 + keep/drop 规则"三件套；SKILL.md 已路由到它且占位注释已更新；无"lens/透镜"字样；无 .py 改动。
- **交叉一致性核**：与骨架接缝一致（只生成不判、2-3 候选、查 /company）；与 `decide-direction` 反空想标准不冲突（付费信号即 critic 的"behavior not interest"）。
- **e2e（可选但推荐，遵循 sop-adding-roles-and-skills 真跑纪律）**：空公司 cold-start，CEO 选 info-product 业态后应读到本 reference、发出**带 marketplace 付费证据问法**的研究-Goal（而非泛泛"调研一下"），并在信号回来后按付费/饱和闸产候选。留作 implement 末步或 follow-up，视执行层就绪度。
