# Growth Role — 设计

> 依据 `prd.md` + 本 session 收敛 + 父任务 `research/skill-reuse-survey.md` + 本任务 `research/env-outbound-interface.md`（CUA）+ `research/growth-skill-scout.md`（vendor 侦察）+ `../07-02-visual-asset-skills/research/visual-asset-skills-research.md`（视觉三原子调研，随子任务迁移）+ `.trellis/spec/backend/peripheral-layer-contracts.md`。
> 纪律：**赋能 > 限制**；原子可组合；**①系统特定 / ②压制 LLM 残余默认 / ③非平凡信号** 三道过滤；防御没观测失败押后。
> ⚠️ 本版**取代** session 早期的"4 块扁平 skill"框架，并按两条 research **回填**（CUA outbound + de-AI-ify 改 vendor）。

## 0. 收敛后的核心

Growth = **真实世界执行者（内容 + 运营）**，不是内容生成器。最缺的不是文采，是**环境**（账号/工具）与**把关**（去 AI 味/真实信号）。

两大事：
- **A. 做优质内容** — 想法 → 够好、不带 AI 味、图文结合的内容。
- **B. 运营内容与账号** — 通过真实账号把内容推出去、持续运营。

落地 = **原子化可组合 skill**（乐高砖），growth 按判断**现场组合**，不写巨石、不规定死流程（本身就是"少给边界"）。

## 1. 系统事实（赋能前提，已核实）

- growth = 常驻 `claude -p` session，`receive-goal` 驱动、`/company` 共享状态。resident 模型让"持续运营"成立（heartbeat 可唤醒看信号/互动）。
- 物化 `shutil.copytree` **递归** → 多文件 skill（`SKILL.md` + `references/`）可用。
- **外设层 inbound**：外部信号/goal-completion 塌成 5 字段 IME 落 inbox（147 测试）。`adapters/` 只有 webhook + email，**无社媒 outbound**。
- **outbound = MCP 优先（设计方向，用户定）**：发布/操作账号**优先用 MCP**——平台/账号 MCP、软件 MCP，或**自写轻量 MCP/skill**。**Computer Use（CUA）= 低效回退**（token 消耗最大、最不稳定），仅在某平台无 MCP 时兜底。现状核实（`research/env-outbound-interface.md`）：环境**当前只 wire 了 CUA**（`cua_mcp.py`：`screenshot/click/type/press_key`）→ MCP-first 意味着要**选/装/写账号 MCP**，未定，需再看（§10 Q1）。本地 `wechat-desktop` 是 CUA 范式，仅作**回退路径**的结构样板。
- **subscription-only 的边界**（澄清）：`cua_mcp` 刻意不套第二个 *orchestrator* LLM——这不等于禁止装**能力工具**（生图等）。给 agent 装 GPT image-gen 之类工具 OK（§5.5）。
- 账号 + 视觉工具**假设已装/已存在**，本任务不 provision，只教怎么用。

## 2. 两个立场修正（本 session 纠正，写进 charter + skill）

### 2.1 verifier 独立，growth 不喂 proof
- **作废** session 早期的"发布→写 proof 到 /company → verifier 核验"：doer 给 judge 递材料 = 破坏分权。
- **正**：growth 只**做事 + 记真状态**；verifier 读 Goal 后**独立核查**（自己登号 / 用读取类 MCP / 兜底 CUA 截图看帖子在不在）。
- **落到 skill**：发布路径**无**任何"为 verifier 产 proof"步骤。

### 2.2 `/company` = 状态（名词），非证明接口
- 不堆 proof receipt / 流水。只更新**公司现在是什么**（positioning、渠道 presence、当前 campaign）。呼应 `foundagent-layer-decoupling`。

## 3. 跨角色边界

- **落地页 / 部署 / 产物 = Builder**，取决于 CEO 定义产物。growth 产**内容 + asset**；需落地页时以 **sub-goal 建议交 CEO**（matrix，不 P2P）。
- **账号 provisioning = 外设/peripheral**，不属本任务。

## 4. skill 模型：原子 + 可组合（backlog，research 回填后）

每个 skill = 单一能力，可现场拼。**vendor 为主、gap 处自写**（research 证实内容侧大半可 vendor）。

| skill | 归属 | 来源 | ①/②/③ 依据 | 状态 |
|---|---|---|---|---|
| `de-AI-ify` | A | **vendor**：`blader/humanizer`(MIT,27k★) 骨架 + 合并 marketingskills 词替换表 + 裁百科垂类；中文另 vendor `qu-ai-wei` | ②残余默认（AI 味）——**内容开源已备齐、非自写** | v1 |
| `mine-customer-voice`（§5.6） | A | **vendor**：coreyhaines `customer-research` + `social/references/listening*.md`（curl 配方） | ③采集配方（搜索算子/subreddit 清单/3星评论法）+ ②压制"凭默认知识编文案"的残余 | v1（07-02 二次修订的核心） |
| 方法类 catalog（post/thread/carousel/caption/短视频写法） | A | vendor 候选已调研（blacktwist + coreyhaines，见 `research/social-vendor-compare.md`） | 缺口分析（`research/copy-capability-gaps.md`）：非真缺口 | **降级 backlog**，按需再加 |
| `copywriting`(+`copy-editing`) | A | **vendor**：coreyhaines，**只留具体表**（CTA 词表/headline 公式/weak→strong/Seven Sweeps） | ③非平凡信号，抽象原则句剔除 | v1 或近 backlog |
| `design-asset`（视觉三原子①） | A | **混合 vendor**：anthropics frontend-design + jiji262 两文件 + theme-factory 色板 + guizang 风格系统（拍板解禁）+ superdesign token 表提取（拍板解禁） | ①静态资产编排/渲染管线 ②压制 AI 默认审美 ③风格系统与数字阈值（§5.5） | ✅ 07-03 落地（子任务 07-02，AC4/6 半开见其 prd） |
| `gen-image`（视觉三原子②） | A | **混合 vendor**：smixs/visual-skills 整树 + JunSeo99 Codex 闭包；调用 wrapper 自写（**API 主路径 / Codex 副路径**） | ①工具调用与模型路由 ②压制空洞 prompt、文字重活禁走生图（§5.5） | ✅ 07-03 落地（子任务 07-02，API-key blocker 见其 prd AC4） |
| `visual-iterate`（视觉三原子③） | A | **vendor** guizang 迭代三件（拍板解禁）+ 自写 loop 编排 | ③终止阈值/评审 rubric ②压制"自评即过"（§5.5） | ✅ 07-03 落地（子任务 07-02，全链 e2e 一轮闭环实测） |
| `use-accounts` | B | **自写**，写 against **平台/账号 MCP（优先）**；CUA 仅低效回退 | ①各账号 MCP 工具用法 + 平台发布机制；CUA 兜底范式参考 `wechat-desktop` | v1（依赖装哪些 MCP，§10 Q1） |
| content-strategy、hook/thread、一稿多平台、voice 匹配 | A | vendor 选搬 | ③信号 | 押后 |
| cadence、engage、read-signal（闭环） | B | 自写 | ③阈值（observation-gated） | 押后 |
| cold-email / SEO / CRO / landing / 变现 | 渠道变体 | vendor 为主 | — | 押后 |

**v1 最小集（待 §10 拍）**：内容侧 `{de-AI-ify, social, (copywriting?)}` + `visual-asset` + 运营侧 `use-accounts`。若求最窄，可先 `{de-AI-ify, social, visual-asset, use-accounts}`。

## 5. `de-AI-ify` 详设（改 vendor+裁剪，research 回填）

**为什么仍是正当的②**：LLM 默认输出本身带 AI 味，强模型也扛不过、headless 压不掉——正是②该管。**但 research 证实：这块的非平凡内容开源已备齐，不该从零自写。**

**方案 = vendor 骨架 + 合并 + 裁剪 + 双语**：
- **骨架**：`blader/humanizer`（MIT, 27k★，基于 Wikipedia「Signs of AI writing」，33 个编号 pattern，每个带 words-to-watch + **Before/After 反例**）。拷进 repo、标来源。
- **裁**：删百科垂类 pattern（notability/media、challenges-future、knowledge-cutoff），只留通用 style/language（em-dash、rule-of-three、-ing 堆叠、promotional、negative parallelism、hedging、signposting、aphorism…）。
- **合并**：把 `marketingskills/seo-audit/references/ai-writing-detection.md` 的 **weak→strong "use instead" 替换表**并进来（blader 只列 words-to-watch、缺替换项）+ `copywriting/references/natural-transitions.md` 的 "Transitions to Avoid" 段。三者皆 MIT。
- **保留**：blader 的 **Detection Guidance / What-NOT-to-flag 假阳性清单**（防过度去味把人味也删了——这条本身就是"少给边界"）。
- **双语**：公司中英双语（用户中文沟通），若 Growth 产中文内容，另 vendor `LifelongLazyLearner/qu-ai-wei` 或 `B1lli/remove-ai-flavor-writing-skill`（均 MIT）。英/中各一套 reference。
- **自写增量收缩为**：裁剪合并 + 双语组织 + 接我们 voice（读 `/company`）。不给死模板（死模板会把 AI 味写回去）。

## 5.5 visual-asset → 三原子 skill（07-02 调研回填 + 单拆子任务）

**已单拆子任务 `../07-02-visual-asset-skills`**（用户定）：需求/AC/详设/实施清单/调研报告均在子任务。本节只留父层边界：

- **口径**：~~自写·复合~~ → **混合 vendor + 自写编排/调用层**；单复合 skill → 三原子 `design-asset` / `gen-image` / `visual-iterate`（原 (a)(b)(c) 三分法一一对应：(b)→design、(a)→gen、(c)→iterate）。
- **生图**：**API 主路径（OPENAI_API_KEY 直连）、Codex 订阅 wrapper 副路径**（feature flag；对抗复核结论见子任务 research §4.4；本机 e2e 已通）。
- **组合关系**：design-asset 产 HTML 资产 → 需插画/底图时调 gen-image → visual-iterate 把关收敛；组合指引写各 host SKILL.md，不写死流程。平台尺寸/brand 读 `/company`。
- **许可证例外**：guizang（AGPL）/superdesign（无 license）用户拍板解禁（内部使用，ATTRIBUTION 注明，§8）。
- **依赖/provisioning（假设已装，归属见 §10 Q2）**：OPENAI_API_KEY、Playwright + 浏览器；副路径另需 `codex login`。

## 5.6 `mine-customer-voice` 详设（07-02 二次修订，取代"4 原子混合 vendor"）

**修订依据**：用户叫停后回到 brainstorm，从"Claude 已经会什么"倒推缺口（全文 `research/copy-capability-gaps.md`）：真缺口 = ①voice 冷启动 ②客户原话（VOC），而非写作方法论。方法类 catalog（上午的 draft-social 等 4 原子）**降级 backlog**；本节取代上午的 §5.6（其取舍分析仍见 `research/social-vendor-compare.md`，再引入零成本）。

**核心**：教会 growth 在动笔前"偷话"——去 Reddit/G2/HN/评论区采集客户描述问题的**原话**，存成 `/company` 里的客户语言库，写文案时从库里取，不凭默认知识编。

**落形（de-ai-ify 模式：host SKILL.md = 唯一原创适配层，上游 verbatim 进 `references/`）**：

| 内容 | 来源 |
|---|---|
| `references/customer-research.md` | coreyhaines `customer-research/SKILL.md`（11.9KB：榨现有材料 + 出门采两模式、JTBD/痛点/language-used 抽取框架、频率×强度汇总模板） |
| `references/source-guides.md` | 同 skill `references/source-guides.md`（16.2KB：Reddit 搜索算子/subreddit 清单/高信号帖型、G2 三星评论法、HN/PH/YouTube/LinkedIn 各一套） |
| `references/listening.md` + `listening-sources-template.md` | coreyhaines `social/references/`（Reddit/HN/Bluesky **curl 配方** = 程序化采集管子，与 source-guides 的"去哪找/抽什么"互补） |

**host 层职责**：
- 何时采：给一个方向/细分写文案而 `/company` 还没有对应客户语言时；进入新细分时。
- 交付物改写：上游产"给营销团队的调研报告/persona"→ 我们产**客户语言库文档写进 `/company`**（按方向/细分组织，**具体落点 growth 自研自定**，不硬编码路径——呼应记忆层"主题由 agent 自划"）。
- **voice 冷启动（用户 07-02 拍板：growth 职责）**：公司还没有 brand voice 时，growth 从采到的客户语言 + `/company` 定位里**自己推导一版 voice 写进 `/company`**（位置同样自定）；后续写文案读它、发现失真就更新它。charter 的职责清单同步加这一条（§7）。
- 统一适配照旧：上游 `.agents/product-marketing.md` 读取 → 读 `/company`；listening 的 `.agents/listening-sources.md` 源清单 → `/company` 里的文档；无任何"喂 proof"步骤，采到的持久事实写 `/company`（状态，非流水）。

**验证（场景倒推）**：盲评 sub-agent 走 `公司定了方向 X → goal：发第一条 launch 帖` 全链：缺 voice → 采话 → 定 voice → 取材写稿 → de-ai-ify。

**gap 记档**：来源均为英文水位（Reddit/G2/HN）；中文水位（小红书/知乎/即刻）绑批2 中文平台方向再议。

## 6. 组合示例（验证"原子+可组合"形状）

Goal「发一条关于 X 的帖」= growth 现场组合：
```
social/copywriting（起草）→ de-AI-ify（去味）→ design-asset/gen-image/visual-iterate（配图，按需组合）→ use-accounts:X（CUA 发布）
```
每 skill 单一职责，编排靠 charter 取向 + growth 判断，**不写死进 skill**。

## 7. charter 增量（placeholder → 真）

`assets/growth-charter.md` 重写（遵父任务通用结构，赋能式）：身份（内容+运营执行者）/ 两大事取向 / 原子 skill 自主组合（列能力、指向 skill、不规定固定流程）/ **brand voice 由 growth 自定并维护进 `/company`（位置自研，§5.6）** / company-state 只记状态（§2.2）/ 不给 verifier 喂 proof（§2.1）/ 跨职能交 CEO（§3）。无防御短句堆砌。

## 8. vendor 策略（research 落实）

统一：拷进 `agents/assets/skills/` + 保留 `LICENSE` + 标来源。

**⚠️ vendor 完整性（de-ai-ify 盲评教训）**：vendor 一个 skill = 带上**整个依赖闭包**，不是拷几个叶子 reference。叶子文件常依赖 ①兄弟文件 ②上游 SKILL.md 里的控制层（如激活矩阵/仲裁顺序）。只拷叶子会留死链、并丢掉 reference 赖以工作的机制。若上游本身自包含，最省事是**整份 intact vendor 进子目录**（de-ai-ify 把 `qu-ai-wei` 整份放 `zh/`）。写完最好派无上下文盲评实测。

三处适配：
- **product-marketing 上下文重接**：coreyhaines 每个 skill 开头读 `.agents/product-marketing.md`（其 product-marketing skill 产出的共享上下文）。vendor 时**改指向我们 `/company` state 路径**（或引入一个等价的 company-memory 读取约定）。这是跨所有 vendor skill 的统一改动。
- **剔泛泛**：逐条删 LLM 自带的营销常识句，**只留表格/公式/反例**（价值密度所在）。
- **最高价值 drop-in（即使不引整 skill 也先拷）**：`seo-audit/references/ai-writing-detection.md` + `copywriting/references/natural-transitions.md` → 直接喂 de-AI-ify。
- 许可证注意：`academic-humanizer` 等为 NOASSERTION，**不用**。**用户拍板例外（2026-07-02，内部使用）**：guizang（AGPL-3.0）、superdesign（无 license）解禁可用，ATTRIBUTION 注明原许可证状态 + 拍板日期；未来对外分发本 repo 需回头处理（research 附录 A 有记录）。

## 9. 声明式落点（零 .py 逻辑改动）

- `agents/growth.yaml`：`skills:` 追加 v1 新条目（保留 `company-state` + `receive-goal`）。
- `agents/assets/growth-charter.md`：重写（§7）。
- `agent/tests/test_resident_loadout.py`：断言 growth 挂新 skill、带 `references/` 多文件 skill 物化存在。
- 无 `agent/*.py` 逻辑改动。

## 10. Open Questions（review gate）

1. **outbound = MCP 优先（用户定），但具体未定**：装哪些平台/账号 MCP？哪些自写轻量 MCP/skill？CUA 仅低效回退。当前只 wire 了 CUA → 需 MCP provisioning（infra，可能属兄弟任务）。**需再看**——决定 `use-accounts` v1 写 against 什么、甚至是否随 MCP 就绪再落。
2. ~~visual-asset 单机制~~ → ~~复合能力~~ → **已收敛（07-02 调研回填 + 用户确认）**：一拆三原子 + 混合 vendor（§5.5）；生图**主路径 = OPENAI_API_KEY 直连（gpt-image-1-mini $0.005/张起）、Codex 订阅 wrapper 仅副路径**（对抗复核：官方推 API 自动化、ToS 灰、配额 3-5x 共享，research §4.4）。剩余：**provisioning 归属**——OPENAI_API_KEY 供给、Playwright 浏览器、codex login（交互式 OAuth 的无头冷启动）属本任务还是 infra 兄弟任务。
3. **v1 最小集**：`{de-AI-ify, mine-customer-voice, 视觉三原子(design-asset/gen-image/visual-iterate), use-accounts}`（含不含 copywriting/copy-editing）？~~若 visual-asset 走 D~~（已过时：三原子 v1 方向已定，§5.5）。
4. ~~de-AI 有无现成~~ → **已解**：`blader/humanizer` 等现成，改 vendor（§5）。
5. **copywriting ↔ de-AI-ify 边界**：`natural-transitions.md` 的 AI-tell 段与 de-AI-ify 重叠 → 归口 de-AI-ify，copywriting 只留正向表。
6. **product-marketing 上下文重接**：`.agents/product-marketing.md` 约定改指 `/company`，还是引入 product-marketing skill？（§8）
</content>
