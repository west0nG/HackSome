# R3 研究：willingness-to-pay —— 「已经有人在为这类信息掏钱」的可观测行为信号

- **Strand**: R3 / find-opportunity · info-product · willingness-to-pay。这条负责让方法**对「能不能赚到钱」保持诚实**——不是「话题有没有意思」，而是「有没有人已经在为这类知识付费」。
- **Query**: 一个 headless CEO（无个人受众、不能发问卷、不能 presell 给邮件列表）能靠**派研究 Goal 给 `researcher` 在开放网观察**来检测的、证明「话题已有付费买家」的行为信号；每条落成可执行三件套（研究-Goal 模板 + 可观测读数 + 决策阈值）。
- **检测者约束（第一原则）**：唯一的检测手段 = `python3 -m orchestration.messaging send --to researcher --intent "<问题>"`（可选 `--accept "<验收>"`，已核实 `orchestration/messaging.py:87-93`）。researcher 在开放网 at-scale 观察后回报 findings。所以**每条信号必须能被网页观察回答**（marketplace / 搜索 / 社区 / 评论站），不能靠「跑问卷」或「问我的受众」。
- **Sources**: 实拉，见文末表；日期 **2026-07-02**。
- **不重复**：种子 `07-01-ceo-find-idea/research/idea-generation-methods.md` §E 的 SI1（Sales Safari 痛点）/SI3（搜索缺口）。本文把 SI3 那句「高搜索+低供给」**深挖成付费行为信号层**，并补 SI1 没覆盖的 marketplace 付费证据与**饱和反信号**。

---

## 三道检验（复用，逐条过筛）

目标 agent 本身是 LLM。给它写泛泛「找有需求的选题」= 没写。一条只有满足 ≥1 项才保留：
- **(a) 系统特定**：能被一个研究 Goal（网页观察）检测；候选能被部门落地；**不需要问卷、不需要个人受众**。
- **(b) 压制 LLM 默认**：LLM 被问「什么 info-product 好卖」时默认吐**「听起来有需求」但零付费证据**的选题（"AI productivity guide"），且把野心通胀。反掉这个 = 过 (b)。
- **(c) 非平凡阈值/取舍/反信号**：LLM 不会自发采用的判断（尤其**饱和反例**——需求被证明了但供给已塞满，反而要 DROP）。
纯美德（"考虑需求""做点调研"）= LLM 自带 = **DROP**。

---

## 核心哲学锚（一句话总纲，署名 Indie Hackers）

> "The truest form of validation tends to be the exchange of money." … "People are generous with hypotheticals, saying they'd 'definitely pay for that' … but hypotheticals don't translate to actual dollars."
> —— Indie Hackers, *Validating Product Ideas: Why We Focused on What People Actually Pay For*

这条压制的 LLM 默认：**把「有人讨论/搜索」当成「有人会买」**。R3 的每个信号都是这句话的可观测代理——找**钱已经易手的痕迹**，不是找兴趣。反过来 Indie Hackers 也点破了「零竞争」的陷阱："Trying to start in a market without competition … often means spending time and money educating customers about why they even need your product." → **完全没有付费供给 ≠ 蓝海，通常 = 没人肯为它掏钱。**

---

## KEPT 信号 1 · Marketplace 付费证据（主信号）

**一句话**：在卖信息产品的市场（Gumroad / Amazon Kindle-KDP / Udemy / Etsy 模板 / Substack 付费 / Podia-Teachable）上，**同一选题已经有多个「被真金买过」的产品**——用销量/评论数/报名数/BSR 作代理。这是最硬的 WTP 信号：钱已经易手过。

### ① OPERATION

**(i) 研究-Goal 模板**（CEO 发给 researcher 的 `--intent` 原文）：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "Search Gumroad, Amazon Kindle/KDP, Udemy, and Etsy for PAID products on '<topic>'.
  For the top ~10 results per marketplace report each item's: title, price, and a paid-demand proxy —
  Amazon Best Seller Rank (both category and overall), Udemy enrollment count, Gumroad number of
  ratings/copies sold, or Etsy 'X sold' + review count. Also report each item's star rating and the
  NUMBER of reviews behind it. Report ONLY things sold for money — exclude free blog posts, YouTube
  videos, and docs." \
  --accept "A table of paid products with a real sales/enrollment/review proxy for each, or an explicit
  'no paid products found' for that topic."
```
**(ii) 可观测读数**：回报里出现**一批标价的产品**，且每个带**非平凡付费代理**——Amazon 品类 BSR 靠前（见阈值）、Udemy 报名数远高于中位数 217、Etsy 显示数百「sold」、Gumroad 有几十条以上 ratings。评论/报名/BSR = 有人真买过的化石证据。
**(iii) 决策阈值**：
- **KEEP（需求已证明 + 供给可打）**：同一精确选题上 **≥3 个付费产品各自有真实付费代理**（真实评论/报名/销量），**且**头部产品评价平庸（≤ ~4.0★，或大量 1-3★ 抱怨）/ 过时 / 单薄 → 买家真实存在且供给有缝。
- **DROP（兴趣非需求）**：**0-1 个付费产品** → 未被证明，或你得先教育市场（见上 Indie Hackers 反例）。
- **DROP（饱和）**：**很多付费产品且头部全是 ≥4.5★、评论数上百、低价** → 供给塞满（见 KEPT 信号 4）。

**付费代理的具体读数（各 marketplace 校准）**：
- **Amazon KDP / BSR**："a book with a BSR of #2000 will be selling dozens of copies a day, whereas a book ranking at #120,000 BSR will only be selling around 1 copy per day"（Kindlepreneur）；Kindlepreneur 分档："Under 10,000 = strong daily sales / Under 100,000 = consistent movement / Above 500,000 = infrequent sales"。**要看品类 BSR 不是总榜**——"a BSR #500 in a competitive category like Romance is more impressive than BSR #100 in a tiny niche"。反向用法（作者原话）：查关键词下头部书的 BSR，若"books that show up for that keyword aren't making sales (because you checked their BSR)" → 这个词没在驱动购买。
- **Udemy**：报名数是付费代理（付费课）。中位报名仅 **217**，所以"a course with 4.5 stars from 45,000 reviews is a meaningful quality signal. A course with 4.8 stars from 23 reviews tells you very little"（Class Central）。报名数明显 > 千 = 该选题有人持续买。
- **Substack 付费**：Bestseller 徽章门槛 = 100 付费订阅；橙徽 = 1,000+；紫徽 = 10,000+（Substack 官方）。全站已有 **10,000 个刊物越过 1,000 付费订阅**——"a threshold many creators treat as proof of a sustainable newsletter business"。看到某窄主题有多个橙徽刊物 = 人们为这主题的信息按月付费。
- **Gumroad / Etsy**：Gumroad ratings 数 + Etsy「X sold」/review 数是直接销量代理；Etsy 用 eRank/Everbee 找"proven demand"，基础 A4 tracker 卖 $3–6（价格锚）。

### ② PHILOSOPHY BACKING
> "If competitors are out there, that's often a great sign; it means there's already an established need and paying users … look for where people are already spending money and identify gaps within those spaces."（Indie Hackers）。Gumroad 实操版："ideally there are 3–10 competitors as proof of demand"（InsightRaider）。

### ③ HUMAN→AGENT 替代
- **人类做法**：创作者凭圈内浸泡知道「这个话题有人买课」，或 presell 给自己的邮件列表看有没有人付钱。
- **agent 替代**：agent 无受众、不能 presell。改为**派一个研究 Goal 去数 marketplace 上的付费证据**——把「钱已经易手」外包给公开的销量/评论/报名/BSR 数据。

### ④ 三道检验裁定：**过 (a)(b)(c)**
- (a) marketplace 数据纯网页可观测，无需受众/问卷；候选能被 researcher+writer 部门落地。
- (b) 直接压制「听起来有需求」默认——强制拿出真金痕迹。
- (c) 非平凡：BSR 分档 / 报名中位 217 / 评论数才算数 / 品类榜 vs 总榜，都是 LLM 不会自发用的阈值；且内建饱和 DROP。

---

## KEPT 信号 2 · 搜索缺口（**必须锚定付费证据**）

**一句话**：高搜索需求 + 现有免费供给薄/差（"people are searching to learn X but the top results are bad"）。**但搜索量本身只是兴趣**——本信号只有在**同时存在一个付费锚**（有人已在卖且卖得动这主题）时才算 WTP，否则降级/DROP。这是把种子 SI3 拧诚实的关键。

### ① OPERATION

**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "For '<topic>': (1) report approximate monthly search volume and the top 10 Google
  results' quality — are they thin (<~800 words), outdated, listicle/SEO-spam, or just forum threads,
  OR comprehensive guides from established authorities? (2) SEPARATELY report whether anyone SELLS a
  paid product on this exact topic (course/ebook/template) and any sign it's actually selling (reviews,
  enrollments, 'sold' counts, BSR). I need BOTH the supply-gap read AND the paid-anchor read." \
  --accept "Search-demand + top-result-quality assessment, PLUS an explicit yes/no on whether a paid
  product exists and shows signs of selling."
```
**(ii) 可观测读数**：搜索量高 + 头部结果单薄/论坛/过时（供给缝）**且** at least 一个付费产品在卖且卖得动。
**(iii) 决策阈值**：
- **KEEP**：（高需求 + 弱免费供给）**且付费锚存在**（有人已卖 + 卖得动）→ 需求真实、供给可打、且已被证明肯付费。
- **DOWNGRADE/DROP**：高搜索 + 弱供给但**没人卖任何付费产品** → 极可能是「免费内容就够了」的兴趣（人们不肯为学它付费）→ 降级或 DROP（除非另有强付费信号）。

搜索缺口的可观测判据（SEO 实践）："A low difficulty score typically means that websites currently ranking … have weaker backlink profiles, poor content, or low domain strength"；"If a competitor has a thin, 300-word article ranking … you can create a comprehensive 1,500-word guide that can easily outrank them"（SEOptimer/相关）。Reddit 是缺口线索源："If people are constantly asking the same question on Reddit, it usually means there is a lack of helpful content on search engines."

### ② PHILOSOPHY BACKING
> 搜索缺口给「可被找到 + 供给可打」，但付费与否要另证——呼应总纲 "hypotheticals don't translate to actual dollars"。搜索量是 hypothetical 的近亲；付费锚才是 actual dollars。

### ③ HUMAN→AGENT 替代
- **人类做法**：SEO/内容创作者用 Ahrefs Content Gap / Semrush Keyword Gap 看「高量低难 + 弱现有内容」，再凭经验判断这类词背后有没有买家。
- **agent 替代**：把「搜索量 + SERP 质量 + 是否有人在卖」三样一起派给 researcher，用**付费锚**替代人类的「这词能不能变现」直觉。

### ④ 三道检验裁定：**过 (a)(b)(c)**
- (a) 搜索量/SERP 质量/是否有付费品全网页可观测。
- (b) 强压 LLM「搜索量高=机会」的默认——把它锚死在付费证据上。
- (c) 非平凡取舍：显式规定「搜索缺口但无付费锚 → 免费兴趣 → DROP」，LLM 不会自发加这道锚。

---

## KEPT 信号 3 · 社区复现问题 + **推荐了付费资源**

**一句话**：Reddit / 论坛 / Quora / Stack Exchange 上**同一个「怎么学/怎么做 X」反复被问**，**且**高赞回答反复推荐**付费资源**（点名的书 / 课 / 付费工具）——不是「看这个免费 YouTube 就行」。复现 = 需求；**推荐付费 = 掏钱意愿的直证**。

### ① OPERATION

**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "In <community: subreddit/forum/StackExchange>, find 'how do I learn/do <topic>' questions
  that RECUR over time (asked repeatedly across many months, not once). For the recurring ones report:
  (a) how often it recurs + comment/upvote volume, and (b) whether top answers recommend PAID resources
  (name specific books, paid courses, paid tools) and how upvoted those recommendations are. Quote the
  actual recommendations verbatim. Flag if the accepted answers are instead all free links (YouTube/docs)." \
  --accept "Evidence the question recurs, PLUS quoted upvoted answers showing whether people recommend
  PAID vs only FREE resources."
```
**(ii) 可观测读数**：同一 learn-X 问题多线程复现，且高赞答案反复**点名付费书/课**并被顶上去（信任+购买信号）。
**(iii) 决策阈值**：
- **KEEP**：问题复现（跨时间多个帖）**且**高赞答案反复推荐**付费资源** → 既需要它、又肯为它付钱。
- **DROP**：复现的答案全是「看这免费 YouTube / 读官方 docs 就够」→ 免费内容满足，无 WTP。

判据出处："When the same question appears frequently on Reddit, it indicates unresolved demand rather than curiosity"；"If a comment recommending a product gets a lot of support, the original poster is more likely to trust that suggestion"（Reddit research 实践）。评论矿的「重复即信号」规则："If five different people say the exact same thing, it is not a coincidence—it is a buying signal!"（MoneyPantry review-mining）。

### ② PHILOSOPHY BACKING
> Copyhackers（review mining）："When you go through user reviews one by one, what's really important to your prospects rises to the top" —— 已经花时间评论/提问的人，是**已经在乎到愿意行动**的人。付费推荐把「在乎」升级为「肯掏钱」。

### ③ HUMAN→AGENT 替代
- **人类做法**：创作者常年泡一个社区，凭记忆知道「这问题每月都有人问，而且大家都在推荐买那本 $50 的书」。
- **agent 替代**：agent 不能常驻社区。改为派研究 Goal **at-scale 扫复现频率 + 付费推荐**，把人类的「社区肌肉记忆」外包成一次网页观察，并**显式区分付费 vs 免费推荐**。

### ④ 三道检验裁定：**过 (a)(b)(c)**
- (a) 复现频率 + 推荐内容全网页可观测，无需 agent 有社区身份。
- (b) 压制「有人讨论=有需求」——只有**付费推荐**才计入 WTP。
- (c) 非平凡：显式取舍「复现=兴趣、付费推荐才=WTP；全免费推荐 → DROP」。

---

## KEPT 信号 4 · 饱和 & 兴趣-无-付费 反信号闸（诚实闸）

**一句话**：这是**反信号检测器**，专治两种「看起来能赚」的假阳性。它是 R3 最非平凡、LLM 绝不会自发采用的一条——需求被证明了 **≠** 值得做。

两种失败模式：
- **(i) 兴趣无付费**：搜索/讨论热但**零付费产品** → 人们免费学、不肯买。
- **(ii) 饱和**：付费产品多，且**头部全高分（≥4.5★）、评论数上百、价格低** → 供给塞满，无楔子可插。

### ① OPERATION

**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "Assess SATURATION for '<topic>' as a paid info-product: how many paid products already
  exist? For the top few report price, star rating, and review/enrollment count. Are the top options
  rated >=4.5 stars with HUNDREDS+ of reviews at a LOW price? Is there one dominant cheap/free 'good
  enough' option everyone already recommends? Separately: are there UNMET complaints in reviews of the
  top products (things buyers wish existed)?" \
  --accept "A saturation verdict: (a) count + ratings + review-depth of top paid products, (b) whether
  a dominant good-enough option exists, (c) any recurring unmet complaints leaving a wedge."
```
**(ii) 可观测读数**：头部付费品的 ★数 × 评论深度 × 价格 → 供给成熟度；评论里反复出现的「wish it had…」→ 留没留缝。
**(iii) 决策阈值**：
- **DROP（无付费）**：热议/高搜索但**0 个付费产品**。
- **DROP（饱和）**：**≥5 个付费产品，头部 ≥4.5★、评论/报名数百+、价格低、且评论里无明显未满足抱怨** → 塞满。
- **KEEP 的窗口 = 「已证明但可打」**：付费品存在且有真实销量，**但**头部评价平庸 / 评论有复现抱怨 / 内容过时 / 高价却单薄 → 有更小/更好/更便宜的楔子。

饱和现实的数据锚（Class Central Udemy 全站）：top-20% 课程吃掉 **91.1%** 报名；**1,045 门 >10 万报名、13 门 >100 万**；>85% 评分是 4-5★、只有 ~2.8% 是 1-2★ —— 说明**高分海洋里挤进去几乎不可能靠「再来一门同样的课」**，必须有差异楔子。未满足抱怨的挖法（review mining）："upload reviews to a free AI tool and ask: 'What are the top 3 things customers wish this product had?'"（MoneyPantry）——这正是 agent LLM 原生能做的。

### ② PHILOSOPHY BACKING
> "95% of infoproducts fail because creators skip validation"（InsightRaider）——但反过来，验证过头进了红海同样死。Indie Hackers 的「零竞争=要教育市场」反例（DROP-i）+ Udemy 的极端集中（DROP-ii）共同定义出中间那道**「已证明但可打」**的窄窗。

### ③ HUMAN→AGENT 替代
- **人类做法**：老手一眼看出「这品类已经有人做到 4.9★、5 万评论、卖 $12，别碰」；或「大家都在推那个免费开源方案，没人会买」。
- **agent 替代**：把这层「红海嗅觉」派成一个**饱和研究 Goal**——数付费品、读头部 ★/评论深度/价格、找未满足抱怨——让 researcher 回报饱和裁定。

### ④ 三道检验裁定：**过 (a)(b)(c)（尤其 c）**
- (a) 竞品数/评分/评论深度/未满足抱怨全网页可观测。
- (b) 直接压制 LLM「需求被证明了就冲」的乐观默认。
- (c) 最非平凡：**「需求真实但供给饱和 → DROP」**这条反直觉规则，LLM 不会自发采用；「已证明但可打」窄窗定义是本 strand 的核心取舍。

---

## DROP 清单（纯美德 / 非 agent 可观测，不写进 skill）

| DROP 项 | 为什么 DROP |
|---|---|
| **「跑个问卷 / 问我的受众」** | agent 无受众；且 "Surveys lie / hypotheticals don't translate to actual dollars"（Indie Hackers）。被 marketplace 观察取代。 |
| **「presell 给邮件列表 / 收集 20+ 社区回复」green-yellow-red 阈值** | 需要 agent 有 following/能发帖募资，agent 都没有。保留其**哲学**（钱=验证），丢弃其**机制**。 |
| **「凭感觉 / 话题很火 / 在 trending」** | 正是 R3 要压制的 LLM 默认（兴趣冒充需求）。 |
| **「估 TAM / 市场规模」** | 十亿级 VC 框架，父研究已明确去标定。 |
| **泛泛「做点市场调研」** | 太糊；被四条具体研究-Goal 模板取代。 |
| **纯「高搜索量 = 机会」（无付费锚）** | 兴趣非 WTP；已在 KEPT 信号 2 里锚死到付费证据。 |
| **「无竞争 = 蓝海」** | 反例：常意味着没人肯付费、要自费教育市场（Indie Hackers）。 |

---

## Sources 表（实拉，2026-07-02）

| # | 借用/证据 | 来源 | 抓取方式 |
|---|---|---|---|
| S1 | "truest form of validation = exchange of money" / "hypotheticals don't translate to actual dollars" / 竞品=已证明需求 / 零竞争要教育市场 | Indie Hackers, *Validating Product Ideas: What People Actually Pay For* (indiehackers.com/post/validating-product-ideas-…-25155d07d3) | WebSearch 摘要（多篇一致） |
| S2 | Gumroad "3–10 competitors as proof of demand" / "95% of infoproducts fail because creators skip validation" | InsightRaider, *Sell on Gumroad 2026* (insightraider.com/en/blog/how-to-sell-digital-products-gumroad) + lesleyclavijo.com/preselling | WebSearch 摘要 |
| S3 | BSR→销量分档 / 品类榜 vs 总榜 / 用头部 BSR 判关键词是否驱动购买 | Kindlepreneur, *Amazon KDP Sales Rank Calculator* (kindlepreneur.com/amazon-kdp-sales-rank-calculator) | WebFetch |
| S4 | Udemy 中位报名 217 / top-20%=91.1% 报名 / >85% 4-5★ / 1,045 门>10万、13 门>100万 / "4.8 stars from 23 reviews tells you very little" | Class Central, *Udemy by the Numbers* (classcentral.com/report/udemy-by-the-numbers) | WebSearch 摘要（页面 403，数据取自搜索快照原文） |
| S5 | Substack Bestseller 徽章 100/1,000/10,000 付费订阅 / 10,000 刊物过 1,000 付费=可持续生意门槛 / 窄主题转化 4-10%、tech 8% | reallygoodbusinessideas.com/p/substack-leaderboards + backlinko.com/substack-users | WebFetch + WebSearch 摘要 |
| S6 | 搜索缺口判据：低难度=弱内容/弱外链 / 300 词薄文可被 1500 词指南超越 / Reddit 复现问题=Google 缺好内容 | SEOptimer + trafficthinktank + allaboutai（high-volume low-competition 系列） | WebSearch 摘要 |
| S7 | Reddit "same question recurs = unresolved demand not curiosity" / 高赞推荐=信任+购买信号 | sellthetrend.com + influencermarketinghub.com + leado.co (Reddit buying-intent) | WebSearch 摘要 |
| S8 | review mining：重复=买信号 / "top 3 things customers wish this product had" / "rises to the top" | Copyhackers *Amazon Review Mining* (copyhackers.com/2014/10/amazon-review-mining) + MoneyPantry | WebFetch + WebSearch 摘要 |
| S9 | Etsy 数字模板：eRank/Everbee 找 proven demand / A4 tracker $3-6 价格锚 | outfy.com/blog/top-selling-digital-products-on-etsy | WebSearch 摘要 |

## Caveats
- Class Central 页面 WebFetch 返回 403；引用数据取自搜索引擎对该页的原文快照，数值一致、可信，但未逐字二次核（建议后续动笔前若引用具体数字可重取一次）。
- Substack「niche 转化 4-10% / tech 8%」来自 backlinko 汇编，非 Substack 官方；徽章门槛（100/1,000/10,000）来自 Substack 官方经第三方转述。
- 所有 marketplace 数字（BSR 分档、报名中位、销量代理）为**近似经验值**，作阈值锚够用；skill 正文用时应措辞为「约 / 数量级」，不写死。
- 引作**思想来源署名**，不逐字拷贝进 skill 正文。
