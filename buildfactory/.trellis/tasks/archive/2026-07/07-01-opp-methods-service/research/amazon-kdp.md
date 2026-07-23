# Amazon KDP 平台子剧本 —— headless agent 如何在 Kindle/KDP 上找一个「已被证明付费 + 可打进」的小型电子书/低内容书机会

- **Strand**: `find-opportunity` 的平台子剧本 · **Amazon KDP (Kindle Direct Publishing)**。父方法（平台无关 7 步）已定「别造想法——找已经有人付钱的证据，再定一个小的文本产品」；本文只回答：这套怎么**具体落到 KDP** 上（niche 非虚构 how-to、低内容书如 planner/journal/workbook——都能被一个文本 agent 独立写出来）。
- **执行者约束（第一原则）**：CEO 是 headless LLM，只有两招：(1) 派研究 Goal —— `python3 -m orchestration.messaging send --to researcher --intent "<问题>"`（可选 `--accept "<验收>"`）→ 由 researcher at-scale 网页观察回报；(2) LLM-native 亲自写书。所以**每条方法的检测都必须能被一个网页观察的研究 Goal 回答**，不能依赖付费 GUI 工具（Publisher Rocket / Chrome 插件）或个人受众。绑定约束 = **KDP 上已被证明的付费需求 + 一个可排名/可打的缝**，不是「我们能不能写」。
- **不重复 r3**：`research/r3-willingness-to-pay.md` 已建立跨 marketplace 的付费证据层与 BSR→销量分档（<10k 强 / <100k 稳 / >500k 罕见）、品类 BSR vs 总榜、以及「查头部书 BSR 看关键词是否真在驱动购买」。本文把这些**深挖成 KDP 专属的完整找机会剧本**：autocomplete 选题生成、7 关键词槽 + 10 品类机制、品类-BSR 可夺榜性、低内容 vs 全内容书形、royalty 价带。r3 的通用付费证据方法不再重述，直接复用。
- **Sources**: 实拉，见文末表；日期 **2026-07-02**。

---

## 三道检验（复用 r3，逐条过筛）

目标 agent 本身是 LLM。给它写泛泛「找个有需求的选题」= 没写。一条只有满足 ≥1 项才保留：
- **(a) 系统特定**：能被一个研究 Goal（网页观察）检测；候选能被部门（researcher + LLM 作者）落地；不需要问卷、不需要个人受众、不需要付费 GUI 工具。
- **(b) 压制 LLM 默认**：LLM 被问「什么书好卖」时默认吐「听起来有需求」的选题（"AI productivity guide"）、把选题做宽（"journal"）、且假设「能写=能卖」。反掉这些 = 过 (b)。
- **(c) 非平凡阈值/取舍/反信号**：LLM 不会自发采用的判断——尤其 **「需求 AND 可打的缝」双闸**、KDP 专属机制（品类-BSR 可夺榜、7 槽/10 品类、royalty 价带）、以及**饱和反信号**（头部全是上千评论 → DROP）。
纯美德（"做点关键词调研""做个好封面"）= LLM 自带 = **DROP**。

---

## 核心哲学锚（一句话总纲，署名 Kindlepreneur / Dave Chesson）

> 好关键词坐在三者交点：**需求（有人真在 Amazon 里搜）、购买意图（搜的人肯买）、可排名（竞争不至于压死你）**。
> "Shoppers are actively typing it into Amazon. If no one searches for it, it cannot drive sales." … "Shoppers who use that phrase are willing to buy." … "The competition is not overwhelmingly difficult. Even high-traffic, high-converting phrases may be too competitive for your book to realistically rank for."
> —— Kindlepreneur, *How to Choose Your Amazon Kindle & Book Keywords*

这条压制的 LLM 默认：**把「这话题听起来有人要」当成「这本书能在 KDP 上卖」**。KDP 剧本的每条方法都是这三交点的可观测代理——在 Amazon 内部（autocomplete + BSR + 竞品评论深度 + 品类榜）找「钱已经在这个关键词下易手 + 我还能挤进头部」的痕迹，不是找兴趣。

---

## KEPT 方法 1 · Kindle autocomplete 选题生成（在 KDP 内部长出候选，而非凭空想）

**一句话**：不让 CEO 凭空吐关键词。派研究 Goal 去枚举 **Amazon/Kindle 搜索框的 autocomplete 建议**（seed 词 + 逐字母 a–z 展开），只保留 Amazon 真的会自动补全的长尾短语——那是「买家真的这么打字」的化石证据。

### ① OPERATION
**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "On Amazon.com (the main store search bar AND the Kindle Store search), type the seed
  '<seed e.g. gratitude journal / sourdough / anxiety workbook>' and record every autocomplete
  suggestion. Then append each letter a-z to the seed ('<seed> a', '<seed> b', ...) and record the
  new suggestions each reveals. Return the FULL list of real autocompleted phrases (these are phrases
  shoppers actually type), flag the 3-5+ word long-tail ones, and mark which are how-to/niche
  non-fiction vs low-content (journal/planner/workbook/logbook)." \
  --accept "A deduplicated list of real Amazon autocomplete phrases for the seed, long-tail ones
  flagged, each tagged full-content-how-to vs low-content."
```
**(ii) 可观测读数**：回报里出现一批 Amazon **真的补全出来的**短语（尤其 3–5 词长尾），而不是 CEO 想象的措辞。
**(iii) 决策规则**：**KEEP** = 只把 Amazon autocomplete 实际吐出的长尾短语纳入候选池（它们证明有人这么搜）。**DROP** = CEO 自己发明、autocomplete 里查无的措辞（"the ultimate AI productivity system for founders" 这种）——没证据有人这么找。长尾优先，因为宽词（"journal"）竞争不可打（见方法 3）。

### ② PHILOSOPHY BACKING
> "Start typing in a word, and look to see what Amazon immediately pre-populates in the search box. Once you've found a phrase that you're interested in, add each letter of the alphabet at the end of your word/phrase, and see what comes up."（Kindlepreneur）

### ③ HUMAN→AGENT 替代
- **人类做法**：作者亲手在 Amazon 搜索框敲字看下拉、或用 Publisher Rocket 拉 "Amazon Searches Per Month"。
- **agent 替代**：agent 没 GUI、买不起 Rocket。改为派研究 Goal 让 researcher 复刻 autocomplete + a–z 展开，把「买家用词」从 Amazon 自己嘴里挖出来。

### ④ 三道检验裁定：**过 (a)(b)(c)**
- (a) autocomplete 纯网页可观测，无需受众/付费工具。
- (b) 强压 LLM「凭感觉想个关键词」——只认 Amazon 补全过的措辞。
- (c) 非平凡：长尾优先 + 显式 DROP「autocomplete 查无 = 无搜索证据」，LLM 不会自发加这道锚。

---

## KEPT 方法 2 · 需求闸：查头部书的 BSR（这个关键词到底带不带销量？）

**一句话**：一个关键词有人搜 ≠ 搜的人会买。对候选关键词，派研究 Goal 拉**当前排在该词前 ~10 名的书的 Best Seller Rank (BSR)**，把 BSR 当作「这个词真在驱动购买」的销量代理。头部书 BSR 差 = 这个词不带货，砍掉。

### ① OPERATION
**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "On Amazon, search the exact phrase '<keyword>' in the Kindle Store. For the top ~10
  results report each book's: title, format (Kindle ebook / paperback low-content), price, Amazon
  Best Seller Rank from the Product Details (report BOTH the overall #_ in Kindle Store AND the
  #_ in each named sub-category), and its review count + star rating. I need to know whether the
  books ranking for this keyword are ACTUALLY SELLING." \
  --accept "A table: top ~10 books for the keyword with price, overall BSR, category BSR(s),
  review count, stars. Explicit note if top results have weak/absent BSR."
```
**(ii) 可观测读数**：头部书的 **BSR 数字**（品类榜 + 总榜）。r3 已建的换算锚：Kindlepreneur "a book with a BSR of #2000 will be selling dozens of copies a day, whereas a book ranking at #120,000 BSR will only be selling around 1 copy per day"；分档 "Under 10,000 = strong daily sales / Under 100,000 = consistent movement / Above 500,000 = infrequent sales"。
**(iii) 决策规则**：
- **KEEP（词带货）**：头部书 BSR 普遍 **≤ ~100,000（稳定动销）**，且**至少一两本 <50,000 / <10,000**（强动销）→ 这个关键词证明能驱动购买。kdpbuilder 复核："If the top results sit around BSR 100,000 or better, there's real demand without total saturation."
- **DROP（词不带货）**：头部书 BSR 普遍 **> 500,000** → 就算有人搜，搜的人不买；Kindlepreneur 原话——若 "the books that show up for that keyword aren't making sales (because you checked their BSR)"，这个词该弃。
- **必看品类 BSR 不是只看总榜**（见方法 4）：品类榜靠前才是可夺榜的入口。

### ② PHILOSOPHY BACKING
> 评估搜索量的正确做法不是猜，是查现排头部书的 ABSR 换算成日销："go to their Amazon Best Seller Rank … paste it into my Kindle Calculator … convert the ABSR … into the estimated sales that day … If top-ranking books show weak performance, it signals either minimal searches or poor buyer conversion for that phrase."（Kindlepreneur）

### ③ HUMAN→AGENT 替代
- **人类做法**：作者手动点开每本头部书的 Product Details 抄 BSR、丢进 Kindlepreneur/Rocket 计算器估日销。
- **agent 替代**：派研究 Goal 让 researcher 批量抄头部书 BSR 回报；换算分档已内建进决策规则，CEO 直接按阈值判。

### ④ 三道检验裁定：**过 (a)(b)(c)**
- (a) BSR 在每本书 Product Details 里，纯网页可观测。
- (b) 这是压制「听起来有需求」的核心闸——强制拿真金销量代理。
- (c) 非平凡：BSR 分档、品类榜 vs 总榜、「头部书 BSR 差 = 词不带货 → DROP」都是 LLM 不会自发用的阈值。

---

## KEPT 方法 3 · 可打的缝闸（双闸核心）：需求在场 BUT 竞争可打

**一句话**：这是 KDP 剧本最非平凡的一条，也是父方法「demand AND rankable-gap」的落地。方法 2 证明了词带货（需求）；本条再问**头部供给是否可打**——结果数少 / 头部书评论浅（几十到几百，不是上千）/ 过时 / 单薄 / 评分平庸。**需求在场且缝可打**才 KEEP；**需求在场但头部全是上千评论的巨兽 → 饱和，DROP**；**没书在卖 → 未证明，DROP**。

### ① OPERATION
**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "For the exact Amazon Kindle Store phrase '<keyword>': (1) roughly how many results does
  Amazon return for it? (2) For the top 5 books report review COUNT, star rating, publication/last-
  updated date, page count/thinness, and cover-quality impression. (3) Are the top books dominated by
  one big brand/publisher, or are they beatable indie titles? (4) Scan the 1-3 star reviews of the top
  books for recurring 'I wish it had…' complaints that leave a wedge. Cross-reference the BSR read from
  the demand check — I need to know if these books SELL but are BEATABLE." \
  --accept "Result count band; top-5 review counts + stars + freshness + thinness; brand-dominance
  read; a list of recurring unmet complaints (or 'none found')."
```
**(ii) 可观测读数**：结果数量级 × 头部书评论深度 × 新鲜度 × 评分 × 未满足抱怨，叠加方法 2 的 BSR。
**(iii) 决策规则**（把需求闸和缝闸交起来）：
- **KEEP（已证明且可打的窄窗）**：头部书**在卖**（方法 2 过关，BSR 好）**且**头部竞争可打——kdpbuilder 锚："Look for top sellers with roughly 50–300 reviews — proven demand with room to enter."；结果数落在低带（业内常引 "sweet spot 200–2,000 results" / "fewer than 10,000 results"）；或头部书过时/单薄/评分平庸/评论有复现抱怨留了缝。
- **DROP（饱和）**：kdpbuilder："If every top-5 book has 1,000+ reviews, the niche is crowded."——头部全是上千评论的成熟巨兽、高分低价、无未满足抱怨 → 无楔子，弃（呼应 r3 KEPT 信号 4）。
- **DROP（未证明）**：几乎没书在卖 / 头部 BSR 全差 → 不是蓝海，是没人肯买（r3：零竞争常意味要自费教育市场）。
- **窄下去可救**："coloring book" 有百万竞品、"bold-line mushroom coloring book for adults" 可能 "fewer than a hundred" 竞品——同样每本 royalty。宽词饱和时，autocomplete 长尾（方法 1）常能把同一需求切成一个可打的窄词。

### ② PHILOSOPHY BACKING
> "High demand + low available supply = Profit potential." + Amazon 内竞争评估要看 "book cover quality, whether keywords appear in titles/subtitles, review count and recency, description quality, publication age"（Kindlepreneur）。缝的判据："Look for books that have fewer reviews [and] still maintain a decent BSR. This usually indicates newer books that are already selling."（Low Content Profits）

### ③ HUMAN→AGENT 替代
- **人类做法**：老手扫一眼 SERP 就知道「头部三本 4.9★、几千评论、$3——别碰」或「这词头部书才 60 评论还在卖——有缝」。
- **agent 替代**：把这层「红海嗅觉」派成研究 Goal——数结果、读头部评论深度/新鲜度、挖未满足抱怨——用可观测阈值代替人类直觉。

### ④ 三道检验裁定：**过 (a)(b)(c)（尤其 c）**
- (a) 结果数/评论深度/新鲜度/未满足抱怨全网页可观测。
- (b) 压制「需求被证明了就冲」的乐观默认。
- (c) 最非平凡：**「需求真实但头部上千评论 → DROP」** + 「50–300 评论 = 已证明且可进」这道反直觉窄窗，是本平台剧本的核心取舍。

---

## KEPT 方法 4 · KDP 专属机制闸：品类可夺榜性 + 关键词槽/品类对齐

**一句话**：KDP 有一个 LLM 不知道的杠杆——**能否在某个具体品类里以极少日销拿到 #1 的橙色 Bestseller 徽章**。同一本书，选对品类 14 单/天就能封榜，选错要 1000 单/天。派研究 Goal 找出候选头部书所在的**具体子品类**及其夺榜门槛，KEEP 那些存在「低日销即可 top-1 或 top-20」的可达品类的选题。同时把 autocomplete 长尾（方法 1）填进 **7 个关键词槽**以锚定品类、并规划最多 **10 个品类**多点曝光。

### ① OPERATION
**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "For '<keyword/niche>': open the top 3-5 selling books and list the exact Amazon
  sub-categories each is filed under (from the 'Best Sellers Rank' breakdown in Product Details).
  For each named sub-category report the BSR of the current #1 and #20 book, so we can estimate how
  few daily sales it takes to hit #1 (bestseller badge) or top-20 there. Flag any sub-category that
  looks reachable with modest sales vs ones dominated by mega-sellers. Also list which long-tail
  keyword phrases would anchor a book INTO those categories." \
  --accept "Per top book: its sub-categories; per sub-category: #1 and #20 BSR as a dominance proxy;
  a shortlist of reachable categories + the anchoring keyword phrases."
```
**(ii) 可观测读数**：每个子品类里 #1/#20 书的 BSR（越高门槛越低=越好夺）；候选书能填进哪些品类。
**(iii) 决策规则**：
- **KEEP**：存在**至少一个可达子品类**——其 #1 的 BSR 不算极低（意味着少量日销就能封顶）→ 新书有现实机会拿橙徽/进 top-20。Kindlepreneur："with the right research, you can find an equivalent category that only requires 14 sales to be a bestseller."（对照：有的品类要 1000 单/天）。
- **DROP / 降级**：候选相关的所有品类里 #1 都是超低 BSR 巨兽 → 拿不到徽章也进不了 top-20；Kindlepreneur："if you can't get the 'bestseller' mark in some category or rank in the top 20 of a popular category, then don't worry about it."
- **机制备忘（写进产品动作，非选题闸）**：出版时可选 3 个品类，可向 KDP 客服申请**最多 10 个**多点曝光；**7 个关键词槽**要留 1–2 个填品类锚定词，否则 Amazon 会按 metadata 把书挪出你想要的品类。

### ② PHILOSOPHY BACKING
> "With over 14,000 book categories on Amazon, there are categories that might require you to make 1000 book sales a day to be #1, or with the right research, you can find an equivalent category that only requires 14 sales to be a bestseller." … "If your book has the LOWEST ABSR of all books that are attached to an Amazon category, then you are the #1 best seller in that category." … 徽章的作用："A best seller mark increases your conversion rate which thus increases sales."（Kindlepreneur）

### ③ HUMAN→AGENT 替代
- **人类做法**：作者用 Publisher Rocket 的 category 模块 / 手动翻 Product Details 找低门槛品类，凭经验填 7 槽 + 申 10 品类。
- **agent 替代**：派研究 Goal 让 researcher 抄头部书的子品类树 + 各品类 #1/#20 BSR，把「哪个品类好夺榜」外包成一次网页观察；7 槽/10 品类作为落地时的确定性动作清单。

### ④ 三道检验裁定：**过 (a)(b)(c)**
- (a) 品类树 + 各品类 #1/#20 BSR 全在 Product Details，可观测。
- (b) 压制「随便选个大品类」——逼向可夺榜的窄品类。
- (c) 高度非平凡且 KDP 专属：品类-BSR 夺榜性、1000 vs 14 单的量级差、橙徽提转化、7 槽锚定品类否则被系统挪走——LLM 完全不会自发知道这套机制。

---

## KEPT 方法 5 · 书形/价带闸：这本书文本 agent 写得出来 + 落在赚钱 royalty 带里吗？

**一句话**：这不是「确认能写」的空泛美德，而是两条 KDP 专属的**结构性淘汰**：(i) 形态——**低内容书里的 coloring/puzzle/绘本类需要美术资产**，纯文本 agent 写不出，即便需求+缝都完美也要 DROP（或改投它能全权产出的形态：niche how-to 非虚构、planner/journal/workbook/logbook 这类「结构+文字提示」书）；(ii) 价带——Kindle 电子书**只有定价落在 $2.99–$9.99 才拿 70% royalty**，band 外只有 35%，这是 LLM 不会套用的 KDP quirk。

### ① OPERATION
**(i) 判定（多为 CEO 本地判 + 一条轻研究 Goal 校价）**：先按方法 1 的 tag 把候选归类：
- **文本 agent 可全权产出**：niche 非虚构 how-to 指南；低内容里的 planner / journal / notebook / logbook / workbook（"users fill in the pages themselves … don't require heavy writing or a detailed manuscript"）。
- **文本 agent 不能全权产出（DROP 或改形）**：coloring book、puzzle/活动书、重插画绘本——需要美术/版式资产，超出纯文本能力。
校价用研究 Goal：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "For the winning '<keyword>' books: what price points do the top sellers use (Kindle ebook
  vs paperback low-content)? Do the top ebooks sit in the $2.99-$9.99 range (the 70% royalty band)?
  Report the price distribution." \
  --accept "Top-seller price distribution and whether the winning format's typical price lands in the
  $2.99-$9.99 70%-royalty band."
```
**(ii) 可观测读数**：候选形态标签 + 头部书定价分布。
**(iii) 决策规则**：
- **KEEP**：形态是 how-to 非虚构或可填式低内容书（agent 能全权写）**且**目标定价能落在 $2.99–$9.99（Kindle 70% 带）或低内容纸质书有健康价（业内 niche 表常引低内容书 buyers "willing to spend $7 to $20 per book"）。
- **DROP / 改形**：需要美术资产的形态（coloring/puzzle/绘本）——文本 agent 交付不了完整产品；或头部定价被挤到 band 外只剩 35% 且无差异化溢价空间。

### ② PHILOSOPHY BACKING
> 低内容书定义："books with minimal content on the interior pages, typically designed for the user to fill in … They don't require heavy writing or a detailed manuscript."（Publishing.com）。Royalty 带："To qualify for 70%, your ebook must be priced between $2.99 and $9.99 … below $2.99 or above $9.99 → 35%."（KDP Help / kdpeasy）

### ③ HUMAN→AGENT 替代
- **人类做法**：作者理所当然知道「coloring book 得请插画师」「定价卡在 $2.99 才有 70%」，凭常识过滤。
- **agent 替代**：把这两条显式写成闸，因为 LLM 既会盲目认为「什么书都能写」（忽略美术依赖），也不会自发套用 $2.99–9.99 这个 KDP 特定 royalty 断点。

### ④ 三道检验裁定：**过 (b)(c)**（(a) 部分——价带需一条轻研究 Goal，形态本地判）
- (b) 压制「能写=能交付」+「随便定价」两个默认。
- (c) 非平凡取舍：「coloring/puzzle 需美术 → 文本 agent DROP」这条反直觉淘汰，加上 $2.99–9.99 70% 断点，都是 KDP 特定、LLM 不自带的判据。
- ⚠️ 边界：本条只做**结构淘汰**，绝不喧宾夺主——绑定约束仍是方法 2+3 的「已证明付费 + 可打的缝」，不是「能不能写」。

---

## DROP 清单（纯美德 / 非 agent 可观测 / 被上面取代——不写进 skill）

| DROP 项 | 为什么 DROP |
|---|---|
| **「用 Publisher Rocket 拉需求/竞争分」** | Rocket 是付费 GUI，headless agent 驱动不了。保留其**分析框架**（需求/竞争/可排名三交点），机制换成 autocomplete + BSR 研究 Goal。 |
| **「装 Chrome 插件（AMG Expander / DS Amazon Quick View）看 BSR」** | 人类 GUI 机制，agent 用不了。被方法 1/2 的研究 Goal 取代。 |
| **「选个 trending / popular 的 niche」** | 正是要压制的 LLM 默认（兴趣冒充需求）；被方法 2 的 BSR 需求闸取代。 |
| **「零竞争 = 蓝海」** | 在 KDP 上通常 = 没人肯为它买（r3 已锚）；方法 3 显式 DROP「无书在卖=未证明」。 |
| **「估 TAM / KDP 市场多大」** | VC 框架，父研究已去标定。 |
| **「做个好封面 / 写本高质量书 / 好好排版」** | 纯执行美德，非**找机会**判据；LLM 自带。 |
| **「先确认我们能写它」当绑定约束** | 显式降级为方法 5 的结构淘汰；绑定约束是已证明付费 + 可打的缝。 |
| **泛泛「做点关键词/市场调研」** | 太糊；被 5 条具体研究-Goal 模板取代。 |

---

## Sources 表（实拉，2026-07-02）

| # | 借用/证据 | 来源 | 抓取方式 |
|---|---|---|---|
| K1 | 好关键词三交点（需求/购买意图/可排名）；autocomplete + a–z 展开；查头部书 ABSR 丢计算器估日销；竞争看封面/标题词/评论数与新鲜度/描述/出版年；点击分布 1000→270→60 | Kindlepreneur, *How to Choose Your Amazon Kindle & Book Keywords* (kindlepreneur.com/how-to-choose-kindle-keywords/) | WebFetch |
| K2 | 7 关键词槽用法（专属词 + 其余词并用）；Rocket 显示真实 Amazon 搜索词与月搜量；竞争分 1–100 | Kindlepreneur, *How to Fill in Your 7 KDP Keyword Boxes* (kindlepreneur.com/7-kindle-keywords/) | WebFetch |
| K3 | 14,000 品类 / 1000 单 vs 14 单夺 #1；最低 ABSR = 品类 #1；徽章助力多卖；可选 3、申 10 品类；关键词锚定品类否则被系统挪走 | Kindlepreneur, *Amazon Book Categories: How to Find the Ones Most Authors Miss* (kindlepreneur.com/how-to-choose-the-best-kindle-ebook-kdp-category/) | WebFetch |
| K4 | 品类榜 vs 关键词搜索榜区别；#1=橙徽提转化；「拿不到徽章也进不了 top-20 就别管这品类」 | Kindlepreneur, *Kindle Rankings: Categories vs. Keywords* (kindlepreneur.com/kindle-rankings-categories-vs-keywords/) | WebFetch |
| K5 | BSR→销量分档（#2000≈日销数十、#120,000≈日销 1）/ <10k 强、<100k 稳、>500k 罕见；用头部书 BSR 判词是否带货 | Kindlepreneur, *KDP Sales Rank Calculator* (kindlepreneur.com/amazon-kdp-sales-rank-calculator) | 复用 r3 S3（WebFetch） |
| K6 | seed 词 + 插件展开；缝的判据「fewer reviews + decent BSR = 新书已在卖」；「有需求不等于易进，需人工核封面/品牌/评论」 | Low Content Profits, *How I Find Low-Competition KDP Niches That Actually Make Money* (lowcontentprofits.com/low-competition-kdp-niches/) | WebFetch |
| K7 | 低内容书定义（内页极简、用户自填、无需 manuscript）；planner/journal/notebook/logbook；避开饱和、切窄需求 | Publishing.com, *Amazon KDP Low-Content Books: A Beginner's Guide* (publishing.com/blog/amazon-kdp-low-content-books) | WebFetch |
| K8 | 数值阈值：BSR 100,000 或更好=有需求未饱和；top-5 若各 1,000+ 评论=拥挤，50–300 评论=已证明且可进；"bold-line mushroom coloring book" <100 竞品 | KDP Builder, *Best KDP Niches 2026* (kdpbuilder.com/blog/best-kdp-niches-2026) | WebFetch |
| K9 | 数值阈值（快照）：结果数 sweet spot 200–2,000 / <10,000；top-books BSR 5,000–50,000 稳动销；top 平均 <500 评论=可控；月搜 100–1,000 | KDP Niche Hunter, *How to Find Profitable KDP Niches* (kdpnichehunter.com/blog/how-to-find-profitable-kdp-niches) | WebSearch 快照（页面 WebFetch 403） |
| K10 | 70% royalty 仅限 $2.99–$9.99；band 外 35%；$0.15/MB delivery fee | KDP Help *eBook Royalties* (kdp.amazon.com/help/topic/G200644210) + kdpeasy.com/guides/2026-kdp-royalty-rates | WebSearch 摘要 |
| K11 | niche 买家愿付 $7–$20/本；planner/fitness journal/「for X」journal 等可被文本 agent 产出的窄形态；避开泛词 | AutomateEd + LivingWriter KDP niche 汇编 | WebSearch 摘要 |

## Caveats
- kdpnichehunter 页面 WebFetch 返回 403；其具体数值（200–2,000 结果 / BSR 5,000–50,000 / <500 评论 / 月搜 100–1,000）取自搜索引擎对该页快照，与 kdpbuilder（K8）的 100,000 BSR / 50–300 评论 / 1,000+ 评论=拥挤大致一致、可互证，作阈值锚够用。
- 所有 BSR/评论/结果数阈值为**近似经验值**，skill 正文应措辞为「约 / 数量级」，不写死；且需强调「品类 BSR 优先于总榜 BSR」。
- Kindlepreneur 页面里凡涉 Publisher Rocket 的**机制**（GUI 工具、月搜量数字）一律降级为 DROP，只借其**判据哲学**（三交点、BSR 判货、品类夺榜）。
- 引作**思想来源署名**，不逐字大段拷贝进 skill 正文。
