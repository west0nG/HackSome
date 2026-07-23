# Etsy 子playbook —— headless agent 如何在 Etsy 上找到「已被证明有人付费」的小型数字产品机会

- **日期**: 2026-07-02
- **归属**: `find-opportunity` 的**平台特定子playbook / Etsy**。父方法（platform-agnostic 7 步）已定「不要凭空想 idea，先找 people ALREADY PAY 的证据，再定义一个小型 text 产品」。本文回答：一个 headless LLM CEO **具体在 Etsy 上**怎么找到一个真实、小、能赚钱、且**由 text/design-light agent 自己就能作出来**的数字下载品（printables / planners / templates / worksheets / spreadsheets）机会。
- **不重复**：本任务 `research/r3-willingness-to-pay.md` 已确立通用 WTP 原则（marketplace 付费证据、饱和反信号、Etsy「X sold」+ 评论数作代理、eRank/Everbee 找 proven demand、基础 tracker $3–6 价格锚）。本文**把 Etsy 那几行深挖成完整的 Etsy 机会发现 playbook**：加上 Etsy 的**搜索-供给缺口量化读数**、**Etsy SEO/tags 是唯一发现引擎**这一平台机制、**「X sold」+ top-10 评论数**读缝法、**2026 AI-flood 反通用信号**、以及**text/design-light agent 能作什么形状**的产品筛。

## 检测者约束（第一原则，继承 r3）
CEO 的唯一两个动作：(1) 派研究 Goal：`python3 -m orchestration.messaging send --to researcher --intent "<问题>"`（可选 `--accept "<验收>"`）；researcher 在开放网 at-scale 观察后回报 findings。(2) LLM-native 自己作文件。**所以本文每条方法的 OPERATION 都必须能被一个研究 Goal（网页观察 Etsy 搜索页 / eRank / EverBee 公开数据）回答**——不能靠 agent 自己有 Etsy 店、有受众、或跑问卷。绑定约束 = ETSY 上已证明的付费需求 + 可打的缝，不是「我们能不能作」。

## 三道检验（复用 r3，逐条过筛，保留仅需 ≥1）
- **(a) 系统特定**：能被一个研究 Goal 检测（Etsy 搜索页 / eRank / EverBee 全网页可观测）、候选能被部门落地、不需受众/问卷。
- **(b) 压制 LLM 默认**：LLM 被问「Etsy 卖什么数字品好」默认吐**「听起来有需求」的通用品**（"printable budget planner"），且以为「我能生成 = 有机会」。反掉这个 = 过 (b)。
- **(c) 非平凡阈值/取舍/反信号**：尤其 **Etsy SEO 缝 + 饱和** 这对——需求被证明了但供给塞满/全是通用 AI 货，反而 DROP。
- 纯美德（"做点调研""让它更好看""加独特功能"）= LLM 自带 = **DROP**。

---

## 核心哲学锚（两句总纲）

**锚一 · Etsy 是「搜索发现」市场，不是「受众」市场**（区别于 Gumroad）：
> "Etsy search gathers all the listings that have keywords that match a shopper's query." 之后 "we use the information we have about each listing and shop to rank the listings"（Etsy Seller Handbook, *The Ultimate Guide to Etsy Search* / *How Etsy Search Works*）。

含义：Etsy 上**没有受众也能被买家找到**——tags/title 的关键词匹配（query matching）+ listing quality score（点击率/购买率）就是发现引擎。这正好适配一个 headless agent：机会 = 一个「有搜索、供给可打、且新 listing 能靠 SEO 排进去」的关键词，而不是「我有多少粉丝」。

**锚二 · 2026 的 Etsy 已被 AI 通用货灌满——通用 = 死**（这是本 playbook 压制 LLM 的核心）：
> "In 2026, listing a generic 'printable planner' isn't enough, as the market has seen a flood of low-effort, AI-generated content, and buyers are looking for curated systems, hyper-specific solutions, and verified human quality."（growingyourcraft / mydesigns）
> "Specificity. 'Watercolor floral clipart' is competitive. 'Watercolor western sunflower clipart' [wins the niche]."（mydesigns）

含义：一个 LLM CEO 的天然默认恰恰是「生成一个通用 printable budget planner」——而那是 2026 Etsy 上最没戏的动作。机会必须**超窄、锚在具体身份/场合/软件版本**上。

---

## KEPT 方法 E1 · 搜索-供给缺口量化读（eRank/EverBee 关键词数据）

**一句话**：拿一个候选关键词，读它的 **Etsy 月搜索量 vs 该词下的 listing 数（供给/竞争）vs keyword difficulty**。高搜索、供给未塞满、难度低 = 可发现的�beatable缝。这是 Etsy 版「搜索缺口」，但用 Etsy-native 数据量化。

### ① OPERATION
**(i) 研究-Goal `--intent` 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "For the Etsy keyword '<keyword>' (a digital-download niche): report (1) approximate MONTHLY
  ETSY SEARCHES (eRank/EverBee 'Average Searches' or equivalent), (2) the NUMBER OF LISTINGS competing
  for it — read the 'X results' count on Etsy's search page AND eRank 'Etsy Seller Competition', (3) the
  keyword-difficulty / competition score if available, and (4) whether it is a broad HEAD term or a
  specific LONG-TAIL term. Do the same for 2-3 more specific long-tail variants of it. Report numbers,
  not adjectives." \
  --accept "A table: keyword | monthly searches | competing-listing count | difficulty | head-vs-longtail,
  for the seed keyword and its long-tail variants."
```
**(ii) 可观测读数**：eRank 的 Average Searches / Average Clicks / CTR / Etsy Seller Competition / Keyword Difficulty；Etsy 搜索页顶部的「X results」= 供给量；EverBee 的 205M+ listing 库按 sales/revenue 过滤。
**(iii) 决策阈值**（经验锚，措辞用「约/数量级」）：
- **KEEP（有需求且可打）**：月搜索 **≳ 数百**（EverBee 实操门槛 "at least 500 monthly searches"），且供给 **未塞满**（EverBee sweet spot "under 100,000 competing listings"；eRank "green zone" 竞争约 **< 20,000** listing），keyword difficulty **低**（"the lower the number, the less competition ... indicating a possible opportunity"）。
- **DROP（需求太薄）**：月搜索 **极低**——Printful 实例把 "**22 people search for this product** monthly" 判为 too low，尽管 CTR 高。
- **DROP（供给饱和/头词打不动）**：宽头词（"digital planner"）或某窄词已 "**853 other stores selling this product**"（Printful 判为对该小众而言已 saturated）。头词交给长尾变体。

### ② PHILOSOPHY BACKING
> "Keyword Difficulty is an eRank score ... The lower the number, the less competition there is for this keyword versus search volume, indicating a possible opportunity in the marketplace."（eRank, *Etsy SEO Tutorial*）。EverBee guide："keywords with at least 500 monthly searches but under 100,000 competing listings, representing the 'sweet spot' for SEO targeting."

### ③ HUMAN→AGENT 替代
- **人类做法**：卖家装 eRank/EverBee Chrome 插件，手动敲词看 searches vs competition，凭经验判 green zone。
- **agent 替代**：agent 无插件 UI。改派研究 Goal 让 researcher 把这些**公开数值**（eRank/EverBee 页面 + Etsy 搜索页 "X results"）取回，用固定阈值替代人类「绿区手感」。

### ④ 三道检验裁定：**过 (a)(b)(c)**
- (a) searches/listing count/difficulty 全网页可观测，无需店铺。
- (b) 强压「我觉得这词有人搜」——逼出真数字 + 供给对比。
- (c) 非平凡：500 搜索 / <100k or <20k 供给 / 头词 vs 长尾 / 22 搜索太低——LLM 不会自发用这些 Etsy 特定阈值。

---

## KEPT 方法 E2 · 「X sold」+ top-10 评论数：Etsy-native 付费证据 + 读缝

**一句话**：Etsy 每个 listing 都露出 **「X sold」计数**、**评论数**、**星级**、有时还有 **Bestseller 徽章 / "in N carts"**。读 top-10 listing 的这几个数就同时得到两件事：**需求是否已被真金证明**（有 listing 卖出成百上千 + 大量评论），以及**缝在哪**（top 位置里若有低评论/平庸星级 listing，就是新品能挤进去的口子）。这是 r3「marketplace 付费证据」的 Etsy 精确落地。

### ① OPERATION
**(i) 研究-Goal `--intent` 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "Search Etsy for '<keyword>' (digital download). For the TOP ~10-15 listings report each one's:
  price, the 'X sold' count, the number of reviews, the star rating, whether it has a Bestseller/Star-Seller
  badge, and (via EverBee if available) estimated MONTHLY sales/revenue. I need two reads: (A) PROVEN PAID
  DEMAND — are multiple top listings selling in the hundreds/thousands with real review depth? and (B) A
  BEATABLE GAP — are there listings ranking in the TOP positions that have LOW review counts, mediocre
  ratings, or complaints? Quote the exact 'sold' and review numbers." \
  --accept "A table of top listings with price / 'X sold' / review count / stars / badges / est. monthly
  sales, PLUS an explicit verdict on (A) demand proven yes/no and (B) is there a low-review or mediocre top
  listing = a gap."
```
**(ii) 可观测读数**：Etsy listing 页/搜索页直接显示的「X sold」、review 数、★、Bestseller 徽章、"in N carts"；EverBee 补估计月销量/营收（Etsy 不直接露）。
**(iii) 决策阈值**：
- **KEEP（已证明 + 可打）**：多个 top listing **成百上千 sold**（付费已发生），**且**至少一个 top-位置 listing **评论数低 / 星级平庸（≤~4.0★）/ 有复现抱怨** → 需求真、有缝插。
- **DROP（未证明）**：top listing 全是个位/几十 sold、评论寥寥 → 兴趣非需求（呼应 r3：0–1 付费产品 = 未证明）。
- **DROP（饱和红海）**：top 全是 **4.5★+、评论/销量上千、价格触底、有 Bestseller 徽章霸榜** → 塞满，新品排不进（r3 饱和 DROP 的 Etsy 版）。
- **EverBee 找新贵缝**："substantial monthly revenue but fewer than 50 reviews" = 尚未被评论护城河锁死的新兴 best-seller → 强 KEEP 信号。

### ② PHILOSOPHY BACKING
> "Search your target keyword on Etsy and study review counts on the top 10 listings—high review counts confirm real buyer demand, while low counts in top positions signal an opening."（printables 实操案例簇：aliciarafieiblog / insightagent）
> EverBee guide："filtering for listings with substantial monthly revenue but fewer than 50 reviews—this surfaces newer best-sellers that haven't yet saturated the review market."

### ③ HUMAN→AGENT 替代
- **人类做法**：卖家肉眼扫 top listing 的「X sold」和评论数，凭手感判「有人买 + 有缝」。
- **agent 替代**：派研究 Goal at-scale 取回 top-10 的 sold/reviews/stars/badges，把「已证明」和「缝」都变成显式数值裁定；EverBee 补 Etsy 不露的月销量。

### ④ 三道检验裁定：**过 (a)(b)(c)**
- (a) sold/reviews/stars/badges 全在 Etsy 页面可观测。
- (b) 压制「这品类听起来有人买」——逼出真实 sold + 评论深度。
- (c) 非平凡：**同一读数既证需求又找缝**、"<50 reviews 但高营收 = 新贵"、"全 4.5★+ 上千评论 = DROP" 都是 LLM 不会自发用的取舍。

---

## KEPT 方法 E3 · Etsy SEO 可排性闸：新 listing 真能被搜到吗（长尾 + 13 tags + recency）

**一句话**：Etsy 是 SEO 发现市场——机会只有在**一个全新、零评论的 listing 真能靠 tags/title 排进目标关键词**时才成立。所以每个候选关键词必须过一道「可排性」闸：**它是足够窄的长尾**（新品能匹配 + 靠 recency boost 起量），而不是被老店 listing-quality-score 霸死的头词。这是 Etsy 区别于 Gumroad 的机制性方法（Gumroad 靠外部导流，Etsy 靠站内 SEO）。

### ① OPERATION
**(i) 研究-Goal `--intent` 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "For candidate Etsy keyword '<keyword>': assess whether a BRAND-NEW zero-review digital listing
  could realistically rank. Report: (1) is it a broad head term or a 3+ word long-tail? (2) what specific
  long-tail phrasings do the current top listings actually use in their TITLES and (if visible) TAGS?
  (3) do the top listings look like entrenched high-review/Bestseller shops that would dominate query
  matching + listing-quality-score, or is there room? Propose 3-5 long-tail keyword phrasings (audience +
  occasion + style/software) that a new listing could target across its 13 tags." \
  --accept "Head-vs-longtail verdict, the actual title/tag phrasings top listings use, a rankability read
  (entrenched vs open), and 3-5 concrete long-tail target phrasings."
```
**(ii) 可观测读数**：Etsy 搜索结果里 top listing 的 title 措辞、可见 tags、评论护城河深度、Bestseller/Star-Seller 徽章密度；候选词的头/长尾属性。
**(iii) 决策阈值**：
- **KEEP**：目标锁在**3+ 词长尾**（"Goodnotes Student Academic Planner 2026" 而非 "Digital Planner"），top 位置**不是全被上千评论老店霸榜** → 新品可经 query matching + 14–21 天 recency boost 起量。
- **DROP/改词**：只瞄宽头词、或 top 全是 Bestseller 老店 → 新零评论 listing 排不进，回 E1 换更窄长尾。
- **落地要点（作产品时）**：title 前 40 字符 front-load 主关键词（移动端截断）；用满 **13 个 tags**、每个不同的长尾变体，别 13 个 listing 复用同一组 tags（内耗）。

### ② PHILOSOPHY BACKING
> Etsy 官方两段式："query matching"（title/tags/attributes/categories 关键词匹配）→ "ranking"（listing quality score = 点击率/加购/购买率 + recency + shop quality）。BetterListing："Front-Load high-volume terms in the first 40 characters"；"Use all 13 tags without repetition"；长尾 "Goodnotes Student Academic Planner 2026 beats Digital Planner"。2026 recency boost 窗口缩到 **14–21 天**（多篇 SEO 指南一致）。

### ③ HUMAN→AGENT 替代
- **人类做法**：卖家凭经验知道「新店别碰头词，挑长尾先起量」，手动抄 top listing 的 tag 措辞。
- **agent 替代**：派研究 Goal 把「头/长尾 + top listing 用的 tag 措辞 + 是否被老店霸榜」取回，把「新店该打哪个词」变成显式可排性裁定；长尾短语直接喂给自己作 listing。

### ④ 三道检验裁定：**过 (a)(b)(c)**
- (a) 头/长尾、top tag 措辞、徽章密度全可观测。
- (b) 压制 LLM「我瞄 'digital planner' 这个大词」的默认——Etsy 上等于自杀。
- (c) 非平凡：Etsy 特有的「query matching + listing quality score + recency 14–21 天 + 长尾可排性」机制，LLM 不会自发建模。

---

## KEPT 方法 E4 · 反通用/反 AI-flood 闸（诚实闸，本 playbook 最压制 LLM 的一条）

**一句话**：这是**反信号检测器**，专治一个 LLM CEO 的头号失败模式——「我生成一个通用 printable budget planner 就行」。2026 Etsy 已被低质 AI 货灌满，通用品即使需求被证明也排不进、卖不动。机会必须**超窄、锚在具体身份/场合/软件/风格**上。

### ① OPERATION
**(i) 研究-Goal `--intent` 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "For '<candidate product>' on Etsy: is the top of search dominated by GENERIC, low-effort,
  interchangeable, likely-AI-generated listings (the same plain 'budget planner' repeated), OR by
  HYPER-SPECIFIC listings anchored to a concrete buyer identity / occasion / software / style? Report the
  degree of generic saturation. Then mine the reviews and Q&A of the top listings for what buyers WISH
  existed (a specific audience/occasion/format not yet served). Propose the most specific defensible angle
  (e.g. 'nurse night-shift budget planner', 'Notion wedding-seating template', not 'budget planner')." \
  --accept "A generic-saturation read (generic vs specific top listings), quoted buyer 'wish it had' gaps,
  and a hyper-specific product angle."
```
**(ii) 可观测读数**：top listing 的通用/雷同度；评论/Q&A 里反复出现的 "wish it had / does it work for <X>" 未满足抱怨；某窄身份/场合是否已有专属供给。
**(iii) 决策阈值**：
- **KEEP**：候选是**超窄、身份/场合/软件锚定**的角度，且评论里有对应的未满足抱怨 → 有可防御的差异。
- **DROP（通用陷阱）**：候选是通用大类（"printable planner" / "budget spreadsheet" 裸词）且 top 已被雷同 AI 货塞满 → 即便需求真也别作（2026 "listing a generic 'printable planner' isn't enough"）。
- **DROP（定价自杀）**：想靠 **$1 低价**抢量 → "$1 listings don't signal quality"，且拉低 listing quality。

### ② PHILOSOPHY BACKING
> "the market has seen a flood of low-effort, AI-generated content, and buyers are looking for curated systems, hyper-specific solutions, and verified human quality."（growingyourcraft/mydesigns）
> review-mining（r3 沿用）："upload reviews ... ask: 'What are the top 3 things customers wish this product had?'"（MoneyPantry）——这正是 agent LLM 原生能做的缝挖动作。

### ③ HUMAN→AGENT 替代
- **人类做法**：老卖家一眼看出「通用 planner 红海了，得挑护士/婚礼/Notion 这种超窄角度」。
- **agent 替代**：把「通用饱和度 + 未满足抱怨」派成研究 Goal，用显式裁定压住 LLM「生成个通用模板就交差」的默认，逼出超窄角度。

### ④ 三道检验裁定：**过 (a)(b)(c)（尤其 b、c）**
- (a) 通用度/评论抱怨全可观测。
- (b) **直接压制 LLM 头号默认**：以为「我能生成通用品 = 有机会」。
- (c) 最非平凡：「需求被证明但角度通用 → DROP」+「$1 低价反而伤 quality score」——反直觉，LLM 不会自发采用。

---

## KEPT 方法 E5 · 产品形状适配闸：text/design-light agent 到底能作什么

**一句话**：Etsy 数字品里，只有一部分是 **text/layout 驱动、design-light** 的——这些 agent 自己就能高质量作出；illustration/美术驱动的（原创 clipart、复杂 SVG cut files、手绘 wall art）超出 design-light agent 能力，即便需求真也 DROP（作不出竞争力）。机会必须落在**可作形状 ∩ 已证明需求**的交集里。

### ① OPERATION
**(i) 研究-Goal `--intent` 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "For the proven-demand niche '<niche>', which SPECIFIC digital-download PRODUCT FORMATS are
  selling? Classify each into (A) TEXT/LAYOUT-DRIVEN & design-light — printable planners, habit/budget
  trackers, worksheets, checklists, spreadsheets (Excel/Google Sheets/Notion), resume/CV templates,
  fill-in Canva text templates — vs (B) ILLUSTRATION/ART-DRIVEN — original clipart, complex SVG cut files,
  hand-drawn wall art, presets. For the type-A formats report typical price and 'X sold'." \
  --accept "For the niche: which selling formats are text/layout-driven (agent-authorable) vs
  illustration-driven, with price + 'sold' for the type-A ones."
```
**(ii) 可观测读数**：该 niche 里在卖的具体格式分类 + type-A 的价格/销量。
**(iii) 决策阈值**：
- **KEEP**：需求落在 **type-A（text/layout 驱动）** 格式上——trackers/planners/worksheets/checklists/spreadsheets/resume/Canva-text templates，agent 能自己作。
- **DROP**：需求主要在 **type-B（美术驱动）**（原创 clipart / 复杂 cut files / 手绘 art / presets）→ design-light agent 作不出有竞争力的货，即便需求真也放弃。
- **价格锚（作产品定价用）**：basic A4 tracker **$3–6**；planner/journal printables **$5–10**；spreadsheets 可到 **$35 均价**（案例：budget tracker 700+ sold、$25k+/月）；Canva templates **$10–40**；bundle 提 AOV（"list a 3-pack alongside your single item"）；**别 $1**。

### ② PHILOSOPHY BACKING
> 最好卖的里，"Habit trackers, budget planners, and goal sheets are simple to design and always in demand, with a basic A4 tracker selling for $3–$6"；spreadsheet 案例 "$25,000+ per month with 700+ sales at an average $35"（aliciarafiei）。这些都是**文字/表格/排版**产物——LLM-native 可作；而 clipart/SVG/preset 是美术产物，另需设计能力。

### ③ HUMAN→AGENT 替代
- **人类做法**：卖家按自己会 Canva/会画图/会做表来选品类。
- **agent 替代**：把「哪些在卖的格式是 text/layout 驱动」派成研究 Goal，用**「agent 能否亲手作」**替代人类的技能自评，硬性把候选夹在「可作 ∩ 已证明」里。

### ④ 三道检验裁定：**过 (a)(b)(c)**
- (a) 在卖格式 + 价格/销量可观测。
- (b) 压制 LLM「随便挑个热门数字品」——很多热门（clipart/SVG/art）它其实作不出。
- (c) 非平凡取舍：**需求真但形状作不出 → DROP**；可作形状的价格锚。

---

## DROP 清单（纯美德 / 非 agent 可观测 / LLM 自带，不写进 skill）

| DROP 项 | 为什么 DROP |
|---|---|
| **「跟 Etsy trending / 追热门品类」** | 兴趣非付费；trending 无付费锚 = r3 的「听起来有需求」默认。热门只有过了 E1/E2 才算数。 |
| **「让 listing 更好看 / 加独特功能 / 强调 quality」**（Printful 泛建议） | 纯美德，LLM 自带；不含可观测阈值。真正可执行的差异化已在 E4（超窄角度）。 |
| **「favorites 数当主信号」** | 弱代理——收藏 ≠ 付费；alicia 明说别把 reviews/favorites 当 primary，用真实营收/「sold」。favorites 只留作 E2 的次要旁证。 |
| **「$1 低价抢首单」** | 反效果："$1 listings don't signal quality"，且拉低 listing quality score。已在 E4 列为反模式。 |
| **「估 Etsy 品类 TAM / 市场规模」** | VC 框架，父研究已去标定。 |
| **泛泛「用 eRank 做点关键词调研」** | 太糊；被 E1 的具体 searches/供给/难度阈值取代。 |
| **「无竞争的蓝海词」** | 继承 r3：Etsy 上零供给通常 = 没人为它买 / 得自费教育；E1 要求「有需求 + 供给可打」而非「零供给」。 |
| **「Chrome 插件手动刷 EverBee」** | agent 无插件 UI；保留其**数据**（经研究 Goal 取回），丢弃其**交互机制**。 |

---

## Sources 表（实拉，2026-07-02）

| # | 借用/证据 | 来源 | 抓取方式 |
|---|---|---|---|
| E-S1 | eRank 指标定义（Average Searches/Clicks/CTR/Etsy Seller Competition）+ "Keyword Difficulty ... lower = less competition ... a possible opportunity" + green zone <~20k | eRank, *Etsy SEO Tutorial* (help.erank.com/listing-optimization/etsy-seo-tutorial) + erank.com | WebFetch + WebSearch 摘要 |
| E-S2 | EverBee 按 sales/revenue/reviews/listing-age 过滤 205M+ listing；"substantial monthly revenue but fewer than 50 reviews = newer best-sellers"；"at least 500 monthly searches but under 100,000 competing listings = sweet spot"；~80% 准、directional | MerchArts, *Complete EverBee Guide* (mercharts.com/etsy-research-complete-everbee-guide-and-strategies) + everbee.io | WebFetch + WebSearch 摘要 |
| E-S3 | 低竞争选品 4 步；"22 people search ... too low"；"853 other stores selling this product" = saturated；searches/clicks/CTR/competition "in green" | Printful, *Find Low-Competition Etsy Niches in 2026* (printful.com/blog/low-competition-etsy-niches) | WebFetch |
| E-S4 | Etsy 官方两段式 query matching + ranking；"Etsy search gathers all the listings that have keywords that match a shopper's query"；listing quality score = clicks/purchases | Etsy Seller Handbook, *Ultimate Guide to Etsy Search* / *How Etsy Search Works* (etsy.com/seller-handbook) | WebSearch 摘要（两个官方 URL 直连 403，取搜索快照原文） |
| E-S5 | 2026 排名 5 因子（relevance / listing quality score / recency / shop quality / buyer experience）；recency boost 缩到 14–21 天；semantic intent 权重升 | Insight Agent, *Etsy SEO 2026 / Algorithm 2026* (insightagent.app/guides) | WebSearch 摘要 |
| E-S6 | digital-download SEO：title 前 40 字符 front-load、用满 13 tags 不重复、长尾 "Goodnotes Student Academic Planner 2026 beats Digital Planner" | BetterListing, *Etsy Digital Downloads SEO 2026* (getbetterlisting.com/en/blog/etsy-digital-downloads-seo-guide) | WebFetch |
| E-S7 | "flood of low-effort, AI-generated content ... buyers want curated / hyper-specific / verified human quality"；"'Watercolor floral clipart' ... 'western sunflower' wins" | growingyourcraft.com + mydesigns.io（digital products / SEO 2026） | WebSearch + WebFetch 摘要 |
| E-S8 | 读缝法："study review counts on the top 10 listings—high review counts confirm real buyer demand, while low counts in top positions signal an opening"；printable 类型 + 营收案例（meal planner $9k/mo、budget spreadsheet 700+ sold @$35 = $25k/mo） | aliciarafieiblog.com/etsy-printables-that-sell + insightagent 案例簇 | WebFetch + WebSearch 摘要 |
| E-S9 | 价格锚（A4 tracker $3–6、planner $5–10、Canva $10–40、单品 $2–6/bundle $8–15）、"$1 listings don't signal quality"、bundle 提 AOV / 3-pack | outfy.com/blog/top-selling-digital-products-on-etsy + mydesigns.io | WebFetch |

## Caveats
- 两个 Etsy 官方 handbook URL（*Ultimate Guide to Etsy Search* / *How Etsy Search Works*）WebFetch 直连均 403；引用取自搜索引擎对该页原文快照，措辞一致可信，动笔前若逐字引官方句建议再取一次。
- 所有数值阈值（500 搜索 / <100k or <20k 供给 / <50 reviews / recency 14–21 天 / 各价格锚）为**近似经验锚**，skill 正文应措辞「约/数量级」，不写死；EverBee 销量估计自承 ~80% 准、只作 directional。
- 「top-10 评论数读缝」那句为搜索快照对 printables 案例簇的转述（aliciarafiei/insightagent），非某一页逐字原文；作 thought-source 署名用足够，逐字引用前建议复取。
- E1/E2/E3 三条常常在**同一个候选关键词上串跑**（先 E1 量供需 → E2 验付费+找缝 → E3 判可排性 → E4 反通用 → E5 判可作），skill 落地时应表述为一条流水线而非五个孤立开关。
