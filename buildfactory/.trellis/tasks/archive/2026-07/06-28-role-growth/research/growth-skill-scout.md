# Research: Growth 角色 skill 复用侦察（两条开源线）

- **Query**: 为 Growth 常驻 agent 的「原子化、可组合」skill 做复用决策。线1=`coreyhaines31/marketingskills` 拆解；线2=de-AI/humanize skill 现状 + AI-tell 清单
- **Scope**: external（GitHub repos + raw 文件真实内容，非印象）
- **Date**: 2026-07-01
- **判据（贯穿全文）**: 目标 agent 本身是 Claude(LLM)。只有「系统特定接口 / 压制 LLM 残余默认 / 带反例的非平凡信号」才值得复用；泛泛营销常识 = LLM 自带 = 不拷。

---

## 线 1：`coreyhaines31/marketingskills`

### 仓库事实（已核实真实内容）

| 项 | 值 |
|---|---|
| URL | https://github.com/coreyhaines31/marketingskills |
| 许可证 | **MIT**（Copyright (c) 2025 Corey Haines）— 可 vendor，保留 LICENSE + 注明来源即可 |
| plugin 版本 | 2.5.1（`.claude-plugin/plugin.json`，name=`marketing-skills`） |
| skill 数量 | **45 个** |
| 目录结构 | `skills/<name>/SKILL.md` + `evals/evals.json` + `references/*.md`（部分 skill 无 references） |
| 外部依赖 | **无 API key、无脚本**。纯 Markdown 方法论 + reference。唯一软依赖：每个 skill 开头都 `Check for .agents/product-marketing.md`（product-marketing skill 产出的上下文文件），这是 repo 内部的组合约定，不是外部服务 |
| 兼容性 | 声明遵循 Agent Skills spec（agentskills.io），Claude Code / Codex / Cursor / Windsurf 通用 |
| frontmatter 形态 | `name` + 很长的 `description`（塞满触发关键词，含大量 "when the user says ..." 同义触发词）+ `metadata.version`。**没有** allowed-tools 字段 |

全部 45 个 skill：ab-testing, ad-creative, ads, ai-seo, analytics, aso, churn-prevention, co-marketing, cold-email, community-marketing, competitor-profiling, competitors, content-strategy, copy-editing, **copywriting**, cro, customer-research, directory-submissions, emails, free-tools, image, launch, lead-magnets, marketing-ideas, marketing-plan, marketing-psychology, offers, onboarding, paywalls, popups, pricing, product-marketing, programmatic-seo, prospecting, public-relations, referrals, revops, sales-enablement, schema, seo-audit, signup, site-architecture, sms, **social**, video。

### copywriting（v2.0.1）结构摘录

- **Body 组织**：Before Writing（读 product-marketing 上下文→4 组提问）→ Copywriting Principles → Writing Style Rules → Best Practices → Page Structure Framework → CTA Guidelines → Page-Specific Guidance → Voice/Tone → Output Format → Related Skills。
- **references**：`copy-frameworks.md`（headline 公式库 + landing page section 类型 + 页面模板）、`natural-transitions.md`（过渡短语库，**内含 "Transitions to Avoid (AI Tells)" 小节**，见线2）。
- **有价值（非平凡、压制 LLM 默认）**：
  - 具体 **weak→strong CTA 词表**（避免 Submit/Sign Up/Learn More；用 Start Free Trial/Get [X]）
  - **headline 公式**（`{Achieve outcome} without {pain point}`、`Turn {input} into {outcome}` …，在 copy-frameworks.md）
  - Writing Style Rules 里 **具体替换表**（utilize→use, facilitate→help, "remove exclamation points"）——这些是可执行的反-AI-默认清单，load-bearing。
- **泛泛（LLM 已会，不该拷）**：Clarity Over Cleverness / Benefits Over Features / Specificity Over Vagueness / One Idea Per Section 这类**抽象原则陈述**；4 组访谈式提问（大多是常识）。价值全在那几张**具体表**里，不在原则句。

### content-strategy（v2.0.0）结构摘录

- **Body 组织**：Before Planning（读上下文→4 组提问）→ Searchable vs Shareable → Content Types → Content Pillars/Topic Clusters → **Keyword Research by Buyer Stage** → Content Ideation Sources → Prioritizing（加权评分）→ Output Format → Related Skills。
- **references**：仅 `headless-cms.md`（CMS 选型，对我们基本无关）。
- **有价值（非平凡）**：
  - **Buyer-stage 关键词修饰词表**（awareness: "what is/how to"；consideration: "best/vs/alternatives"；decision: "pricing/reviews/demo"；implementation: "templates/tutorial"）——具体、可直接套。
  - **content-type 公式**（use-case = `[persona]+[use-case]`；hub-and-spoke URL 结构）。
  - **Forum research site: 查询**（`site:reddit.com [topic]`、`site:quora.com [topic]`）+ **加权评分模板**（Customer Impact 40% / Content-Market Fit 30% / Search 20% / Resources 10%）——现成 scaffolding。
- **泛泛（不该拷）**：Searchable vs Shareable 概念、"have opinions/tell stories"、Task-Specific Questions 列表——LLM 自带。

### drop-in 程度小表

| Skill | drop-in 程度 | 有价值部分（拷） | 泛泛部分（丢） |
|---|---|---|---|
| copywriting (2.0.1) | **near drop-in**（无 deps，仅软依赖 product-marketing.md 约定需适配我们的路径） | CTA 词表、headline 公式(copy-frameworks.md)、weak→strong 替换表 | 抽象原则句、访谈提问 |
| content-strategy (2.0.0) | **near drop-in** | buyer-stage 修饰词、content-type 公式、评分模板、forum 查询 | searchable/shareable 概念散文、提问列表 |
| copy-editing (2.0.0) | near drop-in | **Seven Sweeps** 框架、"cut these words" + weak→strong 表、Expert Panel 打分法 | "good editing enhances not rewrites" 类哲学 |

> 注：三者都以 `.agents/product-marketing.md`（或 `.claude/`、legacy `product-marketing-context.md`）为共享上下文入口。vendor 时要么一并引入 product-marketing skill，要么把该读取约定改写成我们公司 memory 层的 state 文件路径。

### 顺带扫「社媒发布/运营」相关 skill（一句话点评）

| Skill (版本) | 点评 |
|---|---|
| **social** (2.1.0) | 最直接相关：LinkedIn/X/IG/TikTok 内容 + 排期 + **short-form video 脚本** + **social listening/mention 监测/竞品监测**。值得单独细看，v1 大概率要 vendor。 |
| **launch** | 产品/功能上线的 GTM 编排，跨渠道；对「发布运营」有用。 |
| **ai-seo** + **seo-audit** | ai-seo=为 LLM 检索优化（被 LLM 引用）；seo-audit 的 `references/ai-writing-detection.md` = **线2 的金矿**（见下）。 |
| ad-creative / ads | 付费侧；Growth 若含 paid 再看。 |
| emails / cold-email / sms | 触达渠道文案；有具体 benchmark/subject-line 库。 |
| community-marketing / referrals | 社区运营/裂变，增长相关但优先级低。 |
| video / image | 生成素材的 spec/规格参考。 |

---

## 线 2：de-AI / humanize skill（去 AI 味）

### 结论先行：**不用从零自写**——有 27k★ MIT 现成骨架可直接 vendor + 改

### 2a. 现成开源 skill（可 vendor）

| Repo | ★ | 许可证 | 结构 / 特点 |
|---|---|---|---|
| **blader/humanizer** | ~27k | **MIT** | **首选**。单文件 `SKILL.md`（v2.8.2），基于 **Wikipedia「Signs of AI writing」(WikiProject AI Cleanup)** 权威指南。**33 个编号 pattern，每个带 Words-to-watch + Before/After 反例**——完全就是本任务想要的「具体 tell + 反例」形态。含 Voice Calibration（给写作样本对齐语气）、PERSONALITY AND SOUL（防「干净但没灵魂」）、Detection Guidance（**What NOT to flag 假阳性清单** + 人类写作特征保留）。frontmatter 带 `allowed-tools` + `compatibility: any-agent`。近 drop-in。 |
| Aboudjem/humanizer-skill | ~102 | MIT | 「43 patterns / 5 voices / 0–100 AI-tell score」有量化打分，可借鉴其 scoring 思路。 |
| brandonwise/humanizer | ~96 | MIT | OpenClaw skill，同类。 |
| LifelongLazyLearner/qu-ai-wei（去 AI 味） | ~157 | MIT | **中文**去 AI 味 skill。我们公司是中英双语（用户中文沟通），若 Growth 产中文内容值得 vendor。 |
| B1lli/remove-ai-flavor-writing-skill（去AI味） | ~132 | MIT | 中文 Codex 版，紧凑，含 template。 |
| academic-humanizer / humanizer_academic / humanizer-de | 50–124 | 部分 NOASSERTION（许可证不明，慎用） | 学术/德语垂类，对 Growth 营销文案不匹配。 |

> blader/humanizer 的 33 pattern 里有一批是 **Wikipedia/百科垂类**（#2 Notability&Media Coverage、#6 Challenges-and-Future-Prospects 段落、#21 Knowledge-Cutoff Disclaimers），对营销/社媒文案不适用，vendor 时应 **裁掉**；保留通用 style/language 类（em-dash、rule-of-three、-ing 堆叠、promotional language、negative parallelism、filler/hedging、signposting、aphorism 公式等）。

### 2b. AI 写作 tell 清单（自写/改写 skill 的原料，可直接用）

来源：`marketingskills` 的 `seo-audit/references/ai-writing-detection.md` + `copywriting/references/natural-transitions.md`（均 **MIT**，可 vendor）与 `blader/humanizer`（MIT）。三者合并去重如下。

**标点 / 排版层**
- **em-dash（—）滥用 = 头号 tell**（真人几乎不用，键盘无此键）。改用逗号/冒号/括号；超过每页 1 个就重写。en-dash 同理。
- 过度 boldface、inline-header 竖排列表、标题 Title Case、emoji、弯引号（curly quotes）——都是 tell。

**词汇层（动词）**：delve, leverage, utilise/utilize, facilitate, foster, bolster, underscore, unveil, navigate（喻义）, streamline, enhance, endeavour, ascertain, elucidate。
**词汇层（形容词）**：robust, comprehensive, pivotal, crucial, vital, transformative, cutting-edge, groundbreaking, innovative, seamless, intricate, nuanced, multifaceted, holistic；promotional 味：vibrant, rich(喻), profound, nestled, "in the heart of", renowned, breathtaking, must-visit, stunning, boasts a。
**过渡/连接词**：furthermore, moreover, notwithstanding, "that being said", "at its core", "to put it simply", "it is worth noting that", "in the realm/landscape of", "in today's [X]"。
**填充词/空强调**：absolutely, actually, basically, certainly, clearly, definitely, essentially, extremely, fundamentally, incredibly, interestingly, naturally, obviously, quite, really, significantly, simply, surely, truly, ultimately, undoubtedly, very。
**学术腔 tell**："shed light on", "pave the way for", "a myriad/plethora of", paramount, "pertaining to", "prior to", "subsequent to", "in light of", "with respect to", "in terms of", "the fact that"。

**句式 / 结构层（带反例）**
- **"not just X but Y" / "It's not just X, it's Y"**（negative parallelism / tailing negation）→ 直接正面陈述。
- **Rule of three 滥用**（凡事三段排比：`A, B, and C`）→ 打破三段惯性。
- **反射式 -ing 结尾堆叠**假深度：`..., highlighting/underscoring/reflecting/symbolizing/ensuring...` → 拆成独立句、给具体事实。反例：
  - Before: "...resonates with the region's beauty, symbolizing X, reflecting the community's deep connection to the land."
  - After: "The temple uses blue, green, and gold. The architect said these reference local bluebonnets and the Gulf coast."
- **虚假重要性拔高**：`stands/serves as`, `is a testament/reminder to`, `marks a pivotal moment`, `part of a broader movement`, `evolving landscape`, `setting the stage for` → 删掉宏大叙事，只留事实。
- **copula avoidance**（回避 is/are）：`serves as / stands as / boasts / features` 代替 "is a" → 改回 "is"。
- **万能收尾 / generic positive conclusion**：`In conclusion`, `To sum up`, `At the end of the day`, `By doing X, you can achieve Y` → 删或换具体下一步。
- **over-signposting**：`Let's delve into`, `It's worth noting that`, `This begs the question`, `In today's digital landscape` 开头 → 直接进入内容。
- **listicle/aphorism 反射**：`X is the Y of Z`, `X is not a tool but a mirror`, `the currency/architecture/language of ...` → 避免格言公式。
- **协作/谄媚残留**（LLM 对话腔漏进正文）：`I hope this helps`, `Certainly!`, `You're absolutely right!`, `Would you like me to...`, `let me know` → 正文中全删。
- **hedge 过量**：may/might/could/tends to/generally 成串堆叠 → 保留必要 hedge，删冗余。

**别误伤（假阳性 / 保留人味）**：em-dash/三段式偶发一次是正常人类写作；技术/法律/参考类文本「中性平实」本身就是正确人味，别硬塞第一人称和观点；短句+长句混排、真实观点、承认不确定、题外话/半成型想法 = 人类信号，要**保留**。

---

## 对本任务的建议

1. **de-AI-ify skill：改「自写」为「vendor + 裁剪合并」。** 以 **blader/humanizer**（MIT, 27k★, Wikipedia 权威 + 33 带反例 pattern）为骨架直接拷进 repo；裁掉百科垂类 pattern（notability/media、challenges-future、knowledge-cutoff）；把 `marketingskills/seo-audit/references/ai-writing-detection.md` 的 **weak→strong 词替换表**（它有 "use instead" 列，blader 只列 words-to-watch）合并进来补足可执行性。保留 blader 的 **Detection Guidance / What-NOT-to-flag**（防过度去味）。三者皆 MIT，注明来源即可。**结论：不该从零自写，非平凡内容开源已备齐。**
   - 若 Growth 要产**中文**内容，另 vendor `LifelongLazyLearner/qu-ai-wei` 或 `B1lli/remove-ai-flavor-writing-skill`（均 MIT，中文去 AI 味），英文/中文各一套。

2. **线1 v1 该 vendor 哪几个（按价值排序）**：
   - **优先拷两份 reference 文件**（价值密度最高、纯 drop-in）：`seo-audit/references/ai-writing-detection.md`、`copywriting/references/natural-transitions.md`——即使不引整个 skill，这两份也直接喂 de-AI-ify。
   - **social (2.1.0)**：社媒内容/短视频脚本/social listening，与 Growth 常驻职责最贴，建议细看后 vendor。
   - **copywriting + copy-editing + copy-frameworks.md**：vendor 但 **裁掉抽象原则散文，只留具体表/公式/Seven-Sweeps**。
   - **content-strategy**：**选择性搬**（buyer-stage 修饰词、content-type 公式、加权评分模板、forum 查询），丢弃概念性散文。

3. **vendor 时统一两处适配**：①把各 skill 开头 `.agents/product-marketing.md` 上下文读取，改指向我们 memory/company state 的实际路径；②按「no generic skills for LLM」原则，逐条剔除 LLM 自带的营销常识句，只保留系统特定 / 压制默认 / 带反例的信号——**价值在表格和反例里，不在原则陈述里**。

## Caveats / Not Found

- exa web_search 工具在本会话不可用；线2 的外部检索改用 **GitHub Search/Contents API（curl）**，star 数为查询时快照、可能波动。
- `academic-humanizer`、`humanizer_academic`、`humanizer-de` 许可证为 GitHub `NOASSERTION`（未识别标准 SPDX）——vendor 前需人工确认许可证，暂不推荐。
- `social`、`launch` 仅扫了 frontmatter/开头，未逐段拆解；标为「细看后再定」。
- content-strategy 的 `references/headless-cms.md` 与我们无关，未细读。
