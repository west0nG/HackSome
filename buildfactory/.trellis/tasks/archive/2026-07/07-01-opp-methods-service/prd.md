# 找机会的方法：服务/信息产品 (CEO find-opportunity methods · service)

## Goal

把 `find-opportunity` skill 里"服务/信息产品"业态**当前留白的"具体怎么找机会"**填成一份可用的方法正文——专门为 **headless 自治 CEO**（无人类品味/沉浸/人脉）重标定：把人类靠沉浸做的事，翻译成"派研究 Goal 给 `researcher` at-scale 观察 + LLM 原生执行"的可执行配方。承接 find-opportunity 骨架（`07-01-ceo-find-idea`），产出的候选喂给 `decide-direction` 判断。

## Background / 确认事实（repo 已核实，无需再问）

- **骨架现状**：`agents/assets/skills/find-opportunity/SKILL.md` 已交付 = 业态自觉 + 通用信号法（别凭空编→派研究 Goal→产 2-3 候选→交 decide-direction）。SKILL.md line 46-48 有明确占位注释："Each form has sharper, form-specific ways… still being worked out." 本任务就是把 service 这块的占位填掉。
- **种子研究已扎实**：`07-01-ceo-find-idea/research/idea-generation-methods.md` §E 已**实拉** Amy Hoy *Sales Safari* 原文，并产出三个已过三道检验的方法：
  - **SI1 Sales Safari 痛点挖掘（信号接地·主方法）**——派 researcher at-scale 观察一个社区，回报反复出现的痛 + 触发词原话（"finally/relief/I hate when"）+ 他们已在为什么付费/拿什么凑合。
  - **SI2 产品化重复手工活**——找人们反复花钱请 freelancer/agency 做、且 **agent 能亲自 LLM 原生交付**（写作/研究/分析/报告）的活，打包成固定范围服务。
  - **SI3 教他们正搜着学的东西**——高搜索需求 + 低质供给的主题做成 info-product。
  - 标定：pain-killer > vitamin；交付物必须是 **agent 真能产出的文本/内容/分析、低外部基建 → 高 token-ROI**。陷阱：LLM 默认"做个 AI 课程/泛泛咨询"（无观察到的需求）。
- **已建先例（形态模板）**：`decide-direction/references/direction-critic.md` = 自包含、第二人称、大白话、带 HTML 注释 provenance 脚注的 brief。渐进式披露：SKILL.md 主文件轻，重内容进 `references/`。
- **接缝**：本方法只**生成**候选（2-3 个、明显不同），不判 GO/DROP；逐个交 `decide-direction`。生成前查 `/company` 记忆避开已否方向。
- **约束**：声明式、零 `.py`；用户明令**撤"lens/透镜"黑话**，用大白话；引原始来源作思想来源署名，不逐字拷贝。
- **执行门控（父 PRD PR3）**：service 业态今天执行层是空的（部门占位、外设层仅入站）；本任务只交付**生成层**，不假装能端到端跑。

## Scope 收窄（用户决策 2026-07-02）

**本任务只做 info-product 这一条线**（可打包的知识产物：指南/报告/电子书/付费 newsletter/模板/清单/mini-course 等）。同属"服务/信息产品"业态的另两条子线**押后**（不在本任务）：
- done-for-you 服务（代写/研究/分析/报告的 productized service）→ 后续 follow-up。
- research-as-a-service / 数据产品 → 后续 follow-up。

理由：info-product 对 headless agent 是最强契合——纯文本产物，agent **既能找（派研究 Goal 观察需求）又能亲自产（LLM 原生写作）**，外部基建依赖最低、token-ROI 最高。聚焦一条线能挖到可执行深度。

## 职责边界与标定（用户决策 2026-07-02）

- **本 skill = 机会发现 + 候选定义**："定做什么 info-product 这件事"。产出候选喂给 `decide-direction`，**执行（造/交付/变现/搭渠道）交给别的角色/层**，不在本 skill。
- **候选的标准 = 真实 · 最小 · 足以赚到钱**：不是"有人感兴趣的话题"，而是能真正变现的最小 info-product idea。
- **必须带 willingness-to-pay 信号**：方法核心是找"**已经有人在为这类东西掏钱**（买课/买电子书/付费订阅/付费模板）**且现有供给薄/质量差**"的选题——付费行为是真需求信号，反"兴趣≠需求"。
- **承接父 PR3（诚实但不越界）**：本 skill 不解决"怎么交付/怎么收款"，那是执行层的事；只需保证候选是公司**接下来有可能真造出并卖掉**的（标定小而真），不产出空中楼阁。

## Research posture（用户决策 2026-07-02）

**先做全新深研究**，再动笔（✅ 已完成）。种子 §E（Sales Safari）只作起点、不设上限：围绕 **info-product 找机会** 重新实拉一手方法论并给 headless agent 重标定，逐条过三道检验。对齐父 PRD"最该认真研究、不能糊"。

- **研究机制（用户决策）**：**用 subagent 做研究**保护主上下文（有意覆盖种子记录的"子 agent 空跑"教训；强制 prompt 要求实拉命名一手来源、带原文引用、落盘、只回摘要）。
- **⭐ 第一要求：agent 可执行 > 哲学（用户决策）**：产出必须是 agent 理论上能直接执行的方法，不是纯哲学。哲学重要，但**哲学的"翻译"更重要**。每个方法必须有三件套：① agent 实际跑的**操作**（研究-Goal 模板 / 可观测读数 / 决策阈值）；② 一行哲学背书（出处）；③ 人类做法 → agent 替代。只有哲学没有可执行操作 = 不合格。
- **研究产出（已落盘）**：`research/r1-demand-observation.md`（需求观察 6 法）、`research/r2-selection-validation.md`（选题验证 5 法）、`research/r3-willingness-to-pay.md`（付费信号 4 条 + 饱和闸）。综合（R4）+ 落地设计见 `design.md`。
- **平台研究（第二轮，用户决策"每个平台策略不同"）**：各平台单独深挖 `research/gumroad.md`、`research/amazon-kdp.md`、`research/etsy.md`（在 R3 销量信号基础上钻平台特有的找机会玩法）。

## Requirements

方法正文（reference 文件）与 SKILL.md 接线的具体形态见 `design.md`；下列为可测需求。

- **R1 具体方法落地**：`find-opportunity` 的 info-product 业态从"占位"变为一份**可执行的 7 步方法**（见 design.md 第二节 pipeline），取代 SKILL.md line 46-48 的"still being worked out"占位。
- **R2 每步 agent 可执行（第一要求）**：7 步中凡涉及取信号的步骤都必须给出 agent 能直接执行的操作——真实的研究-Goal `--intent` 模板 / LLM 原生扫描规则 / keep-drop 阈值；不允许"只有哲学、没有操作"的步骤。
- **R3 付费意愿是主闸**：方法必须强制"证明已经有人**付费**"这一步（marketplace 销量/评论/报名/BSR、付费推荐、付费竞品），并用三档信号规则（Tier-1 已发生付费 = 唯一 GO 依据；兴趣/搜索量/点赞不算）压制"兴趣冒充需求"。
- **R4 饱和/诚实闸**：必须含反信号闸——(i) 有讨论但零付费 → DROP；(ii) 供给饱和（头部全高分/百评/低价/无未满足抱怨）→ DROP；只保留"已证明但可打"窄窗。
- **R5 可造性 + 最小标定**：每个候选必须 = 1 个具体买家 + 1 个灼痛 + **最小文本交付物**，且 **LLM 原生可写、无重外部基建**（无视频/直播/自研软件）；标定小而真，不产十亿级/空中楼阁。
- **R6 承接骨架接缝**：只**生成** 2-3 个明显互异的候选、**不自判** GO/DROP、逐个交 `decide-direction`；生成前查 `/company` 记忆避开已否方向。
- **R7 形态与接线（三层渐进式披露，用户决策）**：不拆多 skill；一个 skill 内部分层文件（见 design.md 第三节）。新增**父说明** `find-opportunity/references/finding-info-product-opportunities.md`（共通 7 步 + 平台菜单/路由）；小改 `SKILL.md` 路由到父说明并更新占位注释；父说明顶部标注 done-for-you / RaaS 为 follow-up。父/子文件均大白话、第二人称、**无 lens/透镜黑话**、带 provenance。
- **R8 约束合规**：声明式、**零 .py**；数字写成"约/数量级"不写死；命令用真实 `python3 -m orchestration.messaging send …`；来源作思想来源署名、不逐字拷贝。
- **R9 平台子说明（首批 3 个，用户决策）**：新增 `references/platform-{gumroad,amazon-kdp,etsy}.md`，各自把步 4-5（证明付费 / 饱和找缝）平台化——该平台需求信号在哪看的研究-Goal 模板 + 可观测读数 + 阈值 + 适合的产品形态；每步同样满足 R2 的 agent 可执行三件套。Substack / Udemy 在父说明平台菜单里列出并标"待补"，排后续 child。

## Acceptance Criteria

- [x] **AC1**：`references/finding-info-product-opportunities.md` 存在，含 design.md 第二节的 7 步（0 查记忆 / 1 可读性门 / 2 逐字采集 / 3 尖锐+复现 / 4 付费主闸 / 5 饱和+楔子 / 6 定义候选 / 7 交接）。〔核 R1〕
- [x] **AC2**：每个取信号的步骤都带"研究-Goal `--intent` 模板 + 可观测读数 + keep/drop 规则"三件套；无只有哲学没有操作的步骤。〔核 R2，逐步人工核〕
- [x] **AC3**：付费主闸存在且用三档信号规则；文中明确"只有已发生的付费算 GO，兴趣/搜索量/点赞不算"。〔核 R3〕
- [x] **AC4**：饱和/诚实闸存在，含"零付费→DROP""饱和→DROP""已证明但可打→KEEP"三条。〔核 R4〕
- [x] **AC5**：候选定义门存在（1 买家 + 1 灼痛 + 最小文本交付物 + LLM 原生可写/无重基建）；且明确只生成 2-3 互异候选、不自判、交 decide-direction、先查 /company。〔核 R5+R6〕
- [x] **AC6**：`SKILL.md` 已加路由到父说明且 line 46-48 占位注释已更新；父说明顶部注明 done-for-you/RaaS 为 follow-up，末尾有"平台菜单 + 路由"（含 Substack/Udemy 标"待补"）。〔核 R7〕
- [x] **AC9**：三个平台子说明 `references/platform-{gumroad,amazon-kdp,etsy}.md` 存在，各自把步 4-5 平台化（该平台需求信号研究-Goal 模板 + 读数 + 阈值 + 适合形态），每步满足 agent 可执行三件套；父说明能正确路由到它们。〔核 R9〕
- [x] **AC7**：全程无 lens/透镜黑话；无任何 `.py` 改动（`git diff --stat` 只含 md）；数字为"约/数量级"措辞；引用作署名不逐字拷贝。〔核 R8〕
- [x] **AC8（e2e，已跑）**：空公司 heartbeat e2e ✅——CEO cold-start 首心跳选 info-product、signal-first 派研究 Goal（`84db48cf`），且**逐字照做了新父方法**（可读性 <2 硬门 / 40-60 逐字禁摘要 / 触发词表——皆新 reference 独有）。物料化经 loadout 测试(11 passed)+bind-mount 证实。**未现场跑到**：platform 子文件（步 4-5）——在 pipeline 更后、gated on researcher 返回语料，而 researcher 在测试环境 web 研究超时（非 skill 缺陷；platform 分支经 AC9 结构 + 父说明路由验证）。详见 `research/e2e-findings.md`。

## Out of Scope

- 内容/自媒体、产品/软件业态的方法（sibling tasks `07-01-opp-methods-content` / `-product`）。
- 服务业态里的 done-for-you 服务 / research-as-a-service 两条子线（本任务只做 info-product；已登记为 follow-up）。
- **Substack / Udemy 平台子说明**（首批只做 Gumroad/KDP/Etsy；父说明列菜单标"待补"，排后续 child）。
- 服务业态的**执行能力**（部门 charter + 出站交付动作）——父 PRD 层③，另开。
- 度量/token-ROI 读数层（父 PRD 层④）。
