# Gumroad 平台子 playbook —— headless CEO 如何在 Gumroad 上找到「已被证明肯付费 + 有可打缝隙」的小型信息产品机会

- **Strand**: `find-opportunity` 的 Gumroad 子 playbook。共享 7 步母法已确立「别造点子——找『已经有人掏钱』的证据，再定义一个小型文本产品」。本文只做 Gumroad 这一层的**具体、可执行**打法。
- **执行者约束（第一原则）**：CEO 是 headless LLM，只有两招——(1) 派研究 Goal 给 researcher：`python3 -m orchestration.messaging send --to researcher --intent "<问题>" [--accept "<验收>"]`（已核实 `orchestration/messaging.py:83-93`，flags: `--to/--intent/--accept`）；(2) LLM 原生写作——产品它自己能写。所以约束不是「能不能做」（什么都能写），而是「**Gumroad 上有没有被证明的付费需求 + 一条可打的缝**」。
- **不重复 r3**：`r3-willingness-to-pay.md` 已建立跨市场 WTP 三档规则（只认 revealed payment）与 Gumroad ratings/销量作代理的通则。本文**只在 Gumroad 上深挖**：demand 具体长在哪、Gumroad 弱发现意味着什么、winnable gap 在 Gumroad 上长什么样、哪些产品**形状**适合文本-native agent、有哪些 Gumroad 专用工具。
- **Sources**: 全实拉，见文末表；日期 **2026-07-02**。

---

## 三道检验（逐条过筛，纯美德一律 DROP）

目标 agent 本身是 LLM。一条只有满足 ≥1 项才保留：
- **(a) 系统特定**：能被一个研究 Goal（网页观察）检测；候选能被部门（researcher+writer）落地；不需问卷、不需个人受众。
- **(b) 压制 LLM 默认**：LLM 被问「Gumroad 上卖什么好」时默认吐「听起来在风口」（"AI Notion 模板""ChatGPT 提示词包"）——零付费证据、且正好撞进 Gumroad 最饱和的红海。反掉它 = 过 (b)。
- **(c) 非平凡阈值/取舍/反信号**：LLM 不会自发采用的判断，尤其**Gumroad 特有的坑**（弱发现、上架数≠竞争、fee 吃低价、星级被四舍五入）。

---

## Gumroad 平台事实底座（先立事实，方法建在其上）

**F1 · Gumroad 几乎没有 organic discovery——这是整个 playbook 的地基。**
- Indie Hacker 原话："26 products on gumroad. zero organic views. zero from gumroad discover. every single view came from my own traffic." 且 "gumroad discover only shows products after your first sale. but you cant get your first sale without discover. its a catch-22 designed to reward existing sellers."
- 销量来源拆分（多篇一致）：Discover 只占 ~**10–20%** 收入，其余 ~90% 靠创作者自带流量；"organic search drives only 12%… email marketing drives 42%… social media 23%"。
- **对读 demand 的含义**：不能只看「Gumroad 站内热不热」。因为站内不推流，**外部话题需求（搜索/社区/社媒）才是燃料**——它既决定买家从哪来，也是判断需求真伪的独立锚。一个 headless、无受众的 agent 尤其要问：这单机会的流量，我（靠 Discover 或靠部门写 SEO 内容）够得着吗？

**F2 · Discover 的准入、排序与费用（站内那 10–20% 怎么拿）。**
- 准入：真金销售额 ≥ **$10**（自购不算）、产品价 ≤ **$100**、同意「Display your product's 1-5 star rating」、设账号 category + 加 tags、过风控审核。(amypeniston 版流程：开 Discover → 同意展示星级 → 验证账号 → 出一单 → 收到 1 个 rating。)
- 费用：现行 = 直销 **flat 10%**，Discover 归因的单收 **flat 30%**（含支付处理）。⚠️旧的分级费率（premium 13.5%/free 18.5% + $0.30）已被部分文章沿用，作 caveat，别写死。
- Discover 排序/筛选（**可观测的站内 demand 面板**）：`Best Sellers`、`Hot & New`、`Trending`、`New & Trending`（近 9 个月获得关注的产品）、`Rising Stars`（较新 + 评分好 + 销量在涨）、`Recurring Revenue`；筛选：tag、product type（notion template/3d model/…）、file format（pdf/zip/mp4/…）、price range、rating。`gumroad.com/discover?sort=curated` 是策展排序。
- 18 个 category：3D / Audio / Business & Money / Comics & Graphic Novels / Design / Drawing & Painting / Education / Fiction Books / Films / Fitness & Health / Gaming / Music & Sound Design / Photography / Recorded Music / Self Improvement / Software Development / Writing & Publishing（+ Other）。
- Discover 排名偏好（curation + 算法）："your product needs to have a solid sales history, positive ratings, a well-written description, and a high-quality cover image"；"rewards quality and popularity"。

**F3 · Gumroad 上 demand 长在哪（可观测读数）。**
- 产品页公开：**star rating + number of ratings**；**销量数字**在部分产品页公开（MacWhisper 页面显示 "223,515 sales" 与 "1715 ratings"）。**只有约 10% 的产品显示销量**（gumtrends 原话："Only ~10% of Gumroad products display the number of sales"）。
- **只有买家能 rate**（评论来自购买者）→ number of ratings 是「已付费人数」的**下界代理**（比销量更普遍可得）。但 ratings/评论**排序偏正**："Gumroad reviews are not sorted by most recent. It is positive reviews first… no way to see negative reviews for a popular product except clicking and clicking"；星级还被**四舍五入**（MacWhisper 实算 4.37 显示成满 5 星）→ **反信号：别把高星当质量真相**。
- ratings→销量倍率**极不稳定**，不能硬编：Leandro 估「74 ratings ≈ 500–1000+ sales」（≈7–13×，高价窄模板）；但 MacWhisper 1715 ratings / 223,515 sales ≈130×、gumtrends "Old Book Cover" 119 reviews / 20,223 sales ≈170×（低价高量）。→ **把 number of ratings 当序数代理（越多=卖得越多），要硬数字就用第三方估算工具**（F4）。

**F4 · Gumroad 专用数据工具（part 的第三方可观测面板）。**
- **gumtrends.com**：为**所有**产品估算销量（"We are able to estimate it for all products"），字段：estimated revenue / sales count / avg rating / review count / **% mixed reviews（2–4 星占比）** / price / category。示例："4.9⭐ | 119 reviews | 2% mixed reviews | $13.00 | 20,223 sales | $262,899 estimated revenue"。核心洞见（原话）："mixed reviews combined with high sales/revenue indicate a market exists even for non-excellent products"。
- **profitable.app/gumroad**："4.2M Products tracked" 但只 "478.6K With sales or ratings"（→**上架数严重灌水，>88% 零销零评**）；给月销/收入估算、`Best Selling`/`New & Trending`/`Rising Stars` 排序；指引："products published in the last 9 months with 20+ sales show early product-market fit"。
- **marketsy.ai/tools/gumroad-trends**：**只有 category 级增长趋势**（无单品销量/评分）——只能作方向感，不能作选品证据。
- 这些工具页 agent 不能直接 API 拉，但 **researcher 可被派去读它们的公开页面**并回报字段。

**F5 · 什么产品形状在 Gumroad 卖得动（含价格锚）。**
- Digital downloads = Gumroad ~85%，均 **293 sales @ $47.14**；Writing & Publishing 是最佳入门窄类（$15,750/产品，仅 226 个产品）；**Courses 均仅 115 sales @ $95.74 且需已有受众**。
- 文本-native 好卖形状 + 价格锚：ebook/guide **$10–49**；Notion 模板 **$9–29**（入门 $7–12 / 专业 $15–25 / bundle $35–79）；AI prompt pack/library；industry playbook；swipe file；planner/printable。"$29 sweet spot drives volume"；"$19–$39 hit the impulse-buy threshold"。
- **价格坑**："A $1 Notion template on Gumroad resulted in only $0.05 after fees" → 别定 $1–5。Discover 要求 ≤$100。
- 六类 AI 产品单人可做到 $500–1500/月："Prompt libraries, workflow automations, Notion templates, industry playbooks, custom GPT configurations, and AI tool guides."

---

## KEPT 方法 1 · Gumroad revealed-paid-demand 读数（站内 WTP 主探针）

**一句话**：在 Gumroad 上就同一**精确窄选题**，数**有真实 ratings（或第三方销量估算）的卖家**——因为只有买家能 rate，ratings 数 = 已付费人数的下界。多个卖家各自有可观测销量证据 = 钱在 Gumroad 上已经易手过。

### ① OPERATION
**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "On Gumroad, find PAID products for the exact narrow topic '<topic>'. Search gumroad.com/discover
  (filter by relevant tag + category) AND the third-party trackers gumtrends.com and profitable.app/gumroad.
  For the top ~10 products report: title, creator, price, star rating, NUMBER OF RATINGS/reviews, sales count
  IF shown on the page, and the third-party ESTIMATED sales + estimated revenue where available. Exclude
  $0/free products and products with zero ratings. Flag how many of the listed products actually have any
  ratings vs how many are dead zero-sale listings." \
  --accept "A table of paid Gumroad products each with price + a real paid-demand proxy (ratings count and/or
  a third-party sales/revenue estimate), plus a count of how many candidates had NO ratings at all."
```
**(ii) 可观测读数**：同一窄选题上一批标价产品，每个带 **ratings 数**（买家留下=已付费下界）和/或 gumtrends/profitable 的**销量/收入估算**；并看清多少是有销量的活品、多少是零评死链。
**(iii) 决策阈值**：
- **KEEP（需求已在 Gumroad 证明）**：同一精确选题 **≥3 个卖家各自有真实付费证据**——每个 ≥ ~20–50 ratings，**或**第三方销量估算 ≥ 数百，价格落在 $9–49。
- **DROP（未被证明）**：只有 0–1 个有 ratings 的产品；其余全是零评死链（记住 profitable 全站 4.2M 上架仅 478.6K 有销或评——**上架数会骗人**）。
- **DROP（饱和）**：见方法 4。

### ② PHILOSOPHY BACKING
> "Only ~10% of Gumroad products display the number of sales. We are able to estimate it for all products."（gumtrends.com）——number of ratings（只有买家能留）是最普遍可得的**已付费下界**；要硬数字就叠第三方估算。呼应 r3 总纲 "hypotheticals don't translate to actual dollars"。

### ③ HUMAN→AGENT 替代
- **人类**：创作者逛 Gumroad 凭手感觉「这类东西有人买」，或看自己同类产品的后台销量。
- **agent**：无后台、无手感。改为派研究 Goal **数公开 ratings + 读第三方销量估算**，把「钱已易手」外包给 Gumroad 产品页与 gumtrends/profitable 的公开数据。

### ④ 三道检验裁定：**过 (a)(b)(c)** — (a) 全网页可观测；(b) 强制拿真金痕迹压制「风口感」；(c) 非平凡读数：ratings-only-from-buyers 作下界、只 ~10% 显示销量、上架数灌水（4.2M vs 478.6K）、倍率不可硬编——都是 LLM 不会自发用的 Gumroad 特有校准。

---

## KEPT 方法 2 · Discover Best Sellers / Hot & New / Rising Stars 扫描（需求「活着」且新人还挤得进）

**一句话**：用 Gumroad **自带的排序**（Best Sellers / Hot & New / New & Trending=近9月 / Rising Stars=较新+评分好+销量涨），按 category+tag+price+rating 过滤，找**既在 Best Sellers 证明有持续买家、又有近 9 个月新入场者在涨**的选题——后者证明需求不是只被老玩家锁死、一个新品还排得上。

### ① OPERATION
**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "On gumroad.com/discover, for category '<category>' + tag '<tag>' (price under $100): (1) list the
  BEST SELLERS for this topic with their price, star rating and ratings count; (2) SEPARATELY list products
  under 'Hot & New'/'New & Trending'/'Rising Stars' for the same topic — products published in roughly the
  last 9 months that are gaining sales — with their approximate age, price, rating and ratings count. Tell me
  whether recent newcomers appear in the trending lists or whether the top sellers are all old established
  products with no recent movers." \
  --accept "Two lists (established best sellers vs recent risers) for the topic, with a clear verdict on
  whether NEW entrants (<~9 months old) are currently gaining traction or the niche is locked by incumbents."
```
**(ii) 可观测读数**：选题同时出现在 Best Sellers（有持续付费买家）**且** Rising Stars/Hot&New 里有近 9 月发布、销量在涨的新品（新人能上桌的证据）。
**(iii) 决策阈值**：
- **KEEP**：Best Sellers 里有该选题（demand 已证明）**且**至少 1–2 个 <~9 月的新入场者在 Rising Stars/Hot&New 里涨（"20+ sales in the last 9 months show early PMF"）→ 需求活着、门还开着。
- **DROP**：Best Sellers 全是老品、trending 里毫无新面孔 → 需求被在位者锁死，新品进不去（呼应方法 4 的「36 个 established businesses」）。
- **DROP**：该选题在 Discover 根本排不出货（无 Best Seller、无 riser）→ 站内无 pull，只能全靠自带流量（见方法 5 流量闸）。

### ② PHILOSOPHY BACKING
> "'New & Trending' shows products gaining traction in the last 9 months, 'Rising Stars' finds newer products with great ratings and growing sales."（Gumroad Discover 排序）+ "products published in the last 9 months with 20+ sales show early product-market fit"（profitable.app）。Best Sellers 证明**有人持续买**，Rising Stars 证明**新人还挤得进**——两者缺一即坑。

### ③ HUMAN→AGENT 替代
- **人类**：老卖家扫 Discover 榜单凭经验判断「这类还在涨 / 已经被大佬占死」。
- **agent**：把 Discover 的四种排序当**结构化 demand 面板**派 researcher 读，用「有无近 9 月 riser」这条硬信号替代人类的市场手感。

### ④ 三道检验裁定：**过 (a)(b)(c)** — (a) Discover 排序全公开可读；(b) 压制「进个热门类就行」——要求需求既活且门开；(c) 非平凡：区分 Best Seller（持续买家）vs Rising Star（新人可入），并把「榜单全是老品→锁死→DROP」这条反直觉规则显式化。

---

## KEPT 方法 3 · 「卖得动但平庸的在位者」楔子（Gumroad winnable-gap 探针）

**一句话**：Gumroad 上最可打的缝 = **有真实销量但评价平庸/评论有复现抱怨/内容单薄过时**的在位产品——市场已被证明肯付费，而现有供给差到留了缝，一个 LLM-authored 的更好/更窄产品能插进去。gumtrends 甚至把「% mixed reviews」做成显式指标。

### ① OPERATION
**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "For the top-SELLING Gumroad products on '<topic>' (use gumtrends.com which shows a '% mixed
  reviews' / 2-4 star metric alongside sales & revenue): identify products that have HIGH sales/revenue but a
  MEDIOCRE quality signal — average rating <=~4.3, a notable % of 2-4 star reviews, thin/short content, or
  outdated material. Read their actual reviews and quote the recurring complaints and the 'I wish it had…'
  requests. Separately confirm the topic is NOT dominated by a single >=4.7-star, hundreds-of-ratings, cheap
  product that everyone already buys." \
  --accept "For the top sellers: sales/revenue proxy + rating + % mixed reviews, PLUS quoted recurring buyer
  complaints/unmet wishes that a better product could fix — OR an explicit 'top sellers are uniformly
  excellent (>=4.7, low price, deep) = no wedge' verdict."
```
**(ii) 可观测读数**：头部**卖得动**的品里有 rating ≤~4.3 / 高 % mixed reviews / 内容薄旧的；评论反复出现可被修复的抱怨与「wish it had…」。
**(iii) 决策阈值**：
- **KEEP（已证明但可打）**：≥1 个在位者**有真实销量**（ratings/估算）**且**评价平庸或有复现抱怨、内容单薄/过时 → 有更窄/更好/更新的楔子（LLM 原生擅长补齐内容质量）。
- **DROP（饱和）**：头部全 ≥4.7★、数百 ratings、低价、评论无明显未满足抱怨（见方法 4）。

### ② PHILOSOPHY BACKING
> "mixed reviews combined with high sales/revenue indicate a market exists even for non-excellent products."（gumtrends.com）——平庸但卖得动 = 需求被证明 + 供给留缝，正是 headless agent 该切入的点。挖抱怨的方法 r3 已给（"top 3 things customers wish this product had"）。

### ③ HUMAN→AGENT 替代
- **人类**：老手读几页差评就知道「这品有人买但做得烂，我能做更好」。
- **agent**：派研究 Goal 用 gumtrends 的 % mixed reviews + 逐条 review 挖复现抱怨，把「读差评找缝」外包成一次网页观察；补内容质量本就是 LLM 强项。

### ④ 三道检验裁定：**过 (a)(b)(c)** — (a) 销量/评分/% mixed reviews/评论全可观测；(b) 压制「挑评分最高最火的做同款」（那是撞饱和）；(c) 非平凡：把「平庸但卖得动=机会、优秀且饱和=DROP」这条反直觉取舍显式化，并用 Gumroad 特有的 % mixed reviews 指标锚定。

---

## KEPT 方法 4 · Gumroad 饱和闸 + 外部需求闸（Opportunity Score 反信号）

**一句话**：Gumroad 特有的诚实闸——因为站内**不推流**，光看站内竞品数会误判；必须把**外部话题需求**（搜索/社媒，Gumroad 销量的真燃料）÷ **站内供给密度**（有真实 ratings 的竞品数 × 平均 ratings/品）来判饱和。低 = 塞满，高 = 需求强而供给弱。

### ① OPERATION
**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "Assess whether '<topic>' is a winnable Gumroad opportunity or saturated. Report: (1) EXTERNAL
  demand — approximate Google Trends interest (0-100) and whether people actively search/discuss buying help
  on this topic (Gumroad has weak organic discovery, so external demand is what feeds sales); (2) ON-GUMROAD
  supply density — how many products have ANY real ratings/sales (ignore zero-sale dead listings), and the
  AVERAGE ratings-per-product among the established ones; (3) whether the top few are all >=4.7 stars with
  hundreds of ratings at low price. Then judge: is this high-external-demand + weak/mediocre supply, or is it
  a wall of established competitors?" \
  --accept "External-demand read + on-Gumroad supply-density read (competitor count with real ratings + avg
  ratings/product), and an explicit saturated-vs-winnable verdict with the counter-signal noted."
```
**(ii) 可观测读数**：外部搜索/讨论热度 vs 站内**有真实 ratings 的**竞品数 × 平均 ratings/品。Leandro 的比值直觉：`Opportunity ≈ 外部 Interest / ((有效竞品数 × engagement) + 1)`。
**(iii) 决策阈值**（Leandro 校准，作数量级锚）：
- **DROP（饱和）**：比值低（Leandro <5）——如 "36 competing products with 16.8 average ratings per product"，头部 74 ratings ≈500–1000+ sales。原话警示："You're not competing with 36 products. You're competing with 36 established businesses"（各带 affiliate 网络 + email list，而你 0 review / 0 SEO / 0 remarketing）。
- **DROP（外部无需求）**：站内看着有品但外部 Google 兴趣极低 → 站内无流可导，headless agent 尤其死。
- **KEEP（可打窗口）**：外部需求强（Interest 高）**且**站内有效竞品少/评价平庸（Leandro >20 = high demand weak competition）；偏好 "emerging tech (tools launched in last 6 months)" 与 "hyper-specific sub-niches"。**红旗**（Leandro 点名）：泛泛 "Notion templates" / "ChatGPT prompts" = 已饱和，别碰。

### ② PHILOSOPHY BACKING
> "Opportunity Score = Interest / ((Products × Engagement Factor) + 1)… below 5 = saturated… >20 = high demand, weak competition… You're not competing with 36 products. You're competing with 36 established businesses."（Leandro Calado, *I Analyzed 36 "Hot" Products on Gumroad*）。叠加 F1：Gumroad 无 organic discovery → **外部需求必须单独测**，不能只数站内。

### ③ HUMAN→AGENT 替代
- **人类**：老卖家一眼看出「这类已经 36 个大佬各自 email list 几万，别碰」或「这词外面天天有人搜、Gumroad 上却没人做好」。
- **agent**：把「红海嗅觉」拆成外部需求 + 站内有效供给密度两个可观测量派 researcher，用 Opportunity 比值替代直觉。

### ④ 三道检验裁定：**过 (a)(b)(c)（尤其 c）** — (a) 外部兴趣 + 站内有效竞品/平均 ratings 全可观测；(b) 压制 LLM「需求被证明就冲 / 进个 AI 热门类」的乐观默认；(c) 最非平凡：Gumroad 特有的「外部需求÷站内供给密度」比值 + 「上架数≠竞争、要数有 ratings 的」+「泛类=红海红旗」，LLM 绝不会自发采用。

---

## KEPT 方法 5 · 形状 & 价格 & 流量可达性闸（选 WHAT 与「够不够得着买家」）

**一句话**：Gumroad 特有的选择约束——只挑**同时满足**「Gumroad 上卖得动」+「LLM agent 无受众也能独立写出来」+「有一条 headless agent 够得着的流量路径」的产品形状。这不是需求探针，而是把前四条筛出的机会**收敛成能真正落地变现的那一类**。

### ① OPERATION
**(i) 研究-Goal 模板**：
```
python3 -m orchestration.messaging send --to researcher \
  --intent "For the SELLING products on '<topic>' on Gumroad, report the SHAPE and PRICE of the ones that
  actually have sales/ratings: are they mini-guides/ebooks, Notion templates, prompt packs/libraries, swipe
  files, playbooks, printables/planners — or are they courses/software? Report the typical price band. Also
  assess the TRAFFIC path: is this topic actively searched on Google (so SEO content could drive buyers), and
  do same-topic products show pull inside Gumroad Discover (Best Sellers/Rising Stars) — OR do the sellers
  appear to rely purely on a personal social/email audience?" \
  --accept "The dominant SELLING shape + price band for the topic, PLUS a traffic-path verdict: reachable via
  SEO content and/or Discover pull, vs audience-only (which a headless, audience-less agent can't feed)."
```
**(ii) 可观测读数**：该选题里**有销量的**产品是什么形状、什么价位；以及买家能否经「Discover pull（方法 2）或 SEO 可捕获的外部搜索需求（方法 4）」到达。
**(iii) 决策阈值**：
- **KEEP 形状**：mini-guide/ebook（$10–49）、Notion 模板（$9–29，bundle $35–79）、prompt pack/library、swipe file、industry playbook、planner/printable——都在 **$9–49、≤$100（Discover）** 带内；文本-native agent 能独立产出。
- **DROP 形状**：**course**（均仅 115 sales 且 "need an existing audience to sell"，且偏视频）、**software/micro-SaaS**（需工程+持续支持）。
- **DROP 价格**：$1–5（"$1 template → $0.05 after fees"）。
- **KEEP 流量**：话题可经 SEO 内容捕获（部门能写）**或** Discover 里有同题 pull → headless agent 够得着买家。
- **DROP 流量**：卖家全靠个人社媒/邮件受众、站内无 pull、外部搜索也弱 → agent 无受众喂不动，即便需求真也拿不到（F1 catch-22）。

### ② PHILOSOPHY BACKING
> "Courses average only 115 sales… and need an existing audience to sell"（vs digital downloads 均 293 sales @ $47.14）；"$29 sweet spot drives volume… $19–39 hit the impulse-buy threshold"；"A $1 Notion template resulted in only $0.05 after fees"。叠加 F1：Gumroad 是 storefront 不是 marketing team，"You bring the customers"——所以流量可达性是硬闸。

### ③ HUMAN→AGENT 替代
- **人类**：创作者靠自己的受众/社媒把任意形状（含课程）推出去。
- **agent**：无受众。改为**只选它能独立写、且买家能经 SEO 内容或 Discover 到达**的小型文本产品；用「有销量产品的形状」反推该做什么形状，而非凭 LLM「做门大课」的野心通胀。

### ④ 三道检验裁定：**过 (b)(c)（(a) 部分）** — (a) 有销量产品的形状/价位/流量路径可观测、可由部门落地；(b) 强压 LLM「做门大课/大而全产品」的默认，钉死在小型文本形状 + 影响-buy 价带；(c) 非平凡：Discover ≤$100 上限、$1–5 被 fee 吃穿、course 需受众、以及 headless-agent 的**流量可达性闸**（无受众就 DROP audience-only 机会），都是 LLM 不会自发采用的 Gumroad 取舍。

---

## DROP 清单（Gumroad 特定的坑 / 纯美德，不写进 skill）

| DROP 项 | 为什么 DROP |
|---|---|
| **「上架就靠 Discover 带量」** | Discover 只 ~10–20% 收入，且 catch-22（要先出一单才被 discover），90% 靠自带流量。作 demand 策略 = 幻想。 |
| **「上架数=竞争，3–10 个竞品就是需求证明」（不看 ratings）** | Gumroad 上架严重灌水：profitable 全站 4.2M 上架仅 478.6K 有销或评。必须只数**有真实 ratings/销量**的品。 |
| **「进个热门 category 就行」/ 泛做「Notion 模板」「ChatGPT 提示词」** | 正是 LLM 默认吐的红海；Leandro 明确点名为 saturated 红旗。要窄到 hyper-specific sub-niche。 |
| **「category 级增长趋势（marketsy gumroad-trends）」当选品证据** | 只有类目增长%、无单品销量/评分——太粗，只能作方向感。 |
| **「定 $1–5 低价走量」** | fee 吃穿（$1→$0.05）；且 ≤$100 才进 Discover。价带钉 $9–49。 |
| **「星级高=质量好，跟着高星做同款」** | Gumroad 星级四舍五入（4.37→5★）、评论排序偏正，高星不等于真质量；且跟高星做同款=撞饱和。作反信号，不作追逐目标。 |
| **「做门课 / 做个 SaaS」** | course 均 115 sales 且需受众；software 需工程+支持。文本-native、无受众 agent 不适配。 |
| **「跑问卷 / 问受众 / presell」** | agent 无受众（r3 已 DROP，Gumroad 层重申）。被 Discover 榜 + ratings + 第三方估算取代。 |

---

## Sources 表（实拉，2026-07-02）

| # | 借用/证据 | 来源 | 抓取方式 |
|---|---|---|---|
| S1 | Gumroad 零 organic discovery / "26 products… zero organic views… catch-22 designed to reward existing sellers" | Indie Hackers, *Gumroad has zero organic discovery* (indiehackers.com/post/…e9c4d8b629) | WebFetch |
| S2 | 销量来源：Discover ~10–20% / organic search 12% / email 42% / social 23% / "You bring the customers" | mydesigns.io/blog/gumroad-for-selling-digital-products + medium (Tanmoy Das / Travis Nicholson) | WebFetch + WebSearch 摘要 |
| S3 | Discover 准入（$10、≤$100、展示星级、category+tags、风控）/ 现行费率 flat 10% 直销 · 30% Discover / 旧分级 13.5%·18.5%+$0.30 / 个人 Discover 116 views 24 downloads | whop.com/blog/gumroad-tutorial + amypeniston.com/blog/selling-on-gumroad | WebFetch |
| S4 | Discover 排序 Best Sellers/Hot&New/New&Trending(9mo)/Rising Stars/Recurring Revenue + 筛选(tag/type/format/price/rating) / 18 category / 排名偏好(sales history+ratings+description+cover) / curated sort | WebSearch 摘要（gumroad discover 系列）+ gumroad.com/discover?sort=curated | WebSearch |
| S5 | 产品页公开 star+ratings 数 / 销量部分公开(MacWhisper 223,515 sales·1715 ratings) / 只买家能 rate / 评论排序偏正 / 星级四舍五入(4.37→5) | foliovision.com/2025/06/negative-reviews-gumroad + help.gumroad.com/article/222(经转述) | WebFetch + WebSearch 摘要 |
| S6 | gumtrends：为所有产品估销量("only ~10% display sales… we estimate for all") / 字段含 % mixed reviews / "mixed reviews + high sales = market exists for non-excellent products" / 示例 20,223 sales·$262,899 | gumtrends.com | WebFetch |
| S7 | profitable.app：4.2M tracked vs 478.6K with sales/ratings / 销量·收入估算 / "9 months + 20+ sales = early PMF" / Best Selling·Rising Stars 排序 | profitable.app/gumroad | WebFetch |
| S8 | Opportunity Score = Interest/((Products×Engagement)+1) / <5 饱和 >20 可打 / "36 established businesses" / 74 ratings≈500–1000 sales / 泛 Notion·ChatGPT 红旗 / emerging tech + hyper-specific | Leandro Calado, *I Analyzed 36 "Hot" Products on Gumroad* (leandrocaladoferreira.medium.com/…4861ac7fcb96) | WebFetch |
| S9 | 形状/价格：digital downloads 85%·均 293 sales@$47.14 / Writing&Publishing $15,750/品 / Courses 115 sales@$95.74 需受众 / $29 sweet spot·$19–39 impulse / $1→$0.05 after fees / 六类 AI 产品 $500–1500/月 | WebSearch 摘要(accio/conversionproplus) + kupkaike.com(Notion 价带 $7–79·窄类) + digitalapplied.com | WebSearch + WebFetch |
| S10 | marketsy gumroad-trends 只有 category 级增长%（无单品数据） | marketsy.ai/tools/gumroad-trends | WebFetch |

## Caveats
- **费率有版本差**：现行主流报道为「直销 flat 10% + Discover 归因 30%」；amypeniston 沿用旧分级 13.5%/18.5%+$0.30。skill 正文用「约/量级」措辞，动笔前若引具体数字应二次核 Gumroad 官方 help（本次官方 help 页 WebFetch 被登录墙挡，数据取自多篇一致转述）。
- **ratings→销量倍率不可硬编**：观测到 7×~170× 巨幅波动（价位/类目相关）。number of ratings 只作**序数下界代理**；要硬数字用 gumtrends/profitable 估算。
- **第三方估算工具（gumtrends/profitable）本身是估算**，方法论未完全披露；作代理够用，别当账面真值。
- **star rating 有系统性偏高**（四舍五入 + 正评优先排序）——读评价时须显式要求 researcher 挖 2–4 星 / 差评，别信页面顶部星数。
- 所有阈值（≥3 卖家、≥20–50 ratings、Opportunity <5/>20、$9–49、≤$100）为**近似经验锚**，skill 正文措辞为「约/数量级」。
- 思想来源署名引用，不逐字拷进 skill 正文。
